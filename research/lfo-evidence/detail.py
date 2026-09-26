import pathlib,json,subprocess,numpy as np
from scipy.signal import hilbert
from scipy.ndimage import median_filter
D=pathlib.Path(__file__).resolve().parent
R=D/'core/independent-opm/research/periodic'
ov=json.loads((R/'overview.json').read_text());am=json.loads((R/'am_fixed.json').read_text());pm=json.loads((R/'pm_endpoint127.json').read_text());out=[]
for v in ov[:5]:
 name=v['name'];k=name[:2];ss=[s for s in json.loads((R/'stimulus/schedule'/f'{name}.json').read_text()) if s['analyze']];s=ss[-1];a=v['offset']+v['scale']*s['start_s'];p=next((D/'input').glob(k+'*.flac'));start=a-.5
 arrays=[];times=[]
 for block in range(int(a//4)*4,int((a+6)//4)*4+1,4):
  lo=max(0,block-.5)
  b=subprocess.check_output(['ffmpeg','-v','error','-ss',str(lo),'-i',str(p),'-t',str(block+4.5-lo),'-f','f32le','-'])
  x=np.frombuffer(b,np.float32).reshape(-1,2).astype(float);z=hilbert(x,axis=0);ph=np.unwrap(np.angle(z),axis=0);hz=np.gradient(ph,axis=0)*96000/(2*np.pi)
  begin=int((block-lo)*96000);end=begin+384000
  aa=abs(z[begin:end]).reshape(-1,96,2).mean(1);ff=hz[begin:end].reshape(-1,96,2).mean(1)
  arrays.append(np.stack([aa,ff],axis=2));times.append(block+(np.arange(len(aa))+.5)/1000-a)
 ar=np.concatenate(arrays);aa=ar[:,:,0];ff=ar[:,:,1];t=np.concatenate(times)
 if int(k)<40:
  row=next(r for r in am['rows'] if r['file']==k and r['amd']==127);i=np.floor((t-row['offset_s'])/am['step_s']).astype(int)%256;w=255-i if k=='37' else np.where(i<128,255,0) if k=='38' else np.where(i<128,255-2*i,2*i-256);pred=w*127//128*am['unit_db'];y=-20*np.log10(aa[:,0]/aa[:,1]);unit='dB'
 else:
  row=next(r for r in pm['rows'] if r['file']==k and r['index']==127);i=np.floor((t-row['offset_s'])/pm['step_s']).astype(int)%256
  w=np.where(i<128,i,i-255) if k=='40' else np.select([i<64,i<128,i<192],[2*i,255-2*i,256-2*i],default=2*i-511)
  q=np.sign(w)*(abs(w)*127//128)*4;pred=np.array([pm['pitch_table'].get(str(int(a)),np.nan)for a in q]);y=median_filter(1200*np.log2(ff[:,0]/ff[:,1]),5);unit='cent'
 f=(t-row['offset_s'])/am['step_s'];m=(t>.05)&(t<5.9)&np.isfinite(y)&np.isfinite(pred);ids=np.where(m)[0][::3]
 out.append(dict(name=p.name,unit=unit,start=a,condition='AMD=127, AMS=1' if int(k)<40 else 'PMD=127, PMS=7',data=np.round(np.c_[t[ids],y[ids],pred[ids]],6).tolist(),boundary_exclusion_s=.004))
(D/'data/details.json').write_text(json.dumps(out));print('detail plots:',len(out))
