'Regression checks for the fifth panel and comparisons, without running the Test.'
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dati import METHODS,aggregate,compare
from pannelli import grid,method_order
from estensione_random import analyze

NEW="llm_recupero_random"

class FiveTests(unittest.TestCase):
    def runs(self):
        runs={}
        for m,v in zip(METHODS+(NEW,),[0.9,0.8,0.95,0.5,0.7]):
            rows=[dict(circuit_id="a",source_sha256="synthetic",status="success",score=v)]
            cs,s=aggregate(rows,["a"],m)
            runs[m]=dict(rows=rows,circuits=cs,summary=s,source={})
        return runs

    def test_fifth_panel_is_last_and_centered(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t);runs=self.runs()
            grid(out,"score",runs,{m:"PANEL_"+m for m in runs})
            text=(out/"grafici/score.tex").read_text()
            self.assertEqual(text.count(r"\begin{minipage}"),5)
            self.assertEqual(text.count(r"\makebox[\linewidth][c]"),1)
            self.assertGreater(text.index("PANEL_"+NEW),text.index(r"\makebox[\linewidth][c]"))
            self.assertEqual(method_order({}),METHODS)

    def test_extended_pair_included_without_changing_default(self):
        runs=self.runs();plan=dict(bootstrap_seed=1,bootstrap_draws=100,confidence=.95)
        self.assertNotIn(NEW,compare(runs,plan)["pairs"])
        comparison=compare(runs,plan,methods=METHODS+(NEW,))
        self.assertAlmostEqual(comparison["pairs"][NEW]["mean_difference"],.2)
        self.assertEqual(len(comparison["available_methods"]),5)

    def test_qubits_come_from_manifest_not_name(self):
        d=analyze(self.runs(),dict(circuits=[dict(circuit_id="a",split="test",num_qubits=4)]))
        self.assertEqual(d["groups"][0]["n"],1)
        self.assertEqual(d["groups"][0]["equal"],0)
        self.assertAlmostEqual(d["difference"],.2)
        self.assertAlmostEqual(d["relative_decrease"],.2/.9)

if __name__=="__main__":
    unittest.main()
