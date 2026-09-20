import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
from contextlib import closing
import numpy as np
from qdrant_client import QdrantClient
from prototype.quantum_assistant.adapters.rag_dataset import DEFAULT_RAG_ROOT, COLLECTION_NAME
def diff(a, b, path=""):
    if isinstance(a, dict) and isinstance(b, dict):
        for key in a.keys() | b.keys():
            if key not in a or key not in b:
                print(path, key, "missing")
            else:
                diff(a[key], b[key], path + "." + key)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            print(path, "length", len(a), len(b))
        for i, (x, y) in enumerate(zip(a, b)):
            diff(x, y, path + "[" + str(i) + "]")
    elif a != b or type(a) is not type(b):
        print(path, repr(a), type(a).__name__, repr(b), type(b).__name__)
with closing(QdrantClient(path=str(DEFAULT_RAG_ROOT / "index/qdrant"))) as local, closing(QdrantClient(url="http://127.0.0.1:6333")) as server:
    identifier = "0094539a-a12d-5e68-a7ad-97b4953216c9"
    a = local.retrieve(COLLECTION_NAME, [identifier], with_vectors=True)[0]
    b = server.retrieve(COLLECTION_NAME, [identifier], with_vectors=True)[0]
    print("vectors_equal", np.array_equal(np.asarray(a.vector, dtype=np.float32), np.asarray(b.vector, dtype=np.float32)))
    diff(a.payload, b.payload)
