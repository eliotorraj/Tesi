"""Preparazione, congelamento e sigilli indipendenti per ogni studio."""
from __future__ import annotations
import copy
from pathlib import Path
from llm_selection.common import OUTPUT, ROOT, digest, now, read_json, write_json
from llm_selection.provenance import capture, code_hashes
from llm_selection.study import immutable_json, verify_hashes, verify_launch, input_hashes
from scripts.mqt_predictor_protocol import TEST_RELEASE_RECORD, file_sha256
from llm_selection.study import source_manifest
from .settings import CONFIGURATIONS, FIXED, MAX_ATTEMPTS, TIMEOUT_SECONDS, MODEL_KEYS, POLICY, study_root

def prepare(study_id):
    if TEST_RELEASE_RECORD.exists():
        raise ValueError("Test already released")
    root = study_root(study_id)
    if (root / "frozen_study.json").exists():
        raise ValueError("Study already frozen")
    root.mkdir(parents=True, exist_ok=True)
    copied = {}
    for split in ("train", "validation"):
        for source in sorted((OUTPUT / "prompts" / split).glob("*.json")):
            target = root / "prompts" / split / source.name
            immutable_json(target, read_json(source))
            copied[str(target.relative_to(ROOT))] = file_sha256(target)
    if len(list((root / "prompts/validation").glob("*.json"))) != 88:
        raise ValueError("Expected 88 validation prompts")
    profiles = copy.deepcopy(read_json(OUTPUT / "profiles_to_freeze.json"))
    for name, profile in profiles.items():
        profile["guards"].update(maximum_hotspot_c=110, minimum_available_bytes=1073741824,
                                 pause_hotspot_c=105, resume_hotspot_c=100)
        profile["technical_evidence"] = []
        profile.pop("technical_evidence_hashes", None)
        profile["precision_reason"] = "Profilo precedente riutilizzato; nuova verifica tecnica train con schema v4."
    immutable_json(root / "profiles_to_freeze.json", profiles)
    historical = [OUTPUT / "frozen_study.json", OUTPUT / "final_configuration.json", OUTPUT / "selection_complete.json"]
    historical += list((OUTPUT / "studies/local-llm-v1").rglob("*"))
    hashes = {str(p.relative_to(ROOT)): file_sha256(p) for p in historical if p.is_file()}
    immutable_json(root / "preparation.json", {
        "study_id": study_id, "policy": POLICY, "prompt_files": copied,
        "predecessor": "local-llm-v1", "predecessor_files": hashes,
        "development": "Adaptive revision after inspection of previous validation; test remains sealed",
        "hardware": {"gpu": "AMD Radeon RX 6750 XT", "hotspot_limit_c": 110,
                     "edge_limit_c": 95, "ram_floor_gib": 1,
                     "meaning": "User-requested operational limits; no model-specific vendor guarantee established"}})
    return root

def prompt_files(root, split):
    files = sorted((root / "prompts" / split).glob("*.json"))
    if split == "validation":
        expected = {r["circuit_id"] for r in source_manifest()["circuits"] if r["split"] == split}
        if {p.stem for p in files} != expected or len(files) != 88:
            raise ValueError("Validation population mismatch")
    elif split == "train" and len(files) != 5:
        raise ValueError("Expected five technical train cases")
    return files

