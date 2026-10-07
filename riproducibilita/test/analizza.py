'Tables, denominators and LaTeX from saved outcomes only.'
from collections import Counter
from statistics import mean,median
import csv,io
import settings as s

def report():
    contract=s.read(s.TEST/'contratto.json');rows=[];summary={};sources={}
    for method in contract['methods']:
        values=[]
        for path in sorted((s.TEST/method/'circuiti').glob('*/esito.json')):
            item=s.read(path);sources[str(path.relative_to(s.TEST))]=s.sha(path)
            values.append(item);m=(item.get('decision') or {}).get('metrics',{})
            rows.append({"method":method,"circuit_id":item['circuit_id'],"status":item['status'],"score":item.get('score'),"total_seconds":item.get('total_seconds'),"input_tokens":m.get('input_tokens'),"output_tokens":m.get('output_tokens'),"calls":m.get('calls')})
        scores=[x['score'] for x in values if x.get('score') is not None]
        summary[method]={"recorded":len(values),"planned":s.read(s.WORK/'manifest.json')['counts']['test'],"statuses":dict(Counter(x['status'] for x in values)),"score_denominator":len(scores),"mean_score":mean(scores) if scores else None,"median_score":median(scores) if scores else None}
    paired={}
    for i,a in enumerate(contract['methods']):
        for b in contract['methods'][i+1:]:
            maps={m:{x['circuit_id']:x['score'] for x in rows if x['method']==m and x['score'] is not None} for m in (a,b)}
            common=sorted(maps[a].keys()&maps[b].keys());diff=[maps[a][id]-maps[b][id] for id in common]
            paired[a+'__'+b]={"circuits":common,"n":len(common),"mean_difference":mean(diff) if diff else None}
    identity=s.digest({"sources":sources,"analysis":s.sha(__file__),"report":s.sha(s.KIT/"comune/relazioni.py")});dest=s.TEST/'report'/identity
    result={"summary":summary,"paired":paired,"sources":sources,"failures_are_zero":False,"unit":"circuit"}
    s.same_or_save(dest/'riepilogo.json',result)
    if rows:
        buf=io.StringIO();writer=csv.DictWriter(buf,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
        csv_path=dest/'circuiti.csv'
        if not csv_path.exists():csv_path.write_text(buf.getvalue())
    from relazioni import table_report
    table_report(dest,'Method comparison',
        'Means include available scores only. Errors and timeouts do not become zero. Paired denominators and original outcomes are in the JSON summary. Durations are in seconds; unmeasured token counts remain empty. expected_fidelity refers to synthetic Targets, not quantum hardware executions.',
        ['System','Outcomes','Available scores','Mean'],
        [[m,v['recorded'],v['score_denominator'],f"{v['mean_score']:.6f}" if v['mean_score'] is not None else '--'] for m,v in summary.items()])
    return {"directory":str(dest),"summary":summary}
