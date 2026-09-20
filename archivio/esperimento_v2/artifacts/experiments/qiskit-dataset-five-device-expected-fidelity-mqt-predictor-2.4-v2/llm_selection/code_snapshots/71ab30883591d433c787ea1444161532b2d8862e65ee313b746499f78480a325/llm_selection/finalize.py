"""Fissa il vincitore locale senza configurare il modello di frontiera o aprire il test."""
from pathlib import Path
from qiskit_dataset.experiment_v2 import summarize_results
from scripts.mqt_predictor_protocol import METHOD_CONFIG_V2, METHOD_RESULTS_DIR_V2, file_sha256
from .common import OUTPUT, ROOT, digest, read_json, write_json
from .configuration import CONFIGURATIONS, FIXED, TIMEOUT_SECONDS, MAX_ATTEMPTS
from .study import FROZEN, require_all_sealed, immutable_json

FINAL=OUTPUT/"final_configuration.json"
PROOF=OUTPUT/"selection_complete.json"

def local_method_fields(study, model, config, rag):
    artifact=study["models"][model]["artifact"]
    return {"provider":"llama.cpp-local","model_id":artifact["gguf_repository"]+"/"+artifact["filename"],
            "model_revision":artifact["gguf_revision"],"prompt_version":"local-selection-v1/"+config["prompt_variant"]+("/rag" if rag else "/no-rag"),
            "prompt_sha256":digest({"configuration_code":study["code_hashes"]["llm_selection/configuration.py"],
                                   "prompt_variant":config["prompt_variant"],"rag_enabled":rag}),
            "temperature":config["temperature"],"request_timeout_seconds":TIMEOUT_SECONDS,
            "max_output_tokens":FIXED["max_tokens"],"max_attempts":MAX_ATTEMPTS,"rag_enabled":rag}

def finalize():
    study,seal=require_all_sealed()
    analysis=OUTPUT/"studies"/study["study_id"]/"analysis"
    selection=read_json(analysis/"selection.json")
    winner=selection["winner"]
    if winner is None: raise ValueError("No operational winner; local selection remains incomplete")
    model,config_id=winner.split("/")
    config=next(c for c in CONFIGURATIONS if c["id"]==config_id)
    all_rows=read_json(analysis/"episode_results.json")
    rows=[r for r in all_rows if r["trial_id"]==winner]
    if len(rows)!=88: raise ValueError("Winner does not cover exactly 88 circuits")
    methods={key:local_method_fields(study,model,config,rag) for key,rag in (("llm_rag",True),("llm_no_rag",False))}
    final={"schema_version":"1.0.0","status":"local_frozen","study_sha256":digest(study),"winner":winner,
           "profile":study["models"][model],"configuration":config,"fixed":FIXED,"timeout_seconds":TIMEOUT_SECONDS,
           "max_attempts":MAX_ATTEMPTS,"methods":methods,"code_hashes":study["code_hashes"],
           "input_hashes":study["input_hashes"],"selection_sha256":file_sha256(analysis/"selection.json"),
           "test_released":False,"frontier_configuration":"independent prerequisite, not supplied by local selection"}
    immutable_json(FINAL,final)
    config_document=read_json(METHOD_CONFIG_V2)
    original=OUTPUT/"preparation"/"experiment_methods_before_local_freeze.json"
    if not original.exists(): write_json(original,config_document)
    config_document["methods"].update(methods)
    # The existing global status is retained. An unconfigured frontier cannot be advertised as frozen.
    write_json(METHOD_CONFIG_V2,config_document)
    results=read_json(analysis/"baseline_results.json")+rows
    canonical=METHOD_RESULTS_DIR_V2/"validation"/"evaluation"
    fingerprints=read_json(analysis/"input_fingerprints.json")
    summary=summarize_results(results,split="validation",input_fingerprints=fingerprints)
    summary.update(scope="local_llm_selection",selected_trial=winner,
                   local_configuration_sha256=file_sha256(FINAL),selection_sha256=file_sha256(analysis/"selection.json"))
    canonical.mkdir(parents=True,exist_ok=True)
    from qiskit_dataset.experiment_v2 import atomic_jsonl_write
    results_path=canonical/"method_results.jsonl"
    if results_path.exists():
        from qiskit_dataset.experiment_v2 import load_jsonl
        if load_jsonl(results_path)!=results: raise ValueError("Different canonical validation results already exist")
    else: atomic_jsonl_write(results_path,results)
    immutable_json(canonical/"evaluation_summary.json",summary)
    hashes={str(p.relative_to(ROOT)):file_sha256(p) for p in (
        FROZEN,FINAL,analysis/"selection.json",analysis/"episode_results.json",analysis/"baseline_results.json",
        analysis/"input_fingerprints.json",canonical/"evaluation_summary.json",results_path,
        OUTPUT/"studies"/study["study_id"]/"all_decisions_sealed.json")}
    immutable_json(PROOF,{"schema_version":"1.0.0","status":"local_selection_complete","winner":winner,
                          "files":hashes,"local_method_fields_sha256":digest(methods),"test_released":False})
    print("Local configuration frozen:",winner,flush=True)
    return final

def verify_local_selection():
    from .study import verify_hashes
    proof=read_json(PROOF)
    if proof["status"]!="local_selection_complete": raise ValueError("Local selection incomplete")
    verify_hashes(ROOT,proof["files"])
    study,seal=require_all_sealed()
    final=read_json(FINAL)
    if final["study_sha256"]!=digest(study) or final["winner"]!=proof["winner"]: raise ValueError("Winner provenance mismatch")
    analysis=OUTPUT/"studies"/study["study_id"]/"analysis"
    verify_hashes(ROOT,read_json(analysis/"input_fingerprints.json").get("server_resources",{}))
    artifact=final["profile"]["artifact"]
    if file_sha256(Path(artifact["local_path"]))!=artifact["gguf_sha256"]:
        raise ValueError("Selected model weights changed")
    current=read_json(METHOD_CONFIG_V2)["methods"]
    if digest({key:current[key] for key in ("llm_rag","llm_no_rag")})!=proof["local_method_fields_sha256"]:
        raise ValueError("Local method settings changed after selection")
    return {"winner":proof["winner"],"proof_sha256":file_sha256(PROOF),
            "final_configuration_sha256":file_sha256(FINAL)}

if __name__=="__main__": finalize()
