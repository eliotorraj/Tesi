"""Formato compatto condiviso dei prompt dell’assistente."""
from .compact import REVISION, audit, decode, encode, expand_response, model_input
from .rendering import messages

__all__ = ["REVISION", "audit", "decode", "encode", "expand_response", "model_input", "messages"]
