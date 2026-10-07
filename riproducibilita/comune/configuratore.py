"""Named configurations: checks, atomic revisions and protection of prepared runs.

This module does not import settings: creating or reading a configuration does
not load MQT or require a prepared experiment. Internal paths are toolkit-relative.
"""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4
import fcntl
import hashlib
import json
import math
import os
import re

KIT = Path(__file__).resolve().parents[1]
NAMED = KIT / "configurazioni/esperimenti"
METHODS = {
    "llm_rag": 'LLM with retrieval from the train Dataset',
    "llm_senza_rag": 'LLM without retrieved examples',
    "random": 'random device and configuration selection',
    "llm_recupero_random": 'LLM with randomly sampled train examples',
    "mqt": 'MQT selector and RL policies (requires training and a Bell check)',
    "llm_rag_k1": 'LLM with one retrieved example',
    "llm_rag_k10": 'LLM with ten retrieved examples',
    "llm_wl": 'WL structural retrieval (requires validation wl)',
    "llm_wl_sintesi": 'WL with a DAG summary in the prompt',
}
PROFILES = {
    "cpu": dict(context=16384, batch_size=128, ubatch_size=64, gpu_layers=0, workers=1),
    "gpu": dict(context=16384, batch_size=128, ubatch_size=64, gpu_layers=999, workers=1),
}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def identifier(value):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", value):
        raise ValueError('Use a name starting with a letter or digit, followed by letters, digits, _, . or -')
    return value


def config_path(name):
    return NAMED / identifier(name) / "esperimento.json"


def input_path(value):
    p = Path(value).expanduser()
    return (p if p.is_absolute() else KIT / p).resolve()


def portable(path):
    path = Path(path).resolve()
    return str(path.relative_to(KIT)) if path.is_relative_to(KIT) else str(path)


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def load_path(path):
    config = read(path)
    catalog = read(input_path(config["catalog"]))
    registry_path = input_path(config["model_registry"])
    registry = read(registry_path)
    for model in registry["models"]:
        file = Path(model["file"]).expanduser()
        model["file"] = str((file if file.is_absolute() else registry_path.parent / file).resolve())
    return config, catalog, registry


def load(name):
    path = config_path(name)
    if not path.is_file():
        raise ValueError(f'Experiment {name!r} is missing. Create it with: configura.py nuovo {name}')
    return load_path(path)


@contextmanager
def locked(name):
    folder = config_path(name).parent
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / ".lock").open("a") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError('Another command is configuring or preparing this experiment') from exc
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def frozen(name, config):
    work = input_path(config.get("output", ".")) / "esecuzioni" / name
    marker = config_path(name).parent / ".congelato.json"
    recorded = Path(read(marker)["work"]) if marker.exists() else work
    return (recorded / "contratto.json").exists() or (work / "contratto.json").exists()


def ensure_editable(name, config):
    if frozen(name, config):
        raise ValueError(f'{name} has already been prepared. Preserve results and use: configura.py duplica {name} NEW_NAME')


@contextmanager
def preparation_guard(path, config, work):
    'Prevent concurrent edits and remember external --output roots.'
    path = Path(path).resolve()
    if path.parent.parent != NAMED.resolve() or path.name != "esperimento.json":
        yield
        return
    name = path.parent.name
    with locked(name):
        if read(path) != config:
            raise ValueError('Configuration changed during startup: repeat the command')
        marker = path.parent / ".congelato.json"
        if marker.exists():
            previous = Path(read(marker)["work"])
            if previous != work and (previous / "contratto.json").exists():
                raise ValueError('Experiment already prepared in another destination; duplicate it under a new name')
        # Remember the output before starting, even if the process is terminated
        # without running finally. Lock edits only once the contract exists.
        temporary = marker.with_name(".pending-" + uuid4().hex)
        write_json(temporary, {"work": str(work), "config_sha256": file_hash(path)})
        os.replace(temporary, marker)
        yield


