# SPDX-License-Identifier: 0BSD
# Copyright (C) 2026 by I.C.KaZe
import mdx_writer as m
import json
R=m.ROOT
for folder in ['mdx','schedule','traces']:(R/folder).mkdir(exist_ok=True)
t=m.Test('43NOISE','Noise amplitude: sine and noise TL sweeps; all NFRQ at TL0/32')
# All measurements use ch8 C2 alone, algorithm7, both outputs, no AM/PM.
t.voice(7,3,0xc0,kc=0x48,tl=0)
t.w(0x19,0);t.w(0x19,128);t.w(0x3f,0)
def silent(label):
 t.w(8,7);t.w(0x27,7);t.section(label,256,False)
for mode,nfrq in [('sine',0),('noise',0),('noise',31)]:
 silent('block gap before '+mode+' NFRQ='+str(nfrq))
 t.w(0x0f,(128|nfrq) if mode=='noise' else 0)
 t.w(0x7f,0);t.w(0x27,0xc7);t.key(7,3)
 t.section('settling '+mode+' NFRQ='+str(nfrq),128,False)
 for tl in range(128):
  t.w(0x7f,tl)
  t.section(f'{mode} NFRQ={nfrq} TL={tl} flat EG AM=PM=0',128)
for tl in [0,32]:
 silent('block gap before NFRQ sweep TL='+str(tl))
 t.w(0x0f,128);t.w(0x7f,tl);t.w(0x27,0xc7);t.key(7,3)
 t.section('settling NFRQ sweep',128,False)
 for nfrq in range(32):
  t.w(0x0f,128|nfrq)
  t.section(f'noise NFRQ={nfrq} TL={tl} flat EG AM=PM=0',256)
f=t.finish()
p=R/'mdx/43NOISE.MDX'
b=p.read_bytes();i=b.index(b'\r\n\x1a')
# Self-contained protocol retained inside the MDX title for later analysis.
title=('43NOISE NOISE LEVEL TEST v1; 4MHz; TB=224; ch8 C2 ALG7 stereo; '
       'AR31 DR0 SR0 SL0 RR15 MUL1 DT0 AM0 PM0 KC48 KF0; '
       'sync 8,8,24 ticks; block gap256 settle128; '
       'blocks: sine TL0..127, noise NFRQ0 TL0..127, noise NFRQ31 TL0..127 '
       '(128 ticks each); noise TL0 NFRQ0..31, noise TL32 NFRQ0..31 '
       '(256 ticks each); no PDX; Copyright (C) 2026 by I.C.KaZe; 0BSD')
b=t.name.encode('ascii')+b[i:];p.write_bytes(b)
import hashlib
f['sha256']=hashlib.sha256(b).hexdigest()
(R/'manifest.json').write_text(json.dumps({'clock_hz':4000000,'files':[f]},indent=2))
print(json.dumps(f,indent=2))
# Explicit measurement-state checks, independent of expected audio amplitude.
for s in t.sections:
 if not s['analyze']:continue
 assert s['key_masks']==[0]*7+[64]
 r=s['registers']
 assert r['27']==199 and r['3F']==0 and r['BF']==0 and r['DF']==0 and r['9F']==31
 assert s['amd']==s['pmd']==0
print('Measurement states PASS')
