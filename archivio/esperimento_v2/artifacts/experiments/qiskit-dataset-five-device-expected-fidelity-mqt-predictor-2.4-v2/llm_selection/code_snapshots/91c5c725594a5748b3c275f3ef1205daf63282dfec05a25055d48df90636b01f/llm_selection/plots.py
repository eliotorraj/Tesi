"""Grafici eseguiti nel solo ambiente isolato di analisi."""
def figures(rows,trials,groups,directory):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams.update({"font.size":11,"axes.spines.top":False,"axes.spines.right":False,"savefig.bbox":"tight"})
    names=sorted(trials);labels=[n.replace("/","\n") for n in names];x=np.arange(len(names));result=[]
    def save(fig,name,caption):
        fig.savefig(directory/(name+".png"),dpi=220)
        fig.savefig(directory/(name+".svg"))
        plt.close(fig);result.append((name,caption))
    for field,name,title,unit in (
        ("regret_absolute","regret","Regret assoluto",1),
        ("total_call_seconds","tempi","Tempo delle chiamate [min]",60),
        ("total_output_tokens","token","Token di uscita, tutte le chiamate",1),
        ("peak_process_working_set_bytes","memoria","Picco RAM campionato del processo [GiB]",1024**3),
        ("peak_gpu_dedicated_bytes","vram","Picco VRAM campionato del processo [GiB]",1024**3)):
        fig,ax=plt.subplots(figsize=(9,4.6),constrained_layout=True)
        for i,trial in enumerate(names):
            values=[r[field]/unit for r in trials[trial] if r[field] is not None and (field=="regret_absolute" or r["llm_calls"]>0)]
            if values: ax.boxplot(values,positions=[i],widths=.55)
            ax.text(i,1.02,f"n={len(values)}",transform=ax.get_xaxis_transform(),ha="center",fontsize=9)
        ax.set(xticks=x,xticklabels=labels,ylabel=title)
        save(fig,name,title+". La numerosità indica i casi misurabili; i valori assenti non sono sostituiti con zero.")
    fig,ax=plt.subplots(figsize=(9,4.8),constrained_layout=True)
    metrics=[("Scelte valide e compilabili",lambda r:r["status"]=="success"),
             ("Valide alla prima chiamata",lambda r:r["first_attempt_valid"]),
             ("Con correzioni",lambda r:r["repair_count"]>0)]
    for i,(label,test) in enumerate(metrics):
        ax.bar(x+(i-1)*.25,[sum(test(r) for r in trials[n]) for n in names],width=.25,label=label)
    ax.set(xticks=x,xticklabels=labels,ylabel="Circuiti / 88",ylim=(0,88));ax.legend(fontsize=9)
    save(fig,"affidabilita","Affidabilità e correzioni sugli stessi 88 circuiti per ogni impostazione.")
    fig,ax=plt.subplots(figsize=(10,5),constrained_layout=True)
    bottom=np.zeros(len(names))
    for category in sorted({r["failure_category"] for r in rows if r["failure_category"]}):
        counts=np.array([sum(r["failure_category"]==category for r in trials[n]) for n in names])
        ax.bar(x,counts,bottom=bottom,label=category);bottom+=counts
    ax.set(xticks=x,xticklabels=labels,ylabel="Fallimenti / 88")
    if bottom.sum(): ax.legend(fontsize=8,bbox_to_anchor=(1,1))
    save(fig,"errori","Categorie degli errori. I registri distinguono trasporto, contesto, risposta e compilazione.")
    fig,axes=plt.subplots(1,2,figsize=(10,4.7),constrained_layout=True)
    for model in ("qwen","phi","gemma"):
        selected=[r for r in rows if r["trial_id"].startswith(model+"/") and r["input_tokens"] is not None]
        timed=[r for r in selected if r["total_call_seconds"] is not None and r["llm_calls"]>0]
        axes[0].scatter([r["input_tokens"]/1000 for r in timed],[r["total_call_seconds"]/60 for r in timed],s=10,alpha=.4,label=model)
        bad=[r["input_tokens"]/1000 for r in selected if r["status"]!="success"]
        if bad: axes[1].hist(bad,bins=12,histtype="step",label=model)
    axes[0].set(xlabel="Token del prompt [migliaia]",ylabel="Tempo delle chiamate [min]")
    axes[1].set(xlabel="Token del prompt [migliaia]",ylabel="Fallimenti, tutte le impostazioni")
    for ax in axes:
        if ax.get_legend_handles_labels()[0]: ax.legend(fontsize=9)
    save(fig,"lunghezza_prompt","Lunghezza del prompt, tempi e fallimenti. Le impostazioni dello stesso circuito non sono repliche indipendenti.")
    for field in ("family","num_qubits"):
        values=sorted({g["group_value"] for g in groups if g["group_field"]==field},key=lambda v:int(v) if field=="num_qubits" else v)
        for offset in range(0,len(values),6):
            chunk=values[offset:offset+6]
            matrix=np.full((len(names),len(chunk)),np.nan);counts={}
            for g in groups:
                if g["group_field"]==field and g["group_value"] in chunk:
                    i=names.index(g["trial_id"]);j=chunk.index(g["group_value"])
                    matrix[i,j]=100*g["valid_and_compilable"]/g["circuits"];counts[i,j]=g["circuits"]
            fig,ax=plt.subplots(figsize=(9,5.8),constrained_layout=True)
            plot=ax.imshow(matrix,vmin=0,vmax=100,cmap="Blues",aspect="auto")
            ax.set(xticks=range(len(chunk)),xticklabels=chunk,yticks=range(len(names)),yticklabels=names)
            for (i,j),count in counts.items():
                ax.text(j,i,f"{matrix[i,j]:.0f}%\nn={count}",ha="center",va="center",fontsize=9,color="white" if matrix[i,j]>60 else "black")
            fig.colorbar(plot,ax=ax,label="Valide e compilabili [%]")
            save(fig,f"{field}_{offset//6+1}","Affidabilità per "+("famiglia di circuito" if field=="family" else "numero di qubit")+". I regret e gli altri indicatori dei gruppi sono esportati in groups.csv.")
    return result


if __name__=="__main__":
    import argparse,json
    from pathlib import Path
    parser=argparse.ArgumentParser();parser.add_argument("input",type=Path);parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    data=json.loads(args.input.read_text())
    args.output.mkdir(parents=True,exist_ok=True)
    manifest=figures(data["rows"],data["trials"],data["groups"],args.output)
    (args.output/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
