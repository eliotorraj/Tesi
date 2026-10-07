"""Adattatore sperimentale: riusa il framework senza modificarlo o scrivere il suo indice."""
from __future__ import annotations
import copy
import json
import time
from pathlib import Path
from comune import digest, memory_digest, now, read, save, sha, source_path
from memoria import observation_entry, rank_examples
import app
from prototype.prompting import facts, minimal
from prototype.prompting.toon import encode_view, NOTE as TOON_NOTE
from prototype.quantum_assistant.adapters.context import StructuredEvidenceRegistryBuilder
from prototype.quantum_assistant.adapters.rag_dataset import as_example
from runner import compile_job, llm_metrics

NOTE = (
    "Some retrieved examples are single_execution observations from earlier requests. "
    "Their observed_configuration reports one executed pair and one seed; other pairs were not tested. "
    "Their score is not a median, a ranking, or evidence that the pair was best. "
    "selected_pair_among_reported_best is supported only by initial examples with top_configurations. "
    "For single_execution examples you may use the device-match or equal-qubit fact when true. "
    "Initial examples retain their original train comparisons. Do not compare raw scores across different circuits."
)


def prepare(qasm, *, corpus, observations, row, position):
    started = time.perf_counter()
    request, prompt, _ = app.prepare(qasm, rag=False)
    retrieval_started = time.perf_counter()
    devices = [d["id"] for d in prompt["live_request"]["compatible_hardware"]]
    selected = rank_examples(corpus, observations, request.features, devices,
                             row["source_sha256"], position)
    base_examples = [as_example(s["record"], s["distance"]) for s in selected if s["origin"] == "initial"]
    prompt["allowed_evidence_registry"] = StructuredEvidenceRegistryBuilder().build(base_examples).to_dict()
    entries = []
    for item in selected:
        if item["origin"] == "initial":
            example = as_example(item["record"], item["distance"])
            # JSON conversion preserves the framework's tuples and nested structures.
            from prototype.quantum_assistant.adapters.context import _json_ready
            entries.append({"record_id": example.record_id, "distance": example.distance,
                            "example": _json_ready(example.prompt_input)})
        else:
            entry = observation_entry(item["record"], item["distance"])
            entries.append(entry)
            prompt["allowed_evidence_registry"]["records"].append({
                "record_id": entry["record_id"], "evidence_kind": "single_execution",
                "observation": entry["example"]["observation"],
            })
    prompt["retrieved_labeled_examples"] = entries
    prompt["response_contract"] = {"version": "4.0.0", "json_schema": facts.response_schema()}
    log = {
        "seconds": time.perf_counter() - started,
        "rag_seconds": time.perf_counter() - retrieval_started,
        "implementation": "exact_float64_scan_without_qdrant_writes",
        "k": 5, "distance": "Manhattan", "transform_sha256": corpus.transform_artifact["sha256"],
        "memory_before_sha256": memory_digest(observations), "memory_size": len(observations),
        "records": [{"example_id": f"E{i}", "rag_id": r["rag_id"], "distance": r["distance"],
                     "origin": r["origin"],
                     "observation_position": r["record"].get("position")}
                    for i, r in enumerate(selected, 1)],
    }
    return prompt, log


def model_view(prompt):
    view = minimal.model_input(prompt)
    for source, target in zip(prompt["retrieved_labeled_examples"], view["retrieved_labeled_examples"], strict=True):
        observation = source["example"].get("observation")
        if observation is not None:
            target.pop("top_configurations", None)
            target["evidence_kind"] = "single_execution"
            target["observed_configuration"] = copy.deepcopy(observation)
    return view


def messages(prompt, feedback=()):
    if not any(e["example"].get("observation") for e in prompt["retrieved_labeled_examples"]):
        return facts.messages(prompt, feedback)
    view = model_view(prompt)
    schema = {k: v for k, v in facts.response_schema().items() if k not in ("$schema", "$id", "title")}
    fence = chr(96) * 3
    text = facts.NOTE + "\n" + NOTE + "\n" + TOON_NOTE + "\n"
    text += fence + "toon\n" + encode_view(view) + "\n" + fence + "\n"
    text += "fact_rules: " + json.dumps(facts.RULES, separators=(",", ":"))
    text += "\nresponse_schema: " + json.dumps(schema, separators=(",", ":"))
    if feedback:
        text += "\nCorrect the previous response and return the whole JSON. You may keep an allowed pair.\n"
        text += json.dumps(list(feedback), ensure_ascii=False)
    return [{"role": "user", "content": text}]


