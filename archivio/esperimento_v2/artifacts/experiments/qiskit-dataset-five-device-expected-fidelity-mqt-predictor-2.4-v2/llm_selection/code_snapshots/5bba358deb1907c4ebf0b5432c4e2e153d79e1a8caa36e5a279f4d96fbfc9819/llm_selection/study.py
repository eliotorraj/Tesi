"""Congelamento locale e sigilli: nessuna lettura degli score in questo modulo."""
from __future__ import annotations
import argparse
from pathlib import Path
from qiskit_dataset.experiment_v2 import source_manifest
from scripts.mqt_predictor_protocol import SOURCE_MANIFEST_V2, TEST_RELEASE_RECORD, file_sha256
from .common import OUTPUT, ROOT, digest, now, read_json, write_json
from .configuration import CONFIGURATIONS, FIXED, MAX_ATTEMPTS, TIMEOUT_SECONDS
from .provenance import code_hashes, capture

FROZEN = OUTPUT/"frozen_study.json"
MODEL_KEYS = ("qwen","phi","gemma")
NATIVE_CONTEXT = {"qwen":262144,"phi":131072,"gemma":131072}
SELECTION_RULE = {
    "statistical_unit":"circuit",
    "primary_quality_metric":"absolute regret: oracle median score minus chosen median score",
    "order":["maximum valid_and_compilable_count_on_all_88",
             "minimum median_absolute_regret_on_common_successful_oracle_cases_of_tied_candidates",
             "maximum first_call_valid_json_count_on_all_88",
             "minimum total_llm_calls_on_all_88",
             "minimum total_measured_call_seconds_when_complete_for_all_tied_candidates",
             "minimum total_output_tokens_when_complete_for_all_tied_candidates",
             "lexicographic model_key/configuration_id"],
    "missing_regret":"null; never replace a failure with an invented penalty",
    "common_set":"intersection only after equal completion count; publish identities and denominator",
    "empty_common_set":"skip regret criterion and declare inability to compare quality",
    "score":"median of seeds 0,1,2 only if all three succeed",
    "oracle":"available only when every compatible matrix run succeeds",
    "ties":"exact values, no data-dependent tolerance or significance threshold",
    "uncertainty":"paired circuit bootstrap, 2000 draws, seed 20260913; descriptive, not a significance claim",
    "multiple_comparisons":"validation selects; no unbiased final quality claim until sealed test"
}

def immutable_json(path, value):
    path=Path(path)
    if path.exists():
        if read_json(path)!=value: raise ValueError(f"Refusing to replace frozen artifact: {path}")
    else: write_json(path,value)

def input_hashes():
    paths=[SOURCE_MANIFEST_V2, ROOT/"uv.lock", ROOT/"configs/qiskit_dataset_configurations_v2.json"]
    paths.extend(sorted((OUTPUT/"prompts"/"validation").glob("*.json")))
    paths.extend([OUTPUT/"runtime/b10930/llama-server.exe",OUTPUT/"runtime/pstools/pssuspend64.exe",OUTPUT/"runtime/pstools/verified.json"])
    for model in MODEL_KEYS:
        paths.extend((OUTPUT/"models"/model/name) for name in ("official_tokenizer.json","official_tokenizer_config.json","official_config.json"))
    from prototype.quantum_assistant.adapters.rag_dataset import DEFAULT_RAG_ROOT
    paths.extend(p for p in (DEFAULT_RAG_ROOT/"index").rglob("*") if p.is_file() and p.name!=".lock")
    return {str(p.relative_to(ROOT)):file_sha256(p) for p in sorted(paths)}

def verify_hashes(base, hashes):
    for relative, expected in hashes.items():
        path=Path(base)/relative
        if not path.is_file() or file_sha256(path)!=expected:
            raise ValueError(f"Frozen file missing or modified: {path}")

def freeze(study_id, profiles):
    if TEST_RELEASE_RECORD.exists(): raise ValueError("Test already released")
    if FROZEN.exists(): raise ValueError("A study is already frozen; cannot restart selection")
    if not study_id or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in study_id):
        raise ValueError("Invalid study identifier")
    if list(sorted(profiles))!=sorted(MODEL_KEYS): raise ValueError("Exactly three model families required")
    if list((OUTPUT/"studies").glob("*/*/*/*/decision.json")):
        raise ValueError("Validation decisions exist before freezing")
    expected={r["circuit_id"] for r in source_manifest()["circuits"] if r["split"]=="validation"}
    observed={p.stem for p in (OUTPUT/"prompts"/"validation").glob("*.json")}
    if expected!=observed or len(expected)!=88: raise ValueError("Expected 88 validation prompts")
    for model, profile in profiles.items():
        if not 0<int(profile["context"])<=NATIVE_CONTEXT[model]: raise ValueError("Context exceeds native limit")
        artifact=read_json(OUTPUT/"models"/model/(profile["weight_precision"]+"_manifest.json"))
        if file_sha256(Path(artifact["local_path"]))!=artifact["gguf_sha256"]: raise ValueError("Model hash mismatch")
        profile["artifact"]=artifact
        if not profile.get("precision_reason"): raise ValueError("Document the precision choice")
        technical=profile.get("technical_evidence",[])
        if not technical: raise ValueError("Technical feasibility evidence required")
        evidence={}
        successes=0
        for relative in technical:
            path=ROOT/relative
            value=read_json(path)
            if value.get("split")!="train": raise ValueError("Technical evidence must be train only")
            if model not in path.parts: raise ValueError("Technical evidence model mismatch")
            successes+=value.get("status")=="success"
            evidence[relative]=file_sha256(path)
        if not successes: raise ValueError(f"No complete valid technical response for {model}")
        profile["technical_evidence_hashes"]=evidence
    directory=OUTPUT/"studies"/study_id
    directory.mkdir(parents=True,exist_ok=True)
    provenance=capture(directory)
    study={"schema_version":"1.0.0","study_id":study_id,"frozen_at":now(),"phase":"local_llm_validation_selection",
           "test_content_accessed":False,"validation_count":88,"models":profiles,
           "configurations":CONFIGURATIONS,"fixed":FIXED,"timeout_seconds":TIMEOUT_SECONDS,
           "max_attempts":MAX_ATTEMPTS,"selection_rule":SELECTION_RULE,
           "code_hashes":code_hashes(),"input_hashes":input_hashes(),
           "provenance_sha256":file_sha256(directory/"provenance.json")}
    immutable_json(FROZEN,study)
    return study

