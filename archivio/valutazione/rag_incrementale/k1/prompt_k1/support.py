'Local k=1 constraint; the prototype retains its original limits.'
from prototype.prompting import minimal
digest = minimal.digest


def check_one(prompt, max_examples):
    if type(max_examples) is not int or max_examples != 1:
        raise ValueError('This experiment requires k=1.')
    if len(prompt.get("retrieved_labeled_examples", [])) != 1:
        raise ValueError('Expected exactly one RAG example.')


def model_input(prompt, *, max_examples=1):
    check_one(prompt, max_examples)
    return minimal.model_input(prompt)


def citation_context(prompt, *, max_examples=1):
    check_one(prompt, max_examples)
    return minimal.citation_context(prompt)
