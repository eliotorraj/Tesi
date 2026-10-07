'Standalone random retrieval report: reads outcomes without starting runs.'
from __future__ import annotations
import argparse
import hashlib
import json
import math
import platform
import shutil
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from dati import read, sha, digest, write_json, write_csv, load_run
from genera import HERE, REPO, AREA, SOURCE, method_body
from impaginazione import compile_document

METHOD = "llm_recupero_random"
KIND = "exploratory_test_extension"
DEFAULT = AREA/"recupero_random/seed_20260927/risultati/llm_recupero_random/analisi/8306d9dedffd4f3faa69ed74ef058baa.json"


def equal(actual, expected, label):
    if isinstance(expected, float) and isinstance(actual, (int, float)):
        ok = math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12)
    else:
        ok = actual == expected
    if not ok:
        raise ValueError(f'Inconsistent summary ({label}): {actual!r} != {expected!r}')


def validate_summary(saved, run):
    s = run["summary"]
    for key in ("expected_circuits", "completed_circuits", "successes", "failures", "pending"):
        equal(saved.get(key), s[key], key)
    equal(saved.get("retries"), s["metrics"]["retries"]["sum_known"], "retries")
    equal(saved.get("score_denominator"), s["metrics"]["score"]["measured_episodes"], "score_denominator")
    equal(saved.get("mean_score"), s["metrics"]["score"]["mean"], "mean_score")
    equal(saved.get("secondary", {}).get("median_score"), s["metrics"]["score"]["median"], "median_score")
    equal(saved.get("secondary", {}).get("failure_causes"), s["failure_causes"], "failure_causes")
    for key in ("total_seconds", "compilation_seconds", "compilation_process_seconds",
                "choice_seconds", "llm_response_seconds", "total_tokens"):
        value = saved.get(key, {})
        metric = s["metrics"][key]
        for a, b in (("sum_known", "sum_known"), ("mean_known", "mean"),
                     ("measured_circuits", "n"), ("missing_circuits", "missing_circuits")):
            equal(value.get(a), metric[b], key+"."+a)


def load_random(summary_path):
    summary_path = Path(summary_path).resolve()
    base = summary_path.parent.parent
    if summary_path.parent.name != "analisi" or base.name != METHOD:
        raise ValueError("The summary must belong to the random method's analisi/ directory.")
    saved = read(summary_path)
    contract_path = base/"contratto_congelato.json"
    contract = read(contract_path)
    contract_hash = sha(contract_path)
    meta = read(base/"esecuzione.json")
    seed = contract["retrieval"]["seed"]
    for name, obj in (("contratto", contract), ("esecuzione", meta), ("riepilogo", saved)):
        if obj.get("method") != METHOD or obj.get("kind") != KIND:
            raise ValueError('Incorrect identity: '+name)
    for obj in (meta, saved):
        if obj.get("seed") != seed or obj.get("contract_sha256") != contract_hash:
            raise ValueError('Seed or contract differs from the frozen source.')
    plan_path = AREA/"piano.json"
    plan = read(plan_path)
    if sha(plan_path) != contract["parent_plan_sha256"] or plan != contract["inputs"]["plan"]:
        raise ValueError('Plan differs from the frozen source.')
    if sha(SOURCE) != contract["inputs"]["source_sha256"]:
        raise ValueError('Manifest differs from the frozen source.')
    expected = {r["circuit_id"]:r["source_sha256"] for r in read(SOURCE)["circuits"] if r["split"]=="test"}
    if len(expected) != plan["circuits"]:
        raise ValueError('Inconsistent Test size.')
    policy = {k:v for k,v in contract["retrieval"].items() if k != "seed"}
    if policy.get("revision") != "random-examples-v1" or policy.get("k") != 5 or policy.get("sampling") != "uniform_without_replacement" or policy.get("distance") != "not_computed":
        raise ValueError('Retrieval policy is not supported by the report text.')
    run = load_run(base, expected, contract_hash, None, expected_kind=KIND)
    outcomes = {k:v for k,v in run["input_files"].items() if k.endswith("/esito.json")}
    if outcomes != saved.get("sources"):
        raise ValueError("Outcomes do not match the requested summary's fingerprints.")
    if len(run["rows"]) != len(expected) or len({r["circuit_id"] for r in run["rows"]}) != len(expected):
        raise ValueError('Exactly one outcome per Test circuit is required.')
    retrieval_rows = []
    for row in run["rows"]:
        path = base/row["episode_source"]
        retrieval = read(path.parent/"retrieval.json")
        encoded = json.dumps({"seed":seed,"source_sha256":row["source_sha256"]},
                             sort_keys=True,ensure_ascii=False,separators=(",",":")).encode()
        derived = int(hashlib.sha256(encoded).hexdigest(), 16)
        if retrieval.get("policy") != policy or retrieval.get("seed") != seed or retrieval.get("derived_seed") != derived or retrieval.get("source_sha256") != row["source_sha256"]:
            raise ValueError('Inconsistent retrieval record: '+row["circuit_id"])
        records = retrieval["records"]
        if (len(records)!=5 or len({r["rag_id"] for r in records})!=5
                or [r["example_id"] for r in records]!=["E1","E2","E3","E4","E5"]
                or any(r.get("distance") is not None for r in records)):
            raise ValueError('Inconsistent examples or distances: '+row["circuit_id"])
        retrieval_rows.extend(dict(circuit_id=row["circuit_id"], seed=seed,
            candidate_count=retrieval["candidate_count"], **r) for r in records)
    validate_summary(saved, run)
    supporting = {str(p):sha(p) for p in (summary_path, contract_path, plan_path, SOURCE)}
    run["source"] = dict(base=str(base), area=str(base.relative_to(REPO)), exploratory=True,
                         details=dict(seed=seed), supporting_files=supporting)
    run["retrieval_rows"] = retrieval_rows
    return run, contract


