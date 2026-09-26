# SPDX-License-Identifier: 0BSD
# Copyright (C) 2026 by I.C.KaZe
from analyze import *
z=json.loads((R/'am_fit.json').read_text());unit=z['unit_db'];dt=z['step_s'];rows=[]
for name in names[:3]:
 v=load(name);k=name[:2]
 for s in v['ss']:
  t,d,c=section(v,s);D=s['amd'];best=None
  for off in np.arange(-.06,.061,.00025):
   f=(t-off)/dt;i=np.floor(f).astype(int)%256
   w=255-i if k=='37' else np.where(i<128,255,0) if k=='38' else np.where(i<128,255-2*i,2*i-256)
   pred=(w*D//128)*unit;stable=np.minimum(f%1,1-f%1)*dt>.004
   m=stable&(t<4.05);loss=np.mean(np.minimum(abs(d[m]-pred[m]),unit*2))
   if best is None or loss<best[0]:best=(loss,off,pred,stable,i)
  loss,off,pred,stable,i=best;m=stable&(t>4.3)&(t<5.9);e=d[m]-pred[m]
  rows.append(dict(file=k,amd=D,offset_s=float(off),train_clipped_mean_abs_db=float(loss),test_n=int(m.sum()),test_rms_db=float(np.sqrt(np.mean(e*e))),test_max_abs_db=float(max(abs(e))),test_wrong_unit=int(np.sum(abs(e)>unit/2))))
 print(name,flush=True)
(R/'am_fixed.json').write_text(json.dumps(dict(unit_db=unit,step_s=dt,rows=rows),indent=2))
