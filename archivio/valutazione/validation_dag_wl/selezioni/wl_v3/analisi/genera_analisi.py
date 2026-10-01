"""Analisi riproducibile della scelta h, senza modificare gli esiti della validation."""
from pathlib import Path
import json
import statistics
import sys
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
sys.path.insert(0,str(REPO/"archivio/valutazione/test/strumenti"))
from common import read,save,sha
from dag_wl_validation import CANDIDATES, DESIGN, code_identity, summarize

def main():
    run=REPO/"archivio/valutazione/validation_dag_wl/esecuzioni/wl_v3"
    report=read(run/"riepilogo.json")
    contract=read(run/"contratto.json")
    if contract["code"]!=code_identity() or contract["design"]!=DESIGN:
        raise ValueError("Codice o disegno diversi dalla validation.")
    if sha(run/"contratto.json")!=report["contract_sha256"]:
        raise ValueError("Contratto modificato.")
    for name,expected in report["record_hashes"].items():
        if sha(run/name)!=expected:raise ValueError("Record modificato: "+name)
    paths=sorted((run/"circuiti").glob("*/esito.json"))
    rows=[read(p) for p in paths]
    actual=summarize(rows)
    for key,value in actual.items():
        if value!=report[key]:raise ValueError("Riepilogo non riproducibile: "+key)
    assert len(rows)==88 and actual["successes"]==88 and len(actual["common_top1_circuits"])==88
    # Coverage and primary score precede the diagnostic on the five examples.
    def criterion(h):
        m=report["methods"][f"wl_h{h}"]
        return (-m["top1_score"]["n"],m["top1_regret_common"]["mean"],
                m["top1_regret_common"]["median"],
                m["best_displayed_regret_observed"]["mean"],h)
    chosen=min(range(1,31),key=criterion)
    assert chosen==24
    plateau=[h for h in range(1,31)
             if report["methods"][f"wl_h{h}"]["top1_regret_common"]["mean"]==
                report["methods"][f"wl_h{chosen}"]["top1_regret_common"]["mean"]]
    comparisons={}
    for other in ["manhattan"]+[f"wl_h{h}" for h in (23,25,26,27,28,30)]:
        diffs=[]
        wins=ties=losses=pair_diffs=set_diffs=order_diffs=0
        for row in rows:
            a=row["methods"][f"wl_h{chosen}"]
            b=row["methods"][other]
            x=a["transfer"]["top1_score"];y=b["transfer"]["top1_score"]
            delta=x-y
            wins+=int(delta>0);ties+=int(delta==0);losses+=int(delta<0)
            pair_diffs+=int(a["transfer"]["top1_pair"]!=b["transfer"]["top1_pair"])
            set_diffs+=int(set(a["retrieved_ids"])!=set(b["retrieved_ids"]))
            order_diffs+=int(a["retrieved_ids"]!=b["retrieved_ids"])
            if delta:
                diffs.append({"circuit_id":row["circuit_id"],"chosen_score":x,"other_score":y,"delta":delta})
        comparisons[other]={"wins":wins,"ties":ties,"losses":losses,"score_differences":diffs,
                            "top1_pair_differences":pair_diffs,"top5_set_differences":set_diffs,
                            "top5_order_differences":order_diffs}
    data={"selected_h":chosen,"k":5,"primary_plateau":plateau,"circuits":88,
          "criterion":"coverage; minimum mean top1 regret on common circuits; median; secondary diagnostic; smaller h",
          "methods":report["methods"],"comparisons":comparisons,
          "notes":["The h23 improvement is tiny and involves one circuit; no claim of statistical superiority.",
                   "This measures historical transfer, not LLM performance.",
                   "70 incomplete validation matrices; reference is best observed.",
                   "Adaptive selection over three grids on the same 88 validation circuits.",
                   "All descriptors still store rounds 0..30; ranking uses only 0..24."],
          "sources":{"report_sha256":sha(run/"riepilogo.json"),"contract_sha256":sha(run/"contratto.json"),
                     "generator_sha256":sha(Path(__file__))}}
    target=HERE/"analisi_scelta.json"
    if target.exists():
        if read(target)!=data:raise ValueError("Analisi precedente diversa.")
    else:save(target,data)
    print(json.dumps({"selected_h":chosen,"primary_plateau":plateau,"verified_records":len(paths),
                      "analysis":str(target)},indent=2))
if __name__=="__main__":main()
