"""Controllo tecnico train: identità del sorgente e uso delle prove recuperate."""
import json

def check(saved, response=None, *, valid=False):
    if saved.get("circuit_metadata", {}).get("split") != "train":
        return {"applicable": False}
    prompt = saved["prompt"]
    metric = prompt.get("live_request", {}).get("figure_of_merit")
    exact = []
    zeros = []
    for rank, retrieved in enumerate(prompt.get("retrieved_labeled_examples", []), 1):
        example = retrieved["example"]
        if retrieved["distance"] == 0:
            zeros.append(retrieved["record_id"])
        circuit = example.get("input", {}).get("circuit", {})
        if (circuit.get("source_sha256") == saved["source_sha256"]
                and example.get("objective", {}).get("name") == metric):
            selected = example["label"]["selected_device"]
            exact.append({"record_id": retrieved["record_id"], "rank": rank,
                          "distance": retrieved["distance"],
                          "source_sha256": circuit["source_sha256"],
                          "device_id": selected["device_id"],
                          "config_id": selected["best_config_id"],
                          "tied_best_config_ids": selected.get("tied_best_config_ids", [])})
    result = {"applicable": True, "zero_distance_record_ids": zeros, "exact_source_records": exact,
              "self_retrieved_at_zero": any(r["distance"] == 0 for r in exact),
              "comparison": "Exact source SHA-256 and metric; zero feature distance alone is insufficient.",
              "response_checked": response is not None, "response_valid": valid if response is not None else None}
    if response is None:
        return result
    try:
        decoded = json.loads(response) if isinstance(response, str) else response
        if not isinstance(decoded, dict):
            raise ValueError("Output is not an object")
        from qiskit_dataset.catalog import load_catalog
        if "config_id" in decoded:
            config = load_catalog().by_id[decoded["config_id"]].config_id
        else:
            plan = decoded["qiskit_plan"]
            config = load_catalog().find(plan["optimization_level"], plan["layout_method"], plan["routing_method"]).config_id
        device = decoded["selected_device"]
        refs = {r["reference_id"]: r for r in decoded.get("evidence_refs", [])}
        source_ids = {r["record_id"] for r in exact if r["distance"] == 0}
        used = {}
        for kind in ("historical_device_support", "historical_configuration_support"):
            used[kind] = sorted({refs[r]["record_id"] for c in decoded.get("claims", [])
                                 if c.get("claim_type") == kind for r in c.get("evidence_ref_ids", []) if r in refs})
        if "config_id" in decoded:
            aliases = {f"E{i}": entry["record_id"] for i, entry in
                       enumerate(prompt.get("retrieved_labeled_examples", []), 1)}
            cited = [aliases[a] for a in decoded.get("evidence", []) if a in aliases]
            result.update(selected_device=device, selected_config=config,
                matches_primary_label=any(device == r["device_id"] and config == r["config_id"] for r in exact),
                matches_tied_optimum=any(device == r["device_id"] and config in [r["config_id"], *r["tied_best_config_ids"]] for r in exact),
                cited_record_ids=cited, cites_self_record=valid and bool(source_ids.intersection(cited)),
                citation_scope="References only; free-text reasoning and causal use are not verified")
            return result
        result.update(
            selected_device=device, selected_config=config,
            matches_primary_label=any(device == r["device_id"] and config == r["config_id"] for r in exact),
            matches_tied_optimum=any(device == r["device_id"] and config in [r["config_id"], *r["tied_best_config_ids"]] for r in exact),
            historical_claim_records=used,
            uses_self_record_for_both_claims=valid and all(source_ids.intersection(ids) for ids in used.values()))
    except (ValueError, TypeError, KeyError, AttributeError) as error:
        result.update(uses_self_record_for_both_claims=False, diagnostic=str(error))
    return result
