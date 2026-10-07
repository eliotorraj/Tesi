"""Recupero esatto e ammissione di osservazioni, senza etichette di ottimalità."""
from __future__ import annotations
import copy
from comune import digest, finite, valid_score
from prototype.quantum_assistant.adapters.rag_features import manhattan
from prototype.quantum_assistant.adapters.rag_dataset import as_example, record_features


def rank_examples(corpus, observations, features, devices, source_sha256, position, k=5):
    """Unione di train e prefisso già concluso; scala train immutata."""
    query = corpus.transform.apply(features)
    candidates = []
    allowed = set(devices)
    for record in corpus.records:
        source = record["retrieval_input"]["circuit"]
        if (record["selected_device"]["device_id"] in allowed
                and source["source_sha256"] != source_sha256):
            distance = manhattan(query, corpus.transform.apply(record_features(record)))
            candidates.append({"rag_id": record["rag_id"], "distance": distance,
                               "origin": "initial", "record": record})
    for record in observations:
        if record["position"] >= position:
            raise ValueError("Osservazione corrente o futura nella memoria.")
        if record["source_sha256"] == source_sha256:
            continue
        if record["observed_configuration"]["device_id"] in allowed:
            distance = manhattan(query, corpus.transform.apply(record["circuit"]["features"]))
            candidates.append({"rag_id": record["record_id"], "distance": distance,
                               "origin": "incremental", "record": record})
    ranked = sorted(candidates, key=lambda r: (r["distance"], r["rag_id"]))
    if len({r["rag_id"] for r in ranked}) != len(ranked):
        raise ValueError("Identificativi duplicati nella memoria.")
    if len(ranked) < k:
        raise ValueError("Meno di cinque esempi compatibili; nessuna inferenza.")
    return ranked[:k]


def observation_entry(record, distance):
    """Nessun median_score, rank o top_configurations viene inventato."""
    device = record["observed_configuration"]["device_id"]
    return {
        "record_id": record["record_id"], "distance": distance,
        "example": {
            "input": {"circuit": {**record["circuit"], "features": {"values": record["circuit"]["features"]}},
                      "compatible_devices": [{"device_id": d} for d in record["compatible_devices"]]},
            "label": {"selected_device": {"device_id": device}, "top_configurations": []},
            "observation": record["observed_configuration"],
            "evidence_kind": "single_execution",
        },
    }


def make_observation(row, position, result, prompt, decision, compiled, *, known_hashes,
                     experiment_id, order, target_hashes, result_sha256):
    if not valid_score(result):
        return None, "unsuccessful_or_missing_score"
    if row["source_sha256"] in known_hashes:
        return None, "source_already_present"
    if not compiled.get("validation", {}).get("is_executable_on_target"):
        raise ValueError("Successo senza verifica del compilatore.")
    if (compiled.get("status") != "success" or compiled.get("score") != result["score"]
            or compiled.get("device") != decision["selected_device"]
            or result.get("device") != decision["selected_device"]
            or result.get("config_id") != decision["config_id"]):
        raise ValueError("Decisione, risultato e compilazione non concordano.")
    live = prompt["live_request"]
    device = decision["selected_device"]
    configs = {c["config_id"] for c in prompt["configuration_catalog"]["allowed_configurations"]}
    devices = {d["id"]: d for d in live["compatible_hardware"]}
    if (device not in devices or decision["config_id"] not in configs
            or decision["config_id"] not in devices[device].get("allowed_qiskit_configuration_ids", configs)):
        raise ValueError("Coppia non ammessa.")
    circuit = {k: copy.deepcopy(v) for k, v in live["circuit"].items()
               if k in ("name", "num_qubits", "depth", "operation_names", "features")}
    return {
        "schema_version": "incremental-observation/1",
        "record_id": "inc_" + row["source_sha256"],
        "experiment_id": experiment_id, "order": order, "position": position,
        "circuit_id": row["circuit_id"], "source_sha256": row["source_sha256"],
        "source_split": "test", "role": "past_stream_observation",
        "circuit": circuit, "compatible_devices": sorted(devices),
        "observed_configuration": {
            "device_id": device, "config_id": decision["config_id"],
            "score": result["score"], "metric": "expected_fidelity", "seed_transpiler": 0,
            "target_sha256": target_hashes[device], "evaluated_pairs": 1, "evaluated_seeds": 1,
            "optimality_verified": False,
        },
        "provenance": {"result_sha256": result_sha256,
                       "finished_at": result["finished_at"],
                       "hypothesis_reused": False,
                       "accepted_with_unverified_facts": result.get("accepted_with_unverified_facts")},
    }, "admitted"
