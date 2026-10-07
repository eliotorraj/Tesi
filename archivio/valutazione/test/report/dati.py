'Read and aggregate Test results without importing the experiment engine.'
from __future__ import annotations
import csv
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np

METHODS = ('llm_rag', 'llm_senza_rag', 'mqt_predictor', 'random')
LABELS = dict(zip(METHODS, ('LLM + RAG', 'LLM no RAG', 'MQT Predictor', 'Random')))
LABELS['llm_recupero_random'] = 'LLM + Random RAG'
BASE_METRICS = ('score', 'total_seconds', 'compilation_seconds', 'compilation_process_seconds', 'choice_seconds')
LLM_METRICS = ('retries', 'llm_calls', 'input_tokens', 'output_tokens', 'total_tokens', 'llm_response_seconds', 'rag_seconds')
ALL_METRICS = BASE_METRICS + LLM_METRICS


def run_label(method, run):
    suffix = ' (expl.)' if run.get('source', {}).get('exploratory') else ''
    return LABELS[method] + suffix


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def write_csv(path, rows, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def mean(values):
    return statistics.mean(values) if values else None


def stats(values):
    return dict(n=len(values), mean=mean(values), median=statistics.median(values) if values else None,
                minimum=min(values) if values else None, maximum=max(values) if values else None,
                std=statistics.stdev(values) if len(values)>1 else None)


def aggregate(rows, expected_ids, method):
    """Average episodes for each circuit first, then average across circuits.

    Sums are actual episode costs. Available means always retain coverage;
    no imputation is applied. Scores cover successful episodes only.
    """
    grouped = defaultdict(list)
    for row in rows:
        grouped[row['circuit_id']].append(row)
    metrics = BASE_METRICS + (LLM_METRICS if method.startswith('llm') else ())
    circuits = []
    for index, cid in enumerate(expected_ids, 1):
        episodes = grouped.get(cid, [])
        successes = sum(r['status']=='success' for r in episodes)
        c = dict(index=index, circuit_id=cid, episodes=len(episodes), successes=successes,
                 failures=len(episodes)-successes,
                 status='pending' if not episodes else ('success' if successes==len(episodes) else ('mixed' if successes else 'failure')),
                 source_sha256=episodes[0]['source_sha256'] if episodes else None)
        for key in metrics:
            eligible = [r for r in episodes if key!='score' or r['status']=='success']
            vals = [r[key] for r in eligible if number(r.get(key))]
            c[key] = mean(vals)
            c[key+'_n'] = len(vals)
            c[key+'_missing'] = len(eligible)-len(vals)
            c[key+'_sum_known'] = sum(vals) if vals else None
        c['failure_causes'] = '; '.join(f'{k}: {v}' for k,v in sorted(Counter(r.get('error') or r['status'] for r in episodes if r['status']!='success').items()))
        circuits.append(c)
    completed = [c for c in circuits if c['episodes']]
    result = dict(method=method, expected_circuits=len(expected_ids), completed_circuits=len(completed),
                  pending=len(expected_ids)-len(completed), episodes=len(rows),
                  successes=sum(c['successes'] for c in circuits), failures=sum(c['failures'] for c in circuits),
                  circuits_all_success=sum(c['status']=='success' for c in circuits),
                  circuits_with_success=sum(c['successes']>0 for c in circuits),
                  circuits_with_failure=sum(c['failures']>0 for c in circuits),
                  failure_causes=dict(Counter(r.get('error') or r['status'] for r in rows if r['status']!='success')),
                  accepted_with_unverified_facts=sum(r.get('accepted_with_unverified_facts') is True for r in rows),
                  rounded_to_zero=sum(r.get('rounded_to_zero') is True for r in rows),
                  underflow=sum(r.get('underflow') is True for r in rows), metrics={})
    for key in metrics:
        vals=[c[key] for c in completed if number(c.get(key))]
        sums=[c[key+'_sum_known'] for c in completed if number(c.get(key+'_sum_known'))]
        eligible = [r for r in rows if key!='score' or r['status']=='success']
        measured=sum(c[key+'_n'] for c in completed)
        result['metrics'][key] = dict(**stats(vals), sum_known=sum(sums) if sums else None,
            measured_episodes=measured, missing_episodes=len(eligible)-measured,
            missing_circuits=len(completed)-len(vals),
            partially_measured_circuits=sum(c[key+'_n']>0 and c[key+'_missing']>0 for c in completed))
    if method.startswith('llm'):
        result['episodes_with_retry']=sum(number(r.get('retries')) and r['retries']>0 for r in rows)
        result['retry_distribution']=dict(sorted(Counter(str(r.get('retries')) for r in rows).items()))
        for key in ('known_input_tokens','known_output_tokens'):
            vals=[r[key] for r in rows if number(r.get(key))]
            result[key]=dict(sum_known=sum(vals) if vals else None, measured_episodes=len(vals))
    return circuits, result


def load_run(base, expected, contract_hash, plan_hash, *, expected_kind='test'):
    meta = read(base/'esecuzione.json')
    method = base.name
    if meta.get('method')!=method or meta.get('kind')!=expected_kind:
        raise ValueError(f'Incompatible identity or split: {base}')
    if meta.get('contract_sha256')!=contract_hash or meta.get('plan_sha256')!=plan_hash:
        raise ValueError(f'Incompatible contract or plan: {base}')
    if meta.get('expected_circuits')!=len(expected):
        raise ValueError(f'Incompatible expected circuit count: {base}')
    files=sorted((base/'circuiti').rglob('esito.json'))
    rows=[]
    hashes={}
    episode_paths=defaultdict(list)
    for path in files:
        row=read(path)
        cid=row.get('circuit_id')
        if cid not in expected or row.get('source_sha256')!=expected[cid]:
            raise ValueError(f'Circuit or SHA-256 does not match the Test: {path}')
        if row.get('method')!=method or row.get('split')!='test':
            raise ValueError(f'Incorrect method or split: {path}')
        if row.get('status') not in ('success','failure','timeout','interrupted'):
            raise ValueError(f'Non-terminal or unknown outcome: {path}')
        if row['status']=='success' and (not number(row.get('score')) or not 0<=row['score']<=1):
            raise ValueError(f'Success without a valid score: {path}')
        if row['status']!='success' and row.get('score') is not None:
            raise ValueError(f'Failure with a score: {path}')
        for key in ALL_METRICS:
            value=row.get(key)
            if value is not None and (not number(value) or value<0):
                raise ValueError(f'Invalid measurement ({key}): {path}')
        episode_paths[cid].append(path)
        row=dict(row, episode_source=str(path.relative_to(base)))
        rows.append(row)
    for paths in episode_paths.values():
        # Do not mistake a circuit summary and its episodes for replicates.
        if len(paths)>1 and any(a.parent in b.parents for a in paths for b in paths if a!=b):
            raise ValueError(f'Ambiguous nested outcomes: {paths}')
    for folder in ('circuiti','sessioni'):
        for path in sorted((base/folder).rglob('*.json')):
            hashes[str(path.relative_to(base))]=sha(path)
    hashes['esecuzione.json']=sha(base/'esecuzione.json')
    # Record parameters actually sent, not server defaults.
    settings=Counter()
    for path in sorted((base/'circuiti').rglob('request.json')):
        if path.parent.name!='call':
            continue
        req=read(path)
        keys=('temperature','seed','top_p','top_k','min_p','n_predict','repeat_penalty','presence_penalty','frequency_penalty')
        selected={k:req[k] for k in keys if k in req}
        settings[json.dumps(selected,sort_keys=True)]+=1
    circuits,summary=aggregate(rows, sorted(expected), method)
    return dict(meta=meta, rows=rows, circuits=circuits, summary=summary, input_files=hashes,
                generation_settings=[dict(parameters=json.loads(k),calls=v) for k,v in sorted(settings.items())])


def paired(left, right, plan):
    'Paired descriptive interval: one weight per circuit, not per episode.'
    a={r['circuit_id']:r for r in left}
    b={r['circuit_id']:r for r in right}
    common=sorted(k for k in a.keys() & b.keys() if number(a[k].get('score')) and number(b[k].get('score')))
    diffs=np.array([a[k]['score']-b[k]['score'] for k in common])
    ci=None
    if len(common)>1:
        rng=np.random.default_rng(plan['bootstrap_seed'])
        draws=rng.choice(diffs,size=(plan['bootstrap_draws'],len(diffs)),replace=True).mean(axis=1)
        alpha=(1-plan['confidence'])/2
        ci=np.quantile(draws,[alpha,1-alpha]).tolist()
    return dict(circuit_ids=common, n=len(common), mean_left=mean([a[k]['score'] for k in common]),
                mean_right=mean([b[k]['score'] for k in common]), mean_difference=float(diffs.mean()) if len(common) else None,
                median_difference=float(np.median(diffs)) if len(common) else None, paired_bootstrap_95=ci,
                wins=int((diffs>0).sum()), ties=int((diffs==0).sum()), losses=int((diffs<0).sum()),
                differences=[dict(circuit_id=k,difference=float(d)) for k,d in zip(common,diffs)])


def compare(runs, plan, *, methods=METHODS):
    available=[m for m in methods if m in runs and runs[m]['rows']]
    pairs={}
    if 'llm_rag' in available:
        for method in available:
            if method!='llm_rag':
                pairs[method]=paired(runs['llm_rag']['circuits'],runs[method]['circuits'],plan)
                pairs[method]['exploratory'] = bool(runs[method].get('source', {}).get('exploratory'))
    common=set.intersection(*[{c['circuit_id'] for c in runs[m]['circuits'] if number(c.get('score'))} for m in available]) if available else set()
    return dict(available_methods=available, exploratory_methods=[m for m in available if runs[m].get('source', {}).get('exploratory')], missing_methods=[m for m in methods if m not in available],
                pairs=pairs, all_common_successes=sorted(common),
                all_common_means={m:mean([c['score'] for c in runs[m]['circuits'] if c['circuit_id'] in common]) for m in available})
