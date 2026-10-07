'Document and figures from TOON counts; run in the analysis runtime.'
import argparse
import html
import json
from pathlib import Path


def render(audit_directory, destination):
    source = Path(audit_directory)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    data = json.loads((source/"report.json").read_text())
    totals = data["totals"]
    models = list(totals)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), layout="constrained")
    stages = [("original_v2", 'Previous v2', "#8792a2"),
              ("minimal_json", 'Reduced JSON', "#337ab7"),
              ("minimal_toon", 'Reduced + TOON', "#26846f")]
    for ax, selected, title in [(axes[0], stages, 'Overall reduction'),
                                (axes[1], stages[1:], 'Additional TOON savings')]:
        width = .24 if len(selected) == 3 else .34
        for i, (key, label, color) in enumerate(selected):
            x = [j + (i - (len(selected)-1)/2)*width for j in range(len(models))]
            bars = ax.bar(x, [totals[m][key]/1000 for m in models], width, label=label, color=color)
            ax.bar_label(bars, fmt="%.1f", fontsize=9, padding=3)
        ax.set_xticks(range(len(models)), [m.capitalize() for m in models])
        ax.set_ylabel('Thousands of input tokens — sum over 5 circuits')
        ax.set_title(title)
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_ylim(0, ax.get_ylim()[1]*1.14)
        ax.legend(frameon=False, fontsize=9)
    fig.savefig(destination/"confronto_token.png", dpi=180)
    fig.savefig(destination/"confronto_token.svg")
    plt.close(fig)
    def n(value): return f"{value:,}".replace(",", ".")
    def pct(value): return f"{value:.2f}".replace(".", ",")+"%"
    headings = ['Model', 'Previous v2', 'Reduced JSON', 'Reduced + TOON', 'Additional savings', 'Reduction from v2']
    aggregate = [[m.capitalize(), n(t["original_v2"]), n(t["minimal_json"]), n(t["minimal_toon"]),
                  pct(t["reduction_json_to_toon_percent"]), pct(t["reduction_original_to_toon_percent"])] for m,t in totals.items()]
    detailed = [[row["model"], row["circuit"], n(row["tokens"]["original_v2"]),
                 n(row["tokens"]["minimal_json"]), n(row["tokens"]["minimal_toon"]),
                 pct(row["reduction_json_to_toon_percent"])] for row in data["rows"]]
    full = [[m.capitalize(), n(t["original_full_json"])] for m,t in totals.items()]
    def table(headers, rows):
        return "\n".join(["| "+" | ".join(headers)+" |", "| "+" | ".join(["---"]*len(headers))+" |"]+
                         ["| "+" | ".join(row)+" |" for row in rows])
    text = [
        '# Original, reduced and TOON-reduced prompts', "",
        '19 September 2026. Five train circuits, five RAG examples per request. No new inference.',
        'The measurement covers prepared prompt input tokens, not response tokens or future repair consumption.', "",
        '## Overall result', "",
        "Totals across five circuits, computed separately with each model's tokenizer.",
        table(headings, aggregate), "",
        '![Token comparison](confronto_token.png)', "",
        '## Meaning of original', "",
        'The Earlier v2 column is the format used before content reduction: it retained QASM, provenance and multilevel references while already using aliases and reversible encoding. It is the reference used for the earlier Qwen/DJ comparison of 34,318 to 11,667 tokens.',
        'v2 requests are reconstructed on the same examples with the old serializer; original_v2_kind identifies exact matches with historical requests. These are not presented as new inference.',
        'Reduced JSON corresponds to actual first-attempt requests from qwen-prompt-v3-01, phi-prompt-v3-02 and gemma-prompt-v3-01.',
        'Reduced + TOON contains newly prepared requests that have not yet been sent.',
        'A fourth JSON reference without aliases was counted to distinguish the pre-alias format, reconstructed with the old exact complete-graph rule. Totals:', "",
        table(['Model', 'Reconstructed JSON without aliases'], full), "",
        '## TOON configuration', "",
        '@toon-format/toon 4.1.1 is installed from the official project https://github.com/toon-format/toon. Node 22.23.2 and the package are project-local and pinned through hashes and lockfiles. The Python MQT environment, uv.lock and trained models were not changed.',
        'Direct JSON-to-TOON conversion increased tokens. Trials with commas, tabs, vertical bars, edge tables and alternative feature arrangements are preserved. The final choice uses commas and two-space indentation.',
        'The 49 features form a table with one row per feature and columns current, E1...E5. Every zero and original value is retained: no feature selection or numeric rounding is applied.',
        'Hardware links use ordered neighbor lists per source qubit only when this exactly preserves the original edge order. Otherwise the original list remains. Complete topology retains the earlier exact rule.',
        'Each request is decoded and reconstructed automatically before sending. A changed value blocks the request. Nonuniform feature shapes retain their original structure.',
        'The response schema remains JSON and the validator is unchanged. Repair messages are retained. QASM and canonical metadata remain outside the LLM text and available in records.', "",
        '## Measurement method and limitations', "",
        "Native counting uses llama-tokenize.exe b10930 and the three original Q8_0 GGUFs. Text includes each model's chat template, TOON instructions, data, readable schema and checklist. json_schema sent separately to constrain server output adds no text tokens.",
        'For all 15 cases, the full JSON-baseline token sequence matches the server archive. Aggregate percentages use the ratio of sums rather than the mean of percentages.',
        'These measurements do not establish better decision quality, latency or repair rates with TOON. New train checks are required. No validation, Test or experimental training was started.', "",
        '## Per-circuit details', "",
        table(['Model', 'Circuit', 'Previous v2', 'Reduced JSON', 'Reduced + TOON', 'Savings over JSON'], detailed), "",
        '## Available data', "",
        'Files are under ../native_counts/<model>/<circuit>/: original_v2.txt, minimal_json.txt, minimal_toon.txt, original_full_json.txt, data.toon, schema, canonical input and counts. prepared_request_not_sent.json preserves the full native request to test.',
        'The machine-readable report is ../native_counts/report.json. The manifest preserves hashes. Historical attempts remain intact.', "",
        '## Start the checks', "",
        'Run commands one at a time from the WSL root. Each evaluates the five train circuits with p1_t0. TOON is already the default encoding.', "",
    ]
    commands = [
        '.venv/bin/python -m llm_selection.controller --technical --model qwen --label "qwen-toon-01" --precision Q8_0 --context 147456',
        '.venv/bin/python -m llm_selection.controller --technical --model phi --label "phi-toon-01" --precision Q8_0 --context 30000',
        '.venv/bin/python -m llm_selection.controller --technical --model gemma --label "gemma-toon-01" --precision Q8_0 --context 30000',
    ]
    fence = chr(96)*3
    for command in commands: text += [fence+"bash", command, fence, ""]
    text += ['Results go to new technical_episodes/<label>/ directories; each encoding.json records minimal-v3-toon1-20260919 and the TOON version. Choose different labels if these names already exist.',
             'Do not freeze the validation study until these checks finish.', "",
             '## Software checks', "",
             '244 tests passed. They cover complete reconstruction, zeros, precision, directed edges and order, special characters, nonuniform shapes, no-RAG input, repairs and JSON schema. One initial test compared Python tuples against JSON lists; it was corrected to compare the same JSON data model. Logs are preserved.',
             'The first npm installation from Windows through a UNC path failed; installation succeeded with project-local Linux Node. Reproduce it with .venv/bin/python -m llm_selection.setup_toon.', ""]
    (destination/"README.md").write_text("\n".join(text), encoding="utf-8")
    def html_table(headers, rows):
        return "<table><thead><tr>"+"".join("<th>"+html.escape(h)+"</th>" for h in headers)+"</tr></thead><tbody>"+\
            "".join("<tr>"+"".join("<td>"+html.escape(c)+"</td>" for c in row)+"</tr>" for row in rows)+"</tbody></table>"
    page = ['<!doctype html><html lang="en"><meta charset="utf-8"><title>TOON prompt comparison</title>',
        '<style>body{font:16px/1.5 system-ui;max-width:1200px;margin:40px auto;padding:0 24px;color:#192639}table{border-collapse:collapse;width:100%;margin:24px 0}td,th{padding:9px;border-bottom:1px solid #ddd;text-align:right}td:first-child,th:first-child{text-align:left}img{width:100%}pre{white-space:pre-wrap;background:#eef2f6;padding:20px}a{color:#165daf}</style>',
        '<h1>Original, reduced and TOON-reduced prompts</h1><p>19 September 2026 · Five train circuits · Measured input tokens, no new inference.</p>',
        '<p><a href="README.md">Full document: method, limits and commands</a></p>',
        html_table(headings,aggregate),'<img alt="Token comparison" src="confronto_token.png">',
        '<p>Earlier v2: reconstructed historical format. Reduced JSON: archived requests with exact token verification. TOON: prepared requests, not sent.</p>',
        '<h2>Complete prompts</h2><ul>']
    for row in data["rows"]:
        prefix = "../native_counts/"+row["model"]+"/"+row["circuit"]+"/"
        page.append('<li>'+html.escape(row["model"]+" / "+row["circuit"])+": "+
                    " · ".join('<a href="'+prefix+stage+'.txt">'+label+'</a>' for stage,label in [
                        ("original_v2",'Previous'),("minimal_json",'Reduced JSON'),("minimal_toon","TOON")])+"</li>")
    page += ['</ul><h2>Check commands</h2>', *["<pre>"+html.escape(c)+"</pre>" for c in commands], "</html>"]
    (destination/"index.html").write_text("\n".join(page), encoding="utf-8")
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(render(args.audit, args.output))
