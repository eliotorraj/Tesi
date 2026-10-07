'Result sources: the exploratory MQT contract remains separate from the original.'
from pathlib import Path
from dati import METHODS, read, sha, load_run


def validate_exploratory_contract(original, external, plan):
    if external.get('plan') != plan:
        raise ValueError('MQT plan differs from its own frozen contract.')
    if not plan.get('test_id', '').startswith('mqt-esplorativo-') or not isinstance(plan.get('exploratory'), dict) or not plan['exploratory']:
        raise ValueError('The alternative MQT source must declare its exploratory status.')
    # Allow only explicit identity and training deviations. All
    # Evaluation criteria (split, circuit count, score, timeout, analysis)
    # must match; 90 files sharing names are not sufficient.
    comparable = lambda p: {k: v for k, v in p.items() if k not in ('test_id', 'exploratory')}
    if comparable(plan) != comparable(original['plan']):
        raise ValueError('MQT Test criteria are incompatible with the original comparison.')
    for key in ('source_sha256', 'selection', 'rag_seal_sha256'):
        if key not in external or external[key] != original.get(key):
            raise ValueError('Incompatible MQT provenance: ' + key)


def load_sources(area, expected, original, mqt_area=None):
    """Prefer the exploratory area when present; never combine two MQT runs.

    An explicit missing path is an error. If the default area does not exist,
    an MQT run in the original Test area remains supported.
    """
    area = Path(area).resolve()
    explicit = mqt_area is not None
    external_area = Path(mqt_area).resolve() if explicit else area.parent / 'test_mqt_esplorativo'
    external_base = external_area / 'risultati/mqt_predictor'
    use_external = explicit or (external_base / 'esecuzione.json').is_file()
    if use_external and not (external_base / 'esecuzione.json').is_file():
        raise ValueError('MQT record missing from the requested source: ' + str(external_base))
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
            raise ValueError('Original contract changed during reading.')
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
