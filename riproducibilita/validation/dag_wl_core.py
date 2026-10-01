"""DAG e kernel WL diretto. Nessuna lettura di score validation/test."""
from __future__ import annotations
from collections import Counter
import hashlib
import math
from pathlib import Path
import time
from settings import WORK as ROOT, digest, read, save, sha

SUPPORTED_H = tuple(range(1, 31))
MAX_H = max(SUPPORTED_H)

REPRESENTATION = {
    "revision": "dag-wl-v1", "dag": "qiskit.DAGCircuit",
    "decomposition": "none; original parsed QASM operations",
    "nodes": "quantum/classical inputs, outputs, original operations including barriers",
    "labels": "operation name, arity, control state, numeric parameters binned at pi/8",
    "parameters": "nearest integer bin, ties away from zero; no periodic wrapping",
    "edges": "directed multiset, quantum/classical type, local source/target operand positions",
    "symmetric_barrier_ports": True, "wire_names_in_labels": False,
    "kernel": "normalized sum of WL count inner products for rounds 0..h",
    "max_h": MAX_H, "k": 5, "tie_break": "rag_id ascending",
    "summary": "dag-summary-v1; at most 8 operation-to-operation transitions",
}

def graph_from_qasm(qasm):
    from qiskit import qasm2
    from qiskit.converters import circuit_to_dag
    from qiskit.dagcircuit import DAGOpNode, DAGInNode
    qc = qasm2.loads(qasm, custom_instructions=qasm2.LEGACY_CUSTOM_INSTRUCTIONS)
    dag = circuit_to_dag(qc)
    nodes = list(dag.topological_nodes())
    ids = {n._node_id: i for i, n in enumerate(nodes)}
    encoded = []
    for n in nodes:
        if isinstance(n, DAGOpNode):
            params = []
            for p in n.op.params:
                v = float(p)
                if not math.isfinite(v):
                    raise ValueError("Parametro non numerico o non finito.")
                params.append(v)
            def quantize(x):
                return int(math.copysign(math.floor(abs(x)/(math.pi/8)+0.5), x))
            label = ["op", n.op.name, len(n.qargs), len(n.cargs),
                     getattr(n.op, "ctrl_state", None), [quantize(x) for x in params]]
            encoded.append({"label": label, "name": n.op.name, "parameters": params,
                            "qubits": [qc.find_bit(q).index for q in n.qargs]})
        else:
            kind = "q" if n.wire in qc.qubits else "c"
            encoded.append({"label": ["in" if isinstance(n, DAGInNode) else "out", kind]})
    def port(n, wire):
        if not isinstance(n, DAGOpNode):
            return "boundary"
        if n.op.name == "barrier":
            return "barrier"
        if wire in n.qargs:
            return "q" + str(n.qargs.index(wire))
        return "c" + str(n.cargs.index(wire))
    edges = []
    for a, b, wire in dag.edges():
        kind = "q" if wire in qc.qubits else "c"
        edges.append([ids[a._node_id], ids[b._node_id], [kind, port(a, wire), port(b, wire)]])
    return {"nodes": encoded, "edges": sorted(edges), "num_qubits": qc.num_qubits,
            "num_clbits": qc.num_clbits}

def wl_counts(graph, max_h=MAX_H):
    """Tutte le etichette sono hash globali, mai interi assegnati per grafo."""
    if type(max_h) is not int or max_h not in range(MAX_H+1):
        raise ValueError("max_h deve essere un intero fra 0 e 30.")
    incoming = [[] for _ in graph["nodes"]]
    outgoing = [[] for _ in graph["nodes"]]
    for a, b, role in graph["edges"]:
        incoming[b].append((a, role))
        outgoing[a].append((b, role))
    colors = [digest(n["label"]) for n in graph["nodes"]]
    rounds = [dict(Counter(colors))]
    for _ in range(max_h):
        colors = [digest([colors[i],
                          sorted((role, colors[j]) for j, role in incoming[i]),
                          sorted((role, colors[j]) for j, role in outgoing[i])])
                  for i in range(len(colors))]
        rounds.append(dict(Counter(colors)))
    return rounds

def similarity(a, b, h):
    if type(h) is not int or h not in SUPPORTED_H:
        raise ValueError("h deve essere un intero fra 1 e 30.")
    if len(a) <= h or len(b) <= h:
        raise ValueError("Istogrammi WL insufficienti: ricostruire un indice separato fino a h=30.")
    def dot(x, y):
        if len(x) > len(y):
            x, y = y, x
        return sum(v*y.get(k, 0) for k, v in x.items())
    cross = sum(dot(a[i], b[i]) for i in range(h+1))
    aa = sum(dot(a[i], a[i]) for i in range(h+1))
    bb = sum(dot(b[i], b[i]) for i in range(h+1))
    if not aa or not bb:
        raise ValueError("Grafo vuoto: similarita non definita.")
    return min(1.0, max(0.0, cross / math.sqrt(aa*bb)))

