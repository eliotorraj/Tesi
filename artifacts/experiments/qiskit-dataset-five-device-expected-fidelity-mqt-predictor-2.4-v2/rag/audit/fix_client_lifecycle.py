from pathlib import Path
p=Path("prototype/quantum_assistant/adapters/qdrant_context.py")
s=p.read_text().replace("from contextlib import contextmanager","from contextlib import closing, contextmanager")
for expr in ['path=str(database)', 'path=str(staging / "qdrant")']:
 s=s.replace(f"with QdrantClient({expr}) as client:", f"with closing(QdrantClient({expr})) as client:")
p.write_text(s)
p=Path("tests/test_qdrant_retrieval.py")
s=p.read_text().replace("import copy\n","import copy\nfrom contextlib import closing\n")
for expr in ['path=str(self.root / "index/qdrant")','path=str(root / "index/qdrant")','":memory:"']:
 s=s.replace(f"with QdrantClient({expr}) as client:",f"with closing(QdrantClient({expr})) as client:")
 s=s.replace(f"with QdrantClient({expr}):",f"with closing(QdrantClient({expr})):")
p.write_text(s)
