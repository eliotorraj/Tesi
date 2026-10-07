'Supplement text and layout; numbers and JSON come from the audit.'
import json
def esc(text):
    return "".join({"\\":r"\textbackslash{}","_":r"\_","%":r"\%","&":r"\&","#":r"\#",
                    "{":r"\{","}":r"\}","$":r"\$"}.get(c,c) for c in str(text))
def listing(value):
    return "\\begin{lstlisting}\n"+json.dumps(value,ensure_ascii=False,indent=2)+"\n\\end{lstlisting}\n"
PREAMBLE="""
\\documentclass[a4paper,10pt]{article}
\\usepackage[margin=1.85cm]{geometry}
\\usepackage[T1]{fontenc}
\\usepackage[utf8]{inputenc}
\\usepackage[english]{babel}
\\usepackage{lmodern,booktabs,tabularx,xcolor,listings,tikz,hyperref}
\\usetikzlibrary{arrows.meta,positioning}
\\definecolor{ink}{HTML}{163047}
\\definecolor{pale}{HTML}{EEF4F7}
\\definecolor{warn}{HTML}{934618}
\\lstset{basicstyle=\\ttfamily\\fontsize{7.8}{9.1}\\selectfont,breaklines=true,
breakatwhitespace=false,columns=fullflexible,keepspaces=true,showstringspaces=false,
backgroundcolor=\\color{pale},frame=single,rulecolor=\\color{pale},
xleftmargin=4pt,xrightmargin=4pt,aboveskip=6pt,belowskip=6pt}
\\setlength{\\parindent}{0pt}\\setlength{\\parskip}{5pt}
\\newcommand{\\tagline}[1]{{\\small\\color{ink}\\textbf{#1}}\\par}
\\begin{document}
\\tagline{TEST COMPARISON SUPPLEMENT | 27 September 2026}
{\\LARGE\\bfseries Quality and correctness\\\\of verifiable facts}\\par
Analysis of the records for the 90 LLM + RAG decisions and 90 LLM no RAG decisions already collected.
This document supplements the existing comparison without changing it or running new Tests.
\\section*{What is verified}
The JSON response separates \\texttt{facts} from \\texttt{hypothesis}. Facts are assertions selected from four
predefined types: the program compares specific fields with available data. It does not assess the truth of free text.

\\textbf{E1, \\ldots, E5 identify retrieved examples, not facts.}
Each referenced fact specifies a local alias. The example's position in the prompt links it
to a specific train record. E1 can therefore identify different circuits in different requests.
\\begin{center}
\\begin{tikzpicture}[node distance=5mm,every node/.style={draw=ink,rounded corners,
align=center,font=\\small,fill=pale,minimum height=13mm},>=Latex]
\\node(a){Fact in JSON\\\\\\texttt{example\\_id: Ei}};
\\node(b)[right=of a]{Alias Ei\\\\in the prompt};
\\node(c)[right=of b]{Train record\\\\\\texttt{rag\\_id}};
\\node(d)[right=of c]{Record field\\\\being compared};
\\draw[->,thick](a)--(b);\\draw[->,thick](b)--(c);\\draw[->,thick](c)--(d);
\\end{tikzpicture}\\end{center}
\\section*{Results across all cases}

"""
COMMENTS=[
('Two facts supported by the same example',
 "The chosen device matches the one selected in the record. The Falcon 127 / o2\\_dense\\_sabre pair also appears first in the displayed ranking. There is a tie with o3\\_dense\\_sabre: the fact does not certify a unique winner. The value 0.9822170185 is QAOA's historical median, not a measurement of the current groundstate circuit.",
 'The hypothesis proposes that the result transfers to the new circuit. This step is not verified.'),
('Historical pair and equal qubit counts',
 'The selected pair is present in the displayed rows of the Deutsch--Jozsa record. The current circuit and example both have 2 qubits, so the second fact is true. Equal qubit counts do not prove similar topology, gate sequences or compilation behavior.',
 'The phrase \\emph{similar 2-qubit circuit} is a free-text assessment. The validator checks the equality 2 = 2, not structural similarity or performance transfer.'),
('One valid reference and one misattributed reference',
 'The first fact is valid: E4 selects Heron 156, as does the response. The second is invalid under the contract: capacity must be checked against the hardware catalog without \\texttt{example\\_id}. In this case, 156 qubits are sufficient for the 3 required qubits, but E4 is not the permitted source for this assertion. We do not correct the original JSON.',
 'The text also repeats instructions received in the prompt. This repetition reduces clarity and adds no evidence. Depth and qubits mentioned in the prose are not certified by the device fact alone.')]
