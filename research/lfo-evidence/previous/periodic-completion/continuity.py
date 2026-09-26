from pathlib import Path
import json,numpy as np
R=Path(__file__).resolve().parent
v=json.loads((R/'results.json').read_text());old=json.loads((R.parent/'periodic-supplement/results.json').read_text())
# Keep the decision threshold fixed at the previously measured value.
threshold=1.5*old['quantum_db'];report=[]
for name in ['25R1','25R2','25R3']:
 rows=[r for r in v['sections'] if r['file']==name]
 for advance in [42,43]:
  best=None
  for initial in range(16):
   errors=[]
   for idx,row in enumerate(rows):
    obs=np.array(row['jumps_db'])>threshold
    rev=np.array([int(f'{(initial+advance*idx+n)%16:04b}'[::-1],2) for n in range(len(obs))]);pred=rev<row['frequency']%16
    errors.append(int(sum(obs!=pred)))
   score=sum(errors)
   if best is None or score<best['errors']:best=dict(file=name,advance_per_section=advance,initial_phase=initial,errors=score,section_errors=errors)
  report.append(best)
(R/'continuity.json').write_text(json.dumps(report,indent=2));print(report)
# Confirm prior threshold produces exactly the same extracted binary sequences.
changed=sum(sum((np.array(r['jumps_db'])>threshold)!=(np.array(r['jumps_db'])>1.5*v['quantum_db'])) for r in v['sections'])
assert changed==0
print('Prior threshold classification changes:',changed)
