'Configuration command interface; examples are in documentazione/configurazione.md.'
import argparse
from copy import deepcopy
from pathlib import Path

from . import configuratore as c


def parser():
    p = argparse.ArgumentParser(description=__doc__, epilog='Example: configura.py nuovo trial-cpu --profilo cpu; then configura.py mostra trial-cpu')
    subs = p.add_subparsers(dest="command", required=True)
    new = subs.add_parser("nuovo", help='Create a configuration separate from distributed defaults')
    new.add_argument("nome")
    new.add_argument("--profilo", choices=c.PROFILES, default="cpu", help='Initial resources (default: cpu)')
    new.add_argument("--modelli", nargs="+", default=["qwen"], help='Initial candidates: qwen, phi, gemma (default: qwen)')
    new.add_argument("--sistemi", nargs="+", choices=c.METHODS, default=["llm_rag", "llm_senza_rag", "random"])
    dup = subs.add_parser("duplica", help='Copy settings, without results, into a new experiment')
    dup.add_argument("origine"); dup.add_argument("nome")
    subs.add_parser("elenca", help='List created experiments and their status')
    avail = subs.add_parser("disponibili", help='Show available identifiers and their meaning')
    avail.add_argument("cosa", choices=["sistemi", "dispositivi", "compilazioni", "modelli", "profili"])
    for name, help_text in [("mostra", 'Readable summary, paths and maximum grid workload'), ("verifica", 'Check inputs and GGUF hashes without inference')]:
        sub = subs.add_parser(name, help=help_text); sub.add_argument("nome")
    circuits = subs.add_parser("circuiti", help='Connect a directory containing train/, validation/ and test/')
    circuits.add_argument("nome"); circuits.add_argument("--cartella", type=Path, required=True)
    circuits.add_argument("--crea", action="store_true", help='Create missing split directories; do not add or split circuits')
    for name, help_text in [("modelli", 'Select already registered candidates'), ("sistemi", 'Replace the list of methods evaluated on Test'), ("dispositivi", 'Select supported quantum Targets'), ("compilazioni", 'Select Qiskit configurations by ID')]:
        sub = subs.add_parser(name, help=help_text)
        sub.add_argument("nome"); sub.add_argument("valori", nargs="+")
    add = subs.add_parser("aggiungi-compilazione", help='Add a combination of supported Qiskit options')
    add.add_argument("nome"); add.add_argument("id")
    add.add_argument("--ottimizzazione", type=int, choices=[2, 3], required=True)
    add.add_argument("--layout", choices=["default", "sabre", "dense", "trivial"], default="default")
    add.add_argument("--routing", choices=["default", "sabre", "lookahead", "basic"], default="default")
    add.add_argument("--studio", choices=["baseline", "layout", "routing"], default="baseline")
    for name, help_text in [("modello", "Change an LLM's path, context, temperatures or server"), ("aggiungi-modello", 'Register a new local GGUF and compute its SHA-256')]:
        sub = subs.add_parser(name, help=help_text)
        sub.add_argument("nome"); sub.add_argument("id")
        sub.add_argument("--file", type=Path, required=name == "aggiungi-modello")
        if name == "aggiungi-modello":
            sub.add_argument("--fonte", required=True, help='Source URL or provenance description')
            sub.add_argument("--revisione", required=True, help='Verifiable revision or local version identifier')
            sub.add_argument("--precisione", required=True, help='Quantization, for example Q4_K_M')
            sub.add_argument("--repository", help='Base model repository, if known')
        sub.add_argument("--contesto", type=int); sub.add_argument("--token-risposta", type=int)
        sub.add_argument("--temperature", type=float, nargs="+"); sub.add_argument("--timeout", type=float)
        sub.add_argument("--url"); sub.add_argument("--trasporto", choices=["native", "windows"])
        server_options(sub)
    resources = subs.add_parser("risorse", help='Set Qiskit workers, active-candidate servers and the output root')
    resources.add_argument("nome")
    resources.add_argument("--processi", type=int); resources.add_argument("--timeout-compilazione", type=float)
    resources.add_argument("--risultati", type=Path)
    server_options(resources)
    params = subs.add_parser("parametri", help='Set grids, retrieval, validation criterion and seeds')
    params.add_argument("nome")
    params.add_argument("--temperature", nargs="+", type=float)
    params.add_argument("--k", choices=[1, 5, 10], type=int)
    params.add_argument("--passi-rl", type=int)
    for key in ["seed", "seed-test", "seed-random"]:
        params.add_argument("--" + key, type=int)
    params.add_argument("--seed-compilazione", nargs=3, type=int)
    params.add_argument("--wl", nargs="+", type=int)
    params.add_argument("--criterio", choices=["median_regret", "mean_regret"])
    return p


