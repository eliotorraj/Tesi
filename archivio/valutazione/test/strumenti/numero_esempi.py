'Separate runs to measure the number of Manhattan RAG examples.'
from __future__ import annotations
import argparse
from functools import partial
import json
import os
from pathlib import Path
import platform
import sys
from uuid import uuid4
from common import AREA, ROOT, SOURCE, PLAN, read, save, sha, now, code_files
from gates import preflight, frozen_contract
from runner import evaluate, interrupted_result, verify_server

BASE = AREA / "numero_esempi"


def retrieval_policy(k):
    if type(k) is not int or k not in (1, 10):
        raise ValueError('These two runs require exactly 1 or 10 examples.')
    return {
        "revision": "manhattan-example-count-v1",
        "k": k, "distance": "Manhattan", "search": "exact",
        "features": 49, "transform": "same frozen train transform as classic RAG",
        "filters": "same experiment, train, objective, selected device compatible",
        "order": ["distance_float64_ascending", "rag_id_ascending"],
        "insufficient_examples": "fail_without_inference",
        "context_overflow": "fail_without_generation_or_example_removal",
        "max_example_alias": max(5, k),
        "response_contract": "facts-v4" if k == 1 else "facts-v4-k10-toon3-20260928",
    }


def prepare_k(qasm, *, k):
    from app import prepare
    policy = retrieval_policy(k)
    request, prompt, log = prepare(qasm, rag=True, rag_limit=k)
    count = len(log["records"])
    if count != k:
        raise ValueError(f'Requested {k} compatible train examples, retrieved {count}; no inference.')
    return request, prompt, {
        **log, "policy": policy, "requested_examples": k, "returned_examples": count,
        "records": [{"example_id": f"E{i}", **r} for i, r in enumerate(log["records"], 1)],
    }


def summarize(base, paths, expected):
    'Counts and known measurements; missing data never becomes zero.'
    import statistics
    from report import summary
    rows = [read(p) for p in paths]
    result = summary(rows, expected)
    for name in ("rag_seconds", "input_tokens", "output_tokens", "llm_calls"):
        values = [r[name] for r in rows if isinstance(r.get(name), (int, float))]
        result[name] = {
            "sum_known": sum(values), "mean_known": statistics.mean(values) if values else None,
            "measured_circuits": len(values), "missing_circuits": len(rows)-len(values),
        }
    result["complete_token_circuits"] = sum(r.get("token_usage_complete") is True for r in rows)
    validations = sorted((base/"circuiti").glob("*/decision_validation.json"))
    checks = [read(p) for p in validations]
    result["facts"] = {
        "final_responses_with_validation": len(checks),
        "final_responses_all_verified": sum(r["facts_status"] == "verified" for r in checks),
        "final_responses_unverified": sum(r["facts_status"] == "unverified" for r in checks),
        "facts_verified": sum(c["result"] == "verified" for r in checks for c in r["fact_checks"]),
        "facts_total": sum(len(r["fact_checks"]) for r in checks),
        "hypotheses_semantically_verified": False,
        "sources": {str(p.relative_to(base)): sha(p) for p in validations},
    }
    result["timing"] = (
        "Wall clock perf_counter. rag_seconds includes train/index verification and retrieval; "
        "choice_seconds includes preparation, tokenization, all LLM attempts and fact checks; "
        "llm_response_seconds sums physical completion calls. Units: seconds."
    )
    return result

def ensure_contract(path, contract):
    if path.exists():
        if read(path) != contract:
            raise ValueError('Incompatible resume: code, data, plan or example count changed. Preserve the previous run.')
    else:
        save(path, contract)
    return sha(path)

