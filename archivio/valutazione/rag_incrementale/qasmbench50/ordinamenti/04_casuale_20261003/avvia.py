'Standalone launcher for ordering 04_casuale_20261003.'
import sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from esperimento import cli

if __name__ == "__main__":
    raise SystemExit(cli(default_order="04_casuale_20261003"))
