'Descriptive analysis added after the Test: qubits, examples and differences.'
from dati import number
from impaginazione import fmt, table

METHOD="llm_recupero_random"


def analyze(runs, manifest):
    maps={m:{c["circuit_id"]:c for c in runs[m]["circuits"]}
          for m in ("llm_rag", METHOD, "llm_senza_rag")}
    qubits={r["circuit_id"]:r["num_qubits"] for r in manifest["circuits"] if r["split"]=="test"}
    rows=[]
    for cid in sorted(qubits):
        values=[maps[m][cid]["score"] for m in maps]
        if not all(number(v) for v in values):
            raise ValueError('Qubit analysis requires scores for all three LLM variants.')
        a,b,c=values
        rows.append(dict(circuit_id=cid,num_qubits=qubits[cid],rag=a,random_rag=b,
                         no_rag=c,difference=a-b,identical=a==b,within_001=abs(a-b)<=0.01))
    groups=[]
    for name,lo,hi in (('Up to 5',0,5),('6 to 16',6,16),('Over 16',17,float("inf"))):
        selected=[r for r in rows if lo<=r["num_qubits"]<=hi]
        n=len(selected)
        groups.append(dict(group=name,n=n,equal=sum(r["identical"] for r in selected),
            close=sum(r["within_001"] for r in selected),
            mean_rag=sum(r["rag"] for r in selected)/n if n else None,
            mean_random=sum(r["random_rag"] for r in selected)/n if n else None,
            mean_no_rag=sum(r["no_rag"] for r in selected)/n if n else None,
            mean_difference=sum(r["difference"] for r in selected)/n if n else None))
    a=sum(r["rag"] for r in rows)/len(rows);b=sum(r["random_rag"] for r in rows)/len(rows)
    return dict(rows=rows,groups=groups,mean_rag=a,mean_random=b,difference=a-b,
        relative_decrease=(a-b)/a,
        selected_examples=[r for r in rows if r["circuit_id"] in
            ("groundstate_medium_indep_tket_12","qpeexact_indep_qiskit_40")],
        grouping_note='Descriptive groups chosen after reviewing the Test; qubits from the manifest; no equivalence between qubit count and complexity.')


def conclusion(d):
    body='\\subsection{The contribution of example selection}'+"\n"
    body+=(f"LLM + RAG has a mean score of {fmt(d['mean_rag'], 6)}, compared with {fmt(d['mean_random'], 6)} for LLM + Random RAG on the same 90 successful circuits. The gap is {fmt(d['difference'], 6)} in score: approximately {fmt(100 * d['difference'])} points on the 0--100 percentage scale, close to five points. In relative terms, random retrieval is lower by {fmt(100 * d['relative_decrease'])}\\%. These are two different ways to express the difference and must not be confused.\n\nThe mean alone hides substantial differences between circuits. To make the interpretation concrete, we distinguish three qubit groups derived from the manifest. These are descriptive groups defined after observing the results. The number of qubits alone does not measure circuit complexity.\n\n")
    rows=[[g["group"],g["n"],f"{g['equal']}/{g['n']}",f"{g['close']}/{g['n']}",
           fmt(g["mean_rag"],4),fmt(g["mean_random"],4),fmt(g["mean_no_rag"],4)] for g in d["groups"]]
    body+=r"\begin{samepage}"+"\n"
    body+=table(["Qubit",'Cases','Identical',r"$|\Delta|\leq0{,}01$","RAG","Random RAG","No RAG"],rows,size="small")
    body+=r"\end{samepage}"+"\n"
    g=d["groups"][0]
    body+=(f"Among the {g['n']} circuits with at most 5 qubits, {g['close']} have scores differing by at most 0.01 between retrieval methods; only {g['equal']} are identical at the stored precision. The mean gap is {fmt(g['mean_difference'], 6)}. LLM no RAG also achieves a high mean score in this group ({fmt(g['mean_no_rag'], 4)}. These data suggest a limited additional contribution from example selection in many small cases, without proving that all circuits with few qubits are easy.\n\n")
    for r in d["selected_examples"]:
        body+=('For '+r"\nolinkurl{"+r["circuit_id"]+f"}}, LLM + RAG achieves {fmt(r['rag'], 6)} and LLM + Random RAG {fmt(r['random_rag'], 6)}. The difference is {fmt(r['difference'], 6)} in score, or {fmt(100 * r['difference'])} points on the 0--100 scale. The relative decrease from RAG is {fmt(100 * r['difference'] / r['rag'])}\\%.\n\n")
    body+=("""The two examples show that choosing relevant cases can accompany much better proposals even when the overall mean difference seems modest. In the observed sample, the mean advantage is larger in groups with more qubits. The increase is not uniform: there are ties, reversals and large circuits with low scores for both retrieval methods. This suggests that relevant examples may help particularly with more demanding cases, not that more qubits guarantee a benefit.

This is an exploratory interpretation of one draw per circuit, not general proof of a relationship between complexity and the usefulness of examples. More retrieval seeds and structural circuit measurements would help test it. All values and groups are preserved in the analysis CSV files.

""")
    return body
