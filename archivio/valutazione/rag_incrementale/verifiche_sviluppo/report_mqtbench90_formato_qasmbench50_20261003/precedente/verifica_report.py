"""Anteprima del report con dati interamente sintetici, senza leggere esiti reali."""
from __future__ import annotations
from comune import *
import importlib.util
import argparse


def synthetic_data():
    spec = importlib.util.spec_from_file_location("incremental_report_qa", BASE / "report/genera.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    data = {"experiment_id": "VERIFICA_SINTETICA", "kind": "synthetic_verification",
            "created_at": now(), "sources": {}, "oracle": None, "orders": {},
            "limitations": ["Dati interamente sintetici: nessuna valutazione sperimentale è stata eseguita.",
                           "Questa anteprima controlla soltanto tabelle, grafici e impaginazione."]}
    for n, order in enumerate(ORDERS):
        rows, deltas, memory = [], [], 0
        for i in range(1, 91):
            failed = i % 29 == 0
            delta = None if failed else ((i % 9)-4) * 0.002 + n * 0.001
            score = None if failed else 0.8 + delta
            if delta is not None:
                deltas.append(delta)
                memory += 1
            rows.append({
                "order": order, "position": i, "circuit_id": f"SINTETICO_{i}",
                "source_sha256": "synthetic", "status": "timeout" if failed else "success",
                "score": score, "baseline_score": 0.8, "delta_score": delta,
                "cumulative_mean_delta": sum(deltas)/len(deltas) if deltas else None,
                "cumulative_paired_n": len(deltas), "oracle_score": 0.95,
                "oracle_exhaustive": i % 2 == 0, "regret": 0.95-score if score is not None else None,
                "baseline_regret": 0.15, "memory_before": memory-(0 if failed else 1),
                "memory_after": memory, "retrieved_incremental": min(5, i//10),
                "nearest_distance": 1/(i+1), "facts_unverified": i % 13 == 0,
                "total_seconds": 100 if failed else 20+n, "choice_seconds": 18,
                "compilation_seconds": 2, "total_tokens": None if failed else 1000+10*i,
                "llm_calls": 1, "retries": 0, "rag_seconds": 0.1,
                "baseline_total_seconds": 30, "baseline_total_tokens": 1000,
            })
        data["orders"][order] = {"status": "completed", "rows": rows,
                                  "summary": module.summarize(rows, 90)}
    return module, data


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pdf", action="store_true")
    args = ap.parse_args()
    module, data = synthetic_data()
    output = BASE / "verifiche_sviluppo/temporanei" / ("report_sintetico_" + uuid4().hex[:8])
    print(module.write_report(data, output, args.pdf))


if __name__ == "__main__":
    main()
