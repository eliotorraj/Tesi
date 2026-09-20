"""Rigenera solo le sette figure della validation; non modifica sorgenti LaTeX o risultati.

Modificare qui le etichette e i titoli. Eseguire con --pdf per ricompilare
anche il documento esistente, conservando tutte le modifiche manuali.
"""
import argparse
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection"
STUDY = BASE / "studies/local-llm-v2"
# Etichette comuni agli assi e alle legende di tutti i grafici.
TEMPERATURE_LABELS = {"p0_t0": "t=0", "p0_t04": "t=0.4", "p0_t07": "t=0.7"}
METRICS = ("total_call_seconds", "total_input_tokens", "total_output_tokens", "physical_calls")
MODELS = ("qwen", "phi", "gemma")

def render_choices(data, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    output.mkdir(parents=True, exist_ok=True)
    rows, technical = data["rows"], data["technical"]
    names = sorted({r["trial_id"] for r in rows})
    groups = [[r for r in rows if r["trial_id"] == name] for name in names]
    labels = [
        f"{name.split('/')[0]}\n{TEMPERATURE_LABELS.get(name.split('/')[1], name.split('/')[1])}"
        for name in names
    ]
    x = np.arange(len(names))
    manifest = []
    def save(fig, name, caption):
        for suffix in ("png", "svg"):
            fig.savefig(output / (name + "." + suffix), dpi=180, bbox_inches="tight")
        plt.close(fig)
        manifest.append({"name": name, "caption": caption})
    if not technical:
        fig, ax = plt.subplots(figsize=(10, 4))
        for i, group in enumerate(groups):
            values = [r["regret_absolute"] for r in group if r["regret_absolute"] is not None]
            if values:
                ax.boxplot(values, positions=[i], widths=.5)
            ax.text(i, 1.02, f"n={len(values)}", ha="center", transform=ax.get_xaxis_transform())
        ax.set(xticks=x, xticklabels=labels, ylabel="Regret rispetto al miglior risultato osservato")
        save(fig, "regret_osservato", "Regret osservato. Ogni punto statistico rappresenta un circuito; n indica i circuiti valutabili.")
    fig, ax = plt.subplots(figsize=(10, 4))
    for offset, (field, label) in enumerate((
        ("first_attempt_facts_verified", "Fatti verificati alla prima"),
        ("final_verified", "Fatti verificati entro 3 tentativi"),
        ("accepted_with_unverified_facts", "Accettate con fatti errati"))):
        values = [sum(r["facts_status"] == "verified" if field == "final_verified" else bool(r.get(field)) for r in group) for group in groups]
        ax.bar(x + (offset - 1) * .25, values, width=.25, label=label)
    ax.set(xticks=x, xticklabels=labels, ylabel="Circuiti")
    ax.legend(fontsize=8)
    save(fig, "fatti", "Esiti dei controlli sui fatti. La motivazione libera non viene validata semanticamente.")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    axes[0].bar(x, [sum(r["physical_calls"] for r in g) for g in groups])
    axes[0].set(ylabel="Chiamate fisiche, comprese interruzioni")
    axes[1].bar(x, [sum(r["repair_count"] for r in g) for g in groups], label="Correzioni")
    axes[1].bar(x, [sum(r["transport_retries"] for r in g) for g in groups],
                bottom=[sum(r["repair_count"] for r in g) for g in groups], label="Interruzioni")
    axes[1].set(
        title="Correzioni e interruzioni",
        ylabel="Numero di chiamate",
    )   
    axes[1].legend(fontsize=8)
    for ax in axes:
        ax.set(xticks=x, xticklabels=labels)
        ax.tick_params(axis="x", labelsize=8, rotation=45)
        for label in ax.get_xticklabels():
            label.set_horizontalalignment("right")
    save(fig, "chiamate", "Correzioni e interruzioni sono conteggiate separatamente. Le interruzioni non consumano tentativi logici.")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for ax, field, label in zip(axes, ("total_call_seconds", "total_output_tokens"), ("Tempo misurato [s]", "Token di uscita misurati")):
        vals = []
        for g in groups:
            measurements = [r[field] for r in g]
            vals.append(sum(measurements) if all(v is not None for v in measurements) else np.nan)
        ax.bar(x, vals)
        ax.set(xticks=x, xticklabels=labels, ylabel=label)
        ax.tick_params(axis="x", labelsize=8, rotation=45)
        for label in ax.get_xticklabels():
            label.set_horizontalalignment("right")
    save(fig, "costo", "Totali solo quando tutte le chiamate sono misurabili. I valori mancanti non diventano zero; attese e caricamenti sono nei registri del supervisore.")
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))

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

def render_costs(source, destination):
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
        axes[1].bar(x+(j-1)*.24, values, width=.24, label=TEMPERATURE_LABELS.get(c, c))
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
            ax.bar(x+(j-1)*.24, vals, width=.24, label=TEMPERATURE_LABELS.get(c, c))
        ax.set(xticks=x, xticklabels=MODELS, ylabel=title, title="Per temperatura: 88 episodi")
        ax.legend(fontsize=8)
    save(fig, "token_temperature")


def render(data, output):
    """Interfaccia compatibile con i rapporti storici e le prove tecniche."""
    render_choices(data, Path(output))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", action="store_true", help="Ricompila anche standalone.tex senza rigenerare il testo")
    parser.add_argument("input", nargs="?", type=Path, help="Dati per il rapporto storico o tecnico")
    parser.add_argument("--output", type=Path, help="Cartella figure per il rapporto storico o tecnico")
    args = parser.parse_args()
    if (args.input is None) != (args.output is None):
        parser.error("input e --output devono essere specificati insieme")
    if args.input is not None and args.pdf:
        parser.error("--pdf si usa senza input e --output, per il rapporto della validation")
    try:
        import matplotlib
        import numpy
    except ImportError:
        runtime = BASE / "runtime/python/bin/python"
        if runtime.is_file() and Path(sys.executable).absolute() != runtime.absolute():
            subprocess.run([str(runtime), str(Path(__file__).resolve()), *sys.argv[1:]], check=True)
            return
        raise SystemExit("Servono matplotlib e numpy: utilizzare il Python in llm_selection/runtime/python/bin/python.")
    if args.input is not None:
        render(json.loads(args.input.read_text()), args.output)
        return
    source = STUDY / "analysis/episode_results.json"
    output = STUDY / "report_explained"
    rows = json.loads(source.read_text())
    render_choices({"rows": rows, "technical": False}, output / "figures")
    render_costs(source, output / "figures")
    manifest = output / "figures/manifest.json"
    entries = json.loads(manifest.read_text())
    entries.extend({"name": name, "caption": caption} for name, caption in (
        ("tempi_modelli", "Tempi delle chiamate per modello e temperatura."),
        ("token_modelli", "Token complessivi per modello."),
        ("token_temperature", "Token per modello e temperatura."),
    ))
    manifest.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
    print(f"Aggiornate 7 figure PNG/SVG in {output / 'figures'}")
    if args.pdf:
        env = dict(os.environ, TECTONIC_CACHE_DIR=str(BASE / "runtime/tectonic-cache"))
        subprocess.run([str(BASE / "runtime/tectonic/tectonic"), "--keep-logs", "standalone.tex"], cwd=output, env=env, check=True)
        print(f"PDF aggiornato: {output / 'standalone.pdf'}")

if __name__ == "__main__":
    main()
