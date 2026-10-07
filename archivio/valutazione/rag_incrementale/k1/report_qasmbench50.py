'Generate the qasmbench50 k=1 report without starting decisions.'
import sys
from pathlib import Path
sys.dont_write_bytecode = True
area = Path(__file__).resolve().parent / "qasmbench50"
sys.path.insert(0, str(area))
sys.path.insert(0, str(area / "report"))
from genera import main

if __name__ == "__main__":
    main()
