"""Controlli di provenienza e coerenza del report, senza nuovi esperimenti."""
from pathlib import Path
import hashlib,json,sys
BASE=Path(__file__).resolve().parent
REPO=BASE.parents[3]
D=json.loads((BASE/"dati.json").read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert all(sha(REPO/p)==h for p,h in D["sources_sha256"].items())
paths={"M":"risultati/llm_rag","W":"dag_wl_retrieval/risultati/llm_rag_dag_wl","S":"dag_wl_sintesi/risultati/llm_rag_dag_wl_sintesi"}
n=0
for k,rows in D["runs"].items():
 assert len(rows)==90
 for r in rows:
  assert r["status"]=="success"
  f=REPO/"archivio/valutazione/test"/paths[k]/"circuiti"/r["circuit_id"]
  for i in range(1,r["llm_calls"]+1):
   call=json.loads((f/f"attempt_{i}/call/request.json").read_text())
   assert ("dag_summaries:" in call["prompt"])==(k=="S")
   n+=1
assert n==504
sys.path.insert(0,str(REPO/"archivio/valutazione/test/strumenti"))
from dag_wl_core import graph_from_qasm,wl_counts,similarity
prefix='OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\n'
a=graph_from_qasm(prefix+'h q[0]; cx q[0],q[1]; z q[1];')
b=graph_from_qasm(prefix+'h q[0]; z q[1]; cx q[0],q[1];')
ca=wl_counts(a,2);cb=wl_counts(b,2)
assert ca[0]==cb[0] and ca[1]!=cb[1] and ca[2]!=cb[2]
assert len(a["nodes"])==len(b["nodes"])==7
example={"A":a,"B":b,"equal_initial_counts":True,
         "similarity_h1":similarity(ca,cb,1),"similarity_h2":similarity(ca,cb,2)}
(BASE/"esempi_didattici.json").write_text(json.dumps(example,indent=2)+"\n")
log=(BASE/"confronto_manhattan_wl.log").read_text(errors="replace")
assert "Overfull" not in log and "undefined" not in log.lower()
assert "Output written on confronto_manhattan_wl.pdf" in log
report={"source_files_unchanged":len(D["sources_sha256"]),"cases":270,"attempts":n,
        "graph_summary_present_in_final_call_prompts_only_for_S":True,
        "toy_dags_checked_with_actual_implementation":True,
        "latex_overfull_or_undefined":False,
        "artifact_sha256":{p.name:sha(p) for p in BASE.iterdir() if p.suffix in {".py",".tex",".pdf",".md"}},
        "checks":D["checks"]}
(BASE/"verifica_report.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({k:v for k,v in report.items() if k!="artifact_sha256"},indent=2))
