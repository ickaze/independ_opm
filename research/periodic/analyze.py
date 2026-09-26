# SPDX-License-Identifier: 0BSD
# Copyright (C) 2026 by I.C.KaZe
from pathlib import Path
import json,numpy as np
from scipy.ndimage import median_filter
from scipy.signal import find_peaks
R=Path(__file__).resolve().parent
S=R/'stimulus/schedule'
names=['37AMSAW','38AMSQR','39AMTRI','40PMSAW','41PMTRI','42STATE']
def load(name):
 z=np.load(R/(name[:2]+'.npz'));l=z['left'];r=z['right'];t=(np.arange(len(l))+.5)/1000
 on=r[:,0]>.02;d=np.diff(np.r_[False,on,False].astype(int));runs=list(zip(np.where(d==1)[0],np.where(d==-1)[0]));a,b=max(runs,key=lambda v:v[1]-v[0]);a/=1000;b/=1000
 ss=[s for s in json.loads((S/(name+'.json')).read_text()) if s['analyze']]
 scale=(b-a)/(ss[-1]['end_s']-ss[0]['start_s']);offset=a-scale*ss[0]['start_s']
 db=-20*np.log10(np.maximum(l[:,0],1e-12)/np.maximum(r[:,0],1e-12));ct=1200*np.log2(np.maximum(l[:,1],1)/np.maximum(r[:,1],1))
 return dict(name=name,t=t,db=db,ct=ct,l=l,r=r,ss=ss,scale=scale,offset=offset,active=[a,b])
def section(v,s,margin=.03):
 a=v['offset']+v['scale']*s['start_s'];b=v['offset']+v['scale']*s['end_s'];idx=np.where((v['t']>a+margin)&(v['t']<b-margin))[0]
 return v['t'][idx]-a,v['db'][idx],v['ct'][idx]
if __name__=='__main__':
 out=[]
 for name in names:
  v=load(name);rows=[]
  for s in v['ss']:
   t,db,ct=section(v,s,margin=min(.03,(s['end_s']-s['start_s'])/5))
   rows.append(dict(label=s['label'],amd=s['amd'],pmd=s['pmd'],registers=s['registers'],db_quantiles=np.quantile(db,[.05,.5,.95]).tolist(),cents_quantiles=np.quantile(ct,[.05,.5,.95]).tolist()))
  out.append(dict(name=name,scale=v['scale'],offset=v['offset'],active=v['active'],sections=len(rows),results=rows))
 (R/'overview.json').write_text(json.dumps(out,indent=2))
