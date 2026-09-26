# SPDX-License-Identifier: 0BSD
# Copyright (C) 2026 by I.C.KaZe
from analyze import *
import subprocess
from scipy.optimize import minimize_scalar
az=json.loads((R/'am_fixed.json').read_text());pz=json.loads((R/'pm_endpoint127.json').read_text());dt=az['step_s'];out=[]
for name,idxs in [('37AMSAW',[1,32,64,127]),('39AMTRI',[1,32,64,127]),('41PMTRI',[17,31,113,127])]:
 v=load(name);k=name[:2];fname={'37':'37AMSAW.flac','39':'39AMTRI.flac','41':'41PMTRI.flac'}[k]
 for idx in idxs:
  s=v['ss'][idx];row=next(r for r in (az['rows'] if k!='41' else pz['rows']) if r['file']==k and (r.get('amd')==idx if k!='41' else r.get('index')==idx));off=row['offset_s']
  for nominal in [.5,1.5,3.0]:
   local=off+(round((nominal-off)/dt-.5)+.5)*dt;at=v['offset']+v['scale']*s['start_s']+local
   raw=subprocess.check_output(['ffmpeg','-v','error','-ss',str(at-.004),'-i',str(R.parent/'upload'/fname),'-t','0.008','-f','f32le','-'])
   x=np.frombuffer(raw,np.float32).reshape(-1,2).astype(float);t=np.arange(len(x))/96000
   m=(v['t']>at-.004)&(v['t']<at+.004);ans=[]
   for ch,a in enumerate([v['l'],v['r']]):
    f0=float(np.median(a[m,1]));y=x[:,ch]
    def fit(f,ret=False):
     ph=2*np.pi*f*t;A=np.column_stack([np.ones(len(t))]+[fun(h*ph) for h in [1,2,3] for fun in [np.sin,np.cos]])
     coef=np.linalg.lstsq(A,y,rcond=None)[0];err=np.mean((A@coef-y)**2)
     return (np.hypot(coef[1],coef[2]),err) if ret else err
    opt=minimize_scalar(fit,bounds=(f0-5,f0+5),method='bounded',options={'xatol':1e-7});amp,res=fit(opt.x,True);ans.append((amp,opt.x,res))
   db=-20*np.log10(ans[0][0]/ans[1][0]);ct=1200*np.log2(ans[0][1]/ans[1][1]);adb=float(np.median(v['db'][m]));act=float(np.median(v['ct'][m]))
   out.append(dict(file=k,index=idx,time_s=at,native_db=float(db),analytic_db=adb,delta_db=float(db-adb),native_cents=float(ct),analytic_cents=act,delta_cents=float(ct-act),fit_residual=[a[2] for a in ans]))
 print(name,flush=True)
(R/'native_check.json').write_text(json.dumps(out,indent=2))