def build(summary_path=DEFAULT, output_root=None, compile_pdf=True):
    run, contract = load_random(summary_path)
    sources = {p.name:sha(p) for p in sorted(HERE.iterdir()) if p.suffix in (".py",".tex",".md")}
    provenance = dict(kind="independent_random_retrieval_report", source=run["source"],
        input_files=run["input_files"], generation_settings=run["generation_settings"],
        execution=run["meta"], contract=contract, generator=sources,
        environment=dict(python=platform.python_version(),numpy=np.__version__),
        aggregation="one episode per circuit; successful scores only; known costs; missing is not zero",
        comparison="none", summary_path=str(Path(summary_path).resolve()))
    fingerprint = digest(provenance)
    output = Path(output_root or AREA/"report_generati").resolve()/fingerprint[:16]
    if (output/"completato.json").exists():
        complete = read(output/"completato.json")
        if all((output/p).is_file() and sha(output/p)==v for p,v in complete["outputs"].items()) and (not compile_pdf or complete["pdf_available"]):
            return output
        raise ValueError('Completed report changed or PDF missing: use a different --output directory.')
    output.mkdir(parents=True,exist_ok=True)
    write_json(output/"provenienza.json",provenance)
    snapshot = output/"generatore"
    snapshot.mkdir(exist_ok=True)
    for name in sources:
        shutil.copy2(HERE/name,snapshot/name)
    dest = output/"sistemi"/METHOD
    write_json(dest/"riepilogo.json",run["summary"])
    write_json(dest/"tabelle/episodi.json",run["rows"])
    write_csv(dest/"tabelle/episodi.csv",run["rows"])
    write_csv(dest/"tabelle/circuiti.csv",run["circuits"])
    write_csv(dest/"tabelle/esempi_recuperati.csv",run["retrieval_rows"])
    body = method_body(dest,run).replace(
        'The full comparison documents the procedure, pairing and shared limitations.',
        "This report describes random retrieval only. The model's hypotheses are not verified and must not be treated as true statements.")
    body += '\\FloatBarrier\\section{Provenance and reproduction}'+"\n"
    body += 'Analysis identity: '+r"\nolinkurl{"+fingerprint+"}.\n\n"
    body += ("""Outcomes for the 90 circuits were checked against fingerprints in the requested summary, the Test manifest and the separate contract. The summary was recomputed from outcomes. Each of the 90 retrieval records contains five distinct identifiers, with aliases E1--E5, a consistent seed and no distance. This record check does not measure fact quality.

""")
    body += ("""The report directory preserves provenienza.json, a generator copy, CSV files for circuits, episodes and retrieved examples, plots and LaTeX sources. Actual call parameters and server metadata are in the provenance.

""")
    body += """To regenerate the report from the repository root:

"""
    body += r"\begin{quote}\small\texttt{.venv/bin/python} \nolinkurl{archivio/valutazione/test/report/genera_recupero_random.py}"+r"\end{quote}"+"\n"
    body += 'For another summary of the same variant, use the option '+r"\texttt{--riepilogo}"+""". The command reads results only and does not start the Test.

"""
    print('Compile the random retrieval report',flush=True)
    compile_document(dest,'Test: LLM + random retrieval',body,compile_pdf, subtitle='Independent report on the 90 Test circuits')
    (output/"README.md").write_text(
        """# Independent report: LLM + random retrieval

[Open the PDF](sistemi/llm_recupero_random/latex/verifica.pdf).

Exploratory extension with five train examples and seed """+str(contract["retrieval"]["seed"])+
        """. The report does not change the original comparison.

The sistemi/llm_recupero_random directory contains riepilogo.json, CSV tables, plots and LaTeX sources. To include risultati.tex in the thesis, load the packages in preambolo.tex and set TestReportPath to the system directory, with a trailing slash.

""",
        encoding="utf-8")
    # Do not certify a document if its sources changed during generation.
    after, _ = load_random(summary_path)
    if after["input_files"] != run["input_files"] or after["source"] != run["source"]:
        raise RuntimeError('Sources changed during generation.')
    if any(sha(HERE/name)!=value for name,value in sources.items()):
        raise RuntimeError('Generator changed during generation.')
    hashes = {str(p.relative_to(output)):sha(p) for p in sorted(output.rglob("*")) if p.is_file() and p.name!="completato.json"}
    write_json(output/"completato.json",dict(at=datetime.now(timezone.utc).isoformat(),
        fingerprint=fingerprint,pdf_available=compile_pdf,outputs=hashes))
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--riepilogo",type=Path,default=DEFAULT)
    parser.add_argument("--output",type=Path)
    parser.add_argument("--solo-sorgenti",action="store_true")
    args = parser.parse_args()
    print(build(args.riepilogo,args.output,not args.solo_sorgenti))


if __name__=="__main__":
    main()
