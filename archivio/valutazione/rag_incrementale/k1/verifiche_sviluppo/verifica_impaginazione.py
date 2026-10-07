"""Prova tecnica con score inventati: non avvia campagne, server o compilazioni quantistiche."""
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
    # Usa il testo completo dei limiti per verificare anche la pagina più fitta.
    # L'identificativo riservato non deve avere registri sperimentali.
    from unittest.mock import patch
    with patch.object(module, "test_rows", return_value=data["circuits"]):
        limits = module.collect("VERIFICA_IMPAGINAZIONE", None)["limitations"]
    data["limitations"] = limits
    data["limitations"][0] = "Dati interamente sintetici: nessuna valutazione sperimentale eseguita."
    output = root / "verifiche_sviluppo/temporanei" / (
        args.benchmark + "_" + module.uuid4().hex[:8])
    module.write_report(data, output, pdf=True)
    print(json.dumps({"benchmark": args.benchmark, "output": str(output),
                      "synthetic": True, "llm_called": False,
                      "figures": len(list((output / "grafici").glob("*.pdf")))}, indent=2))


if __name__ == "__main__":
    main()
