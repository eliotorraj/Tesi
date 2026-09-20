"""Conta testi nel runtime separato dei tokenizer, senza cambiare uv.lock."""
from pathlib import Path
import json
import subprocess
import sys

def count_texts(texts, tokenizer_path, python_path):
    result = subprocess.run([str(python_path), str(Path(__file__).resolve()), str(tokenizer_path)],
                            input=json.dumps(texts), text=True, capture_output=True, check=True, timeout=120)
    return json.loads(result.stdout)

if __name__ == "__main__":
    from tokenizers import Tokenizer
    tokenizer = Tokenizer.from_file(sys.argv[1])
    print(json.dumps([len(tokenizer.encode(text, add_special_tokens=False).ids) for text in json.load(sys.stdin)]))
