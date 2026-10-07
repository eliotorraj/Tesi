'Independent llm_rag_dag_wl launcher.'
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/"strumenti"))
from dag_wl_campaign import cli
if __name__ == "__main__":
    raise SystemExit(cli(False))
