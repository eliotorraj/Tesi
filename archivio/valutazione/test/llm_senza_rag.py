'Standalone launcher for the llm_senza_rag Test.'
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/"strumenti"))
from runner import cli
if __name__=="__main__":
    raise SystemExit(cli("llm_senza_rag"))
