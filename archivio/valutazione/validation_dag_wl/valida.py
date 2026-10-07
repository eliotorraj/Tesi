'Run DAG/WL retrieval validation only.'
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"test/strumenti"))
from dag_wl_validation import cli
if __name__ == "__main__":
    raise SystemExit(cli())
