"""Raw-register MDX measurement suite. Standard-library only; no emulator core.
MDX format reference: https://w.atwiki.jp/mxdrv/pages/23.html
Nominal tick = 1024*(256-224) master clocks. CPU register-write latency excluded.
"""
from pathlib import Path
import csv,json,struct,hashlib
ROOT=Path(__file__).resolve().parent
CLOCK=4000000
TICK=32768
class Test:
 def __init__(self,name,purpose):
  self.name=name;self.purpose=purpose;self.tick=0;self.events=[];self.sections=[];self.regs={};self.amd=0;self.pmd=0;self.keys=[0]*8
  self.w(1,2);self.w(0x0f,0);self.w(0x19,0);self.w(0x19,128);self.w(0x1b,0);self.w(0x18,0x80)
  for ch in range(8):
   self.w(8,ch);self.w(0x20+ch,0);self.w(0x38+ch,0)
   for op in range(4):self.w(0x60+8*op+ch,127)
  self.section('startup silence',128,False)
  # Three pan-gated tones: 8,8,24 ticks; reference clock markers, not random reset.
  self.voice(0,0,0xc0,kc=0x48);self.key(0,0)
  for i,d in enumerate([8,8,24]):
   self.w(0x20,0xc7);self.section('sync tone '+str(i+1),d,False)
   self.w(0x20,7);self.section('sync gap '+str(i+1),8 if i<2 else 32,False)
  self.w(8,0);self.w(0x20,0);self.section('post marker silence',64,False)
 def w(self,a,v):
  assert 0<=a<256 and 0<=v<256
  self.events.append((self.tick,a,v));self.regs[a]=v
  if a==0x19:
   if v&128:self.pmd=v&127
   else:self.amd=v
  if a==8:self.keys[v&7]=v&0x78
 def key(self,ch,slot,on=True):
  assert slot in (0,3)
  self.w(8,((8 if slot==0 else 64) if on else 0)|ch)
 def voice(self,ch,slot,pan,kc=0x68,tl=24,ame=False):
  self.w(8,ch);self.w(0x20+ch,pan|7);self.w(0x28+ch,kc);self.w(0x30+ch,0);self.w(0x38+ch,1 if ame else 0)
  for op in range(4):
   o=8*op+ch
   for a,v in [(0x40,1),(0x60,tl if op==slot else 127),(0x80,31),(0xa0,128 if op==slot and ame else 0),(0xc0,0),(0xe0,15)]:self.w(a+o,v)
 def am_pair(self):
  self.voice(0,0,0x40,ame=True);self.voice(1,0,0x80)
  self.key(0,0);self.key(1,0);self.w(0x19,127);self.w(0x19,128)
 def lfo(self,f=0x80,w=3):
  self.w(0x18,f);self.w(0x1b,w);self.w(1,0)
 def section(self,label,ticks,analyze=True):
  assert ticks>0
  self.sections.append(dict(label=label,start_tick=self.tick,end_tick=self.tick+ticks,start_s=self.tick*TICK/CLOCK,end_s=(self.tick+ticks)*TICK/CLOCK,analyze=analyze,amd=self.amd,pmd=self.pmd,key_masks=list(self.keys),registers={f'{a:02X}':v for a,v in sorted(self.regs.items())}))
  self.tick+=ticks
 def finish(self):
  for ch in range(8):self.w(8,ch);self.w(0x20+ch,0)
  self.w(0x0f,0);self.w(0x19,0);self.w(0x19,128);self.w(1,0)
  self.section('tail silence',128,False)
  track=bytearray([0xff,224]);last=0
  def rest(n):
   while n:
    count=min(n,128);track.append(count-1);n-=count
  for tick,a,v in self.events:
   rest(tick-last);last=tick;track.extend([0xfe,a,v])
  rest(self.tick-last);track.extend([0xf1,0])
  # Unused but structurally valid 27-byte voice. FM tracks A-H terminate.
  voice=bytes([0,7,15]+[1]*4+[127]*4+[31]*4+[0]*4+[0]*4+[15]*4)
  offsets=[22+len(track)]+[20]*8+[22]
  assert offsets[0]<65536
  body=struct.pack('>10H',*offsets)+b'\xf1\x00'+track+voice
  blob=(self.name+' PERIODIC LFO TEST').encode()+b'\r\n\x1a\x00'+body
  (ROOT/'mdx'/f'{self.name}.MDX').write_bytes(blob)
  (ROOT/'traces'/f'{self.name}.trace').write_text('# nominal master_clock address value; clock=4000000\n'+''.join(f'{t*TICK} 0x{a:02x} 0x{v:02x}\n' for t,a,v in self.events))
  (ROOT/'schedule'/f'{self.name}.json').write_text(json.dumps(self.sections,ensure_ascii=False,indent=2)+'\n')
  with (ROOT/'schedule'/f'{self.name}.csv').open('w',encoding='utf-8-sig',newline='') as f:
   keys=['label','start_tick','end_tick','start_s','end_s','analyze'];writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader();writer.writerows({k:s[k] for k in keys} for s in self.sections)
  return dict(name=self.name,purpose=self.purpose,seconds=self.tick*TICK/CLOCK,ticks=self.tick,register_writes=len(self.events),sha256=hashlib.sha256(blob).hexdigest())