def write_json(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def positive(value, label, minimum=1):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < minimum:
        raise ValueError(f'{label}: requires a finite value >= {minimum}')


def distinct(values, label):
    if not values or len(values) != len(set(values)):
        raise ValueError(f'{label}: provide at least one value, without duplicates')


def validate(config, catalog, registry):
    identifier(config["experiment_id"])
    distinct(config["test_methods"], 'Methods')
    unknown = set(config["test_methods"]) - METHODS.keys()
    if unknown:
        raise ValueError('Unknown methods: ' + ", ".join(sorted(unknown)))
    if config["retrieval_k"] not in (1, 5, 10):
        raise ValueError('Retrieval supports k=1, 5 or 10')
    if config["validation_criterion"] not in ("median_regret", "mean_regret"):
        raise ValueError('Unsupported validation criterion')
    for key in ("seed", "test_seed", "random_seed"):
        if type(config[key]) is not int or not 0 <= config[key] <= 2**32 - 1:
            raise ValueError(key + ': requires an integer between 0 and 2^32-1')
    positive(config["rl_timesteps"], 'RL timesteps')
    distinct(config["wl_iterations"], 'WL depth')
    for h in config["wl_iterations"]:
        positive(h, 'WL depth')
    devices = catalog["supported_device_ids"]
    distinct(devices, 'Devices')
    supported = read(KIT / "configurazioni/catalogo.json")["supported_device_ids"]
    if set(devices) - set(supported):
        raise ValueError('Target not supported by the schemas: extend both code and schemas')
    if catalog["default_device_id"] not in devices or set(catalog["target_sha256"]) != set(devices):
        raise ValueError('Default device or fingerprints are inconsistent with the catalog')
    seeds = catalog["seeds"]
    if len(seeds) != 3 or len(set(seeds)) != 3 or any(type(x) is not int or not 0 <= x <= 2**32 - 1 for x in seeds):
        raise ValueError('The protocol requires three distinct compilation seeds between 0 and 2^32-1')
    for key, value in catalog["execution_policy"].items():
        positive(value, key)
    configs = catalog["configurations"]
    distinct([c["config_id"] for c in configs], 'Qiskit configurations')
    distinct([(c["optimization_level"], c["layout_method"], c["routing_method"]) for c in configs], 'Qiskit combinations')
    for c in configs:
        identifier(c["config_id"])
        if len(c["config_id"]) > 64:
            raise ValueError('Qiskit configuration ID is too long: maximum 64 characters')
        if c["optimization_level"] not in (2, 3) or c["layout_method"] not in (None, "sabre", "dense", "trivial") or c["routing_method"] not in (None, "sabre", "lookahead", "basic") or c["study"] not in ("baseline", "layout", "routing"):
            raise ValueError('Qiskit options unsupported by the toolkit schemas')
    models = registry["models"]
    distinct([m["id"] for m in models], 'Models')
    if not any(m.get("enabled", True) for m in models):
        raise ValueError('Select at least one LLM for validation')
    for m in models:
        identifier(m["id"])
        for key in ("context", "max_output_tokens", "timeout"):
            positive(m[key], m["id"] + ": " + key)
        if m["max_output_tokens"] >= m["context"]:
            raise ValueError('The response budget must be smaller than the context: ' + m["id"])
        temperatures = m.get("temperatures", config["temperatures"])
        distinct(temperatures, "Temperature")
        for t in temperatures:
            positive(t, 'Temperature', 0)
        if m.get("sha256") and not re.fullmatch(r"[0-9a-f]{64}", m["sha256"]):
            raise ValueError('Invalid SHA-256: ' + m["id"])
        url = urlparse(m["url"])
        if url.scheme != "http" or url.hostname not in ("localhost", "127.0.0.1") or not url.port or url.username or url.password or url.path not in ("", "/") or url.query or url.fragment:
            raise ValueError('The server needs a URL such as http://127.0.0.1:8089')
        if m.get("transport", "native") not in ("native", "windows"):
            raise ValueError('Allowed transport: native or windows')
        server = m.get("server", {})
        for key in ("threads", "batch_size", "ubatch_size"):
            positive(server.get(key, 1), key)
        positive(server.get("gpu_layers", 999), 'GPU layers', 0)
        if server.get("ubatch_size", 128) > server.get("batch_size", 512):
            raise ValueError('Microbatch exceeds batch size: ' + m["id"])
        if server.get("gpu_layers") == 0 and server.get("device") not in (None, "none"):
            raise ValueError('With zero GPU layers, the device must be none')


def publish(name, bundle, action):
    'Write new immutable files, then atomically replace only the entry point.'
    config, catalog, registry = deepcopy(bundle)
    config["experiment_id"] = name
    catalog.update(experiment_id=name, catalog_id=name + "-qiskit")
    validate(config, catalog, registry)
    folder = config_path(name).parent
    revision = folder / "revisioni" / uuid4().hex
    revision.mkdir(parents=True)
    for model in registry["models"]:
        file = Path(model["file"])
        model["file"] = os.path.relpath(file, revision) if file.is_relative_to(KIT) else str(file)
    config["catalog"] = portable(revision / "catalogo.json")
    config["model_registry"] = portable(revision / "modelli.json")
    write_json(revision / "catalogo.json", catalog)
    write_json(revision / "modelli.json", registry)
    write_json(revision / "esperimento.json", config)
    write_json(revision / "modifica.json", {"command": action, "utc": datetime.now(timezone.utc).isoformat()})
    temporary = folder / (".pending-" + uuid4().hex)
    write_json(temporary, config)
    os.replace(temporary, config_path(name))


def apply_profile(bundle, profile):
    config, catalog, registry = bundle
    values = PROFILES[profile]
    config["resource_profile"] = profile
    catalog["execution_policy"]["workers"] = values["workers"]
    for model in registry["models"]:
        model["context"] = values["context"]
        model["transport"] = "native"
        model["server"] = {"cache_type_k": "q8_0", "cache_type_v": "q8_0", "parallel": 1,
                           "threads": min(6, os.cpu_count() or 1),
                           **{k: values[k] for k in ("batch_size", "ubatch_size", "gpu_layers")}}


def select_models(registry, names):
    distinct(names, 'Models')
    missing = set(names) - {m["id"] for m in registry["models"]}
    if missing:
        raise ValueError('Register first with aggiungi-modello: ' + ", ".join(sorted(missing)))
    for model in registry["models"]:
        model["enabled"] = model["id"] in names


def create(name, profile="cpu", models=("qwen",), systems=("llm_rag", "llm_senza_rag", "random"), source=None):
    with locked(name):
        if config_path(name).exists():
            raise ValueError('Name already exists; choose a new name or use duplica')
        bundle = load(source) if source else load_path(KIT / "configurazioni/esperimento.json")
        if not source:
            apply_profile(bundle, profile)
            select_models(bundle[2], models)
            bundle[0]["test_methods"] = list(systems)
        ensure_editable(name, bundle[0])
        publish(name, bundle, "duplica " + source if source else "nuovo " + profile)


def edit(name, action, change):
    with locked(name):
        bundle = load(name)
        ensure_editable(name, bundle[0])
        change(*bundle)
        publish(name, bundle, action)
