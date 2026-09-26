# SPDX-License-Identifier: 0BSD
# Copyright (C) 2026 by I.C.KaZe
from analyze import *
from scipy.optimize import minimize_scalar
# Fit acoustic dB/unit only from even-depth square plateaus; not emulator output.
v=load('38AMSQR');sq=[]
for s in v['ss']:
 t,d,c=section(v,s);sq.append(np.median(d[d>np.median(d)-.01]))
D=np.arange(128);train=(D>0)&(D%2==0);q=2*D-1
unit=float(np.dot(q[train],np.array(sq)[train])/np.dot(q[train],q[train]))
print('unit',unit,flush=True)
# Estimate lattice spacing from measured high-depth saw step locations.
v=load('37AMSAW');t,d,c=section(v,v['ss'][-1]);sm=median_filter(d,3);pk,_=find_peaks(abs(sm[3:]-sm[:-3]),height=.06,distance=10)
p=pk[(t[pk]>.05)&(t[pk]<2)];delta=float(np.polyfit(np.arange(len(p)),t[p],1)[0]);print('delta',delta,flush=True)
# Refine spacing from all detected edges with integer gap counts, removing wraps.
pt=t[pk];nn=np.r_[0,np.cumsum(np.rint(np.diff(pt)/delta).astype(int))];delta=float(np.polyfit(nn,pt,1)[0]);print('delta refined',delta,flush=True)
def wave(i,k,variant):
 i=i%256
 if k=='37':return 255-i
 if k=='38':return np.where(i<128,255,0)
 if variant==0:return np.where(i<128,255-2*i,2*i-256)
 if variant==1:return np.abs(255-2*i)
 if variant==2:return np.abs(256-2*i).clip(0,255)
 return np.where(i<128,254-2*i,2*i-256)
rows=[];variants=[]
for name in names[:3]:
 v=load(name);k=name[:2]
 for s in v['ss']:
  amd=s['amd'];t,d,c=section(v,s);fit=t<4.05
  # Nuisance time alignment fitted on first cycle only; evaluate remainder separately.
  best=None
  for variant in (range(4) if k=='39' else [0]):
   for rounding,bias in [('floor',0),('nearest',64),('ceil',127)]:
    for off in np.arange(-.060,.061,.0005):
     f=(t-off)/delta;i=np.floor(f).astype(int);mask=fit&(np.minimum(f%1,1-f%1)*delta>.004)
     pred=((wave(i,k,variant)*amd+bias)//128)*unit
     loss=float(np.median(abs(d[mask]-pred[mask]))) if mask.any() else 1e9
     if best is None or loss<best[0]:best=(loss,variant,rounding,bias,off)
  loss,var,rounding,bias,off=best
  f=(t-off)/delta;i=np.floor(f).astype(int);stable=np.minimum(f%1,1-f%1)*delta>.004
  pred=((wave(i,k,var)*amd+bias)//128)*unit
  test=stable&(t>4.3)&(t<5.9)
  e=d[test]-pred[test]
  rows.append(dict(file=k,amd=amd,variant=var,rounding=rounding,offset_s=float(off),train_median_db=loss,test_n=int(test.sum()),test_rms_db=float(np.sqrt(np.mean(e*e))),test_median_abs_db=float(np.median(abs(e))),test_q95_db=float(np.quantile(abs(e),.95)),test_wrong_unit=int(np.sum(abs(e)>unit*.5))))
 print(name,'done',flush=True)
(R/'am_fit.json').write_text(json.dumps(dict(unit_db=unit,step_s=delta,period_s=256*delta,rows=rows),indent=2))
