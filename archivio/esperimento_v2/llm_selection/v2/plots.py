'Reproducible figures from JSON without inference or circuit compilation.'
import json
from pathlib import Path

def render(data, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    output.mkdir(parents=True, exist_ok=True)
    rows, technical = data["rows"], data["technical"]
    names = sorted({r["trial_id"] for r in rows})
    groups = [[r for r in rows if r["trial_id"] == name] for name in names]
    labels = [n.replace("/", "\n") for n in names]
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
        ax.set(xticks=x, xticklabels=labels, ylabel='Regret relative to the best observed result')
        save(fig, "regret_osservato", 'Observed regret. Each statistical point represents a circuit; n counts evaluable circuits.')
    fig, ax = plt.subplots(figsize=(10, 4))
    for offset, (field, label) in enumerate((
        ("first_attempt_facts_verified", 'Facts verified on first attempt'),
        ("final_verified", 'Facts verified at completion'),
        ("accepted_with_unverified_facts", 'Accepted with incorrect facts'))):
        values = [sum(r["facts_status"] == "verified" if field == "final_verified" else bool(r.get(field)) for r in group) for group in groups]
        ax.bar(x + (offset - 1) * .25, values, width=.25, label=label)
    ax.set(xticks=x, xticklabels=labels, ylabel='Circuits')
    ax.legend(fontsize=8)
    save(fig, "fatti", 'Fact-check outcomes. The free-text explanation is not validated semantically.')
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    axes[0].bar(x, [sum(r["physical_calls"] for r in g) for g in groups])
    axes[0].set(ylabel='Physical calls, including interruptions')
    axes[1].bar(x, [sum(r["repair_count"] for r in g) for g in groups], label='Repairs')
    axes[1].bar(x, [sum(r["transport_retries"] for r in g) for g in groups],
                bottom=[sum(r["repair_count"] for r in g) for g in groups], label='Interruptions')
    axes[1].legend(fontsize=8)
    for ax in axes:
        ax.set(xticks=x, xticklabels=labels)
        ax.tick_params(axis="x", labelsize=8, rotation=45)
        for label in ax.get_xticklabels():
            label.set_horizontalalignment("right")
    save(fig, "chiamate", 'Repairs and interruptions are counted separately. Interruptions do not consume logical attempts.')
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for ax, field, label in zip(axes, ("total_call_seconds", "total_output_tokens"), ('Measured HTTP time [s]', 'Measured output tokens')):
        vals = []
        for g in groups:
            measurements = [r[field] for r in g]
            vals.append(sum(measurements) if all(v is not None for v in measurements) else np.nan)
        ax.bar(x, vals)
        ax.set(xticks=x, xticklabels=labels, ylabel=label)
        ax.tick_params(axis="x", labelsize=8, rotation=45)
        for label in ax.get_xticklabels():
            label.set_horizontalalignment("right")
    save(fig, "costo", 'Totals require every call to be measurable. Missing values do not become zero; waiting and loading are recorded by the supervisor.')
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("input", type=Path)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    render(json.loads(a.input.read_text()), a.output)
