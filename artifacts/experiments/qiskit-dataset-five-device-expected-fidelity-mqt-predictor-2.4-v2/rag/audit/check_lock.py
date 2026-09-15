from pathlib import Path
import tomllib,json
p=Path(__file__).parent
old=tomllib.loads((p/'uv_before.lock').read_text()); new=tomllib.loads(Path('uv.lock').read_text())
a={x['name']:x['version'] for x in old['package']}; b={x['name']:x['version'] for x in new['package']}
changes={k:(v,b.get(k)) for k,v in a.items() if b.get(k)!=v}
assert not changes,changes
print('Preexisting versions unchanged:',len(a)); print('Added:',{k:v for k,v in b.items() if k not in a})
(p/'lock_comparison.json').write_text(json.dumps({'unchanged_packages':len(a),'changed':changes,'added':{k:v for k,v in b.items() if k not in a}},indent=2)+'\n')
