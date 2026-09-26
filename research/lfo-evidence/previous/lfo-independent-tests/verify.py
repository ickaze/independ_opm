"""Decode the deliverable MDX independently and check traces, schedules and intent."""
from pathlib import Path
import struct,json,hashlib
R=Path(__file__).resolve().parent
manifest=json.loads((R/'manifest.json').read_text())
for item in manifest['files']:
 name=item['name'];data=(R/'mdx'/(name+'.MDX')).read_bytes()
 assert hashlib.sha256(data).hexdigest()==item['sha256']
 start=data.index(b'\x0d\x0a\x1a')+3;end=data.index(0,start);assert end==start
 body=data[end+1:];offsets=struct.unpack('>10H',body[:20]);voice=offsets[0]
 assert len(body)-voice==27 and len(body[voice:])==27
 assert all(body[i:i+2]==b'\xf1\x00' for i in offsets[1:9])
 pos=offsets[9];ticks=0;events=[];tempos=[]
 while pos<voice:
  op=body[pos];pos+=1
  if op<128:ticks+=op+1
  elif op==0xff:tempos.append(body[pos]);pos+=1
  elif op==0xfe:
   a,v=body[pos:pos+2];events.append((ticks,a,v));pos+=2
  elif op==0xf1:
   assert body[pos]==0;pos+=1;break
  else:raise AssertionError((name,pos,op))
 assert pos==voice and tempos==[224] and ticks==item['ticks']
 expected=[]
 for line in (R/'traces'/(name+'.trace')).read_text().splitlines():
  if line.startswith('#'):continue
  clock,a,v=[int(s,0) for s in line.split()];assert clock%32768==0
  expected.append((clock//32768,a,v))
 assert events==expected
 sections=json.loads((R/'schedule'/(name+'.json')).read_text())
 assert sections[0]['start_tick']==0 and sections[-1]['end_tick']==ticks
 assert all(x['end_tick']==y['start_tick'] for x,y in zip(sections,sections[1:]))
 assert all(a not in [0x10,0x11,0x12,0x14] for _,a,_ in events),'do not overwrite driver timers'
 # All audible diagnostic operators sustain indefinitely; all key events use M1 or C2.
 for tick,a,v in events:
  if a==8:assert v&0x78 in [0,8,16,32,64,120]
  if 0x80<=a<0xa0:assert v==31
  if 0xa0<=a<0xc0:assert v in [0,128]
  if 0xc0<=a<0xe0:assert v==0
 for s in sections:
  if not s['analyze']:continue
  keys=s['key_masks'];assert sum(bool(x) for x in keys)<=2
  if name in ['01AMLOW','02AMFRQ','03AMDEP','04RESET','08LONG']:assert s['pmd']==0
  if name=='05NOISE':assert s['amd']==s['pmd']==0 and keys[7]==64
 if name in ['01AMLOW','08LONG']:
  s=next(s for s in sections if s['analyze'])
  assert not any(s['start_tick']<t<s['end_tick'] for t,a,v in events)
 # The terminal state must silence all channels and turn noise/depths off.
 final={};key=[0]*8
 for _,a,v in events:
  final[a]=v
  if a==8:key[v&7]=v&0x78
 assert not any(key) and all(final[0x20+c]==0 for c in range(8)) and final[0xf]==0
 print(name,'PASS',len(events),'writes',f'{ticks*32768/4000000:.3f}s')
print('PASS: all MDX streams, nominal traces, finite ends, schedules and measurement constraints')
