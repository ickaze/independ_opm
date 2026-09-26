from pathlib import Path
import json,numpy as np
from scipy.signal import periodogram,find_peaks
from scipy.ndimage import median_filter
R=Path(__file__).resolve().parent
F=json.loads((R/'frequency.json').read_text());cache={};out=[]
for row in F:
 if not row['full']:continue
 k=row['file']
 if k not in cache:cache[k]=dict(np.load(R/(k+'.npz')))
 z=cache[k];lo=max(0,int((row['a']+.15)*1000));hi=int((row['b']-.15)*1000)
 db=-20*np.log10(np.maximum(z['left'][lo:hi,0],1e-8)/np.maximum(z['right'][lo:hi,0],1e-8));db=median_filter(np.clip(db,-1,26),size=3)
 if int(k)<=24:
  amp=z["left"][lo:hi,0];ff,pp=periodogram(amp,1000,nfft=131072);good=(ff>.05)&(ff<100);f=ff[good][np.argmax(pp[good])]
  peaks,_=find_peaks(abs(np.diff(amp)),height=.005,distance=max(3,int(750/f)))
  if len(peaks)>=3:
   cyc=np.r_[0,np.cumsum(np.maximum(1,np.rint(np.diff(peaks)*f/1000)))];fit=np.polyfit(cyc,peaks/1000,1);res=peaks/1000-np.polyval(fit,cyc)
   row.update(refined_period_s=float(fit[0]),timing_rms_ms=float(np.std(res)*1000),n_edges=len(peaks))
  elif len(peaks)==2:row.update(refined_period_s=float(np.diff(peaks)[0]/1000),n_edges=2)
 out.append(row)
(R/'frequency_refined.json').write_text(json.dumps(out,indent=2))
# Fit a register law to high-range periods, validate on odd low nibbles.
g=[v for v in out if 'refined_period_s' in v];train=[v for v in g if v['frequency']%2==0]
# Reciprocal frequency is approximately affine in low nibble after octave normalization.
x=np.array([v['frequency']%16 for v in train]);y=np.array([2**(15-v['frequency']//16)/v['refined_period_s'] for v in train]);coef=np.polyfit(x,y,1)
err=[]
for v in g:
 pred=2**(15-v['frequency']//16)/np.polyval(coef,v['frequency']%16)
 v['predicted_period_s']=float(pred);v['relative_error']=float(v['refined_period_s']/pred-1)
 if v['frequency']%2:err.append(v['relative_error'])
(R/'frequency_law.json').write_text(json.dumps(dict(normalized_rate_slope=float(coef[0]),intercept=float(coef[1]),train=len(train),test=len(err),test_rms_relative=float(np.sqrt(np.mean(np.array(err)**2))),test_max_relative=float(max(abs(np.array(err))))),indent=2))
(R/'frequency_refined.json').write_text(json.dumps(out,indent=2))
print('periods',len(g),'law',coef,'rms',np.sqrt(np.mean(np.array(err)**2)))
