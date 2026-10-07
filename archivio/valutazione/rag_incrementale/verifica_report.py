"""Anteprima del report con dati interamente sintetici, senza leggere esiti reali."""
from __future__ import annotations
from comune import *
import importlib.util
import argparse


def synthetic_data():
    spec = importlib.util.spec_from_file_location("mqtbench_report_qa", BASE / "report/genera.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    circuits = [{"circuit_id": f"SINTETICO_{i:02d}_circuito_di_verifica", "index": i,
                 "source_sha256": "synthetic", "num_qubits": i % 40 + 2}
                for i in range(1, 91)]
    baseline = {r["circuit_id"]: {"score": 0.0 if r["index"] == 90 else .65+.003*r["index"], "status": "success"} for r in circuits}
    refs = {r["circuit_id"]: {"oracle_score": baseline[r["circuit_id"]]["score"] + (.012*(r["index"]%3) if r["index"] != 90 else 0),
                              "exhaustive": r["index"]%2 == 0} for r in circuits}
    data = {"experiment_id": "VERIFICA_SINTETICA", "kind": "synthetic_verification",
            "created_at": now(), "sources": {}, "oracle": {"kind": "synthetic"}, "orders": {},
            "circuits": circuits, "baseline": baseline, "references": refs,
            "limitations": ["Dati interamente sintetici: nessuna valutazione sperimentale è stata eseguita.",
                           "Questa anteprima controlla soltanto tabelle, grafici e impaginazione."]}
    for n, order in enumerate(ORDERS):
        rows, deltas, memory = [], [], 0
        for position, source in enumerate(order_rows(circuits, order), 1):
            i, cid = source["index"], source["circuit_id"]
            failed = (i+n) % 29 == 0
            delta = None if failed else (0.0 if i == 90 else ((i % 9)-4) * .002 + n * .001)
            control = baseline[cid]["score"]
            score = None if failed else control+delta
            oracle = refs[cid]["oracle_score"]
            if delta is not None:
                deltas.append(delta)
                memory += 1
            rows.append({
                "order": order, "position": position, "circuit_id": cid,
                "source_sha256": "synthetic", "num_qubits": source["num_qubits"], "status": "timeout" if failed else "success",
                "score": score, "baseline_score": control, "delta_score": delta,
                "cumulative_mean_delta": sum(deltas)/len(deltas) if deltas else None,
                "cumulative_paired_n": len(deltas), "oracle_score": oracle,
                "oracle_exhaustive": refs[cid]["exhaustive"], "regret": oracle-score if score is not None else None,
                "baseline_regret": oracle-control, "relative_gap_percent": 100*(oracle-score)/oracle if oracle > 0 and score is not None else None,
                "memory_before": memory-(0 if failed else 1),
                "memory_after": memory, "retrieved_incremental": min(5, position//10),
                "nearest_distance": 1/(position+1), "facts_unverified": i % 13 == 0,
                "total_seconds": 100 if failed else 20+n, "choice_seconds": 18,
                "compilation_seconds": 2, "total_tokens": None if failed else 1000+10*i,
                "llm_calls": 1, "retries": 0, "rag_seconds": .1,
                "baseline_total_seconds": 30, "baseline_total_tokens": 1000,
            })
        data["orders"][order] = {"status": "completed", "rows": rows,
                                  "summary": module.summarize(rows, 90)}
    data["comparisons"] = module.oracoli.compare_orders(data)
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
