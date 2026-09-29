# SPDX-License-Identifier: 0BSD
# Copyright (C) 2026 by I.C.KaZe
from pathlib import Path
import numpy as np,json,csv,hashlib,re
R=Path(__file__).resolve().parent
S=R.parent/'stimulus'
rows=[];meta=[]
# Start-marker offsets measured at 10ms resolution. Interior windows avoid edges.
offsets={'43NOISE':13.97,'44NROUTE':9.40,'45NMOD':-0.005,'46NSTATE':1.52}
for name,offset in offsets.items():
 a=np.memmap(R/(name+'.f32'),dtype='<f4',mode='r').reshape(-1,2)
 sections=json.load(open(S/'schedule'/(name+'.json')))
 valid=0;missing=[]
 for s in sections:
  if not s['analyze']:continue
  start=s['start_s']+offset;end=s['end_s']+offset
  if end>len(a)/96000:missing.append(s['label']);continue
  lo=int((start+.2*(end-start))*96000);hi=int((end-.2*(end-start))*96000)
  x=np.asarray(a[lo:hi],dtype='float64');rms=np.sqrt(np.mean(x*x,axis=0));peak=np.max(np.abs(x),axis=0)
  regs=s['registers']
  rows.append(dict(file=name,label=s['label'],start_s=start,end_s=end,alg=int(regs['27'])&7,fb=(int(regs['27'])>>3)&7,noise=bool(int(regs['0F'])&128),nfrq=int(regs['0F'])&31,tl=int(regs['7F']),rms_l=float(rms[0]),rms_r=float(rms[1]),peak_l=float(peak[0]),peak_r=float(peak[1])))
  valid+=1
 p=Path('upload')/(name+'.flac')
 meta.append(dict(file=name+'.flac',sha256=hashlib.sha256(p.read_bytes()).hexdigest(),duration_s=len(a)/96000,nominal_mdx_s=sections[-1]['end_s'],offset_s=offset,complete_sections=valid,missing_sections=len(missing),first_missing=missing[:1],peak=float(np.max(np.abs(a))),clipped_samples=int(np.sum(np.abs(a)>=1))))
(R/'measurements.json').write_text(json.dumps(rows,indent=2))
(R/'recordings.json').write_text(json.dumps(meta,indent=2))
with (R/'measurements.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
for group in ['sine NFRQ=0','noise NFRQ=0','noise NFRQ=31']:
 q=[r for r in rows if r['file']=='43NOISE' and r['label'].startswith(group+' TL=') and 'flat EG' in r['label']]
 a=np.array([r['rms_l'] for r in q[:128]]);n=a/a[0];tl=np.arange(128)
 print(group,'RMS0',a[0],'ratios',[(i,round(n[i],6)) for i in [0,16,32,64,96,120,127]],'linear err',np.sqrt(np.mean((n-(1-tl/128))**2)),'exp err',np.sqrt(np.mean((n-10**(-.75*tl/20))**2)))
print(json.dumps(meta,indent=2))
