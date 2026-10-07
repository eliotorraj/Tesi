'Generate standalone LaTeX and TikZ plots from verified data.'
from pathlib import Path
import argparse,json
HERE=Path(__file__).resolve().parent
def esc(s): return str(s).replace("_",r"\_")
def line(c): return " & ".join(map(str,c))+r" \\"+"\n"
def table(h,rs,cols):
 return r"\begin{tabular}{"+cols+"}\n\\toprule\n"+line(h)+"\\midrule\n"+"".join(line(r) for r in rs)+"\\bottomrule\n\\end{tabular}\n"
def chart(rows):
 t=[r"\begin{tikzpicture}[x=1cm,y=1cm,font=\fontsize{8}{9}\selectfont]",
 '\\node[anchor=west,font=\\bfseries] at (0,.8) {Circuit (* = partial oracle)};',
 '\\node[anchor=west,font=\\bfseries] at (8.8,.8) {Score: RAG and best known};',
 r"\node[anchor=west,font=\bfseries] at (20,.8) {Scarto $R-S$};"]
 for val in [0,.2,.4,.6,.8,1]:
  x=8.8+10*val
  t.extend([fr"\draw[gray!25] ({x},.25)--({x},-11.1);",fr"\node at ({x},.42) {{{val:.1f}}};"])
 for val in [0,.005,.01,.015,.02,.025]:
  x=20+5.5*val/.026
  t.extend([fr"\draw[gray!25] ({x},.25)--({x},-11.1);",fr"\node[font=\scriptsize] at ({x},.42) {{{val:.3f}}};"])
 for i,r in enumerate(rows):
  y=-i*.37
  if i%2==0: t.append(fr"\fill[gray!5] (0,{y-.16}) rectangle (25.6,{y+.16});")
  name=esc(r["circuit_id"])+("*" if not r["exhaustive"] else "")
  t.append(fr"\node[anchor=west] at (0,{y}) {{{r['id']:02d}\quad {name}}};")
  aa=8.8+10*r["system_score"]; b=8.8+10*r["oracle_score"]
  t.extend([fr"\draw[gray,thick] ({aa},{y})--({b},{y});",fr"\draw[orange!85!black,line width=.7pt] ({b},{y}) circle (2pt);",fr"\fill[blue!70!black] ({aa},{y}) circle (1pt);"])
  end=20+5.5*r["gap"]/.026; col="teal!75!black" if r["exhaustive"] else "gray!65"
  t.append(fr"\fill[{col}] (20,{y-.10}) rectangle ({end},{y+.10});" if r["gap"]>1e-12 else fr"\fill[{col}] (20,{y}) circle (.8pt);")
 return "\n".join(t+[r"\end{tikzpicture}"])
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--directory",type=Path,default=HERE/"risultati");a=ap.parse_args()
 d=json.loads((a.directory/"dati.json").read_text());rows=d["rows"];s=d["summary"]
 out=["""\\documentclass[10pt,a4paper,landscape]{article}
\\usepackage[utf8]{inputenc}\\usepackage[T1]{fontenc}\\usepackage[english]{babel}
\\usepackage[margin=15mm]{geometry}
\\usepackage{lmodern,booktabs,array,amsmath,tikz,xcolor,hyperref,fancyhdr}
\\hypersetup{colorlinks=true,linkcolor=blue!50!black}
\\pagestyle{fancy}\\fancyhf{}\\lhead{\\small Test: LLM + RAG, Manhattan, 5 examples}
\\rhead{\\small Comparison with max3 oracle}\\cfoot{\\small\\thepage}
\\setlength{\\headheight}{13pt}\\setlength{\\parindent}{0pt}\\setlength{\\parskip}{5pt}
\\newcommand{\\titolo}[1]{{\\Large\\bfseries #1}\\par\\vspace{3mm}}
\\begin{document}
\\titolo{How far is the best known result?}
{\\large LLM + RAG with 5 examples on 90 Test circuits}\\par
This compares original Manhattan RAG results with the oracle generated on 29 September 2026. \\texttt{expected\\_fidelity} is an estimate on synthetic Targets, not a physical-hardware measurement.
\\textbf{Main result.} The system reaches the best known score in 55/90 cases (61.1\\%) and remains below it in 35 (38.9\\%). No case exceeds the reference. Mean gap is 0.0018434763, or 0.18434763 percentage points on the score scale. Median gap is zero; 84/90 cases have gap at most 0.01.
"""]
 sr=[]
 for label,key in [('Mean RAG score',"mean_system"),('Mean best-known score',"mean_oracle"),('Mean gap',"mean_gap"),('Largest gap',"max_gap")]:
  sr.append([label]+[f"{v[key]:.10f}" for v in [s,s["complete"],s["partial"]]])
 out.append(table(['Measurement','All circuits','Complete oracle','Partial oracle'],[['Circuits',90,30,60]]+sr+[['At the best known score',"55 / 90","9 / 30","46 / 60"],['Below the best known score',"35 / 90","21 / 30","14 / 60"]],"lrrr"))
 out.append("""
\\medskip\\textbf{Definition.} For each circuit, $R=\\max_{d,c,s}F(d,c,s)$ is the maximum valid observed score over five devices, twelve Qiskit configurations and seeds $s\\in\\{0,1,2\\}$, restricted to compatible devices. The system uses one seed-0 compilation with score $S$. Gap is $\\Delta=R-S$: zero indicates a tie; positive values indicate observed headroom. Percentage points are $100\\Delta$; relative percentage loss is $100\\Delta/R$.
\\textbf{Generation finished, but some references remain incomplete.} The 16\\,200 cells include 864 incompatibilities. Of 15\\,336 compatible compilations, 14\\,249 succeed, 1\\,086 exceed 100 seconds and one fails. All 90 circuits have a reference, but only 30 have every compatible compilation succeed. For the other 60, observed maxima may underestimate what completing the grid could achieve. Errors and timeouts remain missing data, never zero scores.
\\textbf{Interpretation.} On nine circuits the system matches the full evaluated grid's maximum; on 46 more it matches an incomplete grid's observed maximum. This proves neither absolute optimality nor an upper bound for compilers outside the grid. This descriptive post-Test comparison never supplied the oracle to retrieval or prompts.
\\newpage\\titolo{Pair selection and seed variability}
The selected pair's maximum is $P=\\max_{s=0,1,2}F(d_{\\mathrm{LLM}},c_{\\mathrm{LLM}},s)$:\\[\\underbrace{R-S}_{\\text{total gap}}=\\underbrace{R-P}_{\\text{headroom from changing pair}}+\\underbrace{P-S}_{\\text{headroom from changing seed within the pair}}.\\]
All 90 selected pairs have three successful oracle compilations. Their seed-0 scores exactly reproduce historical RAG scores in every case. Mean between-pair headroom is 0.0014354875; mean within-pair headroom is 0.0004079888. The selected pair is among the best known in 55/90 cases. Restricting the oracle to seed 0 still gives mean gap 0.0018044775.
\\textbf{Ten largest gaps.} C = complete search; P = partial search. Values are scores, not percentages.
""")
 top=sorted(rows,key=lambda r:r["gap"],reverse=True)[:10]
 out.append(table(['Circuit',"RAG $S$","Oracle $R$",'Total $R-S$','Pair $R-P$',"Seed $P-S$",'Search'],
 [[esc(r["circuit_id"])]+[f"{r[k]:.8f}" for k in ["system_score","oracle_score","gap","choice_gap","within_pair_gap"]]+["C" if r["exhaustive"] else "P"] for r in top],"lrrrrrc"))
 out.append("""
\\medskip\\textbf{Example: \\texttt{qpeexact\\_indep\\_tket\\_6}.} RAG selects \\texttt{ibm\\_heron\\_156} with \\texttt{o3\\_default\\_default}, scoring 0.9460784319. The same pair reaches 0.9622779418 with seed 1 or 2. The best known score is 0.9705120914 on \\texttt{quantinuum\\_h2\\_56}, for example with \\texttt{o2\\_default\\_default} at every seed. Of the 0.0244336595 gap, 0.0161995099 concerns seed and 0.0082341496 concerns pair choice. The reference is partial: 172 valid compilations out of 180.
\\textbf{Example: \\texttt{tsp\\_indep\\_qiskit\\_9}.} This reference is complete. RAG selects \\texttt{quantinuum\\_h2\\_56}, \\texttt{o2\\_default\\_default}, scoring 0.9247191115 at every seed. \\texttt{ibm\\_falcon\\_127} with \\texttt{o2\\_default\\_default} or \\texttt{o3\\_default\\_default} reaches 0.9448083109. The entire 0.0200891994 gap concerns pair choice.
\\textbf{Reading the plots.} Blue point = RAG; orange circle = oracle. Equal scores place the point inside the circle. The right-hand gap plot shares a 0--0.026 scale: green bars = complete oracle; gray = partial. An asterisk marks a partial oracle. IDs and alphabetical order match the tables.
""")
 figs=a.directory/"grafici";figs.mkdir(exist_ok=True)
 for p in range(3):
  c=chart(rows[p*30:(p+1)*30])
  out.append(r"\newpage"+"\n"+'\\titolo{Score and gap per circuit: '+f"{p*30+1}--{(p+1)*30}"+"}\n"+c)
  out.append('\\par\\small Blue: RAG; orange: oracle. Green gap: complete reference; gray: partial. Scales match across the three pages. Small gaps are readable in the tables.')
  (figs/f"confronto_{p+1}.tex").write_text(r"""\documentclass[10pt]{article}
\usepackage[utf8]{inputenc}\usepackage[T1]{fontenc}\usepackage{lmodern,tikz}
\usepackage[paperwidth=28cm,paperheight=14cm,margin=8mm]{geometry}
\pagestyle{empty}\begin{document}\noindent
"""+c+"\n"+r"\end{document}",encoding="utf-8")
 for p in range(3):
  out.append(r"\newpage"+"\n"+'\\titolo{Full table: circuits '+f"{p*30+1}--{(p+1)*30}"+"}\n")
  out.append("""\\small Pair at max: selected pair's three-seed maximum equals the global maximum. C/P: complete/partial oracle. Every RAG outcome is successful.\\par\\vspace{2mm}{\\fontsize{8.5}{10}\\selectfont\\setlength{\\tabcolsep}{5pt}\\renewcommand{\\arraystretch}{1.18}
""")
  out.append(table(["ID",'Circuit',"Qubit","RAG $S$","Oracle $R$",'Gap $R-S$','Pair at maximum',"C/P"],
  [[r["id"],esc(r["circuit_id"]),r["num_qubits"]]+[f"{r[k]:.10f}" for k in ["system_score","oracle_score","gap"]]+['Yes' if r["selected_pair_is_best"] else "No","C" if r["exhaustive"] else "P"] for r in rows[p*30:(p+1)*30]],"rlrrrrcc"))
  out.append('}\\par\\small Ties: $10^{-12}$ tolerance on 10-decimal values. Choices, seeds and all ties are in \\texttt{confronto\\_90\\_circuiti.csv} and \\texttt{dati.json}.')
 out.append("""\\newpage\\titolo{Sources, checks and reproducibility}
\\textbf{System.} Original \\texttt{llm\\_rag} results started on 21 September 2026. Manhattan retrieval and five examples are verified in all 90 records. Selected Qwen profile \\texttt{qwen/p0\\_t0}, Qiskit seed 0; no WL, random retrieval, $k=1$ or $k=10$ variants.
\\textbf{Oracle.} Analysis \\texttt{20260929T210523\\_9df1db2b}, campaign \\texttt{test\\_max3\\_v1}. Maximum across seeds 0, 1 and 2 per pair, then across pairs. Versions: Python 3.12.13, Qiskit 2.5.0, MQT Bench 2.2.3, NumPy 2.5.1, MQT Predictor 2.4.0. Devices: \\texttt{ibm\\_falcon\\_27}, \\texttt{ibm\\_heron\\_133}, \\texttt{ibm\\_falcon\\_127}, \\texttt{ibm\\_heron\\_156}, \\texttt{quantinuum\\_h2\\_56}. Configurations, Targets and options match the oracle contract.
\\textbf{Checks.} Hashes of all 16\\,200 original outcomes were checked. Maxima for 5\\,400 pairs and 90 circuits were recomputed. Source IDs and hashes match between oracle and RAG; RAG scores match compilation results. Arithmetic circuit means use no exclusions. Complete/partial subsets contain different circuits, so their means do not isolate causal effects. The ten cases have the largest gaps; plots, tables and CSV include all 90.
\\textbf{Limits.} The oracle takes the best of three seeds while the system uses one, intentionally favoring the oracle. A partial reference is a lower bound on the full grid's maximum; a tie does not exclude better alternatives. Scores rounded to zero do not prove equal unrounded values. No quantum compilation was started and no original data, decisions, prompts or Dataset were changed. This analysis did not update graphify.
\\textbf{Original sources.}\\par{\\footnotesize
\\path{/home/elio/oracoli_mqt_test/test_max3_v1/analisi/20260929T210523_9df1db2b}\\par
\\path{/home/elio/Tesi-mqt-2.4-v2/archivio/valutazione/test/risultati/llm_rag}\\par
\\path{/home/elio/Tesi-mqt-2.4-v2/archivio/valutazione/test/preparazione/contratto_congelato.json}\\par}
\\textbf{Artifacts.} \\texttt{analizza.py} reads and verifies sources; \\texttt{impagina.py} generates LaTeX. \\texttt{dati.json} preserves measurements and ties. \\texttt{confronto\\_90\\_circuiti.csv} also contains choices, relative gaps and decomposition. \\texttt{provenienza.json} records hashes; \\texttt{grafici/} contains three standalone figures.
\\textbf{Separation.} The report is under \\texttt{oracle\\_test/confronto\\_llm\\_rag\\_k5}; the campaign remains external. No result enters the RAG index or decision pipelines.\\end{document}
""")
 (a.directory/"confronto_oracle_rag5.tex").write_text("\n".join(out),encoding="utf-8")
 print(a.directory/"confronto_oracle_rag5.tex")
if __name__=="__main__":main()
