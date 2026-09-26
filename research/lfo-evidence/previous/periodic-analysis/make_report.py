from pathlib import Path
import json,csv,numpy as np,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent
f=json.loads((R/'frequency_refined.json').read_text());d=json.loads((R/'depth_stable.json').read_text());a=json.loads((R/'alignment.json').read_text())
for name,rows in [('frequency_table',f),('depth_table',d),('recording_coverage',a)]:
 keys=list(dict.fromkeys(k for row in rows for k in row))
 with (R/(name+'.csv')).open('w',newline='',encoding='utf-8-sig') as out:
  w=csv.DictWriter(out,fieldnames=keys);w.writeheader();w.writerows(rows)
fig,ax=plt.subplots(1,2,figsize=(12,4))
g=[x for x in f if 'refined_period_s' in x]
ax[0].semilogy([x['frequency'] for x in g],[x['refined_period_s'] for x in g],'.',label='Recorded wrap intervals')
ax[0].set(xlabel='LFO FREQ register',ylabel='Saw period (s)',title='128 high-range frequency settings');ax[0].grid(True)
for s in [0,1,2,3]:
 v=[x for x in d if x['file']=='15' and x['ams']==s and x['label'].startswith('AMD=')]
 ax[1].plot([x['amd'] for x in v],[x['stable_db_span'] for x in v],label='AMS '+str(s))
ax[1].set(xlabel='AMD',ylabel='Measured square-wave span (dB)',title='Deep AM becomes floor-limited');ax[1].legend();ax[1].grid(True)
fig.tight_layout();fig.savefig(R/'overview.png',dpi=160);plt.close(fig)
# Preserve file provenance without duplicating multi-GB recordings.
inputs=json.loads((R/'inputs.json').read_text())
for x in inputs:
 p=Path(x['file']);h=hashlib.sha256()
 with p.open('rb') as s:
  for b in iter(lambda:s.read(8*1024*1024),b''):h.update(b)
 x['sha256']=h.hexdigest();x['bytes']=p.stat().st_size
(R/'inputs.json').write_text(json.dumps(inputs,indent=2))
print('tables, chart, input hashes written')
