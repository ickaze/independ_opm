from pathlib import Path
import subprocess,json,numpy as np
from scipy.signal import hilbert,resample_poly
R=Path(__file__).resolve().parent
rows=[]
for f in sorted(Path('upload').glob('25R*.flac')):
 meta=json.loads(subprocess.check_output(['ffprobe','-v','quiet','-show_streams','-of','json',str(f)]))['streams'][0]
 row=dict(file=str(f),rate=int(meta['sample_rate']),channels=meta['channels'],bits=meta.get('bits_per_raw_sample'),duration=float(meta['duration']))
 rows.append(row)
 if (R/(f.name[:4]+'.npz')).exists():continue
 # Anti-aliased host decimation. Audio remains stereo; extract each analytic channel.
 raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(f),'-f','f32le','-ar','12000','-'])
 x=np.frombuffer(raw,np.float32).reshape(-1,2);out=[]
 for ch in range(2):
  # Block overlap avoids FFT boundary contamination; discard 0.25s on both edges.
  chunks=[]
  for a in range(0,len(x),12000*20):
   b=min(a+12000*20,len(x));lo=max(0,a-3000);hi=min(len(x),b+3000)
   z=hilbert(x[lo:hi,ch]);amp=abs(z);freq=np.angle(z[1:]*z[:-1].conj())*12000/(2*np.pi);freq=np.r_[freq,freq[-1]]
   amp=amp[a-lo:b-lo];freq=freq[a-lo:b-lo]
   chunks.append(np.column_stack([resample_poly(amp,1,12),resample_poly(freq,1,12)]))
  out.append(np.concatenate(chunks))
 np.savez_compressed(R/(f.name[:4]+'.npz'),left=out[0],right=out[1],rate=1000)
 print(f.name,row['duration'],flush=True)
(R/'inputs.json').write_text(json.dumps(rows,indent=2))
