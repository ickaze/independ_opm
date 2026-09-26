# SPDX-License-Identifier: 0BSD
# Copyright (C) 2026 by I.C.KaZe
from pathlib import Path
import subprocess,json,hashlib
import numpy as np
from scipy.signal import hilbert
R=Path(__file__).resolve().parent
U=R.parent/'upload'
files=['37AMSAW.flac','38AMSQR.flac','39AMTRI.flac','40PMSAW.flac','41PMTRI.flac','42STATE.flac']
meta=[]
for name in files:
 f=U/name;k=name[:2]
 info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(f)]))
 h=hashlib.sha256()
 with f.open('rb') as inp:
  for b in iter(lambda:inp.read(8*1024*1024),b''):h.update(b)
 meta.append(dict(file=name,sha256=h.hexdigest(),bytes=f.stat().st_size,stream=info['streams'][0],format=info['format']))
 if (R/(k+'.npz')).exists():continue
 # Retain native 96 kHz; process overlapped FFT analytic signal in 4-second blocks.
 tmp=R/(k+'.f32')
 subprocess.run(['ffmpeg','-y','-v','error','-i',str(f),'-f','f32le',str(tmp)],check=True)
 x=np.memmap(tmp,dtype='float32',mode='r').reshape(-1,2);N=len(x)//96*96
 out=[]
 for a in range(0,N,384000):
  b=min(a+384000,N);lo=max(0,a-48000);hi=min(N,b+48000)
  z=hilbert(x[lo:hi].astype('float64'),axis=0)
  amp=abs(z[a-lo:b-lo]); ph=np.unwrap(np.angle(z),axis=0)
  # Mean native analytic phase derivative per 1 ms; transitions are rejected later.
  hz=np.gradient(ph,axis=0)*96000/(2*np.pi);hz=hz[a-lo:b-lo]
  out.append(np.stack([amp.reshape(-1,96,2).mean(1),hz.reshape(-1,96,2).mean(1)],axis=2))
 y=np.concatenate(out)
 np.savez_compressed(R/(k+'.npz'),left=y[:,0],right=y[:,1],rate=1000)
 del x;tmp.unlink();print(name,len(y)/1000,flush=True)
(R/'inputs.json').write_text(json.dumps(meta,indent=2))
