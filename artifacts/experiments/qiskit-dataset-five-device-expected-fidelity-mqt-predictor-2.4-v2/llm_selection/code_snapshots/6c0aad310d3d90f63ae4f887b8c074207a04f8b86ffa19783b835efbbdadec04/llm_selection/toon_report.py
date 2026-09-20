"""Documento e figure dai conteggi TOON; eseguire nel runtime delle analisi."""
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
    stages = [("original_v2", "Precedente v2", "#8792a2"),
              ("minimal_json", "JSON ridotto", "#337ab7"),
              ("minimal_toon", "Ridotto + TOON", "#26846f")]
    for ax, selected, title in [(axes[0], stages, "Riduzione complessiva"),
                                (axes[1], stages[1:], "Risparmio aggiuntivo con TOON")]:
        width = .24 if len(selected) == 3 else .34
        for i, (key, label, color) in enumerate(selected):
            x = [j + (i - (len(selected)-1)/2)*width for j in range(len(models))]
            bars = ax.bar(x, [totals[m][key]/1000 for m in models], width, label=label, color=color)
            ax.bar_label(bars, fmt="%.1f", fontsize=9, padding=3)
        ax.set_xticks(range(len(models)), [m.capitalize() for m in models])
        ax.set_ylabel("Migliaia di token input — somma di 5 circuiti")
        ax.set_title(title)
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_ylim(0, ax.get_ylim()[1]*1.14)
        ax.legend(frameon=False, fontsize=9)
    fig.savefig(destination/"confronto_token.png", dpi=180)
    fig.savefig(destination/"confronto_token.svg")
    plt.close(fig)
    def n(value): return f"{value:,}".replace(",", ".")
    def pct(value): return f"{value:.2f}".replace(".", ",")+"%"
    headings = ["Modello", "Precedente v2", "JSON ridotto", "Ridotto + TOON", "Risparmio aggiuntivo", "Riduzione rispetto a v2"]
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
        "# Prompt originale, ridotto e ridotto con TOON", "",
        "19 settembre 2026. Cinque circuiti train, cinque esempi RAG per richiesta. Nessuna nuova inferenza.",
        "La misura riguarda i token di ingresso dei prompt preparati, non i token delle risposte o il consumo delle future correzioni.", "",
        "## Risultato complessivo", "",
        "Totali sui cinque circuiti, calcolati separatamente con il tokenizer di ciascun modello.",
        table(headings, aggregate), "",
        "![Confronto dei token](confronto_token.png)", "",
        "## Che cosa significa originale", "",
        "La colonna «Precedente v2» è il formato usato prima della riduzione dei contenuti: conservava QASM, provenienza e riferimenti multilivello, pur usando già alias e una codifica reversibile. È lo stesso riferimento del precedente confronto 34.318 → 11.667 token per Qwen/DJ.",
        "Le richieste v2 sono ricostruite sui medesimi esempi con il vecchio serializzatore; original_v2_kind nel rapporto indica quali coincidono esattamente con una richiesta storica. Non vengono presentate come nuove inferenze.",
        "La colonna «JSON ridotto» corrisponde alle richieste reali delle prove qwen-prompt-v3-01, phi-prompt-v3-02 e gemma-prompt-v3-01, tutte al primo tentativo.",
        "La colonna «Ridotto + TOON» contiene le nuove richieste preparate, non ancora inviate.",
        "Per distinguere anche il formato anteriore agli alias, abbiamo contato un quarto riferimento JSON senza alias, ricostruito con la vecchia regola esatta del grafo completo. Totali:", "",
        table(["Modello", "JSON senza alias, ricostruito"], full), "",
        "## Come è configurato TOON", "",
        "È installato @toon-format/toon 4.1.1, dal progetto ufficiale https://github.com/toon-format/toon. Node 22.23.2 e il pacchetto sono locali al progetto e fissati con impronte e lockfile. L'ambiente Python MQT, uv.lock e i modelli addestrati non sono stati modificati.",
        "La conversione diretta del JSON in TOON aumentava i token. Sono conservate le prove con virgola, tab e barra verticale, tabelle di archi e diverse disposizioni delle feature. La scelta finale usa virgole e due spazi di rientro.",
        "Le 49 feature sono in una tabella con una riga per caratteristica e colonne current, E1...E5. Ogni zero e valore originale è conservato: non si selezionano feature e non si arrotondano numeri.",
        "I collegamenti hardware sono liste ordinate di vicini per qubit sorgente, solo quando questo conserva esattamente l'ordine originale degli archi. In caso contrario resta la lista originale. La topologia completa mantiene la precedente regola esatta.",
        "Ogni richiesta viene decodificata e ricostruita automaticamente prima dell'invio. Se un valore cambia, la richiesta viene bloccata. Le forme di feature non uniformi mantengono la struttura originale.",
        "Lo schema della risposta resta JSON e il validatore resta invariato. Anche i messaggi correttivi sono conservati. QASM e metadati canonici restano fuori dal testo LLM e disponibili nei registri.", "",
        "## Metodo di misura e limiti", "",
        "Conteggio nativo con llama-tokenize.exe b10930 e i tre GGUF Q8_0 originali. Il testo comprende il template di chat di ciascun modello, le istruzioni TOON, i dati, lo schema leggibile e la checklist. Lo schema json_schema passato separatamente al server vincola l'uscita e non aggiunge token al testo.",
        "Per ciascuno dei 15 casi, l'intera sequenza di token della base JSON coincide con quella archiviata dal server. Le percentuali aggregate usano il rapporto tra le somme, non una media delle percentuali.",
        "Queste misure non dimostrano che TOON migliori la qualità delle scelte, la latenza o le correzioni. Servono le nuove prove train. Non sono stati avviati validation, test o training sperimentale.", "",
        "## Dettaglio per circuito", "",
        table(["Modello", "Circuito", "Precedente v2", "JSON ridotto", "Ridotto + TOON", "Risparmio su JSON"], detailed), "",
        "## Dati consultabili", "",
        "I file sono in ../native_counts/<modello>/<circuito>/: original_v2.txt, minimal_json.txt, minimal_toon.txt, original_full_json.txt, data.toon, schema, input canonico e conteggi. prepared_request_not_sent.json conserva la richiesta nativa completa da provare.",
        "Il rapporto leggibile da programma è ../native_counts/report.json. Il manifesto conserva le impronte. I tentativi storici rimangono intatti.", "",
        "## Avvio delle prove", "",
        "Dalla radice WSL, eseguire uno alla volta. Ogni comando prova i cinque circuiti train con p1_t0. La codifica TOON è già quella predefinita.", "",
    ]
    commands = [
        '.venv/bin/python -m llm_selection.controller --technical --model qwen --label "qwen-toon-01" --precision Q8_0 --context 147456',
        '.venv/bin/python -m llm_selection.controller --technical --model phi --label "phi-toon-01" --precision Q8_0 --context 30000',
        '.venv/bin/python -m llm_selection.controller --technical --model gemma --label "gemma-toon-01" --precision Q8_0 --context 30000',
    ]
    fence = chr(96)*3
    for command in commands: text += [fence+"bash", command, fence, ""]
    text += ["I risultati finiscono nelle nuove cartelle technical_episodes/<etichetta>/; ogni encoding.json registra minimal-v3-toon1-20260919 e la versione TOON. Usare altre etichette se questi nomi esistono già.",
             "Non congelare lo studio di validation finché queste prove non sono concluse.", "",
             "## Verifiche software", "",
             "244 test superati. Coprono ricostruzione completa, zeri, precisione, archi diretti e ordine, caratteri speciali, forme non uniformi, assenza di RAG, correzioni e schema JSON. Un test iniziale confrontava tuple Python con liste JSON; è stato corretto confrontando lo stesso modello di dati JSON. I log restano conservati.",
             "La prima installazione npm da Windows sul percorso UNC ha fallito; è riuscita con Node Linux locale al progetto. La procedura riproducibile è .venv/bin/python -m llm_selection.setup_toon.", ""]
    (destination/"README.md").write_text("\n".join(text), encoding="utf-8")
    def html_table(headers, rows):
        return "<table><thead><tr>"+"".join("<th>"+html.escape(h)+"</th>" for h in headers)+"</tr></thead><tbody>"+\
            "".join("<tr>"+"".join("<td>"+html.escape(c)+"</td>" for c in row)+"</tr>" for row in rows)+"</tbody></table>"
    page = ['<!doctype html><html lang="it"><meta charset="utf-8"><title>Confronto prompt TOON</title>',
        '<style>body{font:16px/1.5 system-ui;max-width:1200px;margin:40px auto;padding:0 24px;color:#192639}table{border-collapse:collapse;width:100%;margin:24px 0}td,th{padding:9px;border-bottom:1px solid #ddd;text-align:right}td:first-child,th:first-child{text-align:left}img{width:100%}pre{white-space:pre-wrap;background:#eef2f6;padding:20px}a{color:#165daf}</style>',
        '<h1>Prompt originale, ridotto e ridotto con TOON</h1><p>19 settembre 2026 · Cinque circuiti train · Token input misurati, nessuna nuova inferenza.</p>',
        '<p><a href="README.md">Documento completo: metodo, limiti e comandi</a></p>',
        html_table(headings,aggregate),'<img alt="Confronto dei token" src="confronto_token.png">',
        '<p>Precedente v2: ricostruzione del formato storico. JSON ridotto: richieste archiviate, token verificati esattamente. TOON: richieste preparate, non inviate.</p>',
        '<h2>Prompt completi</h2><ul>']
    for row in data["rows"]:
        prefix = "../native_counts/"+row["model"]+"/"+row["circuit"]+"/"
        page.append('<li>'+html.escape(row["model"]+" / "+row["circuit"])+": "+
                    " · ".join('<a href="'+prefix+stage+'.txt">'+label+'</a>' for stage,label in [
                        ("original_v2","Precedente"),("minimal_json","JSON ridotto"),("minimal_toon","TOON")])+"</li>")
    page += ['</ul><h2>Comandi per le prove</h2>', *["<pre>"+html.escape(c)+"</pre>" for c in commands], "</html>"]
    (destination/"index.html").write_text("\n".join(page), encoding="utf-8")
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(render(args.audit, args.output))