def server_options(p):
    p.add_argument("--threads", type=int)
    p.add_argument("--gpu-layers", type=int, help='0 for CPU, 999 to request all layers on GPU')
    p.add_argument("--device", help='Identifier from llama.cpp --list-devices; auto lets the backend choose')
    p.add_argument("--server-bin", type=Path, help='Path to the Linux llama-server executable')
    p.add_argument("--batch", type=int); p.add_argument("--microbatch", type=int)


def update_server(model, a):
    server = model.setdefault("server", {})
    for arg, key in [("threads", "threads"), ("gpu_layers", "gpu_layers"), ("batch", "batch_size"), ("microbatch", "ubatch_size")]:
        if getattr(a, arg, None) is not None:
            server[key] = getattr(a, arg)
    if getattr(a, "server_bin", None) is not None:
        server["binary"] = str(a.server_bin.expanduser().resolve())
    if getattr(a, "device", None) is not None:
        server["device"] = None if a.device == "auto" else a.device
    if getattr(a, "gpu_layers", None) == 0 and getattr(a, "device", None) is None:
        server["device"] = None


def change(a, config, catalog, registry):
    models = registry["models"]
    if a.command == "circuiti":
        folder = a.cartella.expanduser().resolve()
        if a.crea:
            for split in ("train", "validation", "test"):
                (folder / split).mkdir(parents=True, exist_ok=True)
        config["corpus"] = c.portable(folder)
    elif a.command == "modelli":
        c.select_models(registry, a.valori)
    elif a.command == "sistemi":
        config["test_methods"] = a.valori
    elif a.command == "dispositivi":
        original = c.read(c.KIT / "configurazioni/catalogo.json")
        unknown = set(a.valori) - set(original["supported_device_ids"])
        if unknown:
            raise ValueError('Unsupported Target; see configura.py disponibili dispositivi: ' + ", ".join(sorted(unknown)))
        catalog["supported_device_ids"] = a.valori
        catalog["default_device_id"] = a.valori[0]
        catalog["target_sha256"] = {d: original["target_sha256"][d] for d in a.valori}
    elif a.command == "compilazioni":
        pool = {x["config_id"]: x for x in c.read(c.KIT / "configurazioni/catalogo.json")["configurations"]}
        pool.update({x["config_id"]: x for x in catalog["configurations"]})
        missing = set(a.valori) - pool.keys()
        if missing:
            raise ValueError('Unknown configurations: ' + ", ".join(sorted(missing)))
        catalog["configurations"] = [pool[key] for key in a.valori]
    elif a.command == "aggiungi-compilazione":
        catalog["configurations"].append(dict(config_id=a.id, study=a.studio, optimization_level=a.ottimizzazione,
            layout_method=None if a.layout == "default" else a.layout, routing_method=None if a.routing == "default" else a.routing))
    elif a.command in ("modello", "aggiungi-modello"):
        index = {m["id"]: m for m in models}
        if a.command == "aggiungi-modello":
            if a.id in index:
                raise ValueError('ID already registered: use modello or choose another name')
            file = a.file.expanduser().resolve()
            if not file.is_file() or file.suffix.lower() != ".gguf":
                raise ValueError('Provide an existing local GGUF file')
            print('Computing the GGUF SHA-256; large files may take time...', flush=True)
            template = deepcopy(next(m for m in models if m.get("enabled", True)))
            model = {key: template[key] for key in ("context", "max_output_tokens", "temperatures", "url", "timeout", "transport", "server")}
            model.update(id=a.id, file=str(file), source=a.fonte, revision=a.revisione, precision=a.precisione,
                         sha256=c.file_hash(file), enabled=True)
            if a.repository:
                model["base_repository"] = a.repository
            models.append(model)
        else:
            if a.id not in index:
                raise ValueError('Model is not registered; use aggiungi-modello')
            model = index[a.id]
        for arg, key in [("contesto", "context"), ("token_risposta", "max_output_tokens"), ("temperature", "temperatures"), ("timeout", "timeout"), ("url", "url"), ("trasporto", "transport")]:
            if getattr(a, arg) is not None:
                model[key] = getattr(a, arg)
        if a.file is not None:
            model["file"] = str(a.file.expanduser().resolve())
        update_server(model, a)
    elif a.command == "risorse":
        if a.processi is not None:
            catalog["execution_policy"]["workers"] = a.processi
        if a.timeout_compilazione is not None:
            catalog["execution_policy"]["timeout_seconds"] = a.timeout_compilazione
        if a.risultati is not None:
            config["output"] = c.portable(a.risultati.expanduser().resolve())
        for model in models:
            if model.get("enabled", True):
                update_server(model, a)
    elif a.command == "parametri":
        for arg, key in [("k", "retrieval_k"), ("passi_rl", "rl_timesteps"), ("seed", "seed"), ("seed_test", "test_seed"), ("seed_random", "random_seed"), ("wl", "wl_iterations"), ("criterio", "validation_criterion")]:
            if getattr(a, arg) is not None:
                config[key] = getattr(a, arg)
        if a.temperature is not None:
            config["temperatures"] = a.temperature
            for model in models:
                if model.get("enabled", True):
                    model["temperatures"] = a.temperature
        if a.seed_compilazione is not None:
            catalog["seeds"] = a.seed_compilazione


