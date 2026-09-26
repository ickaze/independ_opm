from pathlib import Path
import json,numpy as np
from scipy.signal import find_peaks,periodogram
from scipy.ndimage import median_filter,uniform_filter1d
R=Path(__file__).resolve().parent
M=json.loads(Path('lfo-independent-tests/manifest.json').read_text())['files']
summary=[]; depth=[];freqs=[];waves=[];states=[];cal=[];channels=[];joint=[]
for f in M:
 k=f['name'][:2];z=np.load(R/(k+'.npz'));l=z['left'];r=z['right'];N=len(l)
 ss=json.loads(Path('lfo-independent-tests/schedule',f['name']+'.json').read_text());ss=[s for s in ss if s['analyze']]
 on=np.flatnonzero((r[:,0]>.01)&(np.arange(N)>700))
 if not len(on):
  summary.append(dict(name=f["name"],recorded_s=N/1000,planned_s=f["seconds"],status="no test signal",peak=float(np.max(r[:,0]))));continue
 start=on[0]/1000;end=on[-1]/1000
 nominal0=ss[0]['start_s'];nominal1=ss[-1]['end_s'];truncated=int(k) in [25,26]
 scale=(end-start)/(nominal1-nominal0) if not truncated else .99988
 offset=start-scale*nominal0
 summary.append(dict(name=f['name'],recorded_s=N/1000,planned_s=f['seconds'],active_start=start,active_end=end,scale=scale,offset=offset,truncated=truncated))
 for s in ss:
  a=offset+scale*s['start_s'];b=offset+scale*s['end_s'];full=b<=N/1000-.1
  margin=min(.12,(b-a)*.18);lo=max(0,int((a+margin)*1000));hi=min(N,int((b-margin)*1000))
  if hi-lo<50:continue
  sl=l[lo:hi];sr=r[lo:hi]
  db=-20*np.log10(np.maximum(sl[:,0],1e-9)/np.maximum(sr[:,0],1e-9))
  ratio=np.maximum(sl[:,1],1e-9)/np.maximum(sr[:,1],1e-9);cents=1200*np.log2(ratio)
  base=dict(file=k,label=s['label'],a=a,b=b,full=full,db_low=float(np.quantile(db,.1)),db_high=float(np.quantile(db,.9)),db_median=float(np.median(db)),cents_low=float(np.quantile(cents,.1)),cents_high=float(np.quantile(cents,.9)),ref_hz=float(np.median(sr[:,1])))
  if k in ['15','16']:
   reg=s['registers'];base.update(amd=s['amd'],pmd=s['pmd'],ams=reg['38']&3,pms=reg['38']>>4);depth.append(base)
  if k=='13':cal.append(base)
  if k=='14' or k=='36':waves.append(base)
  if k=='33':states.append(base)
  if k=='34':channels.append(base)
  if k=='35':joint.append(base)
  if 17<=int(k)<=32:
   # Saw wraps, robust to small quantization steps; period via full wraps if present.
   peaks,_=find_peaks(-np.diff(db),height=8,distance=8)
   intervals=np.diff(peaks)/1000
   period=float(np.median(intervals)) if len(intervals)>1 else None
   base.update(frequency=s['registers']['18'],wraps=len(peaks),period_s=period,interval_cv=float(np.std(intervals)/np.mean(intervals)) if len(intervals)>1 else None)
   # For slow runs detect quantized amplitude transitions, excluding ramps/noisy edges.
   if int(k)>=25:
    smooth=median_filter(db,size=3);d=abs(smooth[4:]-smooth[:-4]);pk,_=find_peaks(d,height=.055,distance=15)
    base.update(step_count=len(pk),step_median_s=float(np.median(np.diff(pk))/1000) if len(pk)>2 else None)
   freqs.append(base)
for name,data in [('alignment',summary),('depth',depth),('frequency',freqs),('waveforms',waves),('state',states),('calibration',cal),('channels',channels),('joint',joint)]:
 (R/(name+'.json')).write_text(json.dumps(data,indent=2,default=lambda x:x.item()))
print('aligned',len(summary),'depth',len(depth),'frequency',len(freqs))