def verify_frozen_study(*, check_code=True):
    study=read_json(FROZEN)
    if study["configurations"]!=CONFIGURATIONS or study["fixed"]!=FIXED or study["selection_rule"]!=SELECTION_RULE:
        raise ValueError("Frozen experimental rules changed")
    if study["timeout_seconds"]!=TIMEOUT_SECONDS or study["max_attempts"]!=MAX_ATTEMPTS:
        raise ValueError("Frozen budgets changed")
    if check_code and study["code_hashes"]!=code_hashes(): raise ValueError("Experiment code changed after freezing")
    verify_hashes(ROOT,study["input_hashes"])
    for profile in study["models"].values(): verify_hashes(ROOT,profile["technical_evidence_hashes"])
    return study

def verify_launch(study, model, launch):
    profile=study["models"][model]
    for key in ("context","cache_type","gpu_layers","batch","micro_batch"):
        if launch.get(key)!=profile[key]: raise ValueError(f"Server differs from frozen profile: {key}")
    if Path(launch["model_path"].replace("\\","/")).name!=profile["weight_precision"]+".gguf":
        raise ValueError("Different weight precision loaded")
    for flag,value in (("--load-mode","none"),("--fit","off"),("--parallel","1")):
        args=[str(a) for a in launch["arguments"]]
        if flag not in args or args[args.index(flag)+1]!=value: raise ValueError(f"Server flag differs: {flag}")
    if "--no-context-shift" not in launch["arguments"]: raise ValueError("Context shift must be disabled")
    if launch.get("guards")!=profile["guards"]: raise ValueError("Resource limits changed")

def model_root(study, model):
    return OUTPUT/"studies"/study["study_id"]/model

def seal_model(root, study):
    root=Path(root)
    expected={p.stem for p in (OUTPUT/"prompts"/"validation").glob("*.json")}
    paths=sorted(root.glob("*/*/decision.json"))
    expected_pairs={(c["id"],cid) for c in study["configurations"] for cid in expected}
    if {(p.parent.parent.name,p.parent.name) for p in paths}!=expected_pairs: raise ValueError("Incomplete decision grid")
    for p in paths:
        row=read_json(p)
        if row["split"]!="validation" or row["status"] not in ("success","failure","timeout"):
            raise ValueError("Nonterminal or wrong-split decision")
        summaries=[read_json(s) for s in sorted(p.parent.glob("attempt_*/summary.json"))]
        if len(summaries)!=row["attempt_count"] or digest(summaries)!=row["attempts_sha256"]:
            raise ValueError("Attempt provenance mismatch")
    hashes={str(p.relative_to(root)):file_sha256(p) for p in sorted(root.rglob("*"))
            if p.is_file() and p.name!="sealed.json" and not p.name.endswith(".tmp")}
    value={"study_sha256":digest(study),"files":hashes,"decision_count":len(paths)}
    immutable_json(root/"sealed.json",value)
    return value

def verify_model_seal(root, study):
    seal=read_json(Path(root)/"sealed.json")
    if seal["study_sha256"]!=digest(study): raise ValueError("Wrong study seal")
    verify_hashes(root,seal["files"])
    actual={str(p.relative_to(root)) for p in Path(root).rglob("*")
            if p.is_file() and p.name!="sealed.json" and not p.name.endswith(".tmp")}
    if actual!=set(seal["files"]): raise ValueError("Files added after sealing")
    return seal

def seal_all():
    study=verify_frozen_study()
    seals={}
    for model in MODEL_KEYS:
        root=model_root(study,model)
        verify_model_seal(root,study)
        seals[model]=file_sha256(root/"sealed.json")
    value={"study_sha256":digest(study),"model_seals":seals,"decisions_expected":88*len(CONFIGURATIONS)*3}
    immutable_json(OUTPUT/"studies"/study["study_id"]/"all_decisions_sealed.json",value)
    return value

def require_all_sealed():
    study=verify_frozen_study()
    root=OUTPUT/"studies"/study["study_id"]
    seal=read_json(root/"all_decisions_sealed.json")
    if seal["study_sha256"]!=digest(study): raise ValueError("Wrong global seal")
    for model in MODEL_KEYS:
        model_dir=model_root(study,model)
        if file_sha256(model_dir/"sealed.json")!=seal["model_seals"][model]: raise ValueError("Model seal changed")
        verify_model_seal(model_dir,study)
    return study,seal

def main():
    parser=argparse.ArgumentParser()
    sub=parser.add_subparsers(dest="command",required=True)
    p=sub.add_parser("freeze"); p.add_argument("--id",required=True); p.add_argument("--profiles",type=Path,required=True)
    sub.add_parser("verify"); sub.add_parser("seal")
    args=parser.parse_args()
    result=freeze(args.id,read_json(args.profiles)) if args.command=="freeze" else seal_all() if args.command=="seal" else verify_frozen_study()
    print(args.command,digest(result),flush=True)
if __name__=="__main__": main()
