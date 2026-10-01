"""Origini dei risultati: il contratto MQT esplorativo resta distinto dall'originale."""
from pathlib import Path
from dati import METHODS, read, sha, load_run


def validate_exploratory_contract(original, external, plan):
    if external.get('plan') != plan:
        raise ValueError('Piano MQT diverso dal proprio contratto congelato.')
    if not plan.get('test_id', '').startswith('mqt-esplorativo-') or not isinstance(plan.get('exploratory'), dict) or not plan['exploratory']:
        raise ValueError('La fonte MQT alternativa deve dichiarare la natura esplorativa.')
    # Sono ammesse solo identità e deroghe di addestramento esplicite. Tutti i
    # criteri di valutazione (split, numero di circuiti, score, timeout, analisi)
    # devono coincidere; non basta che ci siano 90 file con lo stesso nome.
    comparable = lambda p: {k: v for k, v in p.items() if k not in ('test_id', 'exploratory')}
    if comparable(plan) != comparable(original['plan']):
        raise ValueError('Criteri del Test MQT incompatibili con il confronto originale.')
    for key in ('source_sha256', 'selection', 'rag_seal_sha256'):
        if key not in external or external[key] != original.get(key):
            raise ValueError('Provenienza MQT incompatibile: ' + key)


def load_sources(area, expected, original, mqt_area=None):
    """Preferisce l'area esplorativa presente; non unisce mai due esecuzioni MQT.

    Un percorso esplicito assente è un errore. Se l'area predefinita non esiste,
    resta supportata l'eventuale esecuzione MQT nel Test originale.
    """
    area = Path(area).resolve()
    explicit = mqt_area is not None
    external_area = Path(mqt_area).resolve() if explicit else area.parent / 'test_mqt_esplorativo'
    external_base = external_area / 'risultati/mqt_predictor'
    use_external = explicit or (external_base / 'esecuzione.json').is_file()
    if use_external and not (external_base / 'esecuzione.json').is_file():
        raise ValueError('Registro MQT assente nella fonte richiesta: ' + str(external_base))
    runs = {}
    for method in METHODS:
        run_area = external_area if method == 'mqt_predictor' and use_external else area
        base = run_area / 'risultati' / method
        if not (base / 'esecuzione.json').exists():
            continue
        contract_path = run_area / 'preparazione/contratto_congelato.json'
        plan_path = run_area / 'piano.json'
        contract, plan = read(contract_path), read(plan_path)
        exploratory = run_area != area
        if exploratory:
            validate_exploratory_contract(original, contract, plan)
        elif contract != original or plan != original['plan']:
            raise ValueError('Contratto originale cambiato durante la lettura.')
        run = load_run(base, expected, sha(contract_path), sha(plan_path))
        source_files = [contract_path, plan_path]
        if exploratory:
            source_files += [p for p in (run_area/'README.md', run_area/'provenienza_codice.json') if p.is_file()]
        run['source'] = {
            'base': str(base.resolve()), 'area': str(run_area.resolve()),
            'test_id': plan['test_id'], 'exploratory': exploratory,
            'details': plan.get('exploratory', {}),
            'supporting_files': {str(p.resolve()): sha(p) for p in source_files},
        }
        runs[method] = run
    return runs
