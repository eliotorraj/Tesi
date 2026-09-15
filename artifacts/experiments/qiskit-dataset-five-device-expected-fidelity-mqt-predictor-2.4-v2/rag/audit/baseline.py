from pathlib import Path
import hashlib,json,subprocess,collections
root=Path.cwd(); out=root/'artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/rag/audit'
out.mkdir(parents=True,exist_ok=True)
status=subprocess.check_output(['git','status','--porcelain=v1','-z']); (out/'git_before.bin').write_bytes(status)
print('Git:',dict(collections.Counter(x[:2].decode() for x in status.split(b'\0') if x)),flush=True)
(out/'uv_before.lock').write_bytes((root/'uv.lock').read_bytes())
protected={}
for folder in ['datasets','artifacts','archivio','configs']:
 for p in sorted((root/folder).rglob('*')):
  if not p.is_file() or out.parent in p.parents: continue
  with p.open('rb') as f: protected[str(p.relative_to(root))]=hashlib.file_digest(f,'sha256').hexdigest()
(out/'protected_before.json').write_text(json.dumps(protected,sort_keys=True))
print('Protected files:',len(protected),flush=True)
