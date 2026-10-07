'Reproducible summaries from saved outcomes; scientific plots with PGFPlots.'
from __future__ import annotations
import csv
import json
import math
import statistics
import subprocess
from pathlib import Path
from common import read, save, sha, now, AREA, PLAN

def escaped(text):
    return str(text).replace("\\",r"\textbackslash{}").replace("_",r"\_").replace("%",r"\%").replace("&",r"\&").replace("#",r"\#")

def summary(rows, expected):
    success=[r for r in rows if r["status"]=="success"]
    scores=[r["score"] for r in success]
    result={"expected_circuits":expected,"completed_circuits":len(rows),"successes":len(success),
            "failures":len(rows)-len(success),"pending":expected-len(rows),
            "retries":sum(r.get("retries",0) for r in rows),
            "score_denominator":len(scores),"mean_score":statistics.mean(scores) if scores else None,
            "secondary":{"median_score":statistics.median(scores) if scores else None,
              "failure_causes":{cause:sum(r.get("error",r["status"])==cause for r in rows if r["status"]!="success")
                                for cause in sorted({r.get("error",r["status"]) for r in rows if r["status"]!="success"})}}}
    for name in ("total_seconds","compilation_seconds","compilation_process_seconds","choice_seconds","llm_response_seconds","total_tokens"):
        values=[r[name] for r in rows if isinstance(r.get(name),(int,float))]
        result[name]={"sum_known":sum(values),"mean_known":statistics.mean(values) if values else None,
                      "measured_circuits":len(values),"missing_circuits":len(rows)-len(values)}
    return result

def generate(base):
    files=sorted((base/"circuiti").glob("*/esito.json"))
    rows=[read(p) for p in files]
    meta=read(base/"esecuzione.json")
    expected=meta.get("expected_circuits",1 if meta["kind"]=="technical" else 90)
    fingerprint=__import__("hashlib").sha256(("".join(sha(p) for p in files)+sha(Path(__file__))).encode()).hexdigest()
    output=base/"analisi"/fingerprint[:16]
    if (output/"completato.json").exists():
        return output
    # Each analysis has an identity; original data and earlier analyses are retained.
    output.mkdir(parents=True,exist_ok=True)
    report=summary(rows,expected)
    report["exploratory"]=read(PLAN)["exploratory"]
    report.update(kind=meta["kind"],method=meta["method"],input_sha256=fingerprint,
                  units={"times":"seconds","score":"expected_fidelity [0,1]","tokens":"tokens"},
                  timing="wall clock perf_counter; total includes preparation and all attempts; process startup separate")
    if not (output/"riepilogo.json").exists():
        save(output/"riepilogo.json",report)
    fields=["circuit_id","status","score","retries","total_tokens","total_seconds","compilation_seconds",
            "compilation_process_seconds","choice_seconds","llm_response_seconds","error"]
    tables=output/"tabelle";tables.mkdir(exist_ok=True)
    with (tables/"circuiti.csv").open("w",newline="",encoding="utf-8") as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,extrasaction="ignore")
        writer.writeheader();writer.writerows(rows)
    graphs=output/"grafici";graphs.mkdir(exist_ok=True)
    # CSV and plot sources are separate from the thesis-ready document.
    with (graphs/"score.csv").open("w",newline="",encoding="utf-8") as stream:
        writer=csv.writer(stream);writer.writerow(["indice","score"])
        for i,row in enumerate(rows,1):
            if row["status"]=="success":
                writer.writerow([i,row["score"]])
    plot="""\\begin{tikzpicture}
\\begin{axis}[width=0.95\\linewidth,height=6cm,xlabel={Circuit index},ylabel={Expected fidelity},
ymin=0,ymax=1,grid=major]
\\addplot[only marks,mark=*,mark size=1.4pt] table[x=indice,y=score,col sep=comma]{../grafici/score.csv};
\\end{axis}
\\end{tikzpicture}

"""
    (graphs/"score.tex").write_text(plot,encoding="utf-8")
    mean='unavailable' if report["mean_score"] is None else f'{report["mean_score"]:.8g}'
    body="\\section*{"+escaped({"random":"Random","llm_rag":"LLM + RAG","llm_senza_rag":'LLM no RAG',"mqt_predictor":"MQT Predictor"}[meta["method"]])+"}\n"
    body+=("""Technical check on a synthetic circuit. This is not a Test evaluation.

""" if meta["kind"]=="technical"
           else """Independent Test on held-out circuits. No exhaustive matrix is required.

""")
    body+="""Separate exploratory MQT run: selector trained on 384 of the 396 train samples, with 12 excluded; four observed classes. Collection: 1853/1878 compilations, successes at 100 seconds and recovery attempts at 300 seconds. Does not meet the original Training set completeness requirement.

"""
    body+=f"Completed: {len(rows)}/{expected}. Successes: {len([r for r in rows if r['status'] == 'success'])}. "
    body+=f"Failures: {report['failures']}. Additional attempts: {report['retries']}.\n\n"
    body+=f"Mean score only on the {report['score_denominator']} successes: {mean}. "
    body+="One compilation per circuit; Qiskit seed 0. MQT's internal seed is not controlled. "
    body+="""Failures are not imputed. Missing times are not zeros.

"""
    body+="""\\par\\medskip\\noindent\\begin{tabular}{lrr}\\hline Measurement & Known sum & Measured cases\\\\\\hline
"""+"\n"
    for label,key in [('Total time (s)',"total_seconds"),('Compilation (s)',"compilation_seconds"),
                      ('LLM response (s)',"llm_response_seconds"),("Token LLM","total_tokens")]:
        m=report[key]
        amount=f"{m['sum_known']:.4g}" if m["measured_circuits"] else "--"
        body+=f"{label} & {amount} & {m['measured_circuits']}/{len(rows)}"+r"\\"+"\n"
    body+=r"\hline\end{tabular}"+"\n\n"+r"\input{../grafici/score.tex}"+"\n"
    body+="""
The score estimates fidelity on synthetic Targets. The mean over successes does not prove superiority. """
    body+='The comparison between methods also uses shared circuits and failures. '
    body+="""To reconstruct each case, consult circuiti.csv and the original records.

"""
    latex=output/"latex";latex.mkdir(exist_ok=True)
    (latex/"risultati.tex").write_text(body,encoding="utf-8")
    standalone=r"""\documentclass[a4paper,11pt]{article}
\usepackage[margin=2.2cm]{geometry}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\begin{document}
\input{risultati.tex}
\end{document}
"""
    (latex/"verifica.tex").write_text(standalone,encoding="utf-8")
    import shutil
    if shutil.which("pdflatex"):
        process=subprocess.run(["pdflatex","-interaction=nonstopmode","-halt-on-error","verifica.tex"],
                               cwd=latex,capture_output=True,timeout=90)
        (latex/"compilazione_latex.log").write_bytes(process.stdout+process.stderr)
        if process.returncode:
            raise RuntimeError('LaTeX report not compiled: '+str(latex/"compilazione_latex.log"))
    save(output/"completato.json",{"at":now(),"input_sha256":fingerprint,"pdf_available":(latex/"verifica.pdf").exists()})
    return output
