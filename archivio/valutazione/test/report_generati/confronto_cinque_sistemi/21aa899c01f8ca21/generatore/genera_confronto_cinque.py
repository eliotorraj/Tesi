"""Nuovo confronto a cinque sistemi; conserva interamente il report precedente."""
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
        raise ValueError("Manifest diverso dalla fonte congelata.")
    expected={r["circuit_id"]:r["source_sha256"] for r in read(SOURCE)["circuits"] if r["split"]=="test"}
    runs=load_sources(AREA,expected,contract)
    old=read(baseline/"provenienza.json")
    for method in METHODS:
        if method not in runs:
            raise ValueError("Manca un sistema originale: "+method)
        r=runs[method]
        if r["summary"]!=read(baseline/"sistemi"/method/"riepilogo.json"):
            raise ValueError("Misure diverse dal report di riferimento: "+method)
        if r["rows"]!=read(baseline/"sistemi"/method/"tabelle/episodi.json"):
            raise ValueError("Episodi diversi dal report di riferimento: "+method)
        r["report_model_metadata"]=old["method_parameters"].get(method,{})
    runs[METHOD],random_contract=load_random(summary)
    # Stesso contratto di generazione per RAG pertinente e RAG casuale.
    settings=lambda m: [x["parameters"] for x in runs[m]["generation_settings"]]
    if settings("llm_rag")!=settings(METHOD):
        raise ValueError("Parametri LLM diversi: aggiornare l'interpretazione.")
    for k in ("model_sha256",):
        if runs["llm_rag"]["meta"]["server"].get(k)!=runs[METHOD]["meta"]["server"].get(k):
            raise ValueError("Pesi del modello diversi.")
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
        raise ValueError("L'output deve essere separato dal report originale.")
    output=root/fingerprint[:16]
    if (output/"completato.json").exists():
        done=read(output/"completato.json")
        if all((output/p).is_file() and sha(output/p)==h for p,h in done["outputs"].items()):
            return output
        raise ValueError("Versione conclusa alterata: usare una nuova cartella.")
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
    print("Compilazione del confronto a cinque sistemi",flush=True)
    body=comparison_body(dest,runs,comparison,plan)
    body+=r"\par Per rigenerare questa estensione: \texttt{.venv/bin/python} \nolinkurl{archivio/valutazione/test/report/genera_confronto_cinque.py}."+"\n"
    compile_document(dest,"Confronto di cinque sistemi sul Test",body)
    (output/"README.md").write_text("# Confronto di cinque sistemi\n\n[Apri il PDF](confronto/latex/verifica.pdf).\n\n"
        "Estensione separata del report 30dd5b4f737c058e. Aggiunge LLM + Random RAG "
        "in tutte le tabelle e nei dieci gruppi di grafici, con il quinto pannello centrato "
        "nella terza riga. Le conclusioni includono differenze appaiate e fasce descrittive di qubit.\n\n"
        "Sorgenti LaTeX e CSV sono in confronto/. provenienza.json conserva le impronte "
        "delle fonti e dell'intero report originale. generatore/ conserva il codice usato.\n",encoding="utf-8")
    after,_,_=load_all(baseline,summary)
    if tree_hashes(baseline)!=before:
        raise RuntimeError("Report originale modificato durante la generazione.")
    if any(after[m]["input_files"]!=r["input_files"] or after[m]["source"]!=r["source"] for m,r in runs.items()):
        raise RuntimeError("Fonti cambiate durante la generazione.")
    if any(sha(HERE/name)!=h for name,h in sources.items()) or any(sha(Path(p))!=h for p,h in supporting.items()):
        raise RuntimeError("Generatore o fonti di supporto cambiati.")
    write_json(output/"completato.json",dict(at=datetime.now(timezone.utc).isoformat(),
        fingerprint=fingerprint,pdf_available=True,baseline_unchanged=True,outputs=tree_hashes(output)))
    root.mkdir(exist_ok=True)
    write_json(root/"ultimo.json",dict(directory=str(output),pdf=str(dest/"latex/verifica.pdf")))
    (root/"README.md").write_text("# Confronto esteso con recupero casuale\n\n"
        "[Versione corrente]("+output.name+"/confronto/latex/verifica.pdf).\n"
        "Il report originale resta nella cartella 30dd5b4f737c058e.\n",encoding="utf-8")
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
