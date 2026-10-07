'Generate figures and LaTeX from frozen data without transcribing numbers.'
import argparse
import json
import os
import random
import subprocess
from collections import Counter, defaultdict
from statistics import median
from .common import OUTPUT, ROOT, read_json, write_json
from .finalize import FINAL, verify_local_selection
from .evaluate import write_csv, trial_summary

def tex(value):
    table={"\\":r"\textbackslash{}","&":r"\&","%":r"\%","$":r"\$","#":r"\#","_":r"\_","{":r"\{","}":r"\}"}
    return "".join(table.get(c,c) for c in str(value))

def fmt(value):
    return "n/d" if value is None else f"{value:.4g}"

def bootstrap(values,draws=2000,seed=20260913):
    result={"n":len(values),"median":median(values) if values else None,"ci95":None}
    if len(values)>1:
        rng=random.Random(seed)
        ordered=sorted(median(rng.choices(values,k=len(values))) for _ in range(draws))
        result.update(ci95=[ordered[int(.025*(draws-1))],ordered[int(.975*(draws-1))]],seed=seed,draws=draws)
    return result

def grouped_analysis(rows,winner):
    trials=defaultdict(list)
    for row in rows: trials[row["trial_id"]].append(row)
    reference={r["source_sha256"]:r for r in trials[winner]}
    paired=[];groups=[]
    for trial,records in sorted(trials.items()):
        common=[r for r in records if r["regret_absolute"] is not None and reference[r["source_sha256"]]["regret_absolute"] is not None]
        if trial!=winner:
            values=[reference[r["source_sha256"]]["regret_absolute"]-r["regret_absolute"] for r in common]
            paired.append({"winner":winner,"comparison":trial,"quantity":"median paired regret: winner minus comparison",
                           "source_hashes":[r["source_sha256"] for r in common],**bootstrap(values)})
        for key in ("family","num_qubits"):
            for value in sorted({str(r[key]) for r in records}):
                selected=[r for r in records if str(r[key])==value]
                groups.append({"trial_id":trial,"group_field":key,"group_value":value,**trial_summary(selected)})
    return dict(trials),paired,groups

