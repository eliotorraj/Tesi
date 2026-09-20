"""Rapporto tecnico o di validation, con sorgenti LaTeX e figure."""
from __future__ import annotations
import os
import subprocess
from collections import Counter
from llm_selection.common import ROOT, OUTPUT, read_json, write_json
from llm_selection.evaluate import episode_data, write_csv, attach_resources
from llm_selection.report import tex, fmt, bootstrap
from .evaluate import enrich_costs, summarize
from .settings import study_root, FIXED

def build_report(study_id, *, technical=False, compile_pdf=True):
    root = study_root(study_id)
    directory = root / ("technical_report" if technical else "report")
    directory.mkdir(parents=True, exist_ok=True)
    if technical:
        rows = []
        for p in sorted((root / "technical").glob("*/*/*/decision.json")):
            model, config = p.parts[-4:-2]
            row, _ = episode_data(p.parent, model + "/" + config)
            enrich_costs(row, p.parent)
            row.update(regret_absolute=None, score=None,
                       failure_category=(row.get("failure") or {}).get("category"))
            rows.append(row)
        attach_resources(rows)
        profiles = read_json(root / "profiles_to_freeze.json")
        selection = None
    else:
        from .study import require_sealed
        require_sealed(study_id)
        rows = read_json(root / "analysis/episode_results.json")
        selection = read_json(root / "analysis/selection.json")
        profiles = read_json(root / "frozen_study.json")["models"]
    trials = {name: [r for r in rows if r["trial_id"] == name] for name in sorted({r["trial_id"] for r in rows})}
    summaries = {k: summarize(v) for k, v in trials.items()}
    write_csv(directory / "episodes.csv", rows)
    write_csv(directory / "trials.csv", [{"trial_id": k, **v} for k, v in summaries.items()])
    facts = Counter()
    for base in [root / "technical"] if technical else [root / m for m in profiles]:
        for p in base.glob("*/*/attempt_*/fact_validation.json") if not technical else base.glob("*/*/*/attempt_*/fact_validation.json"):
            for fact in read_json(p)["fact_checks"]:
                facts[(fact["assertion"], fact["result"])] += 1
    write_json(directory / "fact_types.json", [{"assertion": k[0], "result": k[1], "count": v} for k, v in sorted(facts.items())])
    write_json(directory / "plot_input.json", {"technical": technical, "rows": rows})
    python = OUTPUT / "runtime/python/bin/python"
    subprocess.run([str(python), "-m", "llm_selection.v2.plots", str(directory / "plot_input.json"),
                    "--output", str(directory / "figures")], cwd=ROOT, check=True)
    pairs = []
    if selection and selection["winner"]:
        reference = {r["source_sha256"]: r for r in trials[selection["winner"]]}
        for name, records in trials.items():
            if name == selection["winner"]:
                continue
            common = [r for r in records if r["regret_absolute"] is not None
                      and reference[r["source_sha256"]]["regret_absolute"] is not None]
            pairs.append({"winner": selection["winner"], "comparison": name,
                          "source_hashes": [r["source_sha256"] for r in common],
                          **bootstrap([reference[r["source_sha256"]]["regret_absolute"] - r["regret_absolute"] for r in common])})
    write_json(directory / "paired_uncertainty.json", pairs)
    title = "Prove tecniche sul train" if technical else "Seconda selezione dei modelli locali sulla validation"
    parts = [
        r"\providecommand{\ValidationFiguresPath}{figures/}",
        r"\section{" + title + "}",
        "Studio " + tex(study_id) + ". Contratto di risposta 4.0.0. "
        + ("Queste prove verificano il funzionamento su cinque circuiti di train; non misurano la generalizzazione. "
           "Il recupero tecnico può includere lo stesso circuito di train, come documentato nei prompt."
           if technical else "Sono confrontate nove combinazioni sugli stessi 88 circuiti. Il test resta separato."),
        r"\subsection{Dati, impostazioni e controlli}",
        "Qwen, Phi e Gemma usano lo stesso prompt, derivato dalla precedente checklist, alle temperature 0, 0,4 e 0,7. "
        "Si recuperano cinque esempi dal train, con distanza Manhattan sulle 49 caratteristiche e trasformazioni fissate sul train. "
        "Il formato del prompt è TOON e la risposta è JSON. Gli score del circuito corrente non entrano nel prompt né nei messaggi correttivi.",
        "La risposta contiene una coppia ammessa, da uno a due fatti strutturati e un'ipotesi libera fino a 1000 caratteri. "
        "I quattro fatti riguardano la presenza della coppia nei risultati mostrati, il dispositivo storico, "
        "l'uguaglianza del numero di qubit o la capacità del dispositivo. Il testo dell'ipotesi non viene verificato semanticamente.",
        "Si consentono tre tentativi logici. Dopo il terzo, una risposta conforme con coppia ammessa viene accettata "
        "anche se i fatti restano errati. Questo successo operativo non certifica la spiegazione o la qualità della compilazione. "
        "Le chiamate interrotte sono conservate, annullate nel conteggio logico e ripetute al recupero delle risorse.",
        "La GPU è una Radeon RX 6750 XT. Limite hotspot 110 gradi, pausa a 105 e ripresa a 100; limite edge 95 gradi. "
        "Soglia RAM disponibile 1 GiB. Sono impostazioni operative richieste, non una garanzia specifica del produttore. "
        "Il monitor campiona RAM, VRAM e temperature; i massimi campionati possono perdere picchi istantanei.",
        r"\begin{center}\begin{tabular}{lrr}\toprule Modello & Contesto & Micro-batch\\\midrule"]
    for name, p in profiles.items():
        parts.append(tex(name) + " & " + str(p["context"]) + " & " + str(p["micro_batch"]) + r"\\")
    parts += [r"\bottomrule\end{tabular}\end{center}",
              "Pesi Q8\\_0; revisioni, hash, hardware, dipendenze e dati di provenienza sono conservati nei manifest dello studio.",
              r"\begin{center}\begin{tabular}{lr}\toprule Parametro & Valore\\\midrule"]
    for key in ("max_tokens", "top_p", "top_k", "min_p", "seed"):
        parts.append(tex(key) + " & " + str(FIXED[key]) + r"\\")
    parts += [r"\bottomrule\end{tabular}\end{center}",
              r"\subsection{Risultati}",
              r"\begin{center}\small\begin{tabular}{lrrrr}\toprule Prova & Casi & Successi & Fatti verificati & Correzioni\\\midrule"]
    for name, s in summaries.items():
        parts.append(" & ".join([tex(name), str(s["circuits"]), str(s["valid_and_compilable"]),
                                 str(s["final_facts_verified"]), str(s["repairs"])]) + r"\\")
    parts += [r"\bottomrule\end{tabular}\end{center}"]
    if not technical:
        parts += [
            r"\subsection{Qualità della scelta e selezione}",
            r"\[R_{\mathrm{osservato}}(c)=\max_{p\in P_{\mathrm{riuscite}}(c)} \mathrm{mediana}(F_{p,0},F_{p,1},F_{p,2})-F_{\mathrm{scelta}}(c).\]",
            "Si riusano le compilazioni Qiskit. Il riferimento considera solo coppie con tre ripetizioni riuscite. "
            "Copre 88 circuiti; 70 matrici sono incomplete e quindi questo riferimento non certifica il massimo esaustivo. "
            "L'oracle completo sui 18 circuiti resta un'analisi aggiuntiva. Uno score mancante resta null.",
            "La selezione ordina completezza, regret mediano sui circuiti comuni, correzioni, chiamate fisiche, tempi e token. "
            "Il circuito è l'unità statistica. Gli intervalli appaiati al 95 per cento usano 2000 ricampionamenti e seed 20260913; "
            "sono descrittivi e non correggono la selezione tra candidati.",
            "Vincitore: " + tex(selection["winner"]) + ". Passaggi e denominatori sono in selection.json.",
            r"\begin{center}\small\begin{tabular}{lrr}\toprule Prova & Regret n & Mediana regret\\\midrule"]
        for name, s in summaries.items():
            parts.append(tex(name) + " & " + str(s["regret_available"]) + " & " + fmt(s["median_regret_absolute"]) + r"\\")
        parts += [r"\bottomrule\end{tabular}\end{center}"]
    for fig in read_json(directory / "figures/manifest.json"):
        parts += [r"\begin{figure}[htbp]\centering",
                  r"\includegraphics[width=\linewidth]{\ValidationFiguresPath " + fig["name"] + ".png}",
                  r"\caption{" + tex(fig["caption"]) + r"}\end{figure}"]
    parts += [r"\clearpage\subsection{Provenienza e limiti}",
              "Questa versione è stata progettata dopo aver esaminato la prima validation. Le due versioni restano separate. "
              "La correttezza dei fatti strutturati non misura la correttezza del testo libero né dimostra un rapporto causale "
              "fra motivazione e scelta. La presenza di un precedente storico non garantisce prestazioni sul nuovo circuito.",
              "I tempi HTTP includono le pause dentro la chiamata; attese di recupero e caricamenti sono registrati separatamente. "
              "I token mancanti restano espliciti. Tutti i tentativi, anche interrotti, restano disponibili.",
              "Sorgenti e figure si rigenerano con il comando report dello studio; CSV, JSON e JSONL contengono i dati originali. "
              "Ogni risultato di validation viene letto soltanto dopo i sigilli. Nessun dato del test è utilizzato."]
    source = directory / "validation_selection.tex"
    source.write_text("\n\n".join(parts) + "\n")
    standalone = r"""\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[italian]{babel}
\usepackage[margin=2cm]{geometry}
\usepackage{graphicx,booktabs,amsmath,microtype}
\usepackage[hidelinks]{hyperref}
\begin{document}
\input{validation_selection.tex}
\end{document}
"""
    (directory / "standalone.tex").write_text(standalone)
    if compile_pdf:
        env = dict(os.environ)
        env["TECTONIC_CACHE_DIR"] = str(OUTPUT / "runtime/tectonic-cache")
        with (directory / "compile.log").open("w") as log:
            subprocess.run([str(OUTPUT / "runtime/tectonic/tectonic"), "--keep-logs", "--outdir", str(directory),
                            str(directory / "standalone.tex")], cwd=directory, env=env,
                           stdout=log, stderr=subprocess.STDOUT, check=True)
        subprocess.run([str(python), "-m", "llm_selection.render_pdf", str(directory / "standalone.pdf"),
                        "--output", str(directory / "preview")], cwd=ROOT, check=True)
    return str(directory)
