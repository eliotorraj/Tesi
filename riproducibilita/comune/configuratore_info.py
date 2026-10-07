'Summaries and preliminary checks without starting experiments.'
from collections import defaultdict
from pathlib import Path
import shutil
from . import configuratore as c


def show(name):
    config, catalog, registry = c.load(name)
    corpus = c.input_path(config["corpus"])
    counts = {s: len(list((corpus / s).glob("*.qasm"))) for s in ("train", "validation", "test")}
    models = [m for m in registry["models"] if m.get("enabled", True)]
    print(f"Experiment: {name} ({('prepared; duplicate to make changes' if c.frozen(name, config) else 'editable')})")
    print('Configuration:', c.config_path(name))
    print("Corpus:", corpus)
    print('Circuits:', ", ".join(f"{s}={n}" for s, n in counts.items()))
    print('Results:', c.input_path(config.get("output", ".")), f'(separate subdirectories for {name})')
    print('Quantum Targets:', ", ".join(catalog["supported_device_ids"]))
    print('Qiskit configurations:', ", ".join(x["config_id"] for x in catalog["configurations"]))
    print('Test methods:', ", ".join(config["test_methods"]))
    print('Qiskit resources:', catalog["execution_policy"]["workers"], 'workers; timeout', catalog["execution_policy"]["timeout_seconds"], 'seconds')
    print(f"Retrieval: k={config['retrieval_k']}; RL timesteps={config['rl_timesteps']}; criterion={config['validation_criterion']}")
    print('Active LLMs:')
    for m in models:
        server = m.get("server", {})
        path = Path(m["file"])
        print(f"  {m['id']}: context={m['context']}, output={m['max_output_tokens']}, temperature={m.get('temperatures', config['temperatures'])}")
        print(f"    GGUF: {path} ({('present; check the fingerprint with verifica' if path.is_file() else 'MISSING')})")
        print(f"    {m.get('transport', 'native')}, {m['url']}; GPU layers={server.get('gpu_layers', 999)}, thread={server.get('threads', 6)}, batch={server.get('batch_size', 512)}, microbatch={server.get('ubatch_size', 128)}")
        print(f"    server: {server.get('binary', 'llama-server on PATH')}; device={server.get('device') or 'automatic (none on CPU)'}")
    inactive = [m["id"] for m in registry["models"] if not m.get("enabled", True)]
    if inactive: print('Unselected LLMs (reactivate with modelli):', ", ".join(inactive))
    upper = (counts["train"] + counts["validation"]) * len(catalog["supported_device_ids"]) * len(catalog["configurations"]) * len(catalog["seeds"])
    print(f'Dataset: up to {upper} compilations before compatibility filtering; this is not a time estimate.')
    print("Validation:", sum(len(m.get("temperatures", config["temperatures"])) for m in models), 'model/temperature candidates.')
    if "mqt" in config["test_methods"]: print('RL training, Training set, selector and MQT technical check are required.')
    if set(config["test_methods"]) & {"llm_wl", "llm_wl_sintesi"}: print('WL selection on validation is required.')
    print(f'Input check: python configura.py verifica {name}')
    print(f'Pipeline status: python esperimento.py --esperimento {name} stato')


def check(name):
    config, catalog, registry = c.load(name)
    c.validate(config, catalog, registry)
    problems = []
    corpus = c.input_path(config["corpus"])
    names = set()
    hashes = defaultdict(set)
    print('Circuit checks (prepara still performs the required semantic checks):', flush=True)
    for split in ("train", "validation", "test"):
        files = sorted((corpus / split).glob("*.qasm"))
        print(f"  {split}: {len(files)} QASM")
        if not files: problems.append(f'Add .qasm files directly under {corpus / split}')
        for path in files:
            if path.stem in names: problems.append('Duplicate circuit name across splits: ' + path.stem)
            names.add(path.stem)
            hashes[c.file_hash(path)].add(split)
    if any(len(splits) > 1 for splits in hashes.values()):
        problems.append('Identical QASM contents in different splits; keep train, validation and Test separate')
    print('Active-candidate and server checks:', flush=True)
    for model in registry["models"]:
        if not model.get("enabled", True): continue
        file = Path(model["file"])
        if not file.is_file():
            problems.append(f"{model['id']}: missing GGUF: {file}")
        else:
            print(f"  {model['id']}: computing SHA-256...", flush=True)
            sha = c.file_hash(file)
            if model.get("sha256") and sha != model["sha256"]:
                problems.append(f"{model['id']}: GGUF differs from the registered fingerprint; register different weights with aggiungi-modello and a new ID")
            elif not model.get("sha256"):
                print('    fingerprint to freeze during validation:', sha)
            else:
                print('    fingerprint matches')
        if model.get("transport", "native") == "native":
            binary = model.get("server", {}).get("binary", "llama-server")
            if not shutil.which(binary):
                problems.append(f"{model['id']}: Linux executable missing or not executable: {binary}; set it with risorse --server-bin")
        elif not shutil.which("curl.exe"):
            problems.append(f"{model['id']}: Windows transport requires curl.exe available from WSL")
    if problems:
        print("""
Resolve before starting the campaign:""")
        for issue in problems: print("-", issue)
        print('No experiment was started or modified.')
        return 2
    print('Inputs and paths are available. This check does not certify RAM/VRAM, GGUF compatibility or scientific quality.')
    print(f'Next step: python esperimento.py --esperimento {name} prepara')
    return 0
