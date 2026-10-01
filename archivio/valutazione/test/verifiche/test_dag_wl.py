"""Controlli tecnici su circuiti sintetici; nessuna inferenza o Test reale."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"strumenti"))
from common import ROOT, digest, read, save
sys.path.insert(0,str(ROOT))
from dag_wl_core import SUPPORTED_H, descriptor, graph_from_qasm, graph_summary, wl_counts, similarity, rank, prepare_wl
from dag_wl_campaign import prompt_variant, summary_messages, cli
from dag_wl_validation import transfer_metrics, summarize, CANDIDATES, load_selection

HEADER='OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; '
A=HEADER+'h q[0]; cx q[0],q[1]; z q[1];'
B=HEADER+'h q[0]; z q[1]; cx q[0],q[1];'

class KernelTests(unittest.TestCase):
    def test_identity_and_symmetry(self):
        a,b=descriptor(A),descriptor(B)
        for h in SUPPORTED_H:
            self.assertAlmostEqual(similarity(a["counts"],a["counts"],h),1)
            self.assertEqual(similarity(a["counts"],b["counts"],h),similarity(b["counts"],a["counts"],h))
            self.assertLess(similarity(a["counts"],b["counts"],h),1)

    def test_same_gates_different_neighborhoods(self):
        a,b=descriptor(A),descriptor(B)
        self.assertEqual(a["counts"][0],b["counts"][0])
        self.assertNotEqual(a["counts"][1],b["counts"][1])

    def test_wire_renaming_and_independent_instruction_order(self):
        a=descriptor(A)
        renamed=descriptor(HEADER+'h q[1]; cx q[1],q[0]; z q[0];')
        self.assertEqual(a["counts"],renamed["counts"])
        a=descriptor(HEADER+'h q[0]; z q[1]; cx q[0],q[1];')
        b=descriptor(HEADER+'z q[1]; h q[0]; cx q[0],q[1];')
        self.assertEqual(a["counts"],b["counts"])

    def test_control_target_roles(self):
        a=descriptor(HEADER+'h q[0]; cx q[0],q[1];')
        b=descriptor(HEADER+'h q[0]; cx q[1],q[0];')
        self.assertNotEqual(a["counts"][1],b["counts"][1])

    def test_parallel_edges_preserved(self):
        graph=graph_from_qasm(HEADER+'cx q[0],q[1]; cx q[0],q[1];')
        pairs={}
        for a,b,_ in graph["edges"]:
            pairs[a,b]=pairs.get((a,b),0)+1
        self.assertIn(2,pairs.values())
        changed=copy.deepcopy(graph)
        changed["edges"].pop()
        self.assertNotEqual(wl_counts(graph),wl_counts(changed))

    def test_direction_is_preserved(self):
        g=graph_from_qasm(A)
        reverse=copy.deepcopy(g)
        reverse["edges"]=[[b,a,r] for a,b,r in g["edges"]]
        self.assertNotEqual(wl_counts(g)[1],wl_counts(reverse)[1])

    def test_numeric_parameters_and_idle_qubits(self):
        a=descriptor(HEADER+'rz(0.2) q[0];')
        b=descriptor(HEADER+'rz(1.2) q[0];')
        self.assertNotEqual(a["counts"][0],b["counts"][0])
        idle=descriptor(HEADER)
        self.assertEqual(sum(idle["counts"][0].values()),4)
        self.assertAlmostEqual(similarity(idle["counts"],idle["counts"],1),1)

    def test_summary_counts(self):
        summary=descriptor(A)["summary"]
        self.assertEqual(summary["operation_nodes_including_barriers"],3)
        self.assertEqual(summary["two_qubit_interaction_pairs"],1)
        self.assertEqual(summary["dependency_layers_including_barriers"],3)
        self.assertEqual(descriptor(B)["summary"]["dependency_layers_including_barriers"],2)
        self.assertEqual(sum(x["count"] for x in summary["most_frequent_direct_transitions"]),2)

    def test_extended_counts_preserve_first_three_rounds(self):
        graph=graph_from_qasm(A)
        old=wl_counts(graph,max_h=3)
        extended=wl_counts(graph,max_h=30)
        self.assertEqual(len(extended),31)
        self.assertEqual(extended[:4],old)
        for h in (1,2,3):
            self.assertEqual(similarity(old,old,h),similarity(extended,extended,h))

    def test_short_index_refused_for_six_rounds(self):
        old=wl_counts(graph_from_qasm(A),max_h=3)
        with self.assertRaisesRegex(ValueError,"Istogrammi"):
            similarity(old,old,30)

    def test_invalid_h(self):
        for h in (0,31,True):
            with self.assertRaises(ValueError):
                similarity([],[],h)

class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from prototype.quantum_assistant.adapters.rag_dataset import load_corpus
        cls.corpus=load_corpus()
        # Real train labels, synthetic descriptors: pipeline test, never an experiment.
        cls.index={r["rag_id"]:descriptor(A) for r in cls.corpus.records}

    def prepare(self, summary):
        return prepare_wl(A,corpus=self.corpus,index=self.index,h=1,with_summary=summary,index_sha256="synthetic")

    def test_filter_and_deterministic_ties(self):
        query=descriptor(A)
        r=rank(self.corpus,self.index,query,["quantinuum_h2_56"],"expected_fidelity",1)
        self.assertTrue(all(x["selected_device"]["device_id"]=="quantinuum_h2_56" for x,_ in r))
        self.assertEqual([x["rag_id"] for x,_ in r],sorted(x["rag_id"] for x,_ in r))

    def test_same_examples_unchanged_base_prompt(self):
        from prototype.prompting.minimal import model_input
        from prototype.prompting.facts import messages
        _,p1,r1=self.prepare(False)
        _,p2,r2=self.prepare(True)
        self.assertEqual(r1["records"],r2["records"])
        self.assertEqual(model_input(p1),model_input(p2))
        self.assertNotIn("dag_summaries",p1)
        plain=messages(p1)
        augmented=summary_messages(p2)
        self.assertTrue(augmented[0]["content"].startswith(plain[0]["content"]))
        self.assertIn("dag_summaries",augmented[0]["content"])
        self.assertIn("current_circuit",augmented[0]["content"])

    def test_decision_adapter_and_restore(self):
        import app
        _,prompt,_=self.prepare(True)
        directory=Path(tempfile.mkdtemp())
        response={"selected_device":"quantinuum_h2_56","config_id":"o2_default_default",
                  "facts":[{"assertion_type":"selected_device_has_enough_qubits"}],
                  "hypothesis":"Proposta tecnica, da verificare."}
        # Discover exact field name from the frozen schema, do not change schema.
        from prototype.prompting.facts import response_schema
        props=response_schema()["properties"]["facts"]["items"]["properties"]
        if "assertion" in props:
            response["facts"]=[{"assertion":"selected_device_has_enough_qubits"}]
        seen=[]
        def fake_http(endpoint,payload,path):
            seen.append((endpoint,payload))
            if endpoint=="/apply-template":return {"prompt":payload["messages"][0]["content"]}
            if endpoint=="/tokenize":return {"tokens":[1]*500}
            return {"content":json.dumps(response),"stop":True,"tokens_predicted":30}
        original=app.decide
        with prompt_variant(True):
            result=app.decide(prompt,directory,fake_http,60000)
        self.assertIs(app.decide,original)
        self.assertTrue(result["selection_valid"])
        self.assertIn("dag_summaries",seen[0][1]["messages"][0]["content"])
        self.assertIn("dag_summaries",seen[1][1]["content"])
        self.assertEqual(seen[2][1]["temperature"],0)
        self.assertEqual(seen[2][1]["json_schema"],response_schema())

    def test_missing_alias_refused(self):
        _,p,_=self.prepare(True)
        p["dag_summaries"]["examples"][0]["example_id"]="E99"
        with self.assertRaises(ValueError):summary_messages(p)

    def test_missing_score_is_not_zero(self):
        chosen=list(self.corpus.records[:5])
        pairs={(c["device_id"],c["config_id"]) for r in chosen for c in r["top_configurations"]}
        table={p:{"score":.7,"summary_id":"synthetic"} for p in pairs}
        top=chosen[0]["top_configurations"][0]
        table[top["device_id"],top["config_id"]]["score"]=None
        table["other","config"]={"score":.9}
        result=transfer_metrics(chosen,table,{p[0] for p in table})
        self.assertIsNone(result["top1_score"])
        self.assertIsNone(result["top1_regret"])
        self.assertFalse(result["reference_is_exhaustive"])

    def test_test_requires_selection(self):
        for variant in (False,True):
            with self.assertRaises(SystemExit) as cm:
                cli(variant,["--esegui"])
            self.assertEqual(cm.exception.code,2)

    def test_private_index_integrity(self):
        from dag_wl_core import prepare_index
        one = SimpleNamespace(records=self.corpus.records[:1], source_sha256=self.corpus.source_sha256)
        with tempfile.TemporaryDirectory() as tmp:
            index, seal = prepare_index(one, Path(tmp))
            self.assertEqual(len(index), 1)
            self.assertEqual(prepare_index(one, Path(tmp))[1], seal)
            path = next((Path(tmp)/"record").glob("*.json"))
            value = read(path)
            key = next(iter(value["counts"][0]))
            value["counts"][0][key] += 1
            path.write_text(json.dumps(value))
            with self.assertRaises(ValueError):
                prepare_index(one, Path(tmp))

    def test_validation_cli_synthetic_88_resume_and_freeze(self):
        import dag_wl_validation as val
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root/"synthetic.qasm"
            source.write_text(A)
            from common import sha
            rows = [{"circuit_id": f"synthetic_{i:02d}", "source_sha256": sha(source),
                     "split": "validation"} for i in range(88)]
            small_corpus = SimpleNamespace(records=self.corpus.records[:5], transform=self.corpus.transform)
            pairs = {(c["device_id"], c["config_id"]) for r in self.corpus.records for c in r["top_configurations"]}
            tables = {r["circuit_id"]:{p:{"score":.8,"summary_id":"synthetic"} for p in pairs} for r in rows}
            from contextlib import ExitStack, redirect_stdout
            import io
            with ExitStack() as stack:
                for name,value in [("BASE",root),("validation_check",lambda:{"ready":True}),
                                   ("validation_rows",lambda:rows),("code_identity",lambda:{"synthetic":"1"}),
                                   ("aggregate_hash",lambda:"synthetic"),
                                   ("prepare_index",lambda *a:(self.index,"synthetic")),
                                   ("load_scores",lambda _:tables),("source_path",lambda _:source)]:
                    stack.enter_context(patch.object(val,name,value))
                stack.enter_context(patch("prototype.quantum_assistant.adapters.rag_dataset.load_corpus", return_value=small_corpus))
                stack.enter_context(redirect_stdout(io.StringIO()))
                self.assertEqual(val.cli(["--esegui"]),0)
                report = read(root/"esecuzioni/wl_v3/riepilogo.json")
                self.assertEqual(set(report["methods"]), set(CANDIDATES))
                self.assertEqual(len(CANDIDATES), 31)
                tex=(root/"esecuzioni/wl_v3/report_validation.tex").read_text()
                self.assertIn("WL, h=30",tex)
                self.assertIn("longtable",tex)
                self.assertIn("addlegendentry{Manhattan}",tex)
                self.assertNotIn("@@",tex)
                self.assertEqual(report["successes"],88)
                self.assertIsNone(report["selected_h"])
                self.assertEqual(len(report["common_top1_circuits"]),88)
                self.assertEqual(val.cli(["--esegui"]),0)
                self.assertEqual(val.cli(["--congela","--h","30","--motivazione","synthetic test"]),0)
                selected = val.load_selection(root/"selezioni/wl_v3/wl_h30.json")
                self.assertEqual(selected["h"],30)

    def test_invalid_selection_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"bad.json"
            save(p,{"h":2,"k":5,"sha256":"bad"})
            with self.assertRaises(ValueError):load_selection(p)

if __name__=="__main__":
    unittest.main()
