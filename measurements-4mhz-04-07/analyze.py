import numpy as np,json,csv
from scipy.io import wavfile
from scipy.optimize import minimize_scalar
from pathlib import Path
import argparse
p=argparse.ArgumentParser();p.add_argument("input_dir",type=Path);p.add_argument("--output",type=Path,default=Path("metrics.json"));args=p.parse_args()
ROOT=Path(__file__).resolve().parents[1]
out={}
for name in ['04PITCH','05SINE','06PAIR','07LOAD']:
 fs,raw=wavfile.read(args.input_dir/(name+'.wav'));x=raw.astype(float)/2147483648
 hop=960;n=len(x)//hop;rms=np.sqrt(np.mean(x[:n*hop].reshape(n,hop,2)**2,axis=(1,2)));act=rms>rms.max()*.01
 for i in range(1,len(act)-10):
  if act[i-1] and not act[i] and np.any(act[i:i+10]):act[i:i+np.argmax(act[i:i+10])]=True
 e=np.diff(np.r_[False,act,False].astype(int));spans=[(a*.01,b*.01) for a,b in zip(np.where(e==1)[0],np.where(e==-1)[0]) if b-a>30]
 schedule=list(csv.DictReader(open(ROOT/'hardware-tests'/'schedule'/(name+'.csv'),encoding='utf-8-sig')))
 print(name,fs,len(x)/fs,'spans',len(spans),'schedule',len(schedule))
 if name=='07LOAD':
  start=spans[0][0];spans=[(start+i*4.194304,start+(i+1)*4.194304) for i in range(4)]
 assert len(spans)==len(schedule), (name,len(spans),len(schedule))
 rows=[]
 for (a,b),meta in zip(spans,schedule):
  y=x[int((a+.2)*fs):int((b-.2)*fs)].copy();y-=y.mean(axis=0);N=len(y);Y=np.fft.rfft(y*np.hanning(N)[:,None],axis=0);f=np.fft.rfftfreq(N,1/fs)
  u=(f>80)&(f<15000)&(abs(Y[:,0])>abs(Y[:,0]).max()*.025);l,r=Y[u,0],Y[u,1];ff=f[u]
  def err(t):
   q=l*np.exp(-2j*np.pi*ff*t);g=np.vdot(q,r).real/np.vdot(q,q).real;return np.sum(abs(r-g*q)**2)/np.sum(abs(r)**2)
  opt=minimize_scalar(err,bounds=(-50e-6,50e-6),method='bounded',options={'xatol':1e-13})
  row=dict(meta,start=a,end=b,delay_us=opt.x*1e6,residual=float(np.sqrt(opt.fun)));rows.append(row)
  print(meta['channel'],meta['kc'],meta['audible'],round(opt.x*1e6,5),round(row['residual'],6))
 out[name]=rows
json.dump(out,args.output.open('w'),indent=2)
