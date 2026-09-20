"""Messaggi essenziali condivisi da chat, prove e tentativi correttivi."""
import json
from .minimal import NOTE, model_input, response_schema

BASE_INSTRUCTION = NOTE
REPAIR_INSTRUCTION = "Rispondi nuovamente con l’intero JSON richiesto per il circuito corrente."
CHECKLIST = (
    "Check that the device is compatible, config_id is allowed for it, and every cited "
    "example ID was supplied. Do not report a measured score for the new circuit."
)


def messages(prompt, variant, *, compact=True, serialization="toon"):
    if not compact:
        raise ValueError("Full canonical prompts are archival data, not model input")
    represented = model_input(prompt)
    schema = {k: v for k, v in response_schema(prompt).items()
              if k not in ("$schema", "$id", "title")}
    if serialization == "json":
        represented["response_schema"] = schema
        text = BASE_INSTRUCTION + "\n" + json.dumps(represented, ensure_ascii=False, separators=(",", ":"))
    elif serialization == "toon":
        from .toon import encode_view, NOTE as TOON_NOTE
        fence = chr(96) * 3
        text = (BASE_INSTRUCTION + "\n" + TOON_NOTE + "\n" + fence + "toon\n"
                + encode_view(represented) + "\n" + fence + "\nresponse_schema: "
                + json.dumps(schema, ensure_ascii=False, separators=(",", ":")))
    else:
        raise ValueError("Unknown prompt serialization")
    if variant == "checklist":
        text += "\n" + CHECKLIST
    elif variant != "base":
        raise ValueError("Unknown prompt variant")
    if represented.get("previous_validation_errors"):
        text += "\n" + REPAIR_INSTRUCTION
    return [{"role": "user", "content": text}]
