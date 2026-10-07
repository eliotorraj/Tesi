'Technical or validation report with LaTeX sources and figures.'
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
    title = 'Technical checks on train' if technical else 'Second local-model selection on validation'
    parts = [
        r"\providecommand{\ValidationFiguresPath}{figures/}",
        r"\section{" + title + "}",
        'Study ' + tex(study_id) + '. Response contract 4.0.0. '
        + ('These checks verify operation on five train circuits, not generalization. Technical retrieval may include the train input itself, as documented in prompts.'
           if technical else 'Nine combinations are compared on the same 88 circuits. Test remains separate.'),
        '\\subsection{Data, settings and checks}',
        "Qwen, Phi and Gemma use the same prompt, derived from the previous checklist, at temperatures 0, 0.4 and 0.7. Five train examples are retrieved by Manhattan distance on 49 features with train-fitted transformations. Prompts use TOON and responses use JSON. The current circuit's validation scores never enter its prompt or repair messages.",
        "The response contains an allowed pair, one or two structured facts and a free hypothesis up to 1000 characters. The four fact types concern the pair's presence in shown results, the historical device, equal qubit count or device capacity. The hypothesis text is not checked semantically.",
        'Three logical attempts are allowed. After the third, a conforming response with an allowed pair is accepted even if facts remain incorrect. This operational success does not certify explanation or compilation quality. Interrupted calls are preserved, excluded from the logical count and repeated after resources recover.',
        'The GPU is a Radeon RX 6750 XT. Hotspot limit is 110 degrees, pause at 105 and resume at 100; edge limit is 95 degrees. Available-RAM threshold is 1 GiB. These are requested operating settings, not a manufacturer guarantee. The monitor samples RAM, VRAM and temperatures; sampled maxima can miss instantaneous peaks.',
        '\\begin{center}\\begin{tabular}{lrr}\\toprule Model & Context & Microbatch\\\\\\midrule']
    for name, p in profiles.items():
        parts.append(tex(name) + " & " + str(p["context"]) + " & " + str(p["micro_batch"]) + r"\\")
    parts += [r"\bottomrule\end{tabular}\end{center}",
              'Q8\\_0 weights; revisions, hashes, hardware, dependencies and provenance are preserved in study manifests.',
              '\\begin{center}\\begin{tabular}{lr}\\toprule Parameter & Value\\\\\\midrule']
    for key in ("max_tokens", "top_p", "top_k", "min_p", "seed"):
        parts.append(tex(key) + " & " + str(FIXED[key]) + r"\\")
    parts += [r"\bottomrule\end{tabular}\end{center}",
              '\\subsection{Results}',
              '\\begin{center}\\small\\begin{tabular}{lrrrr}\\toprule Trial & Cases & Successes & Verified facts & Repairs\\\\\\midrule']
    for name, s in summaries.items():
        parts.append(" & ".join([tex(name), str(s["circuits"]), str(s["valid_and_compilable"]),
                                 str(s["final_facts_verified"]), str(s["repairs"])]) + r"\\")
    parts += [r"\bottomrule\end{tabular}\end{center}"]
    if not technical:
        parts += [
            '\\subsection{Decision quality and selection}',
            '\\[R_{\\mathrm{observed}}(c)=\\max_{p\\in P_{\\mathrm{successful}}(c)} \\mathrm{median}(F_{p,0},F_{p,1},F_{p,2})-F_{\\mathrm{selected}}(c).\\]',
            'Qiskit compilations are reused. The reference includes only pairs with three successful repetitions. It covers 88 circuits; 70 matrices are incomplete, so it does not certify an exhaustive maximum. The complete oracle on 18 circuits remains a supplementary analysis. Missing scores remain null.',
            'Selection ranks completeness, median regret on common circuits, repairs, physical calls, time and tokens. The circuit is the statistical unit. Paired 95-percent intervals use 2000 resamples and seed 20260913; they are descriptive and do not adjust for candidate selection.',
            'Winner: ' + tex(selection["winner"]) + '. Steps and denominators are in selection.json.',
            '\\begin{center}\\small\\begin{tabular}{lrr}\\toprule Trial & Regret n & Median regret\\\\\\midrule']
        for name, s in summaries.items():
            parts.append(tex(name) + " & " + str(s["regret_available"]) + " & " + fmt(s["median_regret_absolute"]) + r"\\")
        parts += [r"\bottomrule\end{tabular}\end{center}"]
    for fig in read_json(directory / "figures/manifest.json"):
        parts += [r"\begin{figure}[htbp]\centering",
                  r"\includegraphics[width=\linewidth]{\ValidationFiguresPath " + fig["name"] + ".png}",
                  r"\caption{" + tex(fig["caption"]) + r"}\end{figure}"]
    parts += ['\\clearpage\\subsection{Provenance and limitations}',
              'This version was designed after reviewing the first validation. The two versions remain separate. Correct structured facts do not measure free-text correctness or demonstrate a causal link between explanation and choice. A historical precedent does not guarantee performance on a new circuit.',
              'HTTP timings include pauses inside a call; recovery waits and loading are recorded separately. Missing tokens remain explicit. All attempts, including interruptions, remain available.',
              'The study guide explains source and figure regeneration. CSV, JSON and JSONL preserve analysis data. Validation results are read only after sealing. No Test data is used.']
    source = directory / "validation_selection.tex"
    source.write_text("\n\n".join(parts) + "\n")
    standalone = """\\documentclass[11pt,a4paper]{article}
\\usepackage[utf8]{inputenc}
\\usepackage[T1]{fontenc}
\\usepackage[english]{babel}
\\usepackage[margin=2cm]{geometry}
\\usepackage{graphicx,booktabs,amsmath,microtype}
\\usepackage[hidelinks]{hyperref}
\\begin{document}
\\input{validation_selection.tex}
\\end{document}
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
