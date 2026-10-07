"""Controlli dei confronti appaiati e delle figure; nessuna inferenza."""
from comune import *
import unittest
import tempfile
import copy
from unittest.mock import patch
from verifica_report import synthetic_data


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.report, self.data = synthetic_data()
        self.charts = self.report.oracoli

    def test_common_circuits_and_pairwise_denominators(self):
        comparison = self.charts.compare_orders(self.data)
        self.assertEqual(len(comparison["common_circuit_ids"]), 46)
        self.assertEqual(len(comparison["oracle_common_circuit_ids"]), 46)
        self.assertEqual(len(comparison["pairwise"]), 6)
        for row in comparison["pairwise"]:
            self.assertEqual(row["paired"], 48)
            self.assertEqual(row["a_better"]+row["equal"]+row["b_better"], 48)
        baseline = comparison["summary"][0]
        self.assertEqual(baseline["n_common"], 46)
        self.assertEqual(baseline["complete_references"]+baseline["partial_references"], 46)
        # Cambiare l'ordine di presentazione dei registri non cambia gli abbinamenti.
        shuffled = copy.deepcopy(self.data)
        for item in shuffled["orders"].values():
            item["rows"].reverse()
        self.assertEqual(self.charts.compare_orders(shuffled), comparison)

    def test_signed_gaps_missing_and_zero(self):
        low, high = self.charts.gap_limits(self.data)
        self.assertLess(low, 0)
        self.assertGreater(high, 0)
        order = list(ORDERS)[0]
        rows = self.charts.aligned_rows(self.data, order)
        zero = next(r for r in rows if r["id"] == 50)
        self.assertEqual(zero["gap"], 0)
        measured = next(r for r in self.data["orders"][order]["rows"] if r["circuit_id"] == zero["circuit_id"])
        self.assertIsNone(measured["relative_gap_percent"])
        failed = next(r for r in rows if r["status"] == "timeout")
        self.assertIsNone(failed["gap"])
        self.data["orders"][order]["rows"] = []
        self.assertTrue(all(r["gap"] is None and r["status"] == "not_started"
                            for r in self.charts.aligned_rows(self.data, order)))
        self.assertEqual(self.charts.compare_orders(self.data)["common_circuit_ids"], [])

    def test_all_fifty_circuits_and_exported_figures(self):
        specs = self.charts.figure_specs(self.data)
        self.assertEqual(len(specs), 10)
        for order in ORDERS:
            pages = [body for name, body in specs if name.startswith("oracle_"+order+"_")]
            self.assertEqual(len(pages), 2)
            for row in self.data["circuits"]:
                name = self.charts.escape(row["circuit_id"])
                self.assertEqual(sum(name in body for body in pages), 1)
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)/"report"
            self.report.write_report(self.data, output)
            self.assertEqual(len(list((output/"grafici").glob("*.tex"))), 12)
            self.assertEqual(len((output/"distanze_oracle.csv").read_text().splitlines()), 201)
            self.assertEqual(len((output/"confronti_appaiati.csv").read_text().splitlines()), 7)
            tex = (output/"rapporto.tex").read_text()
            self.assertNotIn("@@", tex)
            self.assertIn("DATI SINTETICI", tex)
            self.assertIn("50 circuiti Test QASMBench", tex)

    def test_oracle_summary_tampering_is_rejected(self):
        if str(REPO) not in sys.path:
            sys.path.insert(0, str(REPO))
        from archivio.valutazione.oracle_qasmbench import analizza
        with tempfile.TemporaryDirectory() as tmp:
            analysis = Path(tmp)/"analisi"/"fixture"
            path = analysis/"confronto_llm_rag_k5/risultati/dati.json"
            save(path, {"synthetic": False, "oracle_path": str(analysis),
                        "rows": [{"altered": True}], "oracle_identity": "fixture"})
            with patch.object(analizza, "audit_oracle", return_value=(
                    {"identity": {}, "identity_sha256": "fixture"}, {}, [], [], {}, 0)), \
                 patch.object(analizza, "audit_rag", return_value=({}, {}, {})), \
                 patch.object(analizza, "build_rows", return_value=[]):
                with self.assertRaisesRegex(ValueError, "diverso dagli esiti"):
                    self.charts.load_reference(path, [])


def verify_real_oracle():
    module, _ = synthetic_data()
    data = module.collect(DEFAULT_ID, ORACLE)
    result = {"kind": "read_only_source_verification", "at": now(),
              "oracle_results_verified": data["oracle"]["results_verified"],
              "oracle_identity": data["oracle"]["identity"],
              "references": len(data["references"]), "baseline_results": len(data["baseline"]),
              "partial_references": data["oracle"]["partial_references"],
              "incremental_completed": {k: v["summary"]["completed"] for k,v in data["orders"].items()},
              "llm_calls": 0, "quantum_compilations": 0,
              "source_set_sha256": digest(data["sources"])}
    path = BASE / "verifiche_sviluppo" / ("oracle_" + uuid4().hex[:8] + ".json")
    save(path, result)
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    if sys.argv[1:] == ["--verifica-oracle"]:
        verify_real_oracle()
    else:
        unittest.main(verbosity=2)
