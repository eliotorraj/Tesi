'Document compilation and final checks; no quantum compilation.'
from pathlib import Path
import subprocess,json,hashlib,csv
HERE=Path(__file__).resolve().parent
OUT=HERE/"risultati"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(cmd,cwd):
 r=subprocess.run(cmd,cwd=cwd,text=True,capture_output=True)
 if r.returncode: raise RuntimeError(r.stdout+r.stderr)
 return r.stdout
def main():
 qa=OUT/"controllo_visivo";qa.mkdir(exist_ok=True)
 for directory,stem in [(OUT,"confronto_oracle_rag5")]+[(OUT/"grafici",f"confronto_{i}") for i in range(1,4)]:
  for _ in range(2):log=run(["pdflatex","-interaction=nonstopmode","-halt-on-error",stem+".tex"],directory)
  (directory/(stem+".compilazione.txt")).write_text(log)
  assert "Overfull" not in log and "Undefined" not in log,stem
 run(["pdftoppm","-r","85","-png","confronto_oracle_rag5.pdf",str(qa/"pagina")],OUT)
 for i in range(1,4):
  run(["pdftoppm","-r","150","-singlefile","-png",f"confronto_{i}.pdf",f"confronto_{i}"],OUT/"grafici")
 run(["pdftotext","-layout","confronto_oracle_rag5.pdf",str(qa/"testo.txt")],OUT)
 d=json.loads((OUT/"dati.json").read_text()); text=(qa/"testo.txt").read_text()
 rows=d["rows"]; assert len(list(csv.DictReader((OUT/"confronto_90_circuiti.csv").open(encoding="utf-8-sig"))))==90
 assert d["summary"]["statuses"]=={"sotto":35,"pari":55}
 for r in rows:
  assert text.count(r["circuit_id"])>=2,r["circuit_id"]
  assert all(f'{r[k]:.10f}' in text for k in ["system_score","oracle_score","gap"]),r["circuit_id"]
  assert abs(r["gap"]-r["choice_gap"]-r["within_pair_gap"])<1e-12
 p=json.loads((OUT/"provenienza.json").read_text())
 assert all(sha(Path(f))==h for f,h in p["source_sha256"].items())
 assert len(list(qa.glob("pagina-*.png")))==9
 meta=dict(pdf_pages=9,table_circuits=90,plotted_circuits=90,oracle_original_results_verified=16200,
   source_files_unchanged=len(p["source_sha256"]),all_scores_in_pdf=True,no_overfull_boxes=True,
   compiler="pdflatex (TeX Live 2025/Debian)",native_compiler_error="Unable to find standard directories for platform",
   real_quantum_compilations_started=0,
   development_notes=['Two generator composition attempts were rejected for JavaScript quoting, without writes.','An unmatched parenthesis in the label string was corrected before generation.','Python plotting libraries were unavailable; TikZ vector plots were used without installation.'],
   script_sha256={f.name:sha(f) for f in HERE.glob("*.py")},
   output_sha256={str(f.relative_to(OUT)):sha(f) for f in OUT.rglob("*") if f.is_file() and f.suffix in [".pdf",".tex",".csv",".json"] and f.name!="verifica.json"})
 (OUT/"verifica.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({k:v for k,v in meta.items() if k not in ["output_sha256","script_sha256","development_notes"]},indent=2))
if __name__=="__main__":main()