def decide(prompt, directory, http):
    """Stesso budget e controlli v4; cambia solo la vista delle osservazioni."""
    feedback = []
    context = app.PROFILES["desktop"]
    for attempt in range(1, 4):
        folder = directory / f"attempt_{attempt}"
        folder.mkdir()
        chat = {"messages": messages(prompt, feedback), "chat_template_kwargs": {"enable_thinking": False},
                "reasoning_effort": "none"}
        formatted = http("/apply-template", chat, folder / "template")
        tokenized = http("/tokenize", {"content": formatted["prompt"], "add_special": False,
                                      "parse_special": True}, folder / "tokenize")
        count = len(tokenized["tokens"])
        save(folder / "context.json", {"input_tokens": count, "output_budget": 4096, "context": context})
        if count + 4096 > context:
            raise ValueError("Contesto insufficiente; nessuna generazione o rimozione di esempi.")
        excluded = {"stream_options", "max_tokens", "chat_template_kwargs", "reasoning_effort", "reasoning_format"}
        payload = {k: v for k, v in app.CONFIG["fixed"].items() if k not in excluded}
        payload.update(temperature=0.0, stream=False, prompt=formatted["prompt"],
                       json_schema=facts.response_schema(), n_predict=4096, return_tokens=True)
        response = http("/completion", payload, folder / "call")
        if response.get("truncated") or response.get("stop_type") == "limit" or response.get("stop") is False:
            raise RuntimeError("Risposta incompleta; tentativo conservato.")
        checked = facts.verify(response.get("content", ""), prompt)
        checked.update(attempt=attempt, input_tokens=count, timings=response.get("timings"),
                       tokens_predicted=response.get("tokens_predicted"))
        save(folder / "validation.json", checked)
        if checked["schema_valid"] and checked["selection_valid"] and (checked["facts_status"] == "verified" or attempt == 3):
            checked.update(status="success" if checked["facts_status"] == "verified" else "accepted_with_unverified_facts",
                           completed_attempts=attempt, hypothesis_status="not_semantically_verified")
            return checked
        feedback = checked["issues"]
    raise ValueError("Nessuna coppia valida dopo tre tentativi.")


def evaluate(row, folder, *, corpus, observations, position, url, transport, plan):
    started = time.perf_counter()
    folder.mkdir(parents=True, exist_ok=True)
    source = source_path(row)
    if sha(source) != row["source_sha256"]:
        raise ValueError("Sorgente modificata prima dell'esecuzione.")
    save(folder / "begin.json", {"at": now(), "circuit": row, "position": position,
                                "memory_before_sha256": memory_digest(observations)})
    result = {"circuit_id": row["circuit_id"], "source_sha256": row["source_sha256"],
              "method": "llm_rag_incrementale", "status": "failure", "score": None,
              "split": "external_test", "size_group": row.get("size_group"), "evaluation": "sequential_qasmbench50_campaign", "position": position}
    pending = None
    try:
        qasm = source.read_text(encoding="utf-8")
        (folder / "input.qasm").write_bytes(source.read_bytes())
        choice_started = time.perf_counter()
        prompt, retrieval = prepare(qasm, corpus=corpus, observations=observations, row=row, position=position)
        save(folder / "prompt.json", prompt)
        save(folder / "retrieval.json", retrieval)
        save(folder / "model_view.json", model_view(prompt))
        save(folder / "encoding.json", {
            **facts.audit(prompt), "revision": "incremental-observations-v1",
            "model_view_sha256": digest(model_view(prompt)),
            "messages_sha256": digest(messages(prompt)),
        })
        checked = decide(prompt, folder, app.Http(url, plan["llm_timeout_seconds"], transport))
        save(folder / "decision_validation.json", checked)
        decision = checked["canonical_response"]
        save(folder / "decision.json", decision)
        result.update(choice_seconds=time.perf_counter() - choice_started,
                      rag_seconds=retrieval["rag_seconds"],
                      retrieved_incremental=sum(r["origin"] == "incremental" for r in retrieval["records"]),
                      memory_size=len(observations), config_id=decision["config_id"],
                      accepted_with_unverified_facts=checked["facts_status"] != "verified")
        compiled = compile_job(folder / "compilazione",
                               {"method": "llm_rag_incrementale",
                                "source": str((folder / "input.qasm").resolve()), "decision": decision},
                               plan["compilation_timeout_seconds"])
        compiled.pop("choice_seconds", None)
        result.update(compiled)
    except BaseException as exc:
        result.update(status="interrupted" if isinstance(exc, (KeyboardInterrupt, SystemExit)) else "failure",
                      score=None, error=type(exc).__name__, message=str(exc))
        if isinstance(exc, (KeyboardInterrupt, SystemExit, app.LlmTransportError)):
            pending = exc
    result.update(total_seconds=time.perf_counter() - started, finished_at=now(), **llm_metrics(folder))
    save(folder / "esito.json", result)
    if pending:
        raise pending
    return result