def available(what):
    if what == "sistemi":
        for key, text in c.METHODS.items(): print(f"{key}: {text}")
    elif what == "profili":
        for key, values in c.PROFILES.items():
            print(f"{key}: LLM on {key.upper()}, requested GPU layers={values['gpu_layers']}")
        print('Shared initial resources: context 16384, output 4096, batch 128, microbatch 64, one Qiskit worker.')
        print('Set context and resources separately with modello and risorse. The GPU must be available to the llama.cpp backend.')
    elif what == "modelli":
        for model in c.read(c.KIT / "modelli_llm/modelli.json")["models"]:
            print(f"{model['id']}: {model['precision']} — {model['source']}")
        print('Other local GGUFs: aggiungi-modello. No weights are downloaded.')
    else:
        catalog = c.read(c.KIT / "configurazioni/catalogo.json")
        if what == "dispositivi":
            print("\n".join(catalog["supported_device_ids"]))
            print('Synthetic quantum Targets, not host GPUs. Other Targets require code and schema changes.')
        else:
            for row in catalog["configurations"]:
                print(f"{row['config_id']}: optimization={row['optimization_level']}, layout={row['layout_method'] or 'default'}, routing={row['routing_method'] or 'default'}")


def main(argv=None):
    a = parser().parse_args(argv)
    from .configuratore_info import show, check
    if a.command == "disponibili":
        available(a.cosa); return 0
    if a.command == "elenca":
        paths = sorted(c.NAMED.glob("*/esperimento.json"))
        for path in paths:
            cfg = c.read(path)
            print(path.parent.name + (' — prepared; duplicate it to make changes' if c.frozen(path.parent.name, cfg) else ' — editable'))
        if not paths: print('No experiments. Start with: configura.py nuovo cpu-example --profilo cpu')
        return 0
    if a.command == "nuovo":
        c.create(a.nome, a.profilo, a.modelli, a.sistemi)
    elif a.command == "duplica":
        c.create(a.nome, source=a.origine)
    elif a.command == "verifica":
        return check(a.nome)
    elif a.command != "mostra":
        c.edit(a.nome, a.command, lambda *bundle: change(a, *bundle))
    show(a.nome)
    return 0
