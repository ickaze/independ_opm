# SPDX-License-Identifier: 0BSD
# Copyright (C) 2026 by I.C.KaZe
from analyze import *
from scipy.ndimage import median_filter
z=json.loads((R/'am_fit.json').read_text());dt=z['step_s']
def wave(i,k,var=0):
 i=i%256
 if k=='40':return np.where(i<128,i,i-256)
 return np.select([i<64,i<128,i<192],[2*i,255-2*i,256-2*i],default=2*i-511)
def quant(w,D,P):
 d=np.sign(w)*(abs(w)*D//128)
 if P==0:return d*0
 if P<=5:return np.sign(d)*(abs(d)//(2**(6-P)))
 return d*(2**(P-5))
# Derive a pitch-response table from first-cycle saw observations only.
allrows=[];parts=[]
for name in names[3:5]:
 v=load(name);k=name[:2]
 for idx,s in enumerate(v['ss']):
  t,d,c=section(v,s);c=median_filter(c,5);D=s['pmd'];P=s['registers']['38']>>4;best=None
  for off in np.arange(-.06,.061,.0005):
   f=(t-off)/dt;i=np.floor(f).astype(int);q=quant(wave(i,k),D,P);stable=np.minimum(f%1,1-f%1)*dt>.004
   m=stable&(t<4.05);loss=np.median(abs(c[m]-q[m]*1.5625))
   if best is None or loss<best[0]:best=(loss,off,q,stable)
  loss,off,q,stable=best;parts.append(dict(file=k,idx=idx,D=D,P=P,t=t,c=c,q=q,stable=stable,off=off))
 print(name,'aligned',flush=True)
# Refine phase using the measured pitch mapping, not an equal-temperament approximation.
for iteration in range(3):
 qs=[];cs=[]
 for p in parts:
  if p['file']=='40' and p['idx']%2==0:
   m=p['stable']&(p['t']<4.05);qs.extend(p['q'][m].tolist());cs.extend(p['c'][m].tolist())
 qs=np.array(qs);cs=np.array(cs);uq=np.unique(qs);table={int(q):float(np.median(cs[qs==q])) for q in uq}
 if iteration==2:break
 keys=np.array(sorted(table));vals=np.array([table[int(q)] for q in keys])
 for p in parts:
  t=p['t'];c=p['c'];best=None
  for off in np.arange(-.06,.061,.0005):
   f=(t-off)/dt;i=np.floor(f).astype(int);q=quant(wave(i,p['file']),p['D'],p['P']);stable=np.minimum(f%1,1-f%1)*dt>.004
   m=stable&(t<1.9);pred=np.interp(q[m],keys,vals);loss=np.mean(np.minimum(abs(c[m]-pred),2))
   if best is None or loss<best[0]:best=(loss,off,q,stable)
  _,p['off'],p['q'],p['stable']=best
for p in parts:
 # All triangle data and odd-index saw depths are withheld from pitch-table training.
 held=p['file']=='41' or p['idx']%2==1
 m=p['stable']&(p['t']>(2.2 if held else 4.3))&(p['t']<5.9);q=p['q'][m];obs=p['c'][m]
 known=np.array([int(a) in table for a in q]);pred=np.array([table.get(int(a),np.nan) for a in q]);e=obs[known]-pred[known]
 allrows.append(dict(file=p['file'],index=p['idx'],pmd=p['D'],pms=p['P'],held_depth_or_wave=held,offset_s=float(p['off']),test_n=int(len(q)),known_pitch_n=int(known.sum()),test_rms_cents=float(np.sqrt(np.mean(e*e))) if len(e) else None,test_median_abs_cents=float(np.median(abs(e))) if len(e) else None,test_q95_abs_cents=float(np.quantile(abs(e),.95)) if len(e) else None))
(R/'pm_fit.json').write_text(json.dumps(dict(step_s=dt,pitch_table=table,rows=allrows),indent=2))
