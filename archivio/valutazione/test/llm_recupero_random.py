"""Avvio separato: LLM con cinque esempi train estratti a caso."""
from __future__ import annotations
import argparse
from functools import partial
import json
import os
from pathlib import Path
import platform
import sys
from uuid import uuid4
sys.path.insert(0, str(Path(__file__).resolve().parent / "strumenti"))
from common import AREA, ROOT, SOURCE, PLAN, read, save, sha, now, code_files
from gates import preflight, frozen_contract
from runner import evaluate, interrupted_result, verify_server
from recupero_random import POLICY, prepare_random

METHOD = "llm_recupero_random"
BASE = AREA / "recupero_random"

def ensure_contract(path, contract):
    if path.exists():
        if read(path) != contract:
            raise ValueError("Ripresa incompatibile: codice, dati, piano o seme cambiati. Conservare la prova precedente.")
    else:
        save(path, contract)
    return sha(path)

def cli(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--verifica", action="store_true", help="Controlli senza Test e senza inferenza")
    mode.add_argument("--tecnico", action="store_true", help="Solo Bell sintetico, con server LLM")
    mode.add_argument("--esegui", action="store_true", help="Nuova estensione sui 90 casi Test gia esposti")
    ap.add_argument("--seed", type=int, default=20260927, help="Seme del recupero; distinto dal seme LLM")
    ap.add_argument("--url", default="http://127.0.0.1:8089")
    ap.add_argument("--model-path", type=Path)
    args = ap.parse_args(argv)
    if not args.url.startswith(("http://127.0.0.1:", "http://localhost:")):
        ap.error("Il server deve essere locale.")
    campaign = BASE / ("seed_" + str(args.seed))
    check = preflight(METHOD)
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
    base = campaign / "prove_tecniche" / uuid4().hex if args.tecnico else campaign / "risultati" / METHOD
    base.mkdir(parents=True, exist_ok=True)
    import portalocker
    with portalocker.Lock(str(base / ".lock"), timeout=0):
        contract = {
            "kind": "technical" if args.tecnico else "exploratory_test_extension",
            "note": "Estensione decisa dopo la lettura del Test; non una nuova conferma indipendente.",
            "method": METHOD, "retrieval": {**POLICY, "seed": args.seed},
            "parent_plan_sha256": sha(PLAN),
            "environment": {"python": sys.version, "platform": platform.platform()},
            "inputs": frozen_contract(),
        }
        contract_sha = ensure_contract(base / "contratto_congelato.json", contract)
        begin = base / "esecuzione.json"
        config = {"method": METHOD, "kind": contract["kind"], "seed": args.seed,
                  "contract_sha256": contract_sha, "expected_circuits": 1 if args.tecnico else 90}
        if begin.exists():
            if any(read(begin).get(k) != v for k, v in config.items()):
                raise ValueError("Ripresa incompatibile con il registro di esecuzione.")
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
                raise ValueError("Attesi 90 circuiti Test.")
        for i, row in enumerate(rows, 1):
            folder = base / "circuiti" / row["circuit_id"]
            if (folder / "esito.json").exists():
                continue
            if (folder / "begin.json").exists():
                interrupted_result(row, folder, METHOD)
            else:
                try:
                    evaluate(row, folder, METHOD, args.url, args.tecnico,
                             prepare_fn=partial(prepare_random, seed=args.seed))
                except LlmTransportError as exc:
                    print(f"Esecuzione fermata; tentativo conservato: {exc}", file=sys.stderr)
                    return 1
            print(f"{METHOD}: {i}/{len(rows)} {row['circuit_id']}", flush=True)
        from report import summary
        paths = sorted((base / "circuiti").glob("*/esito.json"))
        result = summary([read(p) for p in paths], len(rows))
        result.update(method=METHOD, kind=contract["kind"], seed=args.seed,
                      contract_sha256=contract_sha,
                      units={"score": "expected_fidelity [0,1]", "times": "seconds", "tokens": "tokens"},
                      sources={str(p.relative_to(base)): sha(p) for p in paths})
        output = base / "analisi" / (uuid4().hex + ".json")
        save(output, result)
        print("Riepilogo: " + str(output))
    return 0

if __name__ == "__main__":
    raise SystemExit(cli())
