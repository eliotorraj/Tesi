'Compare three representations on five train circuits without calling models.'
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
from .common import ROOT, OUTPUT, read_json, write_json, now
from .configuration import payload
from prototype.prompting.rendering import messages
from prototype.prompting.legacy_rendering import messages as legacy_messages
from prototype.prompting.minimal import model_input, audit, REVISION
from prototype.prompting.toon import decode_view, encode_view, metadata

LABELS = {"qwen": "qwen-prompt-v3-01", "phi": "phi-prompt-v3-02", "gemma": "gemma-prompt-v3-01"}
STAGES = ("original_v2", "minimal_json", "minimal_toon", "original_full_json")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def win(path):
    return "//wsl.localhost/Ubuntu" + str(Path(path).resolve())


def prepare(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    write_json(output/"started.json", {"at": now(), "inference_calls": 0, "split": "train", "revision": REVISION})
    sources = sorted((OUTPUT/"prompts/train").glob("*.json"))
    if len(sources) != 5:
        raise ValueError("Expected exactly the five prepared train circuits")
    rows = []
    for model, label in LABELS.items():
        jobs = []
        for source in sources:
            saved = read_json(source)
            if saved["circuit_metadata"]["split"] != "train":
                raise ValueError("Non-train source")
            circuit = saved["circuit_id"]
            attempt = OUTPUT/"technical_episodes"/label/model/"p1_t0"/circuit/"attempt_1"
            old = read_json(attempt/"call/request.json")
            template = read_json(attempt/"audit/template/request.json")
            prompt = read_json(attempt/"prompt.json")
            # The old canonical contract is irrelevant to this projection.
            current = model_input(prompt)
            assert current == model_input(saved["prompt"])
            assert len(current["retrieved_labeled_examples"]) == 5
            assert decode_view(encode_view(current)) == current
            old_message = template["messages"][0]["content"]
            assert len(template["messages"]) == 1 and template["messages"][0]["role"] == "user"
            assert old["prompt"].count(old_message) == 1
            prefix, suffix = old["prompt"].split(old_message)
            json_message = messages(prompt, "checklist", serialization="json")[0]["content"]
            assert json_message == old_message, "JSON baseline no longer matches the real archived request"
            native_toon = payload(prompt, {"temperature": 0, "prompt_variant": "checklist"})
            texts = {
                "original_v2": prefix + legacy_messages(saved["prompt"], "checklist")[0]["content"] + suffix,
                "minimal_json": old["prompt"],
                "minimal_toon": prefix + native_toon["messages"][0]["content"] + suffix,
                "original_full_json": prefix + legacy_messages(saved["prompt"], "checklist", compact=False)[0]["content"] + suffix,
            }
            case = output/model/circuit
            case.mkdir(parents=True)
            write_json(case/"canonical_input.json", prompt)
            write_json(case/"model_input.json", current)
            write_json(case/"encoding.json", audit(prompt))
            write_json(case/"response_schema.json", native_toon["response_format"]["schema"])
            native = {**old, "prompt": texts["minimal_toon"], "json_schema": native_toon["response_format"]["schema"]}
            write_json(case/"prepared_request_not_sent.json", native)
            (case/"data.toon").write_text(encode_view(current), encoding="utf-8")
            for stage, text in texts.items():
                path = case/(stage+".txt")
                path.write_text(text, encoding="utf-8")
                jobs.append({"input": win(path), "output": win(case/(stage+".tokens.json")),
                             "stderr": win(case/(stage+".tokenizer.log"))})
            historical_v2 = OUTPUT/"technical_episodes/qwen-prompt-v2-02/qwen/p1_t0/dj_indep_tket_2/attempt_1/call/request.json"
            exact_v2 = model == "qwen" and circuit == "dj_indep_tket_2" and texts["original_v2"] == read_json(historical_v2)["prompt"]
            rows.append({"model": model, "circuit": circuit, "split": "train", "examples": 5,
                         "archived_attempt": str(attempt.relative_to(ROOT)), "json_baseline_exact": True,
                         "original_v2_kind": "exact_archived_request" if exact_v2 else "reconstructed_legacy_v2",
                         "original_full_kind": "reconstructed_unaliased_legacy_with_exact_complete_graph_rule",
                         "toon_roundtrip_verified": True, "new_inference_calls": 0})
        begin = read_json(attempt.parent/"begin.json")
        write_json(output/(model+"_tokenize.json"),
                   {"executable": win(OUTPUT/"runtime/b10930/llama-tokenize.exe"),
                    "model": begin["launch"]["model_path"], "jobs": jobs})
    write_json(output/"metadata.json", {"at": now(), "revision": REVISION, "toon": metadata(), "rows": rows,
        "tokenizer_executable_sha256": sha(OUTPUT/"runtime/b10930/llama-tokenize.exe"),
        "method": "Native llama.cpp b10930 tokenizer, original Q8_0 GGUF per model, complete native template replay, --no-bos --no-escape --ids",
        "schema": "Readable JSON schema counted once in text; external json_schema constrains generation and is not prompt text.",
        "limits": "No inference, quality, latency, output-token or total-consumption measurement. Counts are prepared input tokens.",
        "stages": list(STAGES)})
    return output


def finish(output):
    output = Path(output)
    report = read_json(output/"metadata.json")
    for row in report["rows"]:
        case = output/row["model"]/row["circuit"]
        counts = {}
        for stage in STAGES:
            path = case/(stage+".tokens.json")
            if not path.exists():
                raise ValueError("Missing token count: " + str(path))
            ids = json.loads(path.read_text(encoding="utf-8-sig"))
            counts[stage] = len(ids)
            if stage == "minimal_json":
                recorded = read_json(ROOT/row["archived_attempt"]/"audit/tokenizer/response.json")["tokens"]
                if recorded != ids:
                    raise ValueError("Native token IDs differ from archived baseline: " + str(case))
        row.update(tokens=counts, archived_token_ids_exact=True,
                   saved_json_to_toon=counts["minimal_json"]-counts["minimal_toon"],
                   reduction_json_to_toon_percent=100*(1-counts["minimal_toon"]/counts["minimal_json"]),
                   reduction_original_to_toon_percent=100*(1-counts["minimal_toon"]/counts["original_v2"]))
    report["totals"] = {}
    for model in LABELS:
        selected = [r for r in report["rows"] if r["model"] == model]
        total = {s: sum(r["tokens"][s] for r in selected) for s in STAGES}
        total["reduction_json_to_toon_percent"] = 100*(1-total["minimal_toon"]/total["minimal_json"])
        total["reduction_original_to_toon_percent"] = 100*(1-total["minimal_toon"]/total["original_v2"])
        report["totals"][model] = total
    write_json(output/"report.json", report)
    lines = ['# Prompt tokens on five train circuits', "",
        'Native measurements per model, including the full template and schema. No inference.',
        'Reduced JSON: actual archived requests, verified against every token ID.',
        'Original: reconstructed earlier v2 format; original_v2_kind identifies exact matches where available.',
        'TOON: prepared request, not yet sent. Future response and repair consumption is not measured.', "",
        '| Model | Circuit | Earlier v2 | Reduced JSON | Reduced + TOON | Savings over JSON |',
        "|---|---|---:|---:|---:|---:|"]
    for row in report["rows"]:
        t = row["tokens"]
        lines.append(f'| {row["model"]} | {row["circuit"]} | {t["original_v2"]} | {t["minimal_json"]} | {t["minimal_toon"]} | {row["reduction_json_to_toon_percent"]:.2f}% |')
    lines += ["", 'Full JSON without aliases, using the earlier exact complete-graph rule, is counted separately in original_full_json.',
              'Aggregate counts and percentages are in report.json. Five train circuits do not measure generalization.']
    (output/"README.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    write_json(output/"manifest.json", {str(p.relative_to(output)): sha(p) for p in output.rglob("*")
                                      if p.is_file() and p.name != "manifest.json"})
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--finish", action="store_true")
    args = parser.parse_args()
    if args.finish:
        print(json.dumps(finish(args.output)["totals"], indent=2))
    else:
        print(prepare(args.output))

if __name__ == "__main__":
    main()
