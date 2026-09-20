from pathlib import Path
import json,collections,sys
sys.path.insert(0,str(Path.cwd()))
from scripts.mqt_predictor_protocol import SOURCE_MANIFEST_V2, TEST_RELEASE_RECORD
from prototype.quantum_assistant.adapters.request import FEATURE_NAMES
p=Path('datasets/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/expected_fidelity/full/global')
r=[json.loads(x) for x in (p/'rag_examples.jsonl').read_text().splitlines()]
print('RAG',len(r),collections.Counter(x['split'] for x in r)); print('FEATURES', FEATURE_NAMES)
print(json.dumps(r[0],indent=2))
m=json.loads(SOURCE_MANIFEST_V2.read_text()); print('SOURCE',SOURCE_MANIFEST_V2, json.dumps(m['circuits'][0],indent=2)); print('TEST RELEASE',TEST_RELEASE_RECORD,TEST_RELEASE_RECORD.exists())
print('RUNS',collections.Counter((x['split'],x['status']) for line in (p/'qiskit_runs.jsonl').open() if (x:=json.loads(line))))
