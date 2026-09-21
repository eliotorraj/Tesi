"""Un rappresentante per contenuto QASM; nessuna modifica al corpus congelato."""
import hashlib
import json
from pathlib import Path

PROFILE = "train-sha256-396-v1"

def select_unique(source_dir: Path, *, frozen: bool = True):
    groups = {}
    for path in sorted(source_dir.glob("*.qasm"), key=lambda p: p.name):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        groups.setdefault(digest, []).append(path)
    representatives = {}
    records = []
    for digest, paths in sorted(groups.items()):
        representative = paths[0]
        representatives[representative.stem] = representative
        records.append(dict(sha256=digest, representative=representative.stem,
                            aliases=[p.stem for p in paths[1:]]))
    count = sum(1 + len(r["aliases"]) for r in records)
    if frozen and (count != 422 or len(records) != 396):
        raise ValueError(f"Train inatteso: {count} sorgenti, {len(records)} hash; attesi 422 e 396")
    selection = dict(profile=PROFILE, source_circuit_count=count,
                     unique_circuit_count=len(records), alias_count=count-len(records),
                     representative_rule="lexicographically-smallest-filename", groups=records)
    selection["sha256"] = hashlib.sha256(json.dumps(selection, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return representatives, selection

def validate_training_names(names, expected):
    names = list(map(str, names))
    if len(names) != len(set(names)) or set(names) != set(expected):
        raise ValueError("Campioni ML diversi dai rappresentanti selezionati; rigenerare gli array")

def validate_selection_metadata(metadata, source_dir):
    _, expected = select_unique(source_dir)
    errors = []
    if metadata.get("training_selection") != expected:
        errors.append("Selezione ML non conforme ai 396 hash train; rigenerare il selettore")
    if metadata.get("training_sample_count") != expected["unique_circuit_count"]:
        errors.append("Numero di campioni ML non conforme: attesi 396")
    return errors
