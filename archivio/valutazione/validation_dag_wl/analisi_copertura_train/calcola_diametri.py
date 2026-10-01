"""Diametri esatti dei DAG train: nessuna inferenza, nessuna compilazione quantistica."""
from pathlib import Path
import argparse,csv,hashlib,json,math,platform,statistics,sys,time
from datetime import datetime,timezone
import networkx as nx

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
sys.path[:0]=[str(REPO/"archivio/valutazione/test/strumenti"),str(REPO/"prototipo")]
from common import SOURCE,digest
from dag_wl_core import graph_from_qasm
from prototype.quantum_assistant.adapters.rag_dataset import load_corpus

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+"\n")
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output",type=Path,default=HERE/"esecuzioni/diametri_v1")
    args=ap.parse_args()
    out=args.output.resolve()
    out.mkdir(parents=True,exist_ok=False)
    start=time.perf_counter()
    index=REPO/"archivio/valutazione/test/dag_wl_retrieval/risultati/llm_rag_dag_wl/indice"
    manifest=json.loads((index/"manifest.json").read_text())
    sources={str(p.relative_to(REPO)):sha(p) for p in [Path(__file__),SOURCE,index/"manifest.json",REPO/"archivio/valutazione/test/strumenti/dag_wl_core.py"]}
    train=[r for r in json.loads(SOURCE.read_text())["circuits"] if r["split"]=="train"]
    corpus=load_corpus()
    rag={r["rag_id"]:r for r in corpus.records}
    assert len(train)==422 and len(rag)==396
    assert sorted(rag)==manifest["identity"]["record_ids"]
    assert {r["source_sha256"] for r in train}=={r["retrieval_input"]["circuit"]["source_sha256"] for r in rag.values()}
    aliases={}
    for r in train:aliases.setdefault(r["source_sha256"],[]).append(r["circuit_id"])
    write(out/"avvio.json",{"at":datetime.now(timezone.utc).isoformat(),"python":platform.python_version(),"networkx":nx.__version__,"scope":"train only","algorithm":"networkx.diameter, usebounds=True, unweighted undirected simple projection, max over connected components","original_representation":manifest["identity"]["representation"],"training_entries":len(train),"distinct_sources":len(rag)})
    rows=[]
    paths=sorted((index/"record").glob("*.json"))
    assert len(paths)==len(rag)
    for i,p in enumerate(paths,1):
        tick=time.perf_counter()
        h=sha(p);assert h==manifest["files"][str(p.relative_to(index))]
        sources[str(p.relative_to(REPO))]=h
        d=json.loads(p.read_text());r=rag[d["rag_id"]];c=r["retrieval_input"]["circuit"]
        assert r["split"]=="train" and digest(r)==d["record_sha256"]
        qasm=(REPO/"prototipo/data"/c["source_ref"]).resolve()
        assert qasm.is_relative_to((REPO/"prototipo/data/circuits/train").resolve())
        assert sha(qasm)==d["source_sha256"]==c["source_sha256"]
        sources[str(qasm.relative_to(REPO))]=sha(qasm)
        assert digest(d["graph"])==d["graph_sha256"]
        assert graph_from_qasm(qasm.read_text())==d["graph"]
        G=nx.Graph()
        G.add_nodes_from(range(len(d["graph"]["nodes"])))
        G.add_edges_from((a,b) for a,b,_ in d["graph"]["edges"])
        comps=sorted(nx.connected_components(G),key=lambda x:(-len(x),min(x)))
        diams=[nx.diameter(G.subgraph(nodes),usebounds=True) for nodes in comps]
        row={"circuit_id":c["circuit_id"],"rag_id":r["rag_id"],"source_sha256":c["source_sha256"],"train_aliases":sorted(aliases[c["source_sha256"]]),"num_qubits":c["num_qubits"],"nodes":len(G),"edges_original":len(d["graph"]["edges"]),"components":len(comps),"component_sizes":[len(x) for x in comps],"component_diameters":diams,"h_full_coverage":max(diams),"dependency_layers":d["summary"]["dependency_layers_including_barriers"],"measurement_seconds":time.perf_counter()-tick}
        rows.append(row)
        with (out/"circuiti.jsonl").open("a") as f:f.write(json.dumps(row,ensure_ascii=False)+"\n")
        if i%25==0 or i==len(paths):print(f"{i}/{len(paths)}; massimo finora {max(x['h_full_coverage'] for x in rows)}",flush=True)
    maximum=max(r["h_full_coverage"] for r in rows)
    winners=sorted([r for r in rows if r["h_full_coverage"]==maximum],key=lambda r:r["circuit_id"])
    # Independent exact cross-check of extrema: all-source BFS distances.
    witnesses=[]
    for r in winners:
        p=index/"record"/(digest(r["rag_id"])+".json")
        d=json.loads(p.read_text());G=nx.Graph()
        G.add_nodes_from(range(len(d["graph"]["nodes"])))
        G.add_edges_from((a,b) for a,b,_ in d["graph"]["edges"])
        best=-1;pair=None
        for a,dist in nx.all_pairs_shortest_path_length(G):
            b=max(dist,key=dist.get)
            if dist[b]>best:best=dist[b];pair=(a,b)
        assert best==maximum
        path=nx.shortest_path(G,*pair)
        witnesses.append({"circuit_id":r["circuit_id"],"independent_all_pairs_diameter":best,"farthest_pair":pair,"shortest_path":path,"path_nodes":[d["graph"]["nodes"][i] for i in path]})
    write(out/"testimoni_massimo.json",witnesses)
    result={"h_train_full_coverage":maximum,"train_entries":len(train),"distinct_train_sources":len(rows),"all_original_train_sources_covered":True,"maximizers":winners,"top_10":sorted(rows,key=lambda r:(-r["h_full_coverage"],r["circuit_id"]))[:10],"diameter_min":min(r["h_full_coverage"] for r in rows),"diameter_median":statistics.median(r["h_full_coverage"] for r in rows),"coverage":[{"h":h,"distinct_covered":sum(r["h_full_coverage"]<=h for r in rows),"distinct_total":len(rows),"train_entries_covered":sum(len(r["train_aliases"]) for r in rows if r["h_full_coverage"]<=h),"train_total":len(train)} for h in sorted({24,30,maximum})],"disconnected_graphs":sum(r["components"]>1 for r in rows),"maximum_verified_by_all_pairs_bfs":True,"seconds":time.perf_counter()-start,"scope":"Every node can receive initial information from every node in its own connected component. Directions remain labels in WL; ignored only for propagation distance. This is not a guarantee of WL discriminative completeness or better retrieval. Train only: validation and Test diameters not measured."}
    write(out/"riepilogo.json",result)
    write(out/"provenienza.json",sources)
    with (out/"diametri_train.csv").open("w",newline="") as f:
        fields=["circuit_id","num_qubits","nodes","components","h_full_coverage","dependency_layers"]
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader()
        w.writerows(sorted(rows,key=lambda r:(-r["h_full_coverage"],r["circuit_id"])))
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
if __name__=="__main__":main()
