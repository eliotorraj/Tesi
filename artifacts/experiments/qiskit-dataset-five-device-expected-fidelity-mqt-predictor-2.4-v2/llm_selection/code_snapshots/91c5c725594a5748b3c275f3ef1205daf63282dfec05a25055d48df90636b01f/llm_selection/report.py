"""Figure e documento LaTeX generati dai dati congelati, senza numeri trascritti."""
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
        r"\section{Selezione del modello LLM locale}",
        "Sono confrontate tre famiglie e tre impostazioni sugli stessi 88 circuiti di validation. "
        "La scelta riguarda il modello locale con RAG. Il test resta separato e non viene aperto da questa procedura.",
        r"\subsection{Hardware, dati e misure}",
        "Il PC usa AMD Ryzen 5 5600G, 16 GB di RAM e Radeon RX 6750 XT con 12 GB di VRAM. "
        "WSL ha un limite di 10 GB di RAM e swap separato. I pesi sono sul disco D. "
        "L'ambiente MQT conserva Python 3.12 e uv.lock; llama.cpp b10930 usa Vulkan e carica un modello alla volta.",
        "Si recuperano cinque esempi dal solo train. La distanza è Manhattan su 49 caratteristiche, con log1p e divisori stimati sul train. "
        "Circuiti completi, catalogo, maschera ed evidenze sono conservati. Il grafo completo di connettività è scritto con una regola esatta "
        "che permette di ricostruire tutti gli archi nello stesso ordine. Nessun prompt viene troncato per farlo entrare nel contesto.",
        "Il monitor conserva campioni di RAM, VRAM e temperatura. Le pause automatiche del solo processo di inferenza sono incluse nei tempi. "
        "I limiti operativi sono prudenziali e non identificano la causa dello spegnimento iniziale del PC. "
        "La potenza del sensore ASIC non è l'energia consumata dall'intero computer.",
        r"\begin{center}\begin{tabular}{llll}\toprule Modello & Pesi & Contesto & Cache KV\\\midrule"]
    for name,profile in study["models"].items():
        parts.append(" & ".join(tex(v) for v in (name,profile["weight_precision"],profile["context"],profile["cache_type"]))+r"\\")
    parts += [r"\bottomrule\end{tabular}\end{center}",
        "Gemma E4B ha un numero di parametri totali maggiore del numero di parametri attivi. "
        "Revisioni, dimensioni, SHA-256, tokenizer e motivazioni della precisione sono conservati nei manifest e nella configurazione finale.",
        r"\subsection{Prove tecniche e sviluppo}",
        "Le prove tecniche precedono il congelamento e usano il train. I file technical\\_episodes.csv e server\\_runs.csv "
        "riportano anche configurazioni scartate, interruzioni e caricamenti arrestati prima di una risposta. "
        "I registri esplorativi precedenti sono conservati in technical/ e incidents/.",
        "Il riepilogo degli episodi tecnici registrati contiene "+str(len(technical["episodes"]))+" episodi: "+
        tex(", ".join(str(count)+" "+status for status,count in sorted(technical["episode_status_counts"].items())))+". "
        "Questi conteggi non fanno parte dei risultati della validation.",
        r"\subsection{Impostazioni e criteri}",
        "Le impostazioni confrontate sono: prompt base a temperatura 0; prompt base a temperatura 0,7; "
        "prompt con controlli espliciti a temperatura 0. Il ragionamento esteso è disabilitato. "
        "La prima risposta valida è definitiva. Si ammettono al massimo tre chiamate per correggere risposte non conformi; "
        "trasporto, interruzioni e correzioni sono registrati separatamente.",
        r"\begin{center}\begin{tabular}{lr}\toprule Parametro & Valore\\\midrule"]
    for key in ("max_tokens","top_p","top_k","min_p","seed","repeat_penalty","presence_penalty","frequency_penalty","mirostat","typical_p"):
        parts.append(tex(key)+" & "+tex(study["fixed"][key])+r"\\")
    parts += ["Timeout per chiamata [s] & "+str(study["timeout_seconds"])+r"\\",
        r"\bottomrule\end{tabular}\end{center}",
        r"\[R(c)=F_{\mathrm{oracle}}(c)-F_{\mathrm{scelta}}(c).\]",
        "La fedeltà di una coppia è la mediana dei seed 0, 1 e 2, solo se tutti e tre riescono. "
        "L'oracle richiede l'intera matrice compatibile riuscita. I regret mancanti restano mancanti. "
        "I punteggi e i tempi Qiskit sono riutilizzati da risultati precedenti. I nuovi tempi delle chiamate LLM sono misurati.",
        "Prima di leggere gli score sono sigillate tutte le decisioni. La selezione privilegia le scelte valide e compilabili; "
        "a parità usa la mediana del regret sullo stesso insieme di circuiti riusciti e valutabili. Seguono validità JSON iniziale, chiamate e costi misurati. "
        "Il circuito è l'unità statistica: seed e tentativi non aumentano la numerosità.",
        r"\subsection{Risultati}",
        r"\begin{center}\small\begin{tabular}{lrrrr}\toprule Prova & Riuscite/88 & Regret $n$ & Mediana regret & Valide alla prima\\\midrule"]
    for trial,s in sorted(selection["summaries"].items()):
        parts.append(" & ".join([tex(trial),str(s["valid_and_compilable"]),str(s["regret_available"]),fmt(s["median_regret_absolute"]),str(s["first_attempt_valid"])])+r"\\")
    parts += [r"\bottomrule\end{tabular}\end{center}",
        "La configurazione selezionata è "+r"\textbf{"+tex(selection["winner"])+r"}. "
        "I passaggi della scelta, con valori e denominatori, sono conservati in selection.json. "
        "Questa selezione non dimostra una superiorità generale del modello."]
    for name,caption in pictures:
        parts += [r"\begin{figure}[htbp]\centering",r"\includegraphics[width=\linewidth]{\ValidationFiguresPath "+name+".png}",
                  r"\caption{"+tex(caption)+r"}\end{figure}"]
    parts += [r"\clearpage\subsection{Incertezza e limiti}",
        "Il file paired\\_uncertainty.json confronta il vincitore e le alternative sugli stessi circuiti valutabili. "
        "Riporta la mediana delle differenze appaiate di regret e intervalli percentili al 95\\%, con 2000 ricampionamenti di circuiti e seed 20260913. "
        "Con meno di due circuiti non si calcola l'intervallo. Questi intervalli sono descrittivi e non correggono la selezione tra più impostazioni.",
        "Cache, ordine delle richieste, pause e altri programmi del PC influenzano i tempi. I massimi campionati possono perdere picchi istantanei. "
        "I valori mancanti rimangono espliciti. Le prove tecniche e le configurazioni scartate sono conservate separatamente.",
        "La validation locale non richiede qcompile completo. Sul test restano previsti modello senza RAG, MQT, modello di frontiera e riferimenti Qiskit, "
        "dopo i controlli richiesti dal protocollo. Questo documento non contiene risultati del test.",
        r"\subsection{Dati e fonti}",
        "Per rigenerare il documento usare la procedura nel README di llm\\_selection. "
        "episodes.csv, trials.csv, groups.csv e i registri JSON/JSONL permettono nuove analisi senza trascrivere i risultati."]
    for model,profile in study["models"].items():
        parts.append(tex(model)+": "+tex(profile["precision_reason"])+". "
                     "Batch "+str(profile["batch"])+", micro-batch "+str(profile["micro_batch"])+", livelli GPU "+tex(profile["gpu_layers"])+".")
    for model,profile in study["models"].items():
        artifact=profile["artifact"]
        parts += [tex(model)+r": \url{https://huggingface.co/"+artifact["base_repository"]+r"}.",
            r"Pesi effettivi: \url{"+artifact["url"]+r"}.",
            r"SHA-256: \texttt{\seqsplit{"+artifact["gguf_sha256"]+r"}}."]
    parts += [r"\url{https://github.com/ggml-org/llama.cpp/blob/b10930/tools/server/README.md}."]
    (directory/"validation_selection.tex").write_text("\n\n".join(parts)+"\n",encoding="utf-8")
    standalone=r"""\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[italian]{babel}
\usepackage[margin=2.1cm]{geometry}
\usepackage{graphicx,booktabs,amsmath,seqsplit,microtype}
\usepackage[hidelinks]{hyperref}
\title{Selezione del modello LLM locale}
\author{Esperimenti di validation}
\date{}
\begin{document}
\maketitle
\input{validation_selection.tex}
\end{document}
"""
    (directory/"standalone.tex").write_text(standalone,encoding="utf-8")
    pdf=None
    if compile_pdf:
        executable=OUTPUT/"runtime/tectonic/tectonic"
        if not executable.exists(): raise RuntimeError("Sorgenti pronti. Prima installare il compilatore: python -m llm_selection.setup_report")
        env=dict(os.environ);env["TECTONIC_CACHE_DIR"]=str(OUTPUT/"runtime/tectonic-cache")
        with (directory/"compile.log").open("w") as log:
            subprocess.run([str(executable),"--keep-logs","--outdir",str(directory),str(directory/"standalone.tex")],
                           cwd=directory,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        pdf=directory/"standalone.pdf"
        subprocess.run([str(OUTPUT/"runtime/python/bin/python"),"-m","llm_selection.render_pdf",str(pdf),
                        "--output",str(directory/"preview")],cwd=ROOT,check=True)
    return {"directory":str(directory),"pdf":str(pdf) if pdf else None,
            "visual_review":"Controllare le pagine PNG prima di inserire il documento nella tesi."}

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--sources-only",action="store_true");args=parser.parse_args()
    print(json.dumps(build_report(compile_pdf=not args.sources_only),indent=2))
