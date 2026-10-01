"""Avvio separato: LLM + RAG Manhattan con 10 esempi train."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "strumenti"))
from numero_esempi import cli

if __name__ == "__main__":
    raise SystemExit(cli(10))
