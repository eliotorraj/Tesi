"""Avvia o riprende RAG fisso e quattro ordini incrementali k=1: qasmbench50."""
import sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent / "qasmbench50"))
from esperimento import cli

if __name__ == "__main__":
    raise SystemExit(cli())
