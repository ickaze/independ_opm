from pathlib import Path
import json,numpy as np
R=Path(__file__).resolve().parent
d=json.loads((R/'depth.json').read_text());data={k:dict(np.load(R/(k+'.npz'))) for k in ['15','16']}
for v in d:
 z=data[v['file']];a=int((v['a']+.08)*1000);b=int((v['b']-.08)*1000);l=z['left'][a:b];r=z['right'][a:b]
 db=-20*np.log10(np.maximum(l[:,0],1e-9)/np.maximum(r[:,0],1e-9));ct=1200*np.log2(np.maximum(l[:,1],1e-8)/np.maximum(r[:,1],1e-8))
 v['stable_db_span']=float(np.quantile(db,.75)-np.quantile(db,.25));v['stable_cents_span']=float(np.quantile(ct,.75)-np.quantile(ct,.25));v['low_amplitude']=float(np.quantile(l[:,0],.25))
fits=[]
for ams in [1,2,3]:
 rows=[v for v in d if v['file']=='15' and v['ams']==ams and 1<=v['amd']<= (110 if ams<3 else 60) and 'AMD=' in v['label']]
 train=[v for v in rows if v['amd']%2==0];test=[v for v in rows if v['amd']%2]
 p=np.polyfit([v['amd'] for v in train],[v['stable_db_span'] for v in train],1)
 e=np.array([v['stable_db_span']-np.polyval(p,v['amd']) for v in test]);fits.append(dict(ams=ams,slope=float(p[0]),intercept=float(p[1]),test=len(test),rms_db=float(np.sqrt(np.mean(e*e))),max_db=float(max(abs(e)))))
print(fits)
(R/'depth_stable.json').write_text(json.dumps(d,indent=2));(R/'depth_fits.json').write_text(json.dumps(fits,indent=2))
