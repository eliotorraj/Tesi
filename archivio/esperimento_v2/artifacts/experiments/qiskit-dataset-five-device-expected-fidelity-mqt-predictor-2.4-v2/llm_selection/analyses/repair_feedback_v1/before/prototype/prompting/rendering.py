"""Messaggi essenziali condivisi da chat, prove e tentativi correttivi."""
import json
from .minimal import NOTE, model_input, response_schema

BASE_INSTRUCTION = NOTE
CHECKLIST = (
    "Check that the device is compatible, config_id is allowed for it, and every cited "
    "example ID was supplied. Do not report a measured score for the new circuit."
)


def messages(prompt, variant, *, compact=True):
    if not compact:
        raise ValueError("Full canonical prompts are archival data, not model input")
    represented = model_input(prompt)
    schema = response_schema(prompt)
    # The same schema also constrains generation. Keep its readable definition once in text.
    represented["response_schema"] = {k: v for k, v in schema.items()
                                      if k not in ("$schema", "$id", "title")}
    text = BASE_INSTRUCTION + "\n" + json.dumps(represented, ensure_ascii=False, separators=(",", ":"))
    if variant == "checklist":
        text += "\n" + CHECKLIST
    elif variant != "base":
        raise ValueError("Unknown prompt variant")
    return [{"role": "user", "content": text}]
