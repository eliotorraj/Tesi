'Separate launcher: Manhattan LLM + RAG with 1 train example.'
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "strumenti"))
from numero_esempi import cli

if __name__ == "__main__":
    raise SystemExit(cli(1))
