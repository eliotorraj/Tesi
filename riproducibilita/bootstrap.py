'Configure imports only; do not execute work during import.'
from pathlib import Path
import sys, os
ROOT=Path(__file__).resolve().parent
for p in [ROOT/"comune",ROOT/"comune/scripts",ROOT/"comune/framework",ROOT/"dataset",ROOT/"mqt",ROOT/"validation",ROOT/"test"]:
    if str(p) not in sys.path:sys.path.insert(0,str(p))
sys.dont_write_bytecode=True
os.environ.setdefault("PYTHONDONTWRITEBYTECODE","1")
os.environ.setdefault("GITHUB_ACTIONS","true")
os.environ.setdefault("QISKIT_PARALLEL","FALSE")
