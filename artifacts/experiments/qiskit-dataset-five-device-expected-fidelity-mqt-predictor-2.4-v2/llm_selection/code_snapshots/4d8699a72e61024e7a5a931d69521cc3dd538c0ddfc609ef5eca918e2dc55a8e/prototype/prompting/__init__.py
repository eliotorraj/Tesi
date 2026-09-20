"""Vista essenziale e contratto corrente condivisi dall'assistente."""
from .minimal import REVISION, audit, model_input, citation_context, response_schema
from .rendering import messages

__all__ = ["REVISION", "audit", "model_input", "citation_context", "response_schema", "messages"]