def cli(k, argv=None):
    policy = retrieval_policy(k)
    method = f"llm_rag_k{k}"
    ap = argparse.ArgumentParser(description=f'LLM + standard RAG with {k} train examples; separate results.')
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--verifica", action="store_true", help='Checks without Test or inference')
    mode.add_argument("--tecnico", action="store_true", help='Synthetic Bell only, with an LLM server')
    mode.add_argument("--esegui", action="store_true", help='New extension on the 90 already exposed Test cases')
    ap.add_argument("--url", default="http://127.0.0.1:8089")
    ap.add_argument("--model-path", type=Path)
    args = ap.parse_args(argv)
    if not args.url.startswith(("http://127.0.0.1:", "http://localhost:")):
        ap.error('The server must be local.')
    campaign = BASE / f"k_{k}"
    check = preflight(method)
    save(campaign / "preparazione/verifiche" / (uuid4().hex + ".json"), check)
    print(json.dumps(check, ensure_ascii=False, indent=2), flush=True)
    if not check["ready"]:
        return 1
    if args.verifica:
        return 0
    from app import LlmTransportError
    server_log = campaign / "preparazione/verifiche" / ("server-" + uuid4().hex + ".json")
    try:
        server = verify_server(args)
        save(server_log, {"at": now(), "ok": True, "details": server})
    except Exception as exc:
        save(server_log, {"at": now(), "ok": False, "error": type(exc).__name__, "message": str(exc)})
        raise
    base = campaign / "prove_tecniche" / uuid4().hex if args.tecnico else campaign / "risultati" / method
    base.mkdir(parents=True, exist_ok=True)
    import portalocker
    with portalocker.Lock(str(base / ".lock"), timeout=0):
        contract = {
            "kind": "technical" if args.tecnico else "exploratory_test_extension",
            "note": 'Extension designed after reading Test, not fresh independent confirmation.',
            "method": method, "retrieval": policy,
            "parent_plan_sha256": sha(PLAN),
            "environment": {"python": sys.version, "platform": platform.platform()},
            "inputs": frozen_contract(),
        }
        contract_sha = ensure_contract(base / "contratto_congelato.json", contract)
        begin = base / "esecuzione.json"
        config = {"method": method, "kind": contract["kind"], "retrieval_k": k,
                  "contract_sha256": contract_sha, "expected_circuits": 1 if args.tecnico else 90}
        if begin.exists():
            if any(read(begin).get(k) != v for k, v in config.items()):
                raise ValueError('Resume is incompatible with the execution record.')
        else:
            save(begin, {**config, "at": now(), "server": server, "code": code_files(),
                         "cpu_count": os.cpu_count(), "memory_measurement": "not collected"})
        save(base / "sessioni" / (uuid4().hex + ".json"), {"at": now(), "server": server})
        if args.tecnico:
            source = ROOT / "examples/bell.qasm"
            rows = [{"circuit_id": "bell_tecnico", "source_sha256": sha(source),
                     "technical_source": str(source)}]
        else:
            rows = sorted((r for r in read(SOURCE)["circuits"] if r["split"] == "test"),
                          key=lambda r: r["circuit_id"])
            if len(rows) != 90:
                raise ValueError('Expected 90 Test circuits.')
        for i, row in enumerate(rows, 1):
            folder = base / "circuiti" / row["circuit_id"]
            if (folder / "esito.json").exists():
                continue
            if (folder / "begin.json").exists():
                interrupted_result(row, folder, method)
            else:
                try:
                    evaluate(row, folder, method, args.url, args.tecnico,
                             prepare_fn=partial(prepare_k, k=k), max_examples=max(5, k))
                except LlmTransportError as exc:
                    print(f'Run stopped; attempt preserved: {exc}', file=sys.stderr)
                    return 1
            print(f"{method}: {i}/{len(rows)} {row['circuit_id']}", flush=True)
        paths = sorted((base / "circuiti").glob("*/esito.json"))
        result = summarize(base, paths, len(rows))
        result.update(method=method, kind=contract["kind"], retrieval_k=k,
                      contract_sha256=contract_sha,
                      units={"score": "expected_fidelity [0,1]", "times": "seconds", "tokens": "tokens"},
                      sources={str(p.relative_to(base)): sha(p) for p in paths})
        output = base / "analisi" / (uuid4().hex + ".json")
        save(output, result)
        print('Summary: ' + str(output))
    return 0


