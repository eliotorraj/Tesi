'New five-system comparison; preserves the previous report in full.'
from __future__ import annotations
import argparse
import platform
import shutil
from datetime import datetime,timezone
from pathlib import Path
from dati import METHODS,read,sha,digest,write_json,write_csv,compare
from genera import AREA,REPO,HERE,SOURCE
from fonti import load_sources
from genera_recupero_random import load_random,DEFAULT
from confronto import comparison_body
from estensione_random import analyze,METHOD
from impaginazione import compile_document

BASELINE=AREA/"report_generati/30dd5b4f737c058e"
ALL_METHODS=METHODS+(METHOD,)


def tree_hashes(folder):
    return {str(p.relative_to(folder)):sha(p) for p in sorted(folder.rglob("*")) if p.is_file()}


def load_all(baseline,summary):
    contract_path=AREA/"preparazione/contratto_congelato.json"
    contract=read(contract_path)
    if sha(SOURCE)!=contract["source_sha256"]:
        raise ValueError('Manifest differs from the frozen source.')
    expected={r["circuit_id"]:r["source_sha256"] for r in read(SOURCE)["circuits"] if r["split"]=="test"}
    runs=load_sources(AREA,expected,contract)
    old=read(baseline/"provenienza.json")
    for method in METHODS:
        if method not in runs:
            raise ValueError('An original system is missing: '+method)
        r=runs[method]
        if r["summary"]!=read(baseline/"sistemi"/method/"riepilogo.json"):
            raise ValueError('Measurements differ from the reference report: '+method)
        if r["rows"]!=read(baseline/"sistemi"/method/"tabelle/episodi.json"):
            raise ValueError('Episodes differ from the reference report: '+method)
        r["report_model_metadata"]=old["method_parameters"].get(method,{})
    runs[METHOD],random_contract=load_random(summary)
    # Use the same generation contract for relevant and random retrieval.
    settings=lambda m: [x["parameters"] for x in runs[m]["generation_settings"]]
    if settings("llm_rag")!=settings(METHOD):
        raise ValueError('LLM parameters differ: update the interpretation.')
    for k in ("model_sha256",):
        if runs["llm_rag"]["meta"]["server"].get(k)!=runs[METHOD]["meta"]["server"].get(k):
            raise ValueError('Model weights differ.')
    runs[METHOD]["comparison_detail"]=analyze(runs,read(SOURCE))
    return runs,contract["plan"],random_contract


def build(baseline=BASELINE,summary=DEFAULT,output_root=None):
    baseline=Path(baseline).resolve()
    before=tree_hashes(baseline)
    runs,plan,random_contract=load_all(baseline,summary)
    comparison=compare(runs,plan["analysis"],methods=ALL_METHODS)
    sources={p.name:sha(p) for p in sorted(HERE.iterdir()) if p.suffix in (".py",".tex",".md")}
    supporting={str(p):sha(p) for p in (SOURCE,REPO/"prototipo/config.json",REPO/"prototipo/docs/protocollo_sperimentale.md")}
    provenance=dict(kind="five_system_exploratory_extension",baseline=str(baseline),baseline_files=before,
        generator_files=sources,supporting_files=supporting,source_summary=str(Path(summary).resolve()),
        input_files={m:r["input_files"] for m,r in runs.items()},
        result_sources={m:r["source"] for m,r in runs.items()},
        run_metadata={m:r["meta"] for m,r in runs.items()},
        generation_settings={m:r["generation_settings"] for m,r in runs.items()},
        random_contract=random_contract,statistical_plan=plan["analysis"],
        extension="paired descriptive comparison with random retrieval; post-test qubit groups; one retrieval seed",
        environment=dict(python=platform.python_version()))
    fingerprint=digest(provenance)
    root=Path(output_root or AREA/"report_generati/confronto_cinque_sistemi").resolve()
    if root==baseline or baseline in root.parents:
        raise ValueError('Output must be separate from the original report.')
    output=root/fingerprint[:16]
    if (output/"completato.json").exists():
        done=read(output/"completato.json")
        if all((output/p).is_file() and sha(output/p)==h for p,h in done["outputs"].items()):
            return output
        raise ValueError('Completed version has changed: use a new directory.')
    output.mkdir(parents=True,exist_ok=True)
    write_json(output/"provenienza.json",provenance)
    (output/"generatore").mkdir(exist_ok=True)
    for name in sources:
        shutil.copy2(HERE/name,output/"generatore"/name)
    dest=output/"confronto"
    write_json(output/"confronto.json",comparison)
    write_json(dest/"tabelle/riepiloghi.json",{m:r["summary"] for m,r in runs.items()})
    write_json(dest/"tabelle/confronti_appaiati.json",comparison)
    write_csv(dest/"tabelle/circuiti_tutti_sistemi.csv",[dict(method=m,**c) for m,r in runs.items() for c in r["circuits"]])
    write_csv(dest/"tabelle/differenze_appaiate.csv",[dict(other_method=m,**c) for m,p in comparison["pairs"].items() for c in p["differences"]])
    detail=runs[METHOD]["comparison_detail"]
    write_json(dest/"tabelle/analisi_qubit.json",detail)
    write_csv(dest/"tabelle/differenze_per_qubit.csv",detail["rows"])
    write_csv(dest/"tabelle/fasce_qubit.csv",detail["groups"])
    print('Compile the five-system comparison',flush=True)
    body=comparison_body(dest,runs,comparison,plan)
    body+='\\par To regenerate this extension: \\texttt{.venv/bin/python} \\nolinkurl{archivio/valutazione/test/report/genera_confronto_cinque.py}.'+"\n"
    compile_document(dest,'Five-system comparison on the Test',body)
    (output/"README.md").write_text("""# Five-system comparison

[Open the PDF](confronto/latex/verifica.pdf).

Separate extension of report 30dd5b4f737c058e. Adds LLM + Random RAG to all tables and ten plot groups, with the fifth panel centered in the third row. Conclusions include paired differences and descriptive qubit groups.

LaTeX sources and CSV files are in confronto/. provenienza.json preserves fingerprints of the sources and the entire original report. generatore/ preserves the code used.

""",encoding="utf-8")
    after,_,_=load_all(baseline,summary)
    if tree_hashes(baseline)!=before:
        raise RuntimeError('Original report changed during generation.')
    if any(after[m]["input_files"]!=r["input_files"] or after[m]["source"]!=r["source"] for m,r in runs.items()):
        raise RuntimeError('Sources changed during generation.')
    if any(sha(HERE/name)!=h for name,h in sources.items()) or any(sha(Path(p))!=h for p,h in supporting.items()):
        raise RuntimeError('Generator or supporting sources changed.')
    write_json(output/"completato.json",dict(at=datetime.now(timezone.utc).isoformat(),
        fingerprint=fingerprint,pdf_available=True,baseline_unchanged=True,outputs=tree_hashes(output)))
    root.mkdir(exist_ok=True)
    write_json(root/"ultimo.json",dict(directory=str(output),pdf=str(dest/"latex/verifica.pdf")))
    (root/"README.md").write_text("""# Extended comparison with random retrieval

[Current version]("""+output.name+"""/confronto/latex/verifica.pdf).
The original report remains in directory 30dd5b4f737c058e.

""",encoding="utf-8")
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline",type=Path,default=BASELINE)
    parser.add_argument("--riepilogo",type=Path,default=DEFAULT)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    print(build(args.baseline,args.riepilogo,args.output))


if __name__=="__main__":
    main()
