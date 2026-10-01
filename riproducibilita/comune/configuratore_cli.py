"""Interfaccia dei comandi di configurazione; esempi in documentazione/configurazione.md."""
import argparse
from copy import deepcopy
from pathlib import Path

from . import configuratore as c


def parser():
    p = argparse.ArgumentParser(description=__doc__, epilog="Esempio: configura.py nuovo prova-cpu --profilo cpu; poi configura.py mostra prova-cpu")
    subs = p.add_subparsers(dest="command", required=True)
    new = subs.add_parser("nuovo", help="Crea una configurazione separata dai valori distribuiti")
    new.add_argument("nome")
    new.add_argument("--profilo", choices=c.PROFILES, default="cpu", help="Risorse iniziali (predefinito: cpu)")
    new.add_argument("--modelli", nargs="+", default=["qwen"], help="Candidati iniziali: qwen, phi, gemma (predefinito: qwen)")
    new.add_argument("--sistemi", nargs="+", choices=c.METHODS, default=["llm_rag", "llm_senza_rag", "random"])
    dup = subs.add_parser("duplica", help="Copia le impostazioni, senza risultati, in un nuovo esperimento")
    dup.add_argument("origine"); dup.add_argument("nome")
    subs.add_parser("elenca", help="Elenca gli esperimenti creati e il loro stato")
    avail = subs.add_parser("disponibili", help="Mostra identificativi e significato delle scelte")
    avail.add_argument("cosa", choices=["sistemi", "dispositivi", "compilazioni", "modelli", "profili"])
    for name, help_text in [("mostra", "Riepilogo leggibile, percorsi e carico massimo della griglia"), ("verifica", "Controlla ingressi e impronte GGUF senza inferenza")]:
        sub = subs.add_parser(name, help=help_text); sub.add_argument("nome")
    circuits = subs.add_parser("circuiti", help="Collega una cartella con train/, validation/ e test/")
    circuits.add_argument("nome"); circuits.add_argument("--cartella", type=Path, required=True)
    circuits.add_argument("--crea", action="store_true", help="Crea le tre cartelle se mancano; non aggiunge né divide circuiti")
    for name, help_text in [("modelli", "Seleziona i candidati già registrati"), ("sistemi", "Sostituisce l'elenco dei sistemi da valutare sul Test"), ("dispositivi", "Seleziona i Target quantistici supportati"), ("compilazioni", "Seleziona le configurazioni Qiskit per ID")]:
        sub = subs.add_parser(name, help=help_text)
        sub.add_argument("nome"); sub.add_argument("valori", nargs="+")
    add = subs.add_parser("aggiungi-compilazione", help="Aggiunge una combinazione delle opzioni Qiskit supportate")
    add.add_argument("nome"); add.add_argument("id")
    add.add_argument("--ottimizzazione", type=int, choices=[2, 3], required=True)
    add.add_argument("--layout", choices=["default", "sabre", "dense", "trivial"], default="default")
    add.add_argument("--routing", choices=["default", "sabre", "lookahead", "basic"], default="default")
    add.add_argument("--studio", choices=["baseline", "layout", "routing"], default="baseline")
    for name, help_text in [("modello", "Cambia percorso, contesto, temperature o server di un LLM"), ("aggiungi-modello", "Registra un GGUF locale nuovo e ne calcola SHA-256")]:
        sub = subs.add_parser(name, help=help_text)
        sub.add_argument("nome"); sub.add_argument("id")
        sub.add_argument("--file", type=Path, required=name == "aggiungi-modello")
        if name == "aggiungi-modello":
            sub.add_argument("--fonte", required=True, help="URL o descrizione della provenienza")
            sub.add_argument("--revisione", required=True, help="Revisione verificabile o identificativo della versione locale")
            sub.add_argument("--precisione", required=True, help="Quantizzazione, per esempio Q4_K_M")
            sub.add_argument("--repository", help="Repository del modello base, se conosciuto")
        sub.add_argument("--contesto", type=int); sub.add_argument("--token-risposta", type=int)
        sub.add_argument("--temperature", type=float, nargs="+"); sub.add_argument("--timeout", type=float)
        sub.add_argument("--url"); sub.add_argument("--trasporto", choices=["native", "windows"])
        server_options(sub)
    resources = subs.add_parser("risorse", help="Imposta processi Qiskit, server dei candidati attivi e destinazione risultati")
    resources.add_argument("nome")
    resources.add_argument("--processi", type=int); resources.add_argument("--timeout-compilazione", type=float)
    resources.add_argument("--risultati", type=Path)
    server_options(resources)
    params = subs.add_parser("parametri", help="Imposta griglie, recupero, criterio validation e seed")
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
    p.add_argument("--gpu-layers", type=int, help="0 per CPU, 999 per richiedere tutti gli strati su GPU")
    p.add_argument("--device", help="Identificativo restituito da llama.cpp --list-devices; auto per scelta del backend")
    p.add_argument("--server-bin", type=Path, help="Percorso dell'eseguibile llama-server Linux")
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
            raise ValueError("Target non previsto; vedere configura.py disponibili dispositivi: " + ", ".join(sorted(unknown)))
        catalog["supported_device_ids"] = a.valori
        catalog["default_device_id"] = a.valori[0]
        catalog["target_sha256"] = {d: original["target_sha256"][d] for d in a.valori}
    elif a.command == "compilazioni":
        pool = {x["config_id"]: x for x in c.read(c.KIT / "configurazioni/catalogo.json")["configurations"]}
        pool.update({x["config_id"]: x for x in catalog["configurations"]})
        missing = set(a.valori) - pool.keys()
        if missing:
            raise ValueError("Configurazioni sconosciute: " + ", ".join(sorted(missing)))
        catalog["configurations"] = [pool[key] for key in a.valori]
    elif a.command == "aggiungi-compilazione":
        catalog["configurations"].append(dict(config_id=a.id, study=a.studio, optimization_level=a.ottimizzazione,
            layout_method=None if a.layout == "default" else a.layout, routing_method=None if a.routing == "default" else a.routing))
    elif a.command in ("modello", "aggiungi-modello"):
        index = {m["id"]: m for m in models}
        if a.command == "aggiungi-modello":
            if a.id in index:
                raise ValueError("ID già registrato: usare modello oppure scegliere un altro nome")
            file = a.file.expanduser().resolve()
            if not file.is_file() or file.suffix.lower() != ".gguf":
                raise ValueError("Fornire un file GGUF locale esistente")
            print("Calcolo SHA-256 del GGUF; per file grandi può richiedere tempo...", flush=True)
            template = deepcopy(next(m for m in models if m.get("enabled", True)))
            model = {key: template[key] for key in ("context", "max_output_tokens", "temperatures", "url", "timeout", "transport", "server")}
            model.update(id=a.id, file=str(file), source=a.fonte, revision=a.revisione, precision=a.precisione,
                         sha256=c.file_hash(file), enabled=True)
            if a.repository:
                model["base_repository"] = a.repository
            models.append(model)
        else:
            if a.id not in index:
                raise ValueError("Modello non registrato; usare aggiungi-modello")
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
            print(f"{key}: LLM su {key.upper()}, strati GPU richiesti={values['gpu_layers']}")
        print("Stesse risorse iniziali: contesto 16384, risposta 4096, batch 128, microbatch 64, un processo Qiskit.")
        print("Contesto e risorse si regolano separatamente con modello e risorse. La GPU deve essere disponibile al backend llama.cpp.")
    elif what == "modelli":
        for model in c.read(c.KIT / "modelli_llm/modelli.json")["models"]:
            print(f"{model['id']}: {model['precision']} — {model['source']}")
        print("Altri GGUF locali: aggiungi-modello. Nessun peso viene scaricato.")
    else:
        catalog = c.read(c.KIT / "configurazioni/catalogo.json")
        if what == "dispositivi":
            print("\n".join(catalog["supported_device_ids"]))
            print("Target sintetici quantistici; non sono le GPU del PC. Altri Target richiedono anche codice e schemi.")
        else:
            for row in catalog["configurations"]:
                print(f"{row['config_id']}: ottimizzazione={row['optimization_level']}, layout={row['layout_method'] or 'default'}, routing={row['routing_method'] or 'default'}")


def main(argv=None):
    a = parser().parse_args(argv)
    from .configuratore_info import show, check
    if a.command == "disponibili":
        available(a.cosa); return 0
    if a.command == "elenca":
        paths = sorted(c.NAMED.glob("*/esperimento.json"))
        for path in paths:
            cfg = c.read(path)
            print(path.parent.name + (" — preparato, da duplicare per modificarlo" if c.frozen(path.parent.name, cfg) else " — modificabile"))
        if not paths: print("Nessun esperimento. Iniziare con: configura.py nuovo prova-cpu --profilo cpu")
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
