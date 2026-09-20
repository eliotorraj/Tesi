"""Confronto riproducibile train, senza inferenza: prepara file per llama-tokenize."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
from .common import ROOT, OUTPUT, read_json, write_json, now
from .configuration import payload
from prototype.prompting.minimal import model_input, audit, REVISION
from prototype.prompting.legacy_rendering import messages as legacy_messages


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def windows(path):
    return "//wsl.localhost/Ubuntu" + str(Path(path).resolve())


def prepare(reference, destination, extra_train=2):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    write_json(destination/"started.json", {"at": now(), "phase": "technical_train_prompt_audit",
               "inference_calls": 0, "revision": REVISION, "test_accessed": False})
    reference = Path(reference).resolve()
    canonical = read_json(reference/"prompt.json")
    before = read_json(reference/"call/request.json")
    template_request = read_json(reference/"audit/template/request.json")
    source_message = template_request["messages"]
    if len(source_message) != 1 or source_message[0]["role"] != "user":
        raise ValueError("Expected one user message for native template replay")
    if before["prompt"].count(source_message[0]["content"]) != 1:
        raise ValueError("Cannot isolate the exact archived native template")
    prefix, suffix = before["prompt"].split(source_message[0]["content"])
    profile = read_json(reference.parent/"begin.json")
    if profile.get("split", profile.get("circuit_metadata", {}).get("split")) != "train":
        raise ValueError("Reference must be a technical train episode")
    write_json(destination/"template_replay.json", {
        "source": str(reference.relative_to(ROOT)), "prefix": prefix, "suffix": suffix,
        "template_request_sha256": sha(reference/"audit/template/request.json"),
        "template_response_sha256": sha(reference/"audit/template/response.json"),
        "method": "Reuse the exact wrapper of one user message, same model, no tools, thinking disabled.",
    })
    sources = [(profile["circuit_id"], canonical, before["prompt"], str(reference.relative_to(ROOT)))]
    for path in sorted((OUTPUT/"prompts/train").glob("*.json")):
        if len(sources) >= extra_train + 1:
            break
        saved = read_json(path)
        if saved["circuit_metadata"]["split"] != "train":
            raise ValueError("Non-train input")
        if saved["circuit_id"] == profile["circuit_id"]:
            continue
        old_text = legacy_messages(saved["prompt"], "checklist")[0]["content"]
        sources.append((saved["circuit_id"], saved["prompt"], prefix + old_text + suffix,
                        str(path.relative_to(ROOT))))
    jobs, rows = [], []
    for index, (circuit_id, prompt, previous, source) in enumerate(sources):
        case = destination/circuit_id
        case.mkdir()
        old = copy.deepcopy(prompt)
        view = model_input(prompt)
        request = payload(prompt, {"temperature": 0.0, "prompt_variant": "checklist"})
        current = prefix + request["messages"][0]["content"] + suffix
        assert prompt == old
        assert view["circuit"]["features"] == prompt["live_request"]["circuit"]["features"]
        assert len(view["retrieved_labeled_examples"]) == len(prompt["retrieved_labeled_examples"]) == 5
        for shown, original in zip(view["retrieved_labeled_examples"], prompt["retrieved_labeled_examples"]):
            assert shown["circuit"]["features"] == original["example"]["input"]["circuit"]["features"]
        write_json(case/"canonical_input.json", prompt)
        write_json(case/"model_input.json", view)
        write_json(case/"encoding.json", audit(prompt))
        write_json(case/"chat_request.json", request)
        write_json(case/"response_schema.json", request["response_format"]["schema"])
        native = {k:v for k,v in before.items() if k not in ("prompt", "json_schema")}
        native.update(prompt=current, json_schema=request["response_format"]["schema"])
        write_json(case/"prepared_native_request.json", native)
        for name, text in (("before", previous), ("after", current)):
            (case/(name+".txt")).write_text(text, encoding="utf-8")
            jobs.append({"input": windows(case/(name+".txt")),
                         "output": windows(case/(name+"_tokens.json")),
                         "stderr": windows(case/(name+"_tokenizer.log"))})
        # Sections include the schema-in-text; their counts are not additive.
        sections = {**view, "response_schema": request["response_format"]["schema"]}
        for name, value in sections.items():
            file = case/("section_"+name+".txt")
            file.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
            jobs.append({"input": windows(file), "output": windows(file.with_suffix(".tokens.json")),
                         "stderr": windows(file.with_suffix(".log"))})
        rows.append({"circuit_id": circuit_id, "source": source, "split": "train",
                     "examples": 5, "features_preserved": True, "canonical_unchanged": True,
                     "before_kind": "archived_native_request" if index == 0 else "legacy_v2_reconstructed",
                     "after_kind": "prepared_native_request_not_sent"})
    write_json(destination/"tokenize_manifest.json", {
        "executable": windows(OUTPUT/"runtime/b10930/llama-tokenize.exe"),
        "model": profile["launch"]["model_path"], "jobs": jobs})
    write_json(destination/"metadata.json", {
        "at": now(), "revision": REVISION, "rows": rows, "reference": str(reference),
        "model_path": profile["launch"]["model_path"],
        "tokenizer_binary_sha256": sha(OUTPUT/"runtime/b10930/llama-tokenize.exe"),
        "tokenizer_options": ["--offline", "--no-bos", "--no-escape", "--ids"],
        "schema_handling": "Readable schema is included once in the message. Native json_schema separately constrains generation and adds no prompt tokens.",
        "limitations": ["No inference or answer-quality measurement.",
                       "Historical train examples may include the current source; not evidence of generalization.",
                       "Native wrapper replay must be checked by exact archived token-ID equality before reporting counts."]})
    return destination


def finish(directory):
    directory = Path(directory)
    metadata = read_json(directory/"metadata.json")
    plan = read_json(directory/"tokenize_manifest.json")
    for job in plan["jobs"]:
        output = Path(job["output"].removeprefix("//wsl.localhost/Ubuntu"))
        if not output.is_file():
            raise ValueError("Incomplete tokenizer run: " + str(output))
    def tokens(path):
        return json.loads(path.read_text(encoding="utf-8-sig"))
    first = directory/metadata["rows"][0]["circuit_id"]
    archived_tokens = read_json(Path(metadata["reference"])/"audit/tokenizer/response.json")["tokens"]
    reproduced_tokens = tokens(first/"before_tokens.json")
    if reproduced_tokens != archived_tokens:
        raise ValueError("Native tokenizer IDs differ from the archived server; do not report a matched measurement")
    for row in metadata["rows"]:
        case = directory/row["circuit_id"]
        before = len(tokens(case/"before_tokens.json"))
        after = len(tokens(case/"after_tokens.json"))
        row.update(before_tokens=before, after_tokens=after,
                   saved_tokens=before-after, reduction_percent=100*(1-after/before),
                   section_tokens_nonadditive={
                       p.name.removeprefix("section_").removesuffix(".tokens.json"): len(tokens(p))
                       for p in sorted(case.glob("section_*.tokens.json"))})
    metadata.update(completed_at=now(), archived_token_ids_exact_match=True,
                    measurement="Actual llama.cpp b10930 tokenizer with original Qwen GGUF; native template replay verified against archived token IDs.")
    write_json(directory/"report.json", metadata)
    write_json(directory/"manifest.json", {
        str(p.relative_to(directory)): sha(p) for p in directory.rglob("*")
        if p.is_file() and p.name != "manifest.json"})
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--reference-attempt", type=Path)
    parser.add_argument("--finish", action="store_true")
    args = parser.parse_args()
    if args.finish:
        report = finish(args.output)
        for row in report["rows"]:
            print(row["circuit_id"], row["before_tokens"], "->", row["after_tokens"],
                  f"({row['reduction_percent']:.2f}%)")
    else:
        if args.reference_attempt is None:
            parser.error("--reference-attempt required")
        print(prepare(args.reference_attempt, args.output))


if __name__ == "__main__":
    main()
