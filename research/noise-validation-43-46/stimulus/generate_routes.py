# SPDX-License-Identifier: 0BSD
# Copyright (C) 2026 by I.C.KaZe
# Independent register stimuli; no expected synthesis algorithm embedded.
import mdx_writer as m
import json,hashlib
R=m.ROOT
items=[]
# Mask notation here is register/internal order M1,M2,C1,C2.
KEYBITS=[3,5,4,6]
def key(t,mask):t.w(8,7|sum(1<<KEYBITS[i] for i in range(4) if mask>>i&1))
def setup(t,alg,fb=0):
 t.w(8,7);t.w(0x27,7);t.section('algorithm gap',128,False)
 t.voice(7,3,0xc0,kc=0x48,tl=24)
 for op in range(4):
  t.w(0x47+8*op,[1,2,3,5][op]);t.w(0x67+8*op,24)
 t.w(0x27,0xc0|(fb<<3)|alg)
 t.w(0x0f,0);t.w(0x19,0);t.w(0x19,128);t.w(0x3f,0)
def sample(t,label,mask,noise,ticks=96):
 key(t,0);t.w(0x0f,(128|16) if noise else 0);key(t,mask)
 t.section(label+' settle',16,False)
 t.section(label,ticks)
def done(t,protocol):
 item=t.finish();p=R/'mdx'/f'{t.name}.MDX';b=p.read_bytes();i=b.index(b'\r\n\x1a')
 title=(t.name+' NOISE ROUTING TEST v1; 4MHz TB224; ch8 ALG0..7 stereo; '
 'mask order M1,M2,C1,C2; AR31 DR0 SR0 SL0 RR15 AM0 PM0 KC48 KF0; '
 'base TL24 MUL1,2,3,5 DT0; NFRQ16; sync8,8,24; alg gap128; '+protocol+
 '; Copyright (C) 2026 by I.C.KaZe; 0BSD')
 b=t.name.encode()+b[i:];p.write_bytes(b);item['sha256']=hashlib.sha256(b).hexdigest();items.append(item)
 for s in t.sections:
  if not s['analyze']:continue
  assert s['key_masks'][:7]==[0]*7
  assert s['amd']==s['pmd']==0
  r=s['registers'];assert r['3F']==0
  for op in range(4):
   assert r[f'{0x87+8*op:02X}']==31
   assert r[f'{0xa7+8*op:02X}']==0 and r[f'{0xc7+8*op:02X}']==0
 print(t.name,item['seconds'])
t=m.Test('44NROUTE','All algorithms, every nonzero operator key subset, noise off/on')
for alg in range(8):
 setup(t,alg)
 for mask in range(1,16):
  for noise in [0,1]:sample(t,f'ALG={alg} mask={mask:X} noise={noise} FB=0',mask,noise)
done(t,'each ALG: mask1..15 each noise0,1; rekey settle16 measure96 ticks')
t=m.Test('45NMOD','Upstream parameter changes with C2 on/off controls, noise off/on')
cases=[(24,1),(0,1),(64,1),(127,1),(24,4),(24,15)]
for alg in range(8):
 setup(t,alg)
 for op in range(3):
  for tl,mul in cases:
   for j in range(4):
    t.w(0x67+8*j,24);t.w(0x47+8*j,[1,2,3,5][j])
   t.w(0x67+8*op,tl);t.w(0x47+8*op,mul)
   for noise in [0,1]:
    for mask in [7,15]:sample(t,f'ALG={alg} upstream={op} TL={tl} MUL={mul} mask={mask:X} noise={noise}',mask,noise,64)
done(t,'each ALG upstream0..2 cases TL/MUL=24/1,0/1,64/1,127/1,24/4,24/15 each noise0,1 mask7,F; rekey settle16 measure64 ticks')
t=m.Test('46NSTATE','Feedback sweep with C2 controls and sustained noise/key transitions')
for alg in range(8):
 setup(t,alg)
 for fb in range(8):
  t.w(0x27,0xc0|(fb<<3)|alg)
  for noise in [0,1]:
   for mask in [7,15]:sample(t,f'ALG={alg} FB={fb} mask={mask:X} noise={noise}',mask,noise)
 # Continuous transitions: do not retrigger unchanged operators.
 t.w(0x27,0xc0|alg);t.w(0x0f,0);key(t,0);key(t,15)
 t.section(f'ALG={alg} continuous normal FM baseline',128)
 for nfrq in [0,16,31]:
  t.w(0x0f,128|nfrq);t.section(f'ALG={alg} noise ON NFRQ={nfrq} no rekey',128)
  key(t,7);t.section(f'ALG={alg} C2 key OFF NFRQ={nfrq}',128)
  key(t,15);t.section(f'ALG={alg} C2 key ON NFRQ={nfrq}',128)
  t.w(0x0f,0);t.section(f'ALG={alg} noise OFF NFRQ={nfrq} no rekey',128)
done(t,'each ALG FB0..7 each noise0,1 mask7,F settle16 measure96; then FB0 sustained FM128; for NFRQ0,16,31 noiseON,C2off,C2on,noiseOFF each128 ticks')
(R/'routes_manifest.json').write_text(json.dumps({'clock_hz':4000000,'files':items},indent=2))
# Use existing independent decoder, with expanded legal key masks.
source=(R/'verify.py').read_text().replace("R/'manifest.json'","R/'routes_manifest.json'")
source=source.replace('v&0x78 in [0,8,16,32,64,120]','v&0x78 in range(0,121,8)')
source=source.replace('sum(bool(x) for x in keys)<=2','sum(bool(x) for x in keys)<=1')
(R/'verify_routes.py').write_text(source)
