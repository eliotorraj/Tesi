"""Synchronize canonical workspace models with MQT's .venv runtime mirror."""

from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path

from mqt.predictor.ml.helper import get_path_training_data as get_ml_training_data
from mqt.predictor.rl.helper import get_path_trained_model as get_rl_model_dir


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STORE = PROJECT_ROOT / "artifacts" / "models"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("capture", "install"))
    parser.add_argument("--directory", type=Path, default=DEFAULT_STORE)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def digest(path: Path) -> str:
    """Return a SHA-256 digest for one file."""
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def copy_group(source: Path, destination: Path, patterns: tuple[str, ...], overwrite: bool) -> int:
    """Copy selected files without silently replacing different artifacts."""
    destination.mkdir(parents=True, exist_ok=True)
    files = sorted({path for pattern in patterns for path in source.glob(pattern) if path.is_file()})
    copied = 0
    for source_path in files:
        destination_path = destination / source_path.name
        if destination_path.exists():
            if digest(source_path) == digest(destination_path):
                print(f"Identico, salto: {destination_path}")
                continue
            if not overwrite:
                raise FileExistsError(f"Artefatto diverso già presente: {destination_path}. Usa --overwrite.")
        shutil.copy2(source_path, destination_path)
        copied += 1
        print(f"Copiato: {source_path} -> {destination_path}")
    return copied


def main() -> int:
    """Capture from the environment or install into it."""
    args = parse_args()
    package_rl = get_rl_model_dir()
    package_ml = get_ml_training_data() / "trained_model"
    store_rl = args.directory / "rl"
    store_ml = args.directory / "device_selector"

    if args.action == "capture":
        copied = copy_group(package_rl, store_rl, ("*.zip",), args.overwrite)
        copied += copy_group(package_ml, store_ml, ("*.joblib",), args.overwrite)
    else:
        if not args.directory.is_dir():
            raise SystemExit(f"Directory dei modelli non trovata: {args.directory}")
        copied = copy_group(store_rl, package_rl, ("*.zip",), args.overwrite)
        copied += copy_group(store_ml, package_ml, ("*.joblib",), args.overwrite)

    print(f"Sincronizzazione completata; file copiati: {copied}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
