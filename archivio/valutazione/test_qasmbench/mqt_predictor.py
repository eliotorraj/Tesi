"""Avvio indipendente QASMBench: mqt_predictor."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/"strumenti"))
from runner import cli
if __name__=="__main__": raise SystemExit(cli("mqt_predictor"))
