"""Genera il report k=1 per mqtbench90, senza avviare decisioni."""
import sys
from pathlib import Path
sys.dont_write_bytecode = True
area = Path(__file__).resolve().parent / "mqtbench90"
sys.path.insert(0, str(area))
sys.path.insert(0, str(area / "report"))
from genera import main

if __name__ == "__main__":
    main()
