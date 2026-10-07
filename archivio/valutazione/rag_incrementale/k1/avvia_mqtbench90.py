'Start/resume fixed RAG and four incremental k=1 orderings on mqtbench90.'
import sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent / "mqtbench90"))
from esperimento import cli

if __name__ == "__main__":
    raise SystemExit(cli())
