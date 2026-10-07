'Start/resume fixed RAG and four incremental k=1 orderings on qasmbench50.'
import sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent / "qasmbench50"))
from esperimento import cli

if __name__ == "__main__":
    raise SystemExit(cli())
