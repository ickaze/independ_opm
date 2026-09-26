import pathlib,json,subprocess,hashlib,concurrent.futures
import numpy as np
D=pathlib.Path(__file__).resolve().parent

def run(p):
 rel=p.relative_to(D/'input').as_posix();out=D/'data'/(rel+'.json');out.parent.mkdir(parents=True,exist_ok=True)
 if out.exists():return p.name
 meta=json.loads(subprocess.check_output(['ffprobe','-v','quiet','-show_streams','-show_format','-of','json',str(p)]));s=meta['streams'][0];rate=int(s['sample_rate']);ch=int(s['channels'])
 proc=subprocess.Popen(['ffmpeg','-v','error','-i',str(p),'-f','f32le','-'],stdout=subprocess.PIPE)
 rows=[];t=0
 while True:
  b=proc.stdout.read(rate*ch*4)
  if not b:break
  a=np.frombuffer(b,np.float32).reshape(-1,ch)
  rows.append([t,*np.max(abs(a),axis=0).tolist(),*np.sqrt(np.mean(a*a,axis=0)).tolist()]);t+=len(a)/rate
 if proc.wait()!=0:raise RuntimeError(p)
 r=np.array(rows); threshold=max(1e-6,r[:,1:ch+1].max()*.2);active=np.where(r[:,1:ch+1].max(axis=1)>threshold)[0];at=float(active[min(3,len(active)-1)]) if len(active) else 0
 b=subprocess.check_output(['ffmpeg','-v','error','-ss',str(at),'-i',str(p),'-t','0.02','-f','f32le','-']);wave=np.frombuffer(b,np.float32).reshape(-1,ch)
 h=hashlib.sha256()
 with open(p,'rb')as f:
  while b:=f.read(8*1024*1024):h.update(b)
 obj=dict(name=rel,sha256=h.hexdigest(),bytes=p.stat().st_size,rate=rate,channels=ch,bits=s.get('bits_per_raw_sample',s.get('bits_per_sample')),duration=float(meta['format']['duration']),overview=np.round(r,7).tolist(),excerpt_s=at,wave=np.round(wave,7).tolist())
 out.write_text(json.dumps(obj,separators=(',',':')));print(p.name,flush=True);return p.name
if __name__=='__main__':
 files=sorted(list((D/'input').rglob('*.flac'))+list((D/'input').rglob('*.wav')))
 with concurrent.futures.ThreadPoolExecutor(max_workers=3)as ex:list(ex.map(run,files))
