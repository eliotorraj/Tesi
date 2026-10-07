'Explanatory post-selection report without new inference or selection.'
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
    axes[0].set(xticks=x, xticklabels=MODELS, ylabel='Minutes in generation calls',
                title='Total: 264 episodes per model')
    for j, c in enumerate(configs):
        values = [value(aggregate([r for r in rows if r["trial_id"] == m+"/"+c])["total_call_seconds"], 1/60) for m in MODELS]
        axes[1].bar(x+(j-1)*.24, values, width=.24, label=c)
    axes[1].set(xticks=x, xticklabels=MODELS, ylabel='Minutes in generation calls',
                title='Per temperature: 88 episodes')
    axes[1].legend(fontsize=8)
    save(fig, "tempi_modelli")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))
    for ax, key, unit, title in zip(axes, ("total_input_tokens", "total_output_tokens"),
            (1e6, 1000), ('Input: millions of tokens', 'Output: thousands of tokens')):
        bars = ax.bar(x, [value(models[m][key], 1/unit) for m in MODELS], color=colors)
        ax.bar_label(bars, fmt="%.2f", padding=3)
        ax.set(xticks=x, xticklabels=MODELS, ylabel=title, title='Total: 264 episodes per model')
    save(fig, "token_modelli")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))
    for ax, key, unit, title in zip(axes, ("total_input_tokens", "total_output_tokens"),
            (1e6, 1000), ('Input: millions of tokens', 'Output: thousands of tokens')):
        for j, c in enumerate(configs):
            vals = [value(aggregate([r for r in rows if r["trial_id"]==m+"/"+c])[key], 1/unit) for m in MODELS]
            ax.bar(x+(j-1)*.24, vals, width=.24, label=c)
        ax.set(xticks=x, xticklabels=MODELS, ylabel=title, title='Per temperature: 88 episodes')
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
    text=text.replace('Verified facts & Repairs', 'Verified responses & Repairs')
    for trial,g in trials.items():
        key=trial.replace("_",r"\_")
        verified=sum(r["facts_status"]=="verified" for r in g)
        repairs=sum(r["repair_count"] for r in g)
        text=text.replace(f"{key} & 88 & 88 & {verified} & {repairs}",
                          f"{key} & 88 & 88 & {verified}/88 & {repairs}")
    explanation="""
\\paragraph{Reading the table.}
Each row covers 88 circuits for one model/temperature combination. Successes counts valid choices with an available compilation result. Verified responses counts episodes in which \\emph{all} final-response facts are correct; it neither counts individual facts nor certifies the free hypothesis. For example, Gemma at temperature zero has 52 verified responses out of 88 (59.1 percent), while 36 were accepted with incorrect facts. Repairs are calls after the first response: an episode can contribute zero, one or two. In that row, 29 episodes need no repair, 18 need one and 41 need two: $18+2\\cdot41=100$, for 188 total calls. Individual-fact counts are separate: 236 verified facts out of 374 checked across all attempts.
"""
    marker='\\subsection{Decision quality and selection}'
    text=text.replace(marker,explanation+"\n"+marker)
    old='\\[R_{\\mathrm{observed}}(c)=\\max_{p\\in P_{\\mathrm{successful}}(c)} \\mathrm{median}(F_{p,0},F_{p,1},F_{p,2})-F_{\\mathrm{selected}}(c).\\]'
    new="""
\\[S(c,p)=\\operatorname{median}_{s\\in\\{0,1,2\\}}F(c,p,s),\\qquad R_{\\mathrm{observed}}(c)=\\max_{p\\in P_{\\mathrm{successful}}(c)}S(c,p)-S(c,p_{\\mathrm{selected}}).\\]
$c$ is the circuit and $p$ the device/configuration pair. $F(c,p,s)$ is expected fidelity after compilation with Qiskit seed $s$. The three-seed median represents the pair, including the model's choice, reducing the influence of one unusually favorable or unfavorable compilation. With three values it is the middle one, not an uncertainty estimate. The maximum includes observed pairs with three successful compilations. Regret is the reference minus the chosen pair's score: zero means a tie with the best observed result; a larger value means greater loss. An illustrative example is $0.90-0.82=0.08$. The table's median regret is a separate later aggregation across 88 circuits, not across the three seeds.
"""
    assert old in text
    text=text.replace(old,new)
    details="""
\\paragraph{Why some medians are zero.}
For 88 sorted values, the median averages the 44th and 45th. Qwen and Phi have at least 45 zeros in each setting, so both middle values are exactly zero despite losses on other circuits. These zeros are not caused by table rounding. Gemma has two zeros out of 88 per temperature and positive medians. Mean and maximum also describe errors hidden by the median; these descriptive additions do not change the frozen selection rule.
\\begin{center}\\small\\begin{tabular}{lrrrr}\\toprule Trial & Zeros out of 88 & Median & Mean & Maximum\\\\\\midrule
"""
    for s in summaries:
        details+=" & ".join([s["trial_id"].replace("_",r"\_"),str(s["zero_regret"]),
                             f'{s["median_regret"]:.4f}',f'{s["mean_regret"]:.4f}',f'{s["max_regret"]:.4f}'])+r"\\"+"\n"
    details+="""
\\bottomrule\\end{tabular}\\end{center}
Quantinuum belongs to the best observed result on 70 of 88 circuits. Qwen and Phi often select it, whereas Gemma never does in this validation. This is an observed decision difference, not evidence of the models' internal reasons. Multiple pairs reach the same observed maximum on 72 circuits. No observed reference has a zero score.
"""
    marker=r"\begin{figure}[htbp]\centering"
    text=text.replace(marker,details+"\n"+marker,1)
    text=text.replace('Observed regret. Each statistical point represents a circuit; n counts evaluable circuits.',
        'Observed regret: the box spans the first to third quartiles (central 50 percent), with an orange median line. Whiskers reach extreme values within 1.5 times the interquartile range. Dots show only circuits beyond the whiskers, not all 88. Equal values can overlap. An outside point is not automatically a data error. n counts evaluable circuits.')
    cost="""
\\clearpage\\subsection{Time and tokens by model}
Each model evaluated 264 episodes: the same 88 circuits at three temperatures. Totals include every generation call and repair, not the cost of a single response. All counters used here are available for every episode. HTTP time includes pauses within calls. It is not total experiment elapsed time: loading, external recovery, context preparation and technical tokenization calls are excluded. Input tokens are counted for every call, even when repairs repeat the context or the server reuses cached parts. Output tokens include all responses, including those subsequently repaired. Different tokenizers mean counts represent neither equal word counts nor monetary costs. Models run sequentially on the same host; temperature, pauses and cache affect timings. These are not isolated measurements of intrinsic model speed.
\\begin{center}\\small\\begin{tabular}{lrrrr}\\toprule Model & Episodes & HTTP minutes & Input tokens & Output tokens\\\\\\midrule
"""
    for m in model_costs:
        cost+=f'{m["model"]} & {m["episodes"]} & {m["total_call_seconds"]/60:.2f} & {m["total_input_tokens"]:,} & {m["total_output_tokens"]:,}'+r"\\"+"\n"
    cost+=r"\bottomrule\end{tabular}\end{center}"+"\n"
    for name,caption in [
        ("tempi_modelli",'Measured call times: totals by model and detail by temperature, including repairs.'),
        ("token_modelli",'Total input and output tokens by model; 264 episodes each. The scales differ.'),
        ("token_temperature",'Input and output tokens by model and temperature; 88 episodes per bar.')]:
        cost+=r"\begin{figure}[htbp]\centering"+"\n"+r"\includegraphics[width=\linewidth]{\ValidationFiguresPath "+name+r".png}"+"\n"+r"\caption{"+caption+r"}\end{figure}"+"\n"
    marker='\\clearpage\\subsection{Provenance and limitations}'
    text=text.replace(marker,cost+"\n"+marker)
    text+="""
This explanatory report is generated after selection from sealed data. Results, winner and frozen code remain unchanged. The original report stays under report; this version is under report\\_explained.
"""
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