def graph_summary(graph):
    """Statistiche del sorgente, senza etichette di prestazione o stime di score."""
    nodes = graph["nodes"]
    ops = {i: n for i, n in enumerate(nodes) if n["label"][0] == "op"}
    predecessors = [[] for _ in nodes]
    indegree = [0]*len(nodes)
    successors = [[] for _ in nodes]
    patterns = Counter()
    for a, b, role in graph["edges"]:
        predecessors[b].append(a)
        successors[a].append(b)
        indegree[b] += 1
        if a in ops and b in ops:
            patterns[(ops[a]["name"], role[0], role[1], ops[b]["name"], role[2])] += 1
    # Kahn: no assumption on storage order; parallel edges retain multiplicity.
    ready = [i for i, d in enumerate(indegree) if not d]
    levels = [0]*len(nodes)
    visited = 0
    for a in ready:
        visited += 1
        levels[a] = max((levels[p] for p in predecessors[a]), default=0) + int(a in ops)
        for b in successors[a]:
            indegree[b] -= 1
            if not indegree[b]:
                ready.append(b)
    if visited != len(nodes):
        raise ValueError("Il grafo deve essere aciclico.")
    widths = Counter(levels[i] for i in ops)
    interactions = Counter()
    for n in ops.values():
        if len(n["qubits"]) == 2 and n["name"] != "barrier":
            interactions[tuple(sorted(n["qubits"]))] += 1
    degrees = Counter()
    for a, b in interactions:
        degrees[a] += 1
        degrees[b] += 1
    ordered = sorted(patterns.items(), key=lambda x: (-x[1], x[0]))
    return {
        "representation": "dag-summary-v1",
        "num_qubits": graph["num_qubits"], "num_clbits": graph["num_clbits"],
        "operation_nodes_including_barriers": len(ops), "wire_edges": len(graph["edges"]),
        "dependency_layers_including_barriers": max(widths, default=0),
        "max_operations_in_same_dependency_layer": max(widths.values(), default=0),
        "operations": dict(sorted(Counter(n["name"] for n in ops.values()).items())),
        "two_qubit_interaction_pairs": len(interactions),
        "max_distinct_neighbors_from_two_qubit_operations": max(degrees.values(), default=0),
        "two_qubit_interaction_count_max": max(interactions.values(), default=0),
        "most_frequent_direct_transitions": [
            {"from": k[0], "wire": k[1], "from_port": k[2], "to": k[3],
             "to_port": k[4], "count": v} for k, v in ordered[:8]],
        "omitted_transition_types": max(0, len(ordered)-8),
    }

def descriptor(qasm):
    start = time.perf_counter()
    graph = graph_from_qasm(qasm)
    graph_seconds = time.perf_counter()-start
    start = time.perf_counter()
    counts = wl_counts(graph)
    return {"source_sha256": hashlib.sha256(qasm.encode()).hexdigest(),
            "graph": graph, "graph_sha256": digest(graph), "counts": counts,
            "summary": graph_summary(graph),
            "timings": {"dag_seconds": graph_seconds, "wl_seconds": time.perf_counter()-start}}

def index_identity(corpus):
    from importlib.metadata import version
    return {"representation": REPRESENTATION, "corpus_sha256": corpus.source_sha256,
            "rag_seal_sha256": sha(ROOT/"data/seal.json"), "qiskit": version("qiskit"),
            "implementation_sha256": sha(Path(__file__)),
            "record_ids": sorted(r["rag_id"] for r in corpus.records)}

