"""Resoconto esplicativo post-selezione: nessuna nuova inferenza o scelta."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection"
METRICS = ("total_call_seconds", "total_input_tokens", "total_output_tokens", "physical_calls")
MODELS = ("qwen", "phi", "gemma")

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def aggregate(rows):
    result = {"episodes": len(rows)}
    for key in METRICS:
        values = [r.get(key) for r in rows]
        result[key] = sum(values) if all(v is not None for v in values) else None
        result[key + "_measured_episodes"] = sum(v is not None for v in values)
    result["median_call_seconds_per_episode"] = statistics.median(
        r["total_call_seconds"] for r in rows if r.get("total_call_seconds") is not None
    ) if any(r.get("total_call_seconds") is not None for r in rows) else None
    return result

def render(source, destination):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    rows = json.loads(source.read_text())
    destination.mkdir(parents=True, exist_ok=True)
    colors = ("#3975a6", "#df8f2d", "#4a9470")
    configs = ("p0_t0", "p0_t04", "p0_t07")
    def save(fig, name):
        fig.tight_layout()
        for suffix in ("png", "svg"):
            fig.savefig(destination / (name + "." + suffix), dpi=180, bbox_inches="tight")
        plt.close(fig)
    def value(v, factor=1):
        return v * factor if v is not None else np.nan
    models = {m: aggregate([r for r in rows if r["trial_id"].startswith(m + "/")]) for m in MODELS}
    x = np.arange(3)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))
    totals = [value(models[m]["total_call_seconds"], 1/60) for m in MODELS]
    bars = axes[0].bar(x, totals, color=colors)
    axes[0].bar_label(bars, fmt="%.1f", padding=3)
    axes[0].set(xticks=x, xticklabels=MODELS, ylabel="Minuti nelle chiamate di generazione",
                title="Totale: 264 episodi per modello")
    for j, c in enumerate(configs):
        values = [value(aggregate([r for r in rows if r["trial_id"] == m+"/"+c])["total_call_seconds"], 1/60) for m in MODELS]
        axes[1].bar(x+(j-1)*.24, values, width=.24, label=c)
    axes[1].set(xticks=x, xticklabels=MODELS, ylabel="Minuti nelle chiamate di generazione",
                title="Per temperatura: 88 episodi")
    axes[1].legend(fontsize=8)
    save(fig, "tempi_modelli")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))
    for ax, key, unit, title in zip(axes, ("total_input_tokens", "total_output_tokens"),
            (1e6, 1000), ("Ingresso: milioni di token", "Uscita: migliaia di token")):
        bars = ax.bar(x, [value(models[m][key], 1/unit) for m in MODELS], color=colors)
        ax.bar_label(bars, fmt="%.2f", padding=3)
        ax.set(xticks=x, xticklabels=MODELS, ylabel=title, title="Totale: 264 episodi per modello")
    save(fig, "token_modelli")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))
    for ax, key, unit, title in zip(axes, ("total_input_tokens", "total_output_tokens"),
            (1e6, 1000), ("Ingresso: milioni di token", "Uscita: migliaia di token")):
        for j, c in enumerate(configs):
            vals = [value(aggregate([r for r in rows if r["trial_id"]==m+"/"+c])[key], 1/unit) for m in MODELS]
            ax.bar(x+(j-1)*.24, vals, width=.24, label=c)
        ax.set(xticks=x, xticklabels=MODELS, ylabel=title, title="Per temperatura: 88 episodi")
        ax.legend(fontsize=8)
    save(fig, "token_temperature")

def build(study_id):
    if study_id != "local-llm-v2":
        raise ValueError("This explanatory report describes local-llm-v2 only")
    from llm_selection.v2.study import require_sealed
    from llm_selection.v2.settings import study_root
    require_sealed(study_id)
    root = study_root(study_id)
    original = root / "report"
    out = root / "report_explained"
    out.mkdir(exist_ok=True)
    sources = [root/"frozen_study.json", root/"analysis/episode_results.json",
               root/"analysis/selection.json", root/"final_configuration.json",
               original/"validation_selection.tex", original/"standalone.pdf"]
    before = {str(p.relative_to(ROOT)): sha(p) for p in sources}
    rows = json.loads((root/"analysis/episode_results.json").read_text())
    assert len(rows) == 792
    trials = {k: [r for r in rows if r["trial_id"]==k] for k in sorted({r["trial_id"] for r in rows})}
    assert len(trials)==9 and all(len(g)==88 for g in trials.values())
    summaries=[]
    for trial, g in trials.items():
        v=sorted(r["regret_absolute"] for r in g if r["regret_absolute"] is not None)
        summaries.append({"trial_id":trial, "regret_n":len(v), "zero_regret":v.count(0),
                          "median_regret":statistics.median(v), "mean_regret":statistics.mean(v),
                          "max_regret":max(v), **aggregate(g)})
    model_costs=[{"model":m, **aggregate([r for r in rows if r["trial_id"].startswith(m+"/")])} for m in MODELS]
    for name, data in (("trial_details.csv",summaries),("model_costs.csv",model_costs)):
        with (out/name).open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
    (out/"model_costs.json").write_text(json.dumps(model_costs,indent=2)+"\n")
    shutil.copytree(original/"figures",out/"figures",dirs_exist_ok=True)
    runtime=BASE/"runtime/python/bin/python"
    subprocess.run([str(runtime),str(Path(__file__).resolve()),"--render",
                    str(root/"analysis/episode_results.json"),str(out/"figures")],cwd=ROOT,check=True)
    text=(original/"validation_selection.tex").read_text()
    text=text.replace("Fatti verificati & Correzioni", "Risposte verificate & Correzioni")
    for trial,g in trials.items():
        key=trial.replace("_",r"\_")
        verified=sum(r["facts_status"]=="verified" for r in g)
        repairs=sum(r["repair_count"] for r in g)
        text=text.replace(f"{key} & 88 & 88 & {verified} & {repairs}",
                          f"{key} & 88 & 88 & {verified}/88 & {repairs}")
    explanation=r"""
