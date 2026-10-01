"""Controlli di installazione senza addestramento né accesso agli score Test."""
import ast
from pathlib import Path
import platform
import settings as s

def installation():
    from scripts.mqt_predictor_protocol import package_version_mismatches
    from gestione import hardware
    from prototype.prompting.toon import encode_view,decode_view,metadata
    if platform.python_version_tuple()[:2]!=('3','12'):raise ValueError('Richiesto Python 3.12')
    errors=package_version_mismatches()
    if errors:raise ValueError('Dipendenze diverse dal lock: '+str(errors))
    paths=[s.KIT/p for p in s.code_identity() if p.endswith('.py')]
    for p in paths:ast.parse(p.read_text(),filename=str(p))
    probe={'check':[1,2,3]}
    if decode_view(encode_view(probe))!=probe:raise ValueError('Codec TOON non reversibile')
    return {'status':'ready','python':platform.python_version(),'python_files':len(paths),
            'hardware':hardware(),'toon':metadata(),'model_weights_checked':False,
            'corpus_counts':{split:len(list((s.CORPUS/split).glob('*.qasm'))) for split in ('train','validation','test')}}