def freeze(study_id):
    root = study_root(study_id)
    if TEST_RELEASE_RECORD.exists() or (root / "frozen_study.json").exists():
        raise ValueError("Test released or study already frozen")
    for m in MODEL_KEYS:
        if list((root / m).glob("*/*/decision.json")):
            raise ValueError("Validation decisions precede freezing")
    profiles = copy.deepcopy(read_json(root / "profiles_to_freeze.json"))
    if set(profiles) != set(MODEL_KEYS):
        raise ValueError("Exactly three model families required")
    current = code_hashes()
    train = prompt_files(root, "train")
    for model in MODEL_KEYS:
        evidence = []
        for config in CONFIGURATIONS:
            for path in train:
                episode = root / "technical" / model / config["id"] / path.stem
                decision = read_json(episode / "decision.json")
                begin = read_json(episode / "begin.json")
                if decision["split"] != "train" or decision["status"] != "success":
                    raise ValueError(f"Technical case not successful: {episode}")
                if begin["code_hashes"] != current:
                    raise ValueError(f"Technical code changed: use a fresh study or archive and repeat technical cases: {episode}")
                if begin["max_attempts"] != MAX_ATTEMPTS or begin["timeout_seconds"] != TIMEOUT_SECONDS:
                    raise ValueError("Technical budget mismatch")
                verify_launch({"models": profiles}, model, begin["launch"])
                evidence.append(str((episode / "decision.json").relative_to(ROOT)))
        artifact = read_json(OUTPUT / "models" / model / (profiles[model]["weight_precision"] + "_manifest.json"))
        from llm_selection.weights import verify_weights
        profiles[model].update(artifact=artifact, weight_verification=verify_weights(artifact),
                               technical_evidence=evidence,
                               technical_evidence_hashes={str(p.relative_to(ROOT)): file_sha256(p)
                                   for p in (root / "technical" / model).rglob("*") if p.is_file()})
    inputs = input_hashes()
    # Legacy shared prompt hashes are retained too, but inference reads the per-study copies.
    inputs.update({str(p.relative_to(ROOT)): file_sha256(p)
                   for split in ("train", "validation") for p in prompt_files(root, split)})
    inputs[str((root / "profiles_to_freeze.json").relative_to(ROOT))] = file_sha256(root / "profiles_to_freeze.json")
    from .evaluate import matrix_paths
    evaluation_hashes = {str(p.relative_to(ROOT)): file_sha256(p) for p in matrix_paths()}
    provenance = capture(root)
    study = {"schema_version": "2.0.0", "study_id": study_id, "frozen_at": now(),
             "phase": "local_llm_validation_selection", "test_content_accessed": False,
             "validation_count": 88, "models": profiles, "configurations": CONFIGURATIONS,
             "fixed": FIXED, "max_attempts": MAX_ATTEMPTS, "timeout_seconds": TIMEOUT_SECONDS,
             "policy": POLICY, "code_hashes": current, "input_hashes": inputs,
             "provenance_sha256": digest(provenance), "evaluation_input_hashes": evaluation_hashes}
    immutable_json(root / "frozen_study.json", study)
    return study

def verify(study_id, *, check_code=True):
    if TEST_RELEASE_RECORD.exists():
        raise ValueError("Test already released")
    root = study_root(study_id)
    study = read_json(root / "frozen_study.json")
    if study["policy"] != POLICY or study["configurations"] != CONFIGURATIONS or study["fixed"] != FIXED:
        raise ValueError("Frozen policy changed")
    if check_code and study["code_hashes"] != code_hashes():
        raise ValueError("Code changed after freeze")
    verify_hashes(ROOT, study["input_hashes"])
    for profile in study["models"].values():
        verify_hashes(ROOT, profile["technical_evidence_hashes"])
    return study

def seal_model(study_id, model):
    root = study_root(study_id)
    study = verify(study_id)
    expected = {p.stem for p in prompt_files(root, "validation")}
    for config in study["configurations"]:
        folder = root / model / config["id"]
        if {p.parent.name for p in folder.glob("*/decision.json")} != expected:
            raise ValueError("Cannot seal incomplete model")
    paths = sorted(p for p in (root / model).rglob("*") if p.is_file() and p.name != "sealed.json")
    seal = {"study_sha256": digest(study), "files": {str(p.relative_to(ROOT)): file_sha256(p) for p in paths}}
    immutable_json(root / model / "sealed.json", seal)
    return seal

def require_sealed(study_id):
    study = verify(study_id)
    root = study_root(study_id)
    seals = {}
    for model in MODEL_KEYS:
        seal = read_json(root / model / "sealed.json")
        if seal["study_sha256"] != digest(study):
            raise ValueError("Model seal belongs to another study")
        verify_hashes(ROOT, seal["files"])
        seals[model] = digest(seal)
    immutable_json(root / "all_decisions_sealed.json", {"study_sha256": digest(study), "models": seals})
    return study

def verify_predecessor(study_id):
    root = study_root(study_id)
    verify_hashes(ROOT, read_json(root / "preparation.json")["predecessor_files"])
