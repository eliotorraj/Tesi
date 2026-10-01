"""Analisi descrittiva aggiunta dopo il Test: qubit, esempi e differenze."""
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
            raise ValueError("Analisi per qubit richiede score presenti per le tre varianti LLM.")
        a,b,c=values
        rows.append(dict(circuit_id=cid,num_qubits=qubits[cid],rag=a,random_rag=b,
                         no_rag=c,difference=a-b,identical=a==b,within_001=abs(a-b)<=0.01))
    groups=[]
    for name,lo,hi in (("Fino a 5",0,5),("Da 6 a 16",6,16),("Oltre 16",17,float("inf"))):
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
        grouping_note="Fasce descrittive scelte dopo la lettura del Test; qubit dal manifest; nessuna equivalenza qubit/complessità.")


def conclusion(d):
    body=r"\subsection{Il contributo della scelta degli esempi}"+"\n"
    body+=(f"LLM + RAG ha score medio {fmt(d['mean_rag'],6)}, contro {fmt(d['mean_random'],6)} "
        f"di LLM + Random RAG sui medesimi 90 circuiti riusciti. Il divario è {fmt(d['difference'],6)} "
        f"di score: circa {fmt(100*d['difference'])} punti sulla scala percentuale 0--100, "
        f"vicino ai cinque punti. In termini relativi, il recupero casuale è inferiore del {fmt(100*d['relative_decrease'])}\\%. "
        "Sono due modi diversi di esprimere la differenza; non vanno confusi.\n\n"
        "La media, da sola, nasconde differenze rilevanti fra circuiti. Per rendere concreta la lettura "
        "distinguiamo tre fasce di qubit ricavate dal manifest. Le fasce sono descrittive, definite dopo "
        "aver osservato i risultati. Il numero di qubit non misura da solo la complessità del circuito.\n")
    rows=[[g["group"],g["n"],f"{g['equal']}/{g['n']}",f"{g['close']}/{g['n']}",
           fmt(g["mean_rag"],4),fmt(g["mean_random"],4),fmt(g["mean_no_rag"],4)] for g in d["groups"]]
    body+=r"\begin{samepage}"+"\n"
    body+=table(["Qubit","Casi","Identici",r"$|\Delta|\leq0{,}01$","RAG","Random RAG","No RAG"],rows,size="small")
    body+=r"\end{samepage}"+"\n"
    g=d["groups"][0]
    body+=(f"Fra i {g['n']} circuiti fino a 5 qubit, {g['close']} hanno score distanti al massimo 0,01 "
        f"fra i due recuperi; solo {g['equal']} sono identici alla precisione conservata. "
        f"Il divario medio è {fmt(g['mean_difference'],6)}. Anche LLM no RAG raggiunge in questa fascia "
        f"uno score medio elevato ({fmt(g['mean_no_rag'],4)}. Questi dati suggeriscono un contributo "
        "aggiuntivo ridotto della selezione degli esempi in molti casi piccoli, pur senza dimostrare "
        "che tutti i circuiti con pochi qubit siano facili.\n\n")
    for r in d["selected_examples"]:
        body+=("Per "+r"\nolinkurl{"+r["circuit_id"]+"}, "
            f"LLM + RAG ottiene {fmt(r['rag'],6)} e LLM + Random RAG {fmt(r['random_rag'],6)}. "
            f"La differenza è {fmt(r['difference'],6)} di score, cioè {fmt(100*r['difference'])} "
            "punti sulla scala 0--100. "
            f"Il calo relativo rispetto a RAG è {fmt(100*r['difference']/r['rag'])}\\%.\n\n")
    body+=("I due esempi mostrano che la scelta di casi pertinenti può accompagnarsi a proposte "
        "molto migliori anche quando la differenza media complessiva sembra modesta. "
        "Nel campione osservato il vantaggio medio è più ampio nelle fasce con più qubit. "
        "Non è però una crescita uniforme: esistono parità, inversioni e circuiti grandi con score "
        "basso per entrambi i recuperi. La lettura proposta è dunque che gli esempi pertinenti "
        "possono aiutare soprattutto nei casi più impegnativi; non che un numero maggiore di qubit "
        "garantisca un beneficio.\n\n"
        "Questa è un'interpretazione esplorativa di una sola estrazione per circuito, non una prova "
        "generale del rapporto fra complessità e utilità degli esempi. Più semi di recupero e misure "
        "strutturali del circuito permetterebbero di verificarla meglio. Tutti i valori e le fasce "
        "sono conservati nei CSV dell'analisi.\n\n")
    return body
