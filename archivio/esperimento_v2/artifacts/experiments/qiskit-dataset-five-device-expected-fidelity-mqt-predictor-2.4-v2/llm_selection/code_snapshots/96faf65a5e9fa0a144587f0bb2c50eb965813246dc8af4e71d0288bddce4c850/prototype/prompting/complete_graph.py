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