def build_report(compile_pdf=True):
    verify_local_selection()
    final=read_json(FINAL);study=read_json(OUTPUT/"frozen_study.json")
    analysis=OUTPUT/"studies"/study["study_id"]/"analysis"
    rows=read_json(analysis/"episode_results.json");selection=read_json(analysis/"selection.json")
    trials,paired,groups=grouped_analysis(rows,selection["winner"])
    directory=OUTPUT/"report";picture_dir=directory/"figures";picture_dir.mkdir(parents=True,exist_ok=True)
    write_json(directory/"paired_uncertainty.json",paired);write_csv(directory/"groups.csv",groups)
    from .technical import technical_summary
    technical=technical_summary()
    write_json(directory/"technical_history.json",technical)
    write_csv(directory/"technical_episodes.csv",technical["episodes"])
    write_csv(directory/"server_runs.csv",technical["servers"])
    write_json(directory/"plot_input.json",{"rows":rows,"trials":trials,"groups":groups})
    plotting_python=OUTPUT/"runtime/python/bin/python"
    subprocess.run([str(plotting_python),"-m","llm_selection.plots",str(directory/"plot_input.json"),
                    "--output",str(picture_dir)],cwd=ROOT,check=True)
    pictures=read_json(picture_dir/"manifest.json")
    parts=[r"\providecommand{\ValidationFiguresPath}{figures/}",
        '\\section{Local LLM selection}',
        'Three model families and three settings are compared on the same 88 validation circuits. Selection concerns the local model with RAG. Test remains separate and is not opened by this procedure.',
        '\\subsection{Hardware, data and measurements}',
        'The host uses an AMD Ryzen 5 5600G, 16 GB of RAM and a Radeon RX 6750 XT with 12 GB of VRAM. WSL has a 10 GB RAM limit and separate swap. Weights are on drive D. The MQT environment retains Python 3.12 and uv.lock; llama.cpp b10930 uses Vulkan and loads one model at a time.',
        'Five examples are retrieved from train only. Manhattan distance uses 49 features with log1p and train-fitted divisors. Full circuits, catalog, mask and evidence are preserved. Fully connected topology uses an exact rule that reconstructs every edge in the same order. Prompts are never truncated to fit context.',
        'The monitor preserves RAM, VRAM and temperature samples. Automatic pauses of the inference process are included in timings. Operational limits are precautionary and do not identify the cause of the initial host shutdown. ASIC sensor power is not whole-computer energy consumption.',
        '\\begin{center}\\begin{tabular}{llll}\\toprule Model & Weights & Context & KV cache\\\\\\midrule']
    for name,profile in study["models"].items():
        parts.append(" & ".join(tex(v) for v in (name,profile["weight_precision"],profile["context"],profile["cache_type"]))+r"\\")
    parts += [r"\bottomrule\end{tabular}\end{center}",
        'Gemma E4B has more total than active parameters. Revisions, sizes, SHA-256, tokenizers and precision choices are preserved in manifests and the final configuration.',
        '\\subsection{Technical checks and development}',
        'Technical checks precede freezing and use train. technical\\_episodes.csv and server\\_runs.csv also retain rejected settings, interruptions and loads stopped before a response. Earlier exploratory records remain in technical/ and incidents/.',
        'The recorded technical-episode summary contains '+str(len(technical["episodes"]))+' episodes: '+
        tex(", ".join(str(count)+" "+status for status,count in sorted(technical["episode_status_counts"].items())))+'. These counts are not validation results.',
        '\\subsection{Settings and criteria}',
        'The compared settings are a base prompt at temperature 0, a base prompt at 0.7 and a prompt with explicit checks at 0. Extended reasoning is disabled. The first valid response is final. Up to three calls can repair nonconforming responses; transport, interruptions and repairs are recorded separately.',
        '\\begin{center}\\begin{tabular}{lr}\\toprule Parameter & Value\\\\\\midrule']
    for key in ("max_tokens","top_p","top_k","min_p","seed","repeat_penalty","presence_penalty","frequency_penalty","mirostat","typical_p"):
        parts.append(tex(key)+" & "+tex(study["fixed"][key])+r"\\")
    parts += ['Timeout per call [s] & '+str(study["timeout_seconds"])+r"\\",
        r"\bottomrule\end{tabular}\end{center}",
        '\\[R(c)=F_{\\mathrm{oracle}}(c)-F_{\\mathrm{selected}}(c).\\]',
        'Pair fidelity is the median of seeds 0, 1 and 2, only when all three succeed. The oracle requires a fully successful compatible matrix. Missing regret remains missing. Qiskit scores and timings are reused from prior results; new LLM call timings are measured.',
        'All decisions are sealed before scores are read. Selection prioritizes valid, compilable choices, then median regret on the same successful, evaluable circuits. Initial JSON validity, calls and measured costs follow. The circuit is the statistical unit: seeds and attempts do not increase sample size.',
        '\\subsection{Results}',
        '\\begin{center}\\small\\begin{tabular}{lrrrr}\\toprule Trial & Successful/88 & Regret $n$ & Median regret & Valid on first call\\\\\\midrule']
    for trial,s in sorted(selection["summaries"].items()):
        parts.append(" & ".join([tex(trial),str(s["valid_and_compilable"]),str(s["regret_available"]),fmt(s["median_regret_absolute"]),str(s["first_attempt_valid"])])+r"\\")
    parts += [r"\bottomrule\end{tabular}\end{center}",
        'The selected configuration is '+r"\textbf{"+tex(selection["winner"])+'}. Selection steps, values and denominators are preserved in selection.json. This selection does not establish general model superiority.']
    for name,caption in pictures:
        parts += [r"\begin{figure}[htbp]\centering",r"\includegraphics[width=\linewidth]{\ValidationFiguresPath "+name+".png}",
                  r"\caption{"+tex(caption)+r"}\end{figure}"]
    parts += [r"\clearpage\subsection{Incertezza e limiti}",
        'paired\\_uncertainty.json compares the winner and alternatives on the same evaluable circuits. It reports median paired regret differences and 95\\% percentile intervals using 2000 circuit resamples and seed 20260913. No interval is computed with fewer than two circuits. These descriptive intervals do not adjust for selection across settings.',
        'Cache, request order, pauses and other host applications affect timings. Sampled maxima may miss instantaneous peaks. Missing values remain explicit. Technical checks and rejected configurations are retained separately.',
        'Local validation does not require full qcompile. The historical Test plan includes a no-RAG model, MQT, a frontier model and Qiskit references after the protocol checks. This document contains no Test results.',
        '\\subsection{Data and sources}',
        "Regenerate the document through llm\\_selection's report command. episodes.csv, trials.csv, groups.csv and JSON/JSONL records support further analysis without transcribing results."]
    for model,profile in study["models"].items():
        parts.append(tex(model)+": "+tex(profile["precision_reason"])+". "
                     "Batch "+str(profile["batch"])+", micro-batch "+str(profile["micro_batch"])+', GPU layers '+tex(profile["gpu_layers"])+".")
    for model,profile in study["models"].items():
        artifact=profile["artifact"]
        parts += [tex(model)+r": \url{https://huggingface.co/"+artifact["base_repository"]+r"}.",
            'Actual weights: \\url{'+artifact["url"]+r"}.",
            r"SHA-256: \texttt{\seqsplit{"+artifact["gguf_sha256"]+r"}}."]
    parts += [r"\url{https://github.com/ggml-org/llama.cpp/blob/b10930/tools/server/README.md}."]
    (directory/"validation_selection.tex").write_text("\n\n".join(parts)+"\n",encoding="utf-8")
    standalone="""\\documentclass[11pt,a4paper]{article}
\\usepackage[utf8]{inputenc}
\\usepackage[T1]{fontenc}
\\usepackage[english]{babel}
\\usepackage[margin=2.1cm]{geometry}
\\usepackage{graphicx,booktabs,amsmath,seqsplit,microtype}
\\usepackage[hidelinks]{hyperref}
\\title{Local LLM selection}
\\author{Validation experiments}
\\date{}
\\begin{document}
\\maketitle
\\input{validation_selection.tex}
\\end{document}
"""
    (directory/"standalone.tex").write_text(standalone,encoding="utf-8")
    pdf=None
    if compile_pdf:
        executable=OUTPUT/"runtime/tectonic/tectonic"
        if not executable.exists(): raise RuntimeError('Sources ready. Install the compiler first: python -m llm_selection.setup_report')
        env=dict(os.environ);env["TECTONIC_CACHE_DIR"]=str(OUTPUT/"runtime/tectonic-cache")
        with (directory/"compile.log").open("w") as log:
            subprocess.run([str(executable),"--keep-logs","--outdir",str(directory),str(directory/"standalone.tex")],
                           cwd=directory,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        pdf=directory/"standalone.pdf"
        subprocess.run([str(OUTPUT/"runtime/python/bin/python"),"-m","llm_selection.render_pdf",str(pdf),
                        "--output",str(directory/"preview")],cwd=ROOT,check=True)
    return {"directory":str(directory),"pdf":str(pdf) if pdf else None,
            "visual_review":'Inspect the PNG pages before including the document in the thesis.'}

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--sources-only",action="store_true");args=parser.parse_args()
    print(json.dumps(build_report(compile_pdf=not args.sources_only),indent=2))
