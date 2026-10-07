"""Vincolo locale k=1; il prototipo conserva i limiti originali."""
from prototype.prompting import minimal
digest = minimal.digest


def check_one(prompt, max_examples):
    if type(max_examples) is not int or max_examples != 1:
        raise ValueError("Questo esperimento richiede k=1.")
    if len(prompt.get("retrieved_labeled_examples", [])) != 1:
        raise ValueError("Atteso esattamente un esempio RAG.")


def model_input(prompt, *, max_examples=1):
    check_one(prompt, max_examples)
    return minimal.model_input(prompt)


def citation_context(prompt, *, max_examples=1):
    check_one(prompt, max_examples)
    return minimal.citation_context(prompt)
