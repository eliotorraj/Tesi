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
        self.assertEqual(len(comparison["common_circuit_ids"]), 78)
        self.assertEqual(len(comparison["oracle_common_circuit_ids"]), 78)
        self.assertEqual(len(comparison["pairwise"]), 6)
        for row in comparison["pairwise"]:
            self.assertEqual(row["paired"], 84)
            self.assertEqual(row["a_better"]+row["equal"]+row["b_better"], 84)
        baseline = comparison["summary"][0]
        self.assertEqual(baseline["n_common"], 78)
        self.assertEqual(baseline["complete_references"]+baseline["partial_references"], 78)
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
        zero = next(r for r in rows if r["id"] == 90)
        self.assertEqual(zero["gap"], 0)
        measured = next(r for r in self.data["orders"][order]["rows"] if r["circuit_id"] == zero["circuit_id"])
        self.assertIsNone(measured["relative_gap_percent"])
        failed = next(r for r in rows if r["status"] == "timeout")
        self.assertIsNone(failed["gap"])
        self.data["orders"][order]["rows"] = []
        self.assertTrue(all(r["gap"] is None and r["status"] == "not_started"
                            for r in self.charts.aligned_rows(self.data, order)))
        self.assertEqual(self.charts.compare_orders(self.data)["common_circuit_ids"], [])

    def test_all_ninety_circuits_and_exported_figures(self):
        specs = self.charts.figure_specs(self.data)
        self.assertEqual(len(specs), 18)
        for order in ORDERS:
            pages = [body for name, body in specs if name.startswith("oracle_"+order+"_")]
            self.assertEqual(len(pages), 4)
            for row in self.data["circuits"]:
                name = self.charts.escape(row["circuit_id"])
                self.assertEqual(sum(name in body for body in pages), 1)
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)/"report"
            self.report.write_report(self.data, output)
            self.assertEqual(len(list((output/"grafici").glob("*.tex"))), 20)
            self.assertEqual(len((output/"distanze_oracle.csv").read_text().splitlines()), 361)
            self.assertEqual(len((output/"confronti_appaiati.csv").read_text().splitlines()), 7)
            tex = (output/"rapporto.tex").read_text()
            self.assertNotIn("@@", tex)
            self.assertIn("DATI SINTETICI", tex)
            self.assertIn("90 circuiti Test MQT Bench", tex)


    def test_no_k5_fallback_before_new_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(self.report, "campaign_path", side_effect=lambda exp, order: Path(tmp)/order):
                data = self.report.collect(DEFAULT_ID, None)
        self.assertEqual(data["k"], 1)
        self.assertEqual(data["fixed_summary"]["completed"], 0)
        self.assertTrue(all(row["score"] is None for row in data["baseline"].values()))
        self.assertEqual(data["comparisons"]["common_circuit_ids"], [])

    def test_new_baseline_used_even_when_oracle_contains_historical_score(self):
        rows = [{"circuit_id": "technical_circuit", "source_sha256": "fixture"}]
        settings = {"plan": {"k": 1}, "train_count": 396, "transform": {}, "targets": {},
                    "versions": {"qiskit": "fixture", "mqt.bench": "fixture", "numpy": "fixture"},
                    "model": {}, "initial_source_hashes": [], "python": "fixture"}
        ref = {"circuit_id": "technical_circuit", "source_sha256": "fixture",
               "system_score": 0.99, "oracle_score": 0.95, "exhaustive": True}
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            contracts = {}
            for order in SYSTEMS:
                campaign = base/order
                contract = {"experiment_id": DEFAULT_ID, "order": order, "rows": rows, **settings}
                contracts[campaign] = contract
                save(campaign/"contratto.json", contract)
                folder = step_folder(campaign, 1, rows[0])
                save(folder/"esito.json", {"status": "success", "score": 0.2 if order == FIXED else 0.8})
                save(folder/"commit.json", {})
            with patch.object(self.report, "test_rows", return_value=rows), \
                 patch.object(self.report, "campaign_path", side_effect=lambda exp, order: base/order), \
                 patch.object(self.report, "check_contract", side_effect=lambda path, **kw: contracts[path]), \
                 patch.object(self.report, "replay", return_value=([], [{"memory_before_count": 0, "memory_after_count": 1}], None)), \
                 patch.object(self.charts, "load_reference", return_value=(
                     {"technical_circuit": ref}, {"targets": {}, "versions": settings["versions"]}, {})):
                data = self.report.collect(DEFAULT_ID, base/"oracle.json")
        self.assertEqual(data["baseline"]["technical_circuit"]["score"], 0.2)
        self.assertNotIn("system_score", data["references"]["technical_circuit"])
        for item in data["orders"].values():
            self.assertAlmostEqual(item["rows"][0]["delta_score"], 0.6)
        text = self.report.render_tex(data)
        self.assertIn("k=1", text)
        self.assertIn("nuova esecuzione", text)
        self.assertNotIn("cinque esempi", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
