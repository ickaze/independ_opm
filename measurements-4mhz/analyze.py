import numpy as np
from scipy.io import wavfile
from scipy.optimize import minimize_scalar
import json, argparse
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument("input_dir",type=Path);parser.add_argument("--output",type=Path,default=Path("metrics.json"));args=parser.parse_args()
results={}
for name in ['01SOLO','02LIVE','03CHSCAN']:
 fs,x=wavfile.read(args.input_dir/(name+'.wav')); x=x.astype(float)/2147483648
 hop=960; rms=np.array([np.sqrt(np.mean(v*v)) for v in np.array_split(x[:len(x)//hop*hop],len(x)//hop)])
 active=rms>max(rms)*.012
 # bridge gaps < .1sec
 for i in range(1,len(active)-10):
  if active[i-1] and not active[i] and np.any(active[i:i+10]): active[i:i+np.argmax(active[i:i+10])]=True
 edges=np.diff(np.r_[False,active,False].astype(int)); spans=[(a*.01,b*.01) for a,b in zip(np.where(edges==1)[0],np.where(edges==-1)[0]) if b-a>30]
 print(name,'peak',np.max(abs(x)), 'spans',spans)
 rows=[]
 if name=='02LIVE': spans=[(.15+i*4.194304,.15+(i+1)*4.194304) for i in range(7)]
 for a,b in spans:
  y=x[int((a+.15)*fs):int((b-.1)*fs)]
  if len(y)<100: continue
  # spectral least-squares delay; cross spectrum after taper, <15kHz
  rail_samples=int(np.sum(abs(y)>=.99999)); y=y-y.mean(axis=0); n=len(y); Y=np.fft.rfft(y*np.hanning(n)[:,None],axis=0); f=np.fft.rfftfreq(n,1/fs)
  use=(f>100)&(f<15000)&(abs(Y[:,0])>abs(Y[:,0]).max()*.025)
  l,r=Y[use,0],Y[use,1]; ff=f[use]
  def fit(t):
   q=l*np.exp(-2j*np.pi*ff*t); gain=np.vdot(q,r).real/np.vdot(q,q).real
   return np.sum(abs(r-gain*q)**2)/np.sum(abs(r)**2)
  opt=minimize_scalar(fit,bounds=(-50e-6,50e-6),method='bounded',options={'xatol':1e-13})
  row=dict(start=a,end=b,delay_us=opt.x*1e6,residual_rms=float(np.sqrt(opt.fun)),rail_samples=rail_samples)
  rows.append(row);print(row)
 results[name]=rows
json.dump(results,args.output.open('w'),indent=2)
