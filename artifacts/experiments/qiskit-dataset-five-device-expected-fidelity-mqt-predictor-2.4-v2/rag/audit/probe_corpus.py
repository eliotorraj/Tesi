import sys,time
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from prototype.quantum_assistant.adapters.rag_dataset import load_corpus
start=time.monotonic(); corpus=load_corpus(verify_features=True)
print('Verified corpus',len(corpus.records),'seconds',time.monotonic()-start)
