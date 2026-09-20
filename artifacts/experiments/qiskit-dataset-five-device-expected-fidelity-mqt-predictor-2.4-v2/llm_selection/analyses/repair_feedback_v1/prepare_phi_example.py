from pathlib import Path
import json, copy, hashlib
from prototype.prompting.minimal import model_input, audit, REVISION
from prototype.prompting.rendering import REPAIR_INSTRUCTION
from llm_selection.configuration import payload
root=Path.cwd()
base=root/'artifacts/experiments/qiskit-dataset-five-device-expected-fidelity-mqt-predictor-2.4-v2/llm_selection'
out=base/'analyses/repair_feedback_v1'
episode=base/'technical_episodes/phi-prompt-v3-01/phi/p1_t0/portfoliovqe_indep_qiskit_6'
read=lambda p:json.loads(p.read_text())
canonical=read(episode/'attempt_1/prompt.json')
configuration={'temperature':0,'prompt_variant':'checklist'}
initial=payload(canonical,configuration)
archived_initial=read(episode/'attempt_1/audit/template/request.json')
assert initial['messages']==archived_initial['messages']
issues=read(episode/'attempt_1/summary.json')['issues']
repair=copy.deepcopy(canonical)
repair['previous_validation_errors']=issues
view=model_input(repair)
prepared=payload(repair,configuration)
old=read(episode/'attempt_2/call/request.json')
archived_message=read(episode/'attempt_2/audit/template/request.json')['messages'][0]['content']
assert old['prompt'].count(archived_message)==1
prefix,suffix=old['prompt'].split(archived_message)
new=prefix+prepared['messages'][0]['content']+suffix
d=out/'phi_example'
d.mkdir()
(d/'prompt_precedente.txt').write_text(old['prompt'])
(d/'prompt_corretto_non_inviato.txt').write_text(new)
(d/'errore_aggiunto.txt').write_text('\n'.join(view['previous_validation_errors'])+'\n'+REPAIR_INSTRUCTION+'\n')
(d/'encoding.json').write_text(json.dumps(audit(repair),ensure_ascii=False,indent=2))
native=copy.deepcopy(old)
native['prompt']=new
native['json_schema']=prepared['response_format']['schema']
(d/'prepared_request_not_sent.json').write_text(json.dumps(native,ensure_ascii=False,indent=2))
metadata={'revision':REVISION,'source_episode':str(episode.relative_to(root)),
          'source_error':issues,'first_message_exactly_unchanged':True,
          'new_inference_calls':0,'new_prompt_sent':False,
          'added_messages':view['previous_validation_errors'],
          'first_prompt_sha256':hashlib.sha256(initial['messages'][0]['content'].encode()).hexdigest()}
(d/'verification.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
print(json.dumps(metadata,ensure_ascii=False,indent=2))
