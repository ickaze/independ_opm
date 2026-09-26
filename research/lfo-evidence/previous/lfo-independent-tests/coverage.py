from pathlib import Path
import json
R=Path(__file__).resolve().parent
manifest=json.loads((R/'manifest.json').read_text())
def rows(prefix):
 return [s for f in manifest['files'] if f['name'].startswith(prefix) for s in json.loads((R/'schedule'/(f['name']+'.json')).read_text()) if s['analyze']]
freq=set()
for f in manifest['files']:
 if 'F' in f['name'] and 17<=int(f['name'][:2])<=32:
  for s in rows(f['name']):freq.add(s['registers']['18'])
assert freq==set(range(256))
am={(s['amd'],s['registers']['38']&3) for s in rows('15') if 'AMD=' in s['label']}
pm={(s['pmd'],s['registers']['38']>>4) for s in rows('16')}
assert am=={(d,s) for d in range(128) for s in range(4)}
assert pm=={(d,s) for d in range(128) for s in range(8)}
assert len(rows('34'))==64
for s in rows('15'):assert s['pmd']==0
for s in rows('16'):assert s['amd']==0
for f in manifest['files']:
 assert len(f['name'])<=8
print('PASS: 256 frequencies, 512 AMD/AMS pairs, 1024 PMD/PMS pairs, 64 operator enable conditions; 8.3 filenames')
