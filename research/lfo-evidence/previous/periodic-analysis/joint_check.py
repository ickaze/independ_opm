from pathlib import Path
import json,numpy as np
R=Path(__file__).resolve().parent
W=json.loads((R/'waveform_fits.json').read_text());D=json.loads((R/'depth_stable.json').read_text());J=json.loads((R/'joint.json').read_text());F=json.loads((R/'frequency_refined.json').read_text());z=dict(np.load(R/'35.npz'))
period=next(v['refined_period_s'] for v in F if v['frequency']==0xb3)
rows=[]
for row in J:
 import re
 w,amd,pmd,ams,pms=map(int,re.findall(r'(?:wave|AMD|PMD|AMS|PMS)=(\d+)',row['label']))
 a=int((row['a']+.2)*1000);b=int((row['b']-.2)*1000);l=z['left'][a:b];r=z['right'][a:b]
 measured=[np.clip(-20*np.log10(np.maximum(l[:,0],1e-8)/np.maximum(r[:,0],1e-8)),-2,90),1200*np.log2(np.maximum(l[:,1],1e-8)/np.maximum(r[:,1],1e-8))]
 for mode,y in zip(['AM','PM'],measured):
  ref=next(v for v in W if v['file']=='14' and f'wave={w} mode={mode} KC=68' in v['label']);t=np.array(ref['template'])
  if mode=='AM':
   target=next(v['stable_db_span'] for v in D if v['file']=='15' and v['amd']==amd and v['ams']==ams and 'AMD=' in v['label'])
   anchor=next(v['stable_db_span'] for v in D if v['file']=='15' and v['amd']==127 and v['ams']==1 and 'AMD=' in v['label'])
  else:
   target=next(v['stable_cents_span'] for v in D if v['file']=='16' and v['pmd']==pmd and v['pms']==pms)
   anchor=next(v['stable_cents_span'] for v in D if v['file']=='16' and v['pmd']==64 and v['pms']==5)
  t=t*target/anchor;n=len(y);valid=(l[:,0]>r[:,0]*.001)&(l[:,1]>0) if mode=='PM' else np.ones(n,dtype=bool);phase=np.arange(n)/1000/period
  def predict(off):return np.interp((phase+off)%1,np.r_[-.5/128,(np.arange(128)+.5)/128,1+.5/128],np.r_[t[-1],t,t[0]])
  errors=[np.mean((y[:n//2][valid[:n//2]]-predict(off)[:n//2][valid[:n//2]])**2) for off in np.arange(256)/256];off=np.argmin(errors)/256;pred=predict(off)
  rows.append(dict(label=row['label'],mode=mode,phase_fit=off,excluded_fraction=float(1-np.mean(valid)),holdout_rms=float(np.sqrt(np.mean((y[n//2:][valid[n//2:]]-pred[n//2:][valid[n//2:]])**2))),unit='dB' if mode=='AM' else 'cents'))
(R/'joint_prediction.json').write_text(json.dumps(rows,indent=2))
for mode in ['AM','PM']:
 v=[x['holdout_rms'] for x in rows if x['mode']==mode];print(mode,'median/max RMS',np.median(v),max(v))
