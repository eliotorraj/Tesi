'Technical check with synthetic scores; no campaigns, servers or quantum compilation.'
from pathlib import Path
import argparse
import json
import sys

sys.dont_write_bytecode = True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("benchmark", choices=("mqtbench90", "qasmbench50"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / args.benchmark))
    from verifica_report import synthetic_data
    module, data = synthetic_data()
    # Use the full limitations text to check the most crowded page too.
    # The reserved identifier must not have experimental records.
    from unittest.mock import patch
    with patch.object(module, "test_rows", return_value=data["circuits"]):
        limits = module.collect("VERIFICA_IMPAGINAZIONE", None)["limitations"]
    data["limitations"] = limits
    data["limitations"][0] = 'Entirely synthetic data: no experimental evaluation performed.'
    output = root / "verifiche_sviluppo/temporanei" / (
        args.benchmark + "_" + module.uuid4().hex[:8])
    module.write_report(data, output, pdf=True)
    print(json.dumps({"benchmark": args.benchmark, "output": str(output),
                      "synthetic": True, "llm_called": False,
                      "figures": len(list((output / "grafici").glob("*.pdf")))}, indent=2))


if __name__ == "__main__":
    main()
