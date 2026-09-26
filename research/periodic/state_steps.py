# SPDX-License-Identifier: 0BSD
# Copyright (C) 2026 by I.C.KaZe
from analyze import *
v=load('42STATE');rows=[]
rev=np.array([int(f'{i:04b}'[::-1],2) for i in range(16)])
for j in range(0,len(v['ss']),4):
 s=v['ss'][j];t,d,c=section(v,s);sm=median_filter(d,3);pk,_=find_peaks(abs(sm[3:]-sm[:-3]),height=.055,distance=9)
 pk=pk[(pk>8)&(pk<len(d)-9)];changes=np.array([np.median(d[p-7:p-3])-np.median(d[p+4:p+8]) for p in pk]);valid=(changes>.045)&(changes<.25)
 # Only uninterrupted interior runs are used: no gap concatenation.
 if not valid.all() or len(changes)<40:rows.append(dict(label=s['label'],status='excluded incomplete step train',steps=len(changes)));continue
 bits=(changes>.14).astype(int);L=s['registers']['18']%16;n=np.arange(len(bits));train=min(16,len(n))
 errs=[]
 for model in ['reverse4','accumulate']:
  preds=[((rev[(n+p)%16]<L).astype(int) if model=='reverse4' else (((n+1)*L+p)//16-(n*L+p)//16)) for p in range(16)]
  pp=int(np.argmin([sum(a[:train]!=bits[:train]) for a in preds]));pred=preds[pp]
  errs.append(dict(model=model,phase=pp,train_wrong=int(sum(pred[:train]!=bits[:train])),test_wrong=int(sum(pred[train:]!=bits[train:])),test_n=len(bits)-train))
 rows.append(dict(label=s['label'],frequency=s['registers']['18'],status='used',steps=len(bits),times=t[pk].tolist(),changes_db=changes.tolist(),models=errs))
(R/'state_steps.json').write_text(json.dumps(rows,indent=2))
for model in ['reverse4','accumulate']:
 a=[p for r in rows if r['status']=='used' for p in r['models'] if p['model']==model];print(model,len(a),sum(p['train_wrong'] for p in a),sum(p['test_wrong'] for p in a),sum(p['test_n'] for p in a))
