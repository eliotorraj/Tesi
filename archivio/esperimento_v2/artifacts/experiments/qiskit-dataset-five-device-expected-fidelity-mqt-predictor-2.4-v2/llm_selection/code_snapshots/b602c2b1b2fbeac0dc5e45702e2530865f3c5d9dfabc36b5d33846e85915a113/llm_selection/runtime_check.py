"""Inventario breve del runtime isolato, senza caricare i modelli."""
import importlib.util
import importlib.metadata
import json
import sys
def main():
    modules={"tokenizers":"tokenizers","jinja2":"Jinja2","matplotlib":"matplotlib","pymupdf":"PyMuPDF"}
    result={"python":sys.version.split()[0],"packages":{}}
    for module,package in modules.items():
        result["packages"][module]=importlib.metadata.version(package) if importlib.util.find_spec(module) else None
    print(json.dumps(result))
if __name__=="__main__":main()
