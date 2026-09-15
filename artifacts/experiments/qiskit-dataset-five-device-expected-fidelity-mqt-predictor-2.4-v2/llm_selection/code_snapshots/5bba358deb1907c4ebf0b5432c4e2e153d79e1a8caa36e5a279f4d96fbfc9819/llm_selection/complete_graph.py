"""Rappresentazione esatta e breve dei soli grafi completi di connettività."""
import copy
import json
NOTE=("For coupling_edges only, {representation: complete_directed_without_self_loops, "
      "num_vertices: N, order: source_then_target} denotes every ordered pair [i,j] "
      "with 0 <= i,j < N and i != j, ordered by i then j. This is the full graph, not a sampled edge list.")

def encode(prompt):
    result=copy.deepcopy(prompt)
    for device in result["live_request"]["compatible_hardware"]:
        size=device["num_qubits"]
        edges=device["coupling_edges"]
        expected=[[i,j] for i in range(size) for j in range(size) if i!=j]
        if edges==expected:
            device["coupling_edges"]={"representation":"complete_directed_without_self_loops",
                                      "num_vertices":size,"order":"source_then_target"}
    if decode(result)!=prompt: raise ValueError("Full graph round-trip mismatch")
    return result

def decode(prompt):
    result=copy.deepcopy(prompt)
    for device in result["live_request"]["compatible_hardware"]:
        edges=device["coupling_edges"]
        if isinstance(edges,dict) and edges.get("representation")=="complete_directed_without_self_loops":
            if set(edges)!={"representation","num_vertices","order"} or edges["order"]!="source_then_target":
                raise ValueError("Unknown graph representation")
            size=edges["num_vertices"]
            device["coupling_edges"]=[[i,j] for i in range(size) for j in range(size) if i!=j]
    return result

def main():
    from tokenizers import Tokenizer
    from .common import OUTPUT, read_json, write_json, now
    rows=[]
    for model in ("qwen","phi","gemma"):
        tokenizer=Tokenizer.from_file(str(OUTPUT/"models"/model/"official_tokenizer.json"))
        for split in ("train","validation"):
            for path in sorted((OUTPUT/"prompts"/split).glob("*.json")):
                prompt=read_json(path)["prompt"]
                converted=encode(prompt)
                text=NOTE+"\n\n"+json.dumps(converted,ensure_ascii=False,separators=(",",":"))
                rows.append({"model":model,"split":split,"circuit_id":path.stem,"exact_roundtrip":True,
                             "graph_tokens":len(tokenizer.encode(text,add_special_tokens=False).ids)})
        del tokenizer
    target=OUTPUT/"preparation"/"complete_graph_token_probe.json"
    if target.exists(): raise ValueError("Probe already saved")
    write_json(target,{"at":now(),"measurement":"official tokenizer, excludes native chat wrapper","rows":rows})
    for model in ("qwen","phi","gemma"):
        for split in ("train","validation"):
            selected=[r["graph_tokens"] for r in rows if r["model"]==model and r["split"]==split]
            print(model,split,"count",len(selected),"min",min(selected),"max",max(selected),flush=True)
if __name__=="__main__": main()
