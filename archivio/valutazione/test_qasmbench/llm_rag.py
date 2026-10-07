'Independent QASMBench launch: llm_rag.'
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/"strumenti"))
from runner import cli
if __name__=="__main__": raise SystemExit(cli("llm_rag"))