\paragraph{Come leggere la tabella.}
Ogni riga riguarda 88 circuiti per una combinazione di modello e temperatura.
Successi indica scelte valide con risultato di compilazione disponibile.
Risposte verificate conta gli episodi in cui \emph{tutti} i fatti della risposta
finale sono corretti; non conta i singoli fatti e non certifica l'ipotesi libera.
Per esempio, Gemma a temperatura zero ha 52 risposte verificate su 88
(59,1 per cento), mentre 36 sono state accettate con fatti ancora errati.
Le correzioni sono chiamate aggiuntive dopo la prima risposta: un episodio
può contribuire zero, una o due correzioni. Nella stessa riga, 29 episodi
non richiedono correzioni, 18 ne richiedono una e 41 ne richiedono due:
$18+2\cdot41=100$. In totale sono 188 chiamate. Il conteggio dei singoli fatti
è distinto: 236 fatti verificati su 374 controllati in tutti i tentativi.
"""
    marker=r"\subsection{Qualità della scelta e selezione}"
    text=text.replace(marker,explanation+"\n"+marker)
    old=r"\[R_{\mathrm{osservato}}(c)=\max_{p\in P_{\mathrm{riuscite}}(c)} \mathrm{mediana}(F_{p,0},F_{p,1},F_{p,2})-F_{\mathrm{scelta}}(c).\]"
    new=r"""
\[
 S(c,p)=\operatorname{mediana}_{s\in\{0,1,2\}} F(c,p,s), \qquad
 R_{\mathrm{osservato}}(c)=\max_{p\in P_{\mathrm{riuscite}}(c)}S(c,p)-S(c,p_{\mathrm{scelta}}).
\]
$c$ è il circuito; $p$ è la coppia dispositivo/configurazione.
$F(c,p,s)$ è la expected fidelity ottenuta dalla compilazione con seed Qiskit $s$.
La mediana dei tre seed è lo score rappresentativo della coppia, anche per
quella scelta dal modello: attenua l'effetto di una compilazione isolata
particolarmente favorevole o sfavorevole. Con tre valori è quello centrale;
non è una stima di incertezza. Il massimo considera le coppie osservate
con tutte e tre le compilazioni riuscite.
Il regret è la differenza fra questo riferimento e lo score della scelta:
zero significa pareggio col migliore risultato osservato; un valore maggiore
indica una perdita maggiore. Esempio illustrativo: $0{,}90-0{,}82=0{,}08$.
La mediana del regret nella tabella è un'altra aggregazione:
si calcola dopo, sui risultati degli 88 circuiti, non sui tre seed.
"""
    assert old in text
    text=text.replace(old,new)
    details=r"""
\paragraph{Perché alcune mediane sono zero.}
Con 88 valori ordinati la mediana è la media del 44-esimo e del 45-esimo.
Qwen e Phi hanno almeno 45 zeri in ogni configurazione: entrambi i valori
centrali sono quindi esattamente zero, anche se altri circuiti hanno perdite.
Non si tratta di zeri dovuti all'arrotondamento della tabella.
Gemma ha due zeri su 88 per ciascuna temperatura e mediane positive.
La media e il massimo descrivono anche gli errori che la mediana nasconde;
sono aggiunte descrittive e non modificano il criterio di selezione congelato.

\begin{center}\small
\begin{tabular}{lrrrr}\toprule
Prova & Zeri su 88 & Mediana & Media & Massimo\\\midrule
"""
    for s in summaries:
        details+=" & ".join([s["trial_id"].replace("_",r"\_"),str(s["zero_regret"]),
                             f'{s["median_regret"]:.4f}',f'{s["mean_regret"]:.4f}',f'{s["max_regret"]:.4f}'])+r"\\"+"\n"
    details+=r"""
