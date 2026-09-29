from pathlib import Path
import subprocess,numpy as np,json
R=Path(__file__).resolve().parent
for name in ['43NOISE','44NROUTE','45NMOD','46NSTATE']:
 p=Path('upload')/(name+'.flac')
 raw=R/(name+'.f32')
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(p),'-f','f32le',str(raw)],check=True)
 a=np.memmap(raw,dtype='<f4',mode='r').reshape(-1,2)
 n=len(a)//960
 rms=np.sqrt(np.mean(np.asarray(a[:n*960]).reshape(n,960,2).astype('float64')**2,axis=1))
 np.save(R/(name+'_rms.npy'),rms)
 active=np.max(rms,axis=1)>0.0001
 edges=np.diff(np.r_[False,active,False].astype(int))
 runs=list(zip(np.where(edges==1)[0]/100,np.where(edges==-1)[0]/100))
 print(p.stem,'peak',np.max(np.abs(a)),'first',runs[:12],'last',runs[-12:],flush=True)
