"""Verifica/esporta prompt senza inferenza. Non apre gli score di validation."""
from __future__ import annotations
import argparse
import hashlib
from .tokenization import count_texts
from .common import OUTPUT, now, read_json, write_json
from prototype.prompting.compact import encode, decode, model_input, audit, REVISION
from .configuration import messages
from .train_check import check

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("--verify-retrieval", action="store_true")
    parser.add_argument("--all-splits", action="store_true", help="Include i prompt validation già preparati; mai il test")
    args = parser.parse_args()
    import re
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", args.label):
        raise ValueError("Invalid audit label")
    directory = OUTPUT/"prompt_audits"/args.label
    directory.mkdir(parents=True, exist_ok=False)
    write_json(directory/"started.json", {"at": now(), "revision": REVISION, "llm_calls": 0, "arguments": vars(args)})
    tokenizer_path = OUTPUT/"models/qwen/official_tokenizer.json"
    tokenizer_python = OUTPUT/"runtime/python/bin/python"
    service = None
    if args.verify_retrieval:
        from prototype.quantum_assistant.factory import build_default_service
        from prototype.quantum_assistant.adapters.llm import UnconfiguredLlmGateway
        from scripts.mqt_predictor_protocol import FROZEN_DEVICES
        service = build_default_service(device_names=FROZEN_DEVICES, llm_gateway=UnconfiguredLlmGateway(), retrieval_limit=5)
    rows = []
    splits = ("train", "validation") if args.all_splits else ("train",)
    for split in splits:
        for path in sorted((OUTPUT/"prompts"/split).glob("*.json")):
            saved = read_json(path)
            prompt = saved["prompt"]
            if saved["circuit_metadata"]["split"] != split:
                raise ValueError("Split mismatch")
            retrieval_verified = False
            if service is not None and split == "train":
                from .run import prepare_context
                prepare_context(service, saved)
                retrieval_verified = True
            encoded = encode(prompt)
            restored = decode(encoded)
            assert restored == prompt
            assert restored["live_request"]["circuit"]["qasm2"].encode() == prompt["live_request"]["circuit"]["qasm2"].encode()
            self_check = check(saved)
            if split == "train" and not self_check["self_retrieved_at_zero"]:
                raise ValueError("No exact source example at distance zero: "+path.stem)
            clarified = messages(prompt, "checklist", compact=False)[0]["content"]
            compact = messages(prompt, "checklist")[0]["content"]
            clarified_tokens, compact_tokens = count_texts([clarified, compact], tokenizer_path, tokenizer_python)
            row = {"split": split, "circuit_id": path.stem, "source_sha256": saved["source_sha256"],
                   "original_prompt_sha256": saved["prompt_sha256"], "roundtrip_verified": True,
                   "rag_examples": len(prompt["retrieved_labeled_examples"]),
                   "clarified_tokens": clarified_tokens, "compact_tokens": compact_tokens,
                   "clarified_characters": len(clarified), "compact_characters": len(compact),
                   "retrieval_reexecuted_and_verified": retrieval_verified, "train_self_check": self_check}
            row["token_reduction_percent"] = 100*(1-row["compact_tokens"]/row["clarified_tokens"])
            rows.append(row)
            if split == "train":
                target = directory/split/path.stem
                write_json(target/"encoding.json", audit(prompt, encoded))
                write_json(target/"model_input.json", model_input(encoded))
                (target/"prompt_chat.txt").write_text(compact, encoding="utf-8")
                write_json(target/"check.json", row)
            write_json(directory/"progress.json", {"at": now(), "rows": rows})
            print(split, path.stem, row["clarified_tokens"], "->", row["compact_tokens"], flush=True)
    report = {"at": now(), "revision": REVISION, "llm_calls": 0, "test_accessed": False,
              "token_method": "Official Qwen tokenizer on message text; native chat template and special tokens excluded.",
              "tokenizer_sha256": hashlib.sha256((OUTPUT/"models/qwen/official_tokenizer.json").read_bytes()).hexdigest(),
              "rows": rows}
    write_json(directory/"report.json", report)
    files = [p for p in directory.rglob("*") if p.is_file()]
    write_json(directory/"manifest.json", {str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
    print(directory, flush=True)

if __name__ == "__main__":
    main()