\bottomrule\end{tabular}\end{center}
Il dispositivo Quantinuum appartiene al migliore risultato osservato in
70 circuiti su 88. Qwen e Phi lo scelgono spesso, mentre Gemma non lo sceglie
mai in questa validation. Questa è una differenza osservata nelle decisioni,
non una prova del motivo interno per cui i modelli scelgono.
In 72 circuiti più coppie raggiungono lo stesso score massimo osservato.
Nessun riferimento osservato ha score zero.
"""
    marker=r"\begin{figure}[htbp]\centering"
    text=text.replace(marker,details+"\n"+marker,1)
    text=text.replace("Regret osservato. Ogni punto statistico rappresenta un circuito; n indica i circuiti valutabili.",
        "Regret osservato: rettangolo fra primo e terzo quartile (50 per cento centrale), linea arancione alla mediana. "
        "I baffi arrivano ai valori estremi entro 1,5 volte la distanza fra quartili. "
        "I puntini mostrano solo i circuiti oltre i baffi; non tutti gli 88 circuiti. Valori uguali possono sovrapporsi. "
        "Un punto esterno non è automaticamente un errore nei dati. n indica i circuiti valutabili.")
    cost=r"""
\clearpage\subsection{Tempi e token per modello}
Ogni modello ha affrontato 264 episodi: gli stessi 88 circuiti a tre temperature.
I totali includono tutte le chiamate di generazione, comprese le correzioni;
non rappresentano il costo di una sola risposta. Tutti i contatori qui usati
sono disponibili per tutti gli episodi.
Il tempo HTTP misura la durata delle chiamate e comprende eventuali pause
dentro di esse. Non è il tempo totale trascorso dall'avvio alla fine
dell'esperimento: caricamento, recupero esterno, preparazione dei contesti
e chiamate tecniche di tokenizzazione sono esclusi da questo totale.
I token di ingresso vengono contati per ogni chiamata, anche se il contesto
viene ripetuto nelle correzioni o il server ne riusa parti in cache.
I token di uscita comprendono tutte le risposte, anche quelle corrette
successivamente. I modelli usano tokenizzatori diversi: il conteggio non
corrisponde allo stesso numero di parole né a un costo monetario.
I modelli sono eseguiti in sequenza sullo stesso computer: temperature,
pause e cache possono influenzare i tempi. Non è una misura isolata
della velocità intrinseca del modello.

\begin{center}\small\begin{tabular}{lrrrr}\toprule
Modello & Episodi & Minuti HTTP & Token ingresso & Token uscita\\\midrule
"""
    for m in model_costs:
        cost+=f'{m["model"]} & {m["episodes"]} & {m["total_call_seconds"]/60:.2f} & {m["total_input_tokens"]:,} & {m["total_output_tokens"]:,}'+r"\\"+"\n"
    cost+=r"\bottomrule\end{tabular}\end{center}"+"\n"
    for name,caption in [
        ("tempi_modelli","Tempi misurati nelle chiamate: totale per modello e dettaglio per temperatura. Correzioni incluse."),
        ("token_modelli","Token complessivi di ingresso e uscita per modello; 264 episodi ciascuno. Le due scale sono differenti."),
        ("token_temperature","Token di ingresso e uscita per modello e temperatura; 88 episodi per barra.")]:
        cost+=r"\begin{figure}[htbp]\centering"+"\n"+r"\includegraphics[width=\linewidth]{\ValidationFiguresPath "+name+r".png}"+"\n"+r"\caption{"+caption+r"}\end{figure}"+"\n"
    marker=r"\clearpage\subsection{Provenienza e limiti}"
    text=text.replace(marker,cost+"\n"+marker)
    text+="\nQuesto resoconto esplicativo è generato dopo la selezione dai dati già sigillati. "\
          "I risultati, il vincitore e il codice congelato non sono modificati. "\
          "Il rapporto originale resta nella cartella report; questa versione è in report\\_explained.\n"
    (out/"validation_selection.tex").write_text(text)
    shutil.copy2(original/"standalone.tex",out/"standalone.tex")
    env=dict(os.environ,TECTONIC_CACHE_DIR=str(BASE/"runtime/tectonic-cache"))
    with (out/"compile.log").open("w") as log:
        subprocess.run([str(BASE/"runtime/tectonic/tectonic"),"--keep-logs","--outdir",str(out),str(out/"standalone.tex")],
                       cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    subprocess.run([str(runtime),"-m","llm_selection.render_pdf",str(out/"standalone.pdf"),"--output",str(out/"preview")],cwd=ROOT,check=True)
    assert before=={str(p.relative_to(ROOT)):sha(p) for p in sources}
    require_sealed(study_id)
    (out/"provenance.json").write_text(json.dumps({"source_sha256":before,"script_sha256":sha(Path(__file__)),
        "script":str(Path(__file__).relative_to(ROOT)),"no_new_inference":True,
        "original_report_unchanged":True,"selection_unchanged":True},indent=2)+"\n")
    print(out)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--study",default="local-llm-v2")
    p.add_argument("--render",nargs=2,type=Path)
    args=p.parse_args()
    if args.render:render(*args.render)
    else:build(args.study)
