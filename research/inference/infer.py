"""SPDX-License-Identifier: 0BSD
Copyright (C) 2026 by I.C.KaZe
Infer binary linear recurrence degree and coefficients without a preset order.
Input: measured attenuation and measured noise signs, not an emulator sequence.
"""
from pathlib import Path
import json,numpy as np
R=Path(__file__).resolve().parent
TRAIN=512

def bm(bits):
    C=B=1;L=0;m=1;history=0
    for n,b in enumerate(bits):
        history=(history<<1)|int(b)
        discrepancy=(C&history).bit_count()&1
        if discrepancy:
            previous=C;C^=B<<m
            if 2*L<=n:L=n+1-L;B=previous;m=1
            else:m+=1
        else:m+=1
    return L,[i for i in range(1,L+1) if (C>>i)&1]

def predict(bits,lags,train,indices=None):
    if indices is None:indices=np.arange(len(bits))
    pred=list(map(int,bits[:train]))
    for i in range(train,int(indices[-1])+1):
        b=0
        for lag in lags:b^=pred[i-lag]
        pred.append(b)
    wrong=np.flatnonzero(np.array(pred)[indices[train:]]!=bits[train:])
    return dict(test_bits=len(bits)-train,errors=len(wrong),first_error=None if not len(wrong) else int(train+wrong[0]))

def main():
    # Only the training attenuation values determine threshold/polarity/order.
    record=np.load(R/'data/long.npz');levels=record['db'];times=record['times'];period=float(np.median(np.diff(times[:TRAIN])));indices=np.rint((times-times[0])/period).astype(int);assert np.array_equal(indices[:TRAIN],np.arange(TRAIN));a=np.sort(levels[:TRAIN]);thresholds=(a[:-1]+a[1:])/2
    thresholds=thresholds[(thresholds>=np.quantile(a,.25))&(thresholds<=np.quantile(a,.75))]
    fits=[]
    for threshold in thresholds:
        for polarity in [0,1]:
            bits=((levels[:TRAIN]<threshold).astype(np.uint8)^polarity)
            degree,lags=bm(bits)
            fits.append((degree,len(lags),float(threshold),polarity,lags))
    degree,_,threshold,polarity,lags=min(fits,key=lambda x:(x[0],x[1],x[2],x[3]))
    bits=(levels<threshold).astype(np.uint8)^polarity
    result=dict(train=TRAIN,threshold_db=threshold,polarity=polarity,degree=degree,lags=lags,threshold_candidates=len(thresholds),period_s=period,missing_updates=int(indices[-1]+1-len(indices)),validation=predict(bits,lags,TRAIN,indices))
    noises=[]
    for f in sorted((R/'data').glob('noise_*.npz')):
        b=np.load(f)['bits'].astype(np.uint8);d,t=bm(b[:TRAIN]);noises.append(dict(file=f.name,degree=d,lags=t,validation=predict(b,t,TRAIN)))
    result['noise']=noises
    (R/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
