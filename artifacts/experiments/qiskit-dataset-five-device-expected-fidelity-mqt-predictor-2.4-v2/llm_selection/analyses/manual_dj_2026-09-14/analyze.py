"""Analisi locale della chat manuale: nessuna generazione o compilazione."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import json, hashlib, re
from prototype.quantum_assistant.schema_validation import validate_instance
from llm_selection.common import OUTPUT, ROOT
from llm_selection.run import prepare_context
from prototype.quantum_assistant.factory import build_default_service
from prototype.quantum_assistant.adapters.llm import UnconfiguredLlmGateway
from prototype.quantum_assistant.adapters import validation as validation_module
from scripts.mqt_predictor_protocol import FROZEN_DEVICES

DEST = Path(__file__).resolve().parent
ATTACHMENT = Path("/mnt/c/Users/User/.codex/attachments/f4b3083e-f14d-4381-82b2-ed68a7ab5137/pasted-text.txt")
SERVER = OUTPUT/"servers/qwen-chat-20260914-182526"
def read(path):
    return json.loads(path.read_text())
def write(name, value):
    with (DEST/name).open("x") as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write("\n")
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def copy_exact(source, name):
    with (DEST/name).open("xb") as f:
        f.write(source.read_bytes())

copy_exact(ATTACHMENT, "reasoning_utente.txt")
copy_exact(SERVER/"stderr.log", "server.stderr.snapshot.log")
copy_exact(SERVER/"launch.json", "server.launch.snapshot.json")
copy_exact(SERVER/"resources.jsonl", "server.resources.snapshot.jsonl")
saved_path = OUTPUT/"prompts/train/dj_indep_tket_2.json"
saved = read(saved_path)
response = read(DEST/"risposta_utente_normalizzata.json")
schema = saved["prompt"]["response_contract"]["json_schema"]
schema_errors = validate_instance(schema, response, error_code="LLM_OUTPUT_SCHEMA_INVALID")
reasoning = (DEST/"reasoning_utente.txt").read_text()
log = (DEST/"server.stderr.snapshot.log").read_text()
timings = {}
for key, text in [("prompt", "prompt eval time"), ("generation", "eval time"), ("total", "total time")]:
    match = re.search(r"task 93 \|\s+" + text + r" =\s*([\d.]+) ms /\s*(\d+) tokens", log)
    if match:
        timings[key] = {"seconds": float(match[1])/1000, "tokens": int(match[2])}
        timings[key]["tokens_per_second"] = int(match[2]) / (float(match[1])/1000)
write("preliminary.json", {
    "json_syntax_valid_after_markdown_normalization": True,
    "schema_valid": not schema_errors,
    "schema_errors": [e.to_dict() for e in schema_errors],
    "schema_validation_method": "Validatore del sottoinsieme JSON Schema del progetto.",
    "reasoning_characters": len(reasoning), "reasoning_words_whitespace": len(reasoning.split()),
    "reasoning_wait_occurrences_case_insensitive": len(re.findall(r"\bwait\b", reasoning, flags=re.I)),
    "server_task_id": 93, "timings": timings,
    "limits": ["I token di generazione includono l'uscita del server e non distinguono reasoning e JSON.",
               "L'allegato non è una cattura grezza del flusso API.",
               "I byte della risposta sono trascritti dal messaggio, con normalizzazione degli escape Markdown prima degli underscore."]
})
print("Schema valid:", not schema_errors, "timings:", timings, flush=True)
service = build_default_service(device_names=FROZEN_DEVICES, llm_gateway=UnconfiguredLlmGateway(), retrieval_limit=5)
context, registry, seconds = prepare_context(service, saved)
def validate(obj):
    return service.validator.validate(json.dumps(obj), context.request, context.mask_result,
                                      context.hardware_catalog, evidence_registry=registry)
result = validate(response)
write("validation.json", {"is_valid": result.is_valid, "issues": [i.to_dict() for i in result.issues]})
# Amplia solo il resoconto locale, senza modificare controlli o file del validatore.
original_bound = validation_module.MAX_FEEDBACK_ISSUES
try:
    validation_module.MAX_FEEDBACK_ISSUES = 1000
    diagnostic = validate(response)
finally:
    validation_module.MAX_FEEDBACK_ISSUES = original_bound
issues = [i.to_dict() for i in diagnostic.issues]
write("validation_all_issues.json", {
    "is_valid": diagnostic.is_valid, "issue_count": len(issues), "issues": issues,
    "diagnostic_only": "Limite di restituzione errori alzato nel processo locale da 12 a 1000; controlli invariati."
})
record = next(r for r in saved["prompt"]["allowed_evidence_registry"]["records"]
              if r["record_id"] == response["evidence_refs"][0]["record_id"])
write("cited_registry_record.json", record)
provenance = {
    "created_at": datetime.now(timezone.utc).isoformat(),
    "kind": "technical_manual_chat_offline_analysis", "split": "train",
    "circuit_id": "dj_indep_tket_2", "server_label": SERVER.name, "server_task_id": 93,
    "model_inference_launched_by_analysis": False, "scores_read_for_new_decision": False,
    "context_reconstruction_seconds": seconds,
    "original_prompt_sha256": saved["prompt_sha256"],
    "original_source_sha256": saved["source_sha256"],
    "response_origin": "Trascrizione del messaggio utente; escape Markdown prima degli underscore rimossi; nessuna correzione semantica.",
    "reasoning_origin": str(ATTACHMENT),
    "source_sha256": {str(p): sha(p) for p in [ATTACHMENT, saved_path, ROOT/"schemas/llm_recommendation.schema.json",
            ROOT/"prototype/quantum_assistant/adapters/validation.py", ROOT/"prototype/quantum_assistant/adapters/context.py"]},
    "comparison_limits": ["Parametri della chat non ricostruibili completamente dal solo log.",
                          "Ragionamento presente nella chat; prova automatica p1_t0 chiedeva enable_thinking=false.",
                          "Associazione chat/risposta dal prompt indicato dall'utente e dagli identificativi corrispondenti."]
}
write("provenance.json", provenance)
print("Semantic valid:", result.is_valid, "total diagnostics:", len(issues))
print("Error counts:", dict(Counter(i["code"] for i in issues)))
print("Source claims:", json.dumps(record["source_claims"], ensure_ascii=False))
print("Caveats:", json.dumps(record.get("caveats"), ensure_ascii=False))
print("Record keys:", list(record))
