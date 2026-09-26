"""SPDX-License-Identifier: 0BSD
Copyright (C) 2026 by I.C.KaZe
Verify the compact composition against the degree/coefficients inferred from data.
"""
from pathlib import Path
import json
R=Path(__file__).resolve().parent
v=json.loads((R/'result.json').read_text());width=v['degree'];lags=v['lags'];mask=(1<<width)-1
# The emitted closed form is specialized to the measured result, not used to infer it.
assert width==17 and lags==[14,17], 'Re-derive the optimized expression for this measurement result'
def one(s):
 feedback=0
 for lag in lags:feedback^=(s>>(width-lag))&1
 return (s>>1)|(feedback<<(width-1))
def direct(s):
 q=s^(s>>3)
 return (s>>16)^(((q<<1)^(q<<15))&mask)
for s in range(mask+1):
 r=s
 for _ in range(16):r=one(r)
 assert r==direct(s)
s=1;period=0
while True:
 s=one(s);period+=1
 if s==1:break
 assert period<=mask and s!=0
r=dict(inferred_degree=width,inferred_lags=lags,verified_states=mask+1,model_period=period)
(R/'derivation.json').write_text(json.dumps(r,indent=2));print(r)