def prepare_index(corpus, directory):
    """Indice privato della campagna, riprendibile e verificato prima dell'uso."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    import portalocker
    with portalocker.Lock(str(directory/".lock"), timeout=0):
        identity = index_identity(corpus)
        contract = directory/"contratto.json"
        if contract.exists():
            if read(contract) != identity:
                raise ValueError("Indice WL incompatibile. Conservare la campagna precedente.")
        else:
            save(contract, identity)
        by_id, files = {}, {}
        for i, record in enumerate(sorted(corpus.records, key=lambda r:r["rag_id"]), 1):
            if record["split"] != "train":
                raise ValueError("L'indice ammette soltanto train.")
            c = record["retrieval_input"]["circuit"]
            source = (ROOT/"data"/c["source_ref"]).resolve()
            if not source.is_relative_to((ROOT/"data/circuits/train").resolve()):
                raise ValueError("Sorgente fuori train.")
            if sha(source) != c["source_sha256"]:
                raise ValueError("QASM train modificato.")
            path = directory/"record"/(digest(record["rag_id"])+".json")
            if not path.exists():
                value = descriptor(source.read_text())
                value.update(rag_id=record["rag_id"], record_sha256=digest(record))
                save(path, value)
            value = read(path)
            if (value["source_sha256"] != c["source_sha256"] or
                value["record_sha256"] != digest(record) or value["rag_id"] != record["rag_id"] or
                value["graph_sha256"] != digest(value["graph"])):
                raise ValueError("Record indice WL alterato.")
            # Verify derived content as well, including before sealing resumed builds.
            if value["counts"] != wl_counts(value["graph"]) or value["summary"] != graph_summary(value["graph"]):
                raise ValueError("Contenuto derivato WL incoerente.")
            files[str(path.relative_to(directory))] = sha(path)
            by_id[record["rag_id"]] = value
            if i % 100 == 0:
                print(f"Indice WL: {i}/{len(corpus.records)}", flush=True)
        manifest = {"identity": identity, "files": files}
        target = directory/"manifest.json"
        if target.exists():
            if read(target) != manifest:
                raise ValueError("Sigillo indice WL alterato.")
        else:
            save(target, manifest)
        return by_id, sha(target)

def rank(corpus, index, query, devices, objective, h):
    from prototype.quantum_assistant.adapters.qdrant_context import matching_records
    from prototype.quantum_assistant.adapters.rag_dataset import EXPERIMENT_ID
    candidates = matching_records(corpus, devices=devices, objective=objective, experiment_id=EXPERIMENT_ID)
    if len(candidates) < 5:
        raise ValueError("Servono cinque esempi train compatibili.")
    values = [(r, similarity(query["counts"], index[r["rag_id"]]["counts"], h)) for r in candidates]
    return sorted(values, key=lambda item: (-item[1], item[0]["rag_id"]))

def request_context(qasm):
    from qiskit_dataset.catalog import load_catalog
    from prototype.quantum_assistant.adapters.hardware import MqtHardwareCatalog, HardwareMaskBuilder
    from prototype.quantum_assistant.adapters.request import QasmRequestParser, RequestSemanticValidator
    from prototype.quantum_assistant.models import UiSubmission
    from uuid import uuid4
    catalog = load_catalog()
    hardware = MqtHardwareCatalog(catalog.supported_device_ids, configuration_catalog=catalog).snapshot()
    parsed = QasmRequestParser().parse(UiSubmission(request_id=str(uuid4()), user_text="", qasm2=qasm))
    request = RequestSemanticValidator().normalize(parsed, hardware)
    mask = HardwareMaskBuilder().filter(request, hardware)
    if not mask.available_device_ids:
        raise ValueError("Nessun dispositivo compatibile.")
    return catalog, request, mask

def prepare_wl(qasm, *, corpus, index, h, with_summary, index_sha256):
    from prototype.quantum_assistant.adapters.rag_dataset import as_example
    from prototype.quantum_assistant.adapters.context import StructuredEvidenceRegistryBuilder, StructuredPromptBuilder
    start = time.perf_counter()
    catalog, request, mask = request_context(qasm)
    rag_start = time.perf_counter()
    query = descriptor(qasm)
    retrieval_start = time.perf_counter()
    ranked = rank(corpus, index, query, mask.available_device_ids, request.figure_of_merit, h)
    ranking_seconds = time.perf_counter()-retrieval_start
    chosen = ranked[:5]
    examples = tuple(as_example(r, 1-s) for r, s in chosen)
    registry = StructuredEvidenceRegistryBuilder(configuration_catalog=catalog).build(examples)
    prompt = StructuredPromptBuilder(configuration_catalog=catalog).build(request, mask, examples, evidence_registry=registry).payload
    if with_summary:
        prompt["dag_summaries"] = {
            "current_circuit": query["summary"],
            "examples": [{"example_id": f"E{i}", "summary": index[r["rag_id"]]["summary"]}
                         for i, (r, _) in enumerate(chosen, 1)]}
    rag_seconds = time.perf_counter()-rag_start
    return request, prompt, {
        "seconds": time.perf_counter()-start, "rag_seconds": rag_seconds,
        "query": query, "ranking_seconds": ranking_seconds,
        "index_sha256": index_sha256, "h": h, "k": 5, "representation": REPRESENTATION,
        "index_preparation_included_in_rag_seconds": False,
        "dag_summaries_sha256": digest(prompt["dag_summaries"]) if with_summary else None,
        "records": [{"example_id": f"E{i}", "rag_id": r["rag_id"], "similarity": s, "distance": 1-s}
                    for i, (r, s) in enumerate(chosen, 1)],
        "all_candidates": [{"rag_id": r["rag_id"], "similarity": s} for r, s in ranked],
    }