def render(data):
    from analizza_fatti import SAMPLES
    r=data["reports"]["llm_rag"]["counts"]
    out=[PREAMBLE,"""\\begin{tabularx}{\\linewidth}{Xrr}\\toprule Measurement & LLM + RAG & No RAG\\\\\\midrule
"""]
    for label,a,b in [
        ('Final responses with all facts valid',f"{r['verified']}/90","90/90"),
        ('Final responses with at least one invalid fact',f"{r['unverified']}/90","0/90"),
        ('Valid facts in final responses',f"{r['fact_verified']}/180","90/90"),
        ('Responses valid on the first attempt',f"{r['first_verified']}/90","90/90"),
        ('Complete responses, including repairs',str(r["attempts"]),"90")]:
        out.append(f"{label} & {a} & {b}"+r"\\")
    out += [r"\bottomrule\end{tabularx}",
        f"In RAG, {r['historical_verified']} final facts referring to examples are all consistent with the cited fields. All 17 invalid facts concern device capacity with an unauthorized Ei reference. Capacity is still sufficient; the error is in evidence attribution. After three attempts, these choices were accepted under the specified rule, preserving their unverified status.",
        '\\textbf{The 90/90 without RAG concerns qubit capacity only.} This is a simpler check: it does not demonstrate better explanations or superior compilation performance.',
        "\\textbf{Hypotheses are not checked for semantic correctness and must not be taken as true statements.} Checks of format, length or permitted choices do not certify the text's claims."]
    for i,name in enumerate(SAMPLES):
        s=next(s for s in data["samples"] if s["circuit"]==name)
        alias=next(iter(s["records"])); record=s["records"][alias]
        e=next(e for e in s["view"]["retrieved_labeled_examples"] if e["id"]==alias)
        title,explanation,limit=COMMENTS[i]
        out += [r"\newpage",'\\tagline{SAMPLE '+str(i+1)+' / 3 | illustrative selection}',
          r"\section*{"+title+"}",'\\textbf{Test circuit:} \\texttt{'+esc(name)+f"}}. Final response, attempt {s['attempt']}.",
          '\\textbf{Original LLM JSON.} Complete values; only layout changed.',
          listing(s["response"]),'\\textbf{Link to train evidence}',
          r"\begin{center}\begin{tikzpicture}[>=Latex,every node/.style={draw=ink,fill=pale,rounded corners,font=\small,align=center}]"
          r"\node(a){\texttt{example\_id: "+alias+r"}};"
          r"\node(b)[right=8mm of a]{"+alias+' in the prompt};\\node(c)[right=8mm of b]{\\texttt{'+esc(e["circuit"]["circuit_id"])+'}\\\\train example};\\draw[->,thick](a)--(b);\\draw[->,thick](b)--(c);\\end{tikzpicture}\\end{center}',
          '{\\footnotesize Complete record: \\texttt{'+esc(record["rag_id"])+r"}}\par",
          '\\textbf{Record excerpt (first ranking row)}',
          listing({"id":alias,"num_qubits":e["circuit"]["num_qubits"],"selected_device":e["selected_device"],
                   "top_configurations":[e["top_configurations"][0]]}),
          '\\textbf{Check outcome.} '+explanation,
          r"{\color{warn}\textbf{Limite dell'ipotesi.}} "+limit,
          r"{\small Stati registrati, in ordine: \texttt{"+esc(", ".join(c["result"] for c in s["checks"]))+'}. Response status: \\texttt{'+esc(s["status"])+r"}.}"]
    out += ['\\newpage\\tagline{SCOPE OF RESULTS AND REPRODUCIBILITY}',
       '\\section*{Fact correctness and explanation quality}',
       '\\begin{tabularx}{\\linewidth}{Xrr}\\toprule Final RAG fact type & Valid & Total\\\\\\midrule']
    labels={"selected_device_matches_example":'Same device as the example',
            "selected_pair_among_reported_best":'Pair among the displayed configurations',
            "same_qubit_count_as_example":'Same qubit count',
            "selected_device_has_enough_qubits":'Sufficient qubit capacity'}
    for kind,label in labels.items():
        rows=[x for x in data["reports"]["llm_rag"]["kinds"] if x["assertion"]==kind]
        out.append(label+f" & {sum(x['count'] for x in rows if x['result']=='verified')} & {sum(x['count'] for x in rows)}"+r"\\")
    out += [r"\bottomrule\end{tabularx}",
       'The system makes a limited part of the explanation checkable. Most historical facts concern only the device: 88 assertions. Only 5 explicitly concern the device/configuration pair. The 2 qubit-count equalities describe size without demonstrating similar behavior.',
       "\\textbf{A correct fact does not mean an optimal choice.} A pair's presence in the top rows applies to that circuit, those synthetic Targets and that procedure. The pair rule accepts displayed rows and declared ties; it does not always imply first place or superiority on the current circuit. Qubit capacity is only a necessary condition.",
       '\\textbf{Hypotheses: no semantic verification.} The system does not compare prose with experiments, external knowledge or a logical proof. It does not certify quality promises, causal explanations, circuit similarity or configuration suitability. Even a response with all facts valid retains \\texttt{explanation\\_fully\\_verified=false}. The three observations about prose on the previous pages are manual qualitative comments, not an automatic measurement or a systematic evaluation of all 90 hypotheses.',
       '\\section*{How the analysis was performed}',
       "We reread all response and check JSON files, including rejected attempts. The final attempt's JSON matches the preserved decision. Ei mappings, view fingerprints and example contents were checked against prompts, records and the verified train Dataset. The four rules were reapplied, including explicit comparisons separate from saved outcomes. Results match the recorded checks.",
       f"The {r['attempts']} RAG responses contain a total of {r['attempt_fact_verified'] + r['attempt_fact_unsupported']} facts: {r['attempt_fact_verified']} valid and {r['attempt_fact_unsupported']} invalid. This denominator includes repairs and must not be confused with the 180 final facts. Samples illustrate three different cases; overall counts come from the full set of 90 circuits.",
       r"\section*{Fonti locali e ricostruzione}",
       '{\\small\\raggedright Generator: \\texttt{archivio/valutazione/test/report/analizza\\_fatti.py}. Data: \\texttt{test/risultati/llm\\_rag} and \\texttt{llm\\_senza\\_rag}. For each circuit: \\texttt{prompt.json}, \\texttt{encoding.json}, \\texttt{decision\\_validation.json}, \\texttt{decision.json} and \\texttt{attempt\\_*/call/response\\_raw.json}.\\par}',
       'The \\texttt{audit\\_fatti.json} file preserves counts, checks of all attempts, the three complete JSON responses, full train examples and source SHA-256 fingerprints. Reanalysis does not repeat historical compilations: correctness here means consistency with the supplied data, not physical verification of fidelity.',r"\end{document}"]
    return "\n".join(x + (r"\par" if x.endswith(".") or x.endswith(r"\end{tabularx}") else "") for x in out)
