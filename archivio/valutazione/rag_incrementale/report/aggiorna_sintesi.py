"""Rigenera in posto la sola presentazione di un report, conservando misure e versione precedente.

Uso: python aggiorna_sintesi.py PERCORSO_DEL_REPORT
Il percorso deve contenere dati.json e provenienza.json già generati.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import zipfile

sys.dont_write_bytecode = True


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def update(output):
    output = output.resolve()
    generator = output.parents[2] / "genera.py"
    if not generator.is_file():
        raise ValueError("Il report deve essere in report/risultati/<esperimento>/<versione>.")
    data_file = output / "dati.json"
    data = json.loads(data_file.read_text(encoding="utf-8"))
    previous_provenance = sha(output / "provenienza.json")
    measurements = [data_file, *output.glob("*.csv")]
    before = {p.name: sha(p) for p in measurements}
    backups = output / "revisioni"
    backups.mkdir(exist_ok=True)
    backup = backups / "prima_sintesi_20261003.zip"
    if not backup.exists():
        with zipfile.ZipFile(backup, "x", zipfile.ZIP_DEFLATED) as archive:
            for path in output.rglob("*"):
                if path.is_file() and backups not in path.parents:
                    archive.write(path, "report/" + path.relative_to(output).as_posix())
    with zipfile.ZipFile(backup) as archive:
        previous_provenance = hashlib.sha256(archive.read("report/provenienza.json")).hexdigest()
    spec = importlib.util.spec_from_file_location("generatore_report_sintesi", generator)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory(prefix=".revisione_sintesi_", dir=output.parent) as tmp:
        stage = Path(tmp) / "report"
        module.write_report(data, stage, pdf=True)
        for name, fingerprint in before.items():
            if not (stage / name).is_file() or sha(stage / name) != fingerprint:
                raise ValueError("La rigenerazione cambierebbe le misure: " + name)
        for source in stage.rglob("*"):
            if not source.is_file() or source.name in before or source.name == "provenienza.json":
                continue
            destination = output / source.relative_to(stage)
            destination.parent.mkdir(exist_ok=True, parents=True)
            shutil.copy2(source, destination)
        revision = {
            "kind": "editorial_revision_only", "at": datetime.now(timezone.utc).isoformat(),
            "description": "Introduzione breve, grafici oracle con croci rosse, conclusioni sui campioni.",
            "previous_provenance_sha256": previous_provenance,
            "previous_report_archive": backup.relative_to(output).as_posix(),
            "previous_report_archive_sha256": sha(backup),
            "unchanged_measurements_sha256": before,
            "llm_calls": 0, "quantum_compilations": 0,
            "revision_script_sha256": sha(Path(__file__)),
        }
        (output / "revisione_sintesi.json").write_text(
            json.dumps(revision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        provenance = json.loads((stage / "provenienza.json").read_text())
        provenance["artifacts"] = {
            path.relative_to(output).as_posix(): sha(path)
            for path in sorted(output.rglob("*"))
            if path.is_file() and path.name != "provenienza.json" and backups not in path.parents
        }
        (output / "provenienza.json").write_text(
            json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    assert all(sha(output / name) == fingerprint for name, fingerprint in before.items())
    print(output / "rapporto.pdf", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    update(parser.parse_args().report)
