"""Messaggi comuni dell’assistente, indipendenti da modello e trasporto."""
import json

BASE_INSTRUCTION = (
    "Read the complete request below. Recommend one compatible device and one allowed "
    "Qiskit configuration. Return only the JSON object required by response_contract. "
    "Use the historical examples as evidence, never as a measurement of the new circuit."
)
CHECKLIST = (
    "Before answering, check internally: copy the live request_id and catalog_snapshot_id; "
    "select hardware from the compatible list; match all plan fields to one allowed configuration; "
    "include live_compatibility; support both device and exact configuration with historical claims. "
    "Each historical reference needs the exact record_id, evidence source_id and source_claim_id "
    "from allowed_evidence_registry. The parameters of each cited historical claim must match "
    "the corresponding source claim. Do not output this checklist or extra prose."
)

def messages(prompt, variant, *, compact=True):
    from .complete_graph import encode as graph_encode, NOTE as graph_note
    from .compact import encode, model_input, NOTE
    from .output_contract import RULES
    represented = model_input(encode(prompt)) if compact else graph_encode(prompt)
    note = (NOTE + "\n\n" if compact else "") + graph_note
    text = BASE_INSTRUCTION + "\n\n" + RULES + "\n\n" + note + "\n\n" + json.dumps(represented,ensure_ascii=False,separators=(",",":"))
    if variant == "checklist":
        checklist=CHECKLIST if prompt.get("retrieved_labeled_examples") else (
            "Before answering, check internally: copy the live request_id and catalog_snapshot_id; "
            "select hardware from the compatible list; match all plan fields to one allowed configuration; "
            "include live_compatibility and use only the evidence actually provided. "
            "No historical examples were retrieved; do not invent historical references or claims. "
            "Do not output this checklist or extra prose.")
        text += "\n\n" + checklist
    elif variant != "base": raise ValueError("Unknown prompt variant")
    return [{"role":"user","content":text}]

