"""Riepiloghi e controlli preliminari senza avviare esperimenti."""
from collections import defaultdict
from pathlib import Path
import shutil
from . import configuratore as c


def show(name):
    config, catalog, registry = c.load(name)
    corpus = c.input_path(config["corpus"])
    counts = {s: len(list((corpus / s).glob("*.qasm"))) for s in ("train", "validation", "test")}
    models = [m for m in registry["models"] if m.get("enabled", True)]
    print(f"Esperimento: {name} ({'preparato; duplicare per modificarlo' if c.frozen(name, config) else 'modificabile'})")
    print("Configurazione:", c.config_path(name))
    print("Corpus:", corpus)
    print("Circuiti:", ", ".join(f"{s}={n}" for s, n in counts.items()))
    print("Risultati:", c.input_path(config.get("output", ".")), f"(sottocartelle separate per {name})")
    print("Target quantistici:", ", ".join(catalog["supported_device_ids"]))
    print("Configurazioni Qiskit:", ", ".join(x["config_id"] for x in catalog["configurations"]))
    print("Sistemi Test:", ", ".join(config["test_methods"]))
    print("Risorse Qiskit:", catalog["execution_policy"]["workers"], "processi; timeout", catalog["execution_policy"]["timeout_seconds"], "secondi")
    print(f"Recupero: k={config['retrieval_k']}; passi RL={config['rl_timesteps']}; criterio={config['validation_criterion']}")
    print("LLM attivi:")
    for m in models:
        server = m.get("server", {})
        path = Path(m["file"])
        print(f"  {m['id']}: contesto={m['context']}, risposta={m['max_output_tokens']}, temperature={m.get('temperatures', config['temperatures'])}")
        print(f"    GGUF: {path} ({'presente; impronta da controllare con verifica' if path.is_file() else 'MANCANTE'})")
        print(f"    {m.get('transport', 'native')}, {m['url']}; strati GPU={server.get('gpu_layers', 999)}, thread={server.get('threads', 6)}, batch={server.get('batch_size', 512)}, microbatch={server.get('ubatch_size', 128)}")
        print(f"    server: {server.get('binary', 'llama-server nel PATH')}; dispositivo={server.get('device') or 'automatico (none in CPU)'}")
    inactive = [m["id"] for m in registry["models"] if not m.get("enabled", True)]
    if inactive: print("LLM non selezionati (riattivabili con modelli):", ", ".join(inactive))
    upper = (counts["train"] + counts["validation"]) * len(catalog["supported_device_ids"]) * len(catalog["configurations"]) * len(catalog["seeds"])
    print(f"Dataset: fino a {upper} compilazioni prima dei filtri di compatibilità; non è una stima del tempo.")
    print("Validation:", sum(len(m.get("temperatures", config["temperatures"])) for m in models), "candidati modello/temperatura.")
    if "mqt" in config["test_methods"]: print("Previsti addestramento RL, Training set, selettore e prova tecnica MQT.")
    if set(config["test_methods"]) & {"llm_wl", "llm_wl_sintesi"}: print("Prevista selezione WL sulla validation.")
    print(f"Controllo ingressi: python configura.py verifica {name}")
    print(f"Stato della pipeline: python esperimento.py --esperimento {name} stato")


def check(name):
    config, catalog, registry = c.load(name)
    c.validate(config, catalog, registry)
    problems = []
    corpus = c.input_path(config["corpus"])
    names = set()
    hashes = defaultdict(set)
    print("Controllo dei circuiti (gli stessi controlli semantici di prepara restano necessari):", flush=True)
    for split in ("train", "validation", "test"):
        files = sorted((corpus / split).glob("*.qasm"))
        print(f"  {split}: {len(files)} QASM")
        if not files: problems.append(f"Aggiungere file .qasm direttamente in {corpus / split}")
        for path in files:
            if path.stem in names: problems.append("Nome circuito duplicato tra split: " + path.stem)
            names.add(path.stem)
            hashes[c.file_hash(path)].add(split)
    if any(len(splits) > 1 for splits in hashes.values()):
        problems.append("Contenuti QASM identici in split diversi; mantenere train, validation e test separati")
    print("Controllo dei candidati attivi e dei server:", flush=True)
    for model in registry["models"]:
        if not model.get("enabled", True): continue
        file = Path(model["file"])
        if not file.is_file():
            problems.append(f"{model['id']}: GGUF mancante: {file}")
        else:
            print(f"  {model['id']}: calcolo SHA-256...", flush=True)
            sha = c.file_hash(file)
            if model.get("sha256") and sha != model["sha256"]:
                problems.append(f"{model['id']}: GGUF diverso dall'impronta registrata; per pesi diversi usare aggiungi-modello con un nuovo ID")
            elif not model.get("sha256"):
                print("    impronta da congelare in validation:", sha)
            else:
                print("    impronta corrispondente")
        if model.get("transport", "native") == "native":
            binary = model.get("server", {}).get("binary", "llama-server")
            if not shutil.which(binary):
                problems.append(f"{model['id']}: eseguibile Linux assente o non eseguibile: {binary}; indicarlo con risorse --server-bin")
        elif not shutil.which("curl.exe"):
            problems.append(f"{model['id']}: trasporto Windows richiede curl.exe disponibile da WSL")
    if problems:
        print("\nDa sistemare prima della campagna:")
        for issue in problems: print("-", issue)
        print("Nessun esperimento è stato avviato o modificato.")
        return 2
    print("Ingressi e percorsi disponibili. Questo controllo non certifica RAM/VRAM, compatibilità GGUF o qualità scientifica.")
    print(f"Prossimo passo: python esperimento.py --esperimento {name} prepara")
    return 0
