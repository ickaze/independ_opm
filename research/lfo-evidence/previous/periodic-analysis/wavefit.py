from pathlib import Path
import json,numpy as np
from scipy.signal import periodogram
from scipy.optimize import minimize_scalar
R=Path(__file__).resolve().parent
rows=json.loads((R/'waveforms.json').read_text());cache={};out=[]
for row in rows:
 k=row['file']
 if k not in cache:cache[k]=dict(np.load(R/(k+'.npz')))
 z=cache[k];a=int((row['a']+.2)*1000);b=int((row['b']-.2)*1000);l=z['left'][a:b];r=z['right'][a:b]
 mode='PM' if 'mode=PM' in row['label'] else 'AM'
 y=1200*np.log2(np.maximum(l[:,1],1e-6)/np.maximum(r[:,1],1e-6)) if mode=='PM' else -20*np.log10(np.maximum(l[:,0],1e-7)/np.maximum(r[:,0],1e-7))
 y=np.clip(y,-200,200) if mode=='PM' else np.clip(y,-2,30)
 n=len(y);train=y[:n//2];f,p=periodogram(train,1000,nfft=65536);valid=(f>.1)&(f<100);peak=f[valid][np.argmax(p[valid])];p0=1/peak
 def obj(period):
  shift=period*1000;t=np.arange(len(train)-int(np.ceil(shift))-2)
  if len(t)<100:return 1e9
  delta=train[t]-np.interp(t+shift,np.arange(len(train)),train)
  return np.mean(np.minimum(delta*delta,100))
 fit=minimize_scalar(obj,bounds=(p0*.85,p0*1.15),method='bounded',options={'xatol':1e-7});period=float(fit.x)
 phase=(np.arange(n)/1000/period)%1;nb=128;bi=(phase*nb).astype(int)
 sums=np.bincount(bi[:n//2],weights=train,minlength=nb);counts=np.bincount(bi[:n//2],minlength=nb);template=sums/np.maximum(counts,1)
 pred=np.interp(phase[n//2:],np.r_[-.5/nb,(np.arange(nb)+.5)/nb,1+.5/nb],np.r_[template[-1],template,template[0]])
 err=y[n//2:]-pred
 out.append(dict(status='usable' if fit.fun<1e8 and len(train)/1000>=2*period else 'insufficient training cycles',file=k,label=row['label'],signal=mode,period_s=period,train_points=len(train),test_points=len(err),holdout_rms=float(np.sqrt(np.mean(err*err))),unit='cents' if mode=='PM' else 'dB',train_repeat_mse=float(fit.fun),template=template.tolist()))
(R/'waveform_fits.json').write_text(json.dumps(out,indent=2))
print('waveform fits',len(out))
