"""Extended audit of three LLM methods from records without new runs.

Produces JSON only; never overwrites the editable LaTeX report source."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[4]
AREA=ROOT/"archivio/valutazione/test"
sys.path.insert(0,str(ROOT/"prototipo"))
from prototype.prompting.facts import verify
from prototype.prompting.minimal import model_input,citation_context,digest
from prototype.quantum_assistant.adapters.rag_dataset import load_corpus
from prototype.quantum_assistant.adapters.context import _compact_rag_example
SAMPLES=("groundstate_small_indep_tket_4","qpeexact_indep_qiskit_2","routing_indep_qiskit_6")
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text(encoding="utf-8"))
def check(ok,msg):
    if not ok: raise ValueError(msg)
def collect():
    records={r["rag_id"]:r for r in load_corpus().records}
    sources={}; reports={}; samples=[]; attempts=[]
    def tracked(p):
        sources[str(p.relative_to(ROOT))]=sha(p)
        return read(p)
    method_roots = {
        "llm_rag": AREA/"risultati/llm_rag",
        "llm_senza_rag": AREA/"risultati/llm_senza_rag",
        "llm_recupero_random": AREA/"recupero_random/seed_20260927/risultati/llm_recupero_random",
    }
    for method, method_root in method_roots.items():
        counts=Counter(); kinds=Counter()
        folders=sorted((method_root/"circuiti").iterdir())
        check(len(folders)==90,'Expected 90 circuits.')
        execution=tracked(method_root/"esecuzione.json")
        for folder in folders:
            prompt=tracked(folder/"prompt.json"); enc=tracked(folder/"encoding.json")
            final=tracked(folder/"decision_validation.json"); decision=tracked(folder/"decision.json")
            view=model_input(prompt); ctx=citation_context(prompt)
            check(enc["model_view_sha256"]==digest(view),'View changed')
            check(enc["citation_context"]==ctx.to_dict(),'Aliases changed')
            check(final["canonical_response"]==decision,'Inconsistent decision')
            for entry in prompt["retrieved_labeled_examples"]:
                r=records[entry["record_id"]]
                check(r["split"]=="train" and entry["example"]==_compact_rag_example(r),'Example was modified')
            for path in sorted(folder.glob("attempt_*/validation.json")):
                saved=tracked(path); raw=tracked(path.parent/"call/response_raw.json")
                fresh=verify(raw["content"],prompt)
                for key in ("schema_valid","selection_valid","facts_status","fact_checks","canonical_response"):
                    check(saved[key]==fresh[key],f'Outcome was not reproduced: {path}, {key}')
                # Independent comparisons against prompt fields.
                resp=fresh["canonical_response"]; examples={e["id"]:e for e in view["retrieved_labeled_examples"]}
                hardware={d["id"]:d for d in view["compatible_hardware"]}
                for f,c in zip(resp["facts"],saved["fact_checks"],strict=True):
                    kind=f["assertion"]; alias=f.get("example_id"); e=examples.get(alias)
                    device=resp["selected_device"]; config=resp["config_id"]; ok=False
                    if kind=="selected_device_has_enough_qubits":
                        ok=alias is None and hardware[device]["num_qubits"]>=view["circuit"]["num_qubits"]
                    elif e is not None:
                        if kind=="selected_device_matches_example": ok=device==e["selected_device"]
                        elif kind=="same_qubit_count_as_example": ok=view["circuit"]["num_qubits"]==e["circuit"]["num_qubits"]
                        elif kind=="selected_pair_among_reported_best":
                            ok=any(r["device_id"]==device and config in [r["config_id"],*r.get("tied_score_config_ids",[])] for r in e["top_configurations"])
                    check(ok==(c["result"]=="verified"),'Independent check disagrees')
                    counts["attempt_fact_"+c["result"]]+=1
                counts["attempts"]+=1;counts["attempt_"+saved["facts_status"]]+=1
                if path.parent.name=="attempt_1": counts["first_"+saved["facts_status"]]+=1
                attempts.append({"method":method,"circuit":folder.name,"attempt":saved["attempt"],
                                 "final":saved["attempt"]==final["attempt"],"checks":saved["fact_checks"]})
            raw=tracked(folder/f"attempt_{final['attempt']}"/"call/response_raw.json")["content"]
            check(json.loads(raw)==decision,'Original JSON is inconsistent')
            counts["responses"]+=1;counts[final["facts_status"]]+=1
            for c in final["fact_checks"]:
                counts["fact_"+c["result"]]+=1;kinds[(c["assertion"],c["result"])]+=1
                if c["example_id"] is not None and c["result"]=="verified": counts["historical_verified"]+=1
            if final["facts_status"]=="unverified":
                check(final["status"]=="accepted_with_unverified_facts" and final["attempt"]==3,'Unexpected acceptance')
                check(all(c["assertion"]=="selected_device_has_enough_qubits" and c["example_id"] is not None
                          for c in final["fact_checks"] if c["result"]=="unsupported"),'Unexpected error')
                check(hardware[decision["selected_device"]]["num_qubits"]>=view["circuit"]["num_qubits"],'Insufficient capacity')
            if method=="llm_rag" and folder.name in SAMPLES:
                used=list(dict.fromkeys(f["example_id"] for f in decision["facts"] if f.get("example_id")))
                samples.append({"circuit":folder.name,"source":str(folder.relative_to(ROOT)),"response":decision,
                    "raw_response":raw,"attempt":final["attempt"],"status":final["status"],"aliases":ctx.aliases,
                    "view":view,"checks":final["fact_checks"],"records":{a:records[ctx.aliases[a]] for a in used}})
        reports[method]={"counts":dict(counts),"kinds":[{"assertion":k,"result":v,"count":n} for (k,v),n in sorted(kinds.items())],
                         "historical_code_hashes":execution["code"]}
    for path in (Path(__file__),ROOT/"prototipo/data/rag_examples.jsonl",ROOT/"prototipo/data/seal.json",
                 ROOT/"prototipo/prototype/prompting/facts.py",ROOT/"prototipo/prototype/prompting/minimal.py",
                 Path(__file__).with_name("testo_fatti.py"),
                 AREA/"report_generati/30dd5b4f737c058e/confronto/latex/verifica.pdf"):
        sources[str(path.relative_to(ROOT))]=sha(path)
    return {"reports":reports,"samples":samples,"all_attempts":attempts,"source_sha256":sources,
            "selection":'Three valid final responses and one first attempt with an invalid fact; selected illustrative cases, not random.',
            "scope":'Reanalysis of records without semantic hypothesis verification.'}

def collect_extended():
    data = collect()
    # Retain the failure example requested in the previous revision.
    folder = AREA/"risultati/llm_rag/circuiti/qpeexact_indep_qiskit_13"
    def tracked(path):
        data["source_sha256"][str(path.relative_to(ROOT))] = sha(path)
        return read(path)
    prompt = tracked(folder/"prompt.json")
    saved = tracked(folder/"attempt_1/validation.json")
    raw = tracked(folder/"attempt_1/call/response_raw.json")["content"]
    fresh = verify(raw, prompt)
    for key in ("schema_valid", "selection_valid", "facts_status", "fact_checks", "canonical_response"):
        check(saved[key] == fresh[key], 'Failure-example check disagrees')
    check(saved["facts_status"] == "unverified", 'Invalid failure example')
    records = {r["rag_id"]: r for r in load_corpus().records}
    ctx = citation_context(prompt)
    aliases = list(dict.fromkeys(f["example_id"] for f in fresh["canonical_response"]["facts"] if f.get("example_id")))
    failure = {
        "circuit": folder.name, "source": str(folder.relative_to(ROOT)),
        "response": fresh["canonical_response"], "raw_response": raw,
        "attempt": 1, "final": False, "status": saved["facts_status"],
        "status_source": "facts_status", "aliases": ctx.aliases,
        "view": model_input(prompt), "checks": saved["fact_checks"],
        "records": {a: records[ctx.aliases[a]] for a in aliases},
        "validation": saved, "final_validation": tracked(folder/"decision_validation.json"),
        "selection_reason": 'Capacity fact with disallowed evidence attribution.',
    }
    data["samples"].insert(2, failure)
    dual = data["samples"][3]
    check(dual["circuit"] == "routing_indep_qiskit_6", 'Unexpected sample order')
    check(len(dual["records"]) == 2 and len({r["rag_id"] for r in dual["records"].values()}) == 2,
          'The new example must cite two different records')
    check(all(c["result"] == "verified" for c in dual["checks"]), 'New example was not verified')
    tracked(AREA/"recupero_random/seed_20260927/risultati/llm_recupero_random/contratto_congelato.json")
    data["random_campaign"] = {
        "seed": 20260927, "retrieved_examples": 5,
        "scope": 'One fixed-seed campaign; descriptive counts, not averages across seeds.',
    }
    return data

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, required=True, help='JSON file to create; no PDF is overwritten.')
    args = ap.parse_args()
    data = collect_extended()
    if args.output.exists() and read(args.output) != data:
        raise ValueError('A different audit already exists: choose a new --output.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k:v["counts"] for k,v in data["reports"].items()}, indent=2))

if __name__ == "__main__":
    main()
