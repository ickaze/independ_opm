from pathlib import Path
import numpy as np,json
from scipy.signal import find_peaks
from scipy.ndimage import median_filter
R=Path(__file__).resolve().parent
rows=[];files=[]
for key,first,n,seconds in [('25R1',6,4,180),('25R2',10,4,180),('25R3',14,2,180)]:
 z=dict(np.load(R/(key+'.npz')));l=z['left'];r=z['right'];on=r[:,0]>.01;d=np.diff(np.r_[False,on,False].astype(int));starts=np.flatnonzero(d==1);ends=np.flatnonzero(d==-1);i=np.argmax(ends-starts);start=starts[i]/1000;end=ends[i]/1000
 nominal=np.ceil(seconds/.008192)*.008192
 scale=(end-start)/(n*nominal) if key!='25new' else 1.0
 files.append(dict(file=key,seconds=len(l)/1000,active_start=start,active_end=end,scale=scale))
 for j in range(n):
  a=start+j*nominal*scale;b=a+nominal*scale
  if a>end:continue
  full=b<=end+.05;bclip=min(b,end)-.15;lo=int((a+.15)*1000);hi=int(bclip*1000)
  if hi-lo<100:continue
  db=-20*np.log10(np.maximum(l[lo:hi,0],1e-8)/np.maximum(r[lo:hi,0],1e-8));db=median_filter(db,size=11)
  pk,_=find_peaks(abs(db[20:]-db[:-20]),height=.045,distance=200)
  times=[];jumps=[]
  for p in pk:
   if p<100 or p+120>=len(db):continue
   jump=float(np.median(db[p+50:p+100])-np.median(db[p-80:p-30]))
   if .04<abs(jump)<.4:times.append((lo+p+10)/1000);jumps.append(abs(jump))
  period=float(np.median(np.diff(times))) if len(times)>2 else None
  rows.append(dict(file=key,frequency=first+j,full=full,start=a,end=bclip,step_count=len(times),step_period_s=period,jumps_db=jumps,times=times))
# Infer the two jump clusters from recordings, not emulator values.
allj=np.array([j for row in rows for j in row['jumps_db']]);q=float(np.median(allj[allj<.14]))
for row in rows:
 bits=np.array(row['jumps_db'])>1.5*q
 row['double_steps']=int(sum(bits));row['mean_increment']=float(1+np.mean(bits));row['quantum_db']=q
(R/'results.json').write_text(json.dumps(dict(files=files,quantum_db=q,sections=rows),indent=2,default=lambda v:v.item()))
for row in rows:print(hex(row['frequency']),row['full'],row['step_count'],row['step_period_s'],round(row['mean_increment'],4))
