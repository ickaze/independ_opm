"""Build finite, PDX-free raw-OPM MDX measurements using MDX track P as controller.
Only FF tempo, FE register writes, rests and F1/00 end are emitted.
All FM tracks end without notes; normal note/volume/pitch processing is bypassed.
"""
from pathlib import Path
import struct,csv,json
ROOT=Path(__file__).resolve().parent
CLOCK=4000000; TEMPO=224; TICK_CLOCKS=1024*(256-TEMPO)
ROWS=[(31,7,0,7,15,17,0,0,0,0,0),(24,12,0,7,1,0,0,1,0,0,0),
      (24,12,0,7,1,0,0,2,3,0,0),(21,12,0,7,1,0,0,0,7,0,0)]
NAMES=['M1','M2','C1','C2']
class Test:
 def __init__(self,name):
  self.name=name;self.tick=0;self.events=[];self.sections=[]
  self.w(0x0f,0);self.w(0x19,0);self.w(0x19,128)
  for ch in range(8):self.w(8,ch);self.w(0x20+ch,0);self.w(0x38+ch,0)
  self.wait(128)
 def w(self,r,v):self.events.append((self.tick,r,v))
 def wait(self,n):self.tick+=n
 def voice(self,ch,kc=0x48,alg=5,flat=False,zero=False,sine=False,gain_tl=0):
  self.w(8,ch);self.w(0x20+ch,0xc0|(0 if sine else 7<<3)|alg);self.w(0x28+ch,kc);self.w(0x30+ch,0);self.w(0x38+ch,0)
  for i,row in enumerate(ROWS):
   ar,dr,sr,rr,sl,tl,ks,mul,dt,dt2,ame=row
   if flat and i==0:dr=0
   if zero:dt=0
   if sine:ar,dr,sr,rr,sl,tl,ks,mul,dt,dt2,ame=31,0,0,7,0,0,0,1,0,0,0
   if i>0 or sine:tl=min(127,tl+gain_tl)
   for base,v in [(0x40,dt*16+mul),(0x60,tl),(0x80,ks*64+ar),(0xa0,ame*128+dr),(0xc0,dt2*64+sr),(0xe0,sl*16+rr)]:self.w(base+i*8+ch,v)
 def mask(self,ch,slots,alg=5,sine=False):
  for i in (range(4) if alg==7 else range(1,4)):
   self.w(0x60+i*8+ch,(0 if sine else ROWS[i][5]) if i in slots else 127)
 def section(self,label,n,ch,kc,slots):
  self.sections.append(dict(start_tick=self.tick,end_tick=self.tick+n,start_s_4MHz=self.tick*TICK_CLOCKS/CLOCK,
   end_s_4MHz=(self.tick+n)*TICK_CLOCKS/CLOCK,channel=ch,kc=f'{kc:02X}',audible='+'.join(NAMES[i] for i in slots),label=label))
  self.wait(n)
 def fresh(self,ch,kc,slots,n=512,**kw):
  alg=kw.get('alg',5);self.voice(ch,kc,**kw);self.mask(ch,slots,alg,kw.get('sine',False));self.w(8,0x78|ch)
  self.section('fresh '+str(kw),n,ch,kc,slots);self.w(8,ch);self.w(0x20+ch,0);self.wait(64)
 def save(self):
  for ch in range(8):self.w(8,ch);self.w(0x20+ch,0)
  self.wait(128)
  data=bytearray([0xff,TEMPO]);at=0
  def rests(n):
   while n:
    step=min(n,128);data.append(step-1);n-=step
  for t,r,v in self.events:rests(t-at);at=t;data.extend([0xfe,r,v])
  rests(self.tick-at);data.extend([0xf1,0])
  # Voice table is unused but one valid voice is included for reader compatibility.
  voice=bytearray([0,0x3d,15])
  for field in range(6):
   for ar,dr,sr,rr,sl,tl,ks,mul,dt,dt2,ame in ROWS:
    voice.append([dt*16+mul,tl,ks*64+ar,ame*128+dr,dt2*64+sr,sl*16+rr][field])
  offsets=[22+len(data)]+[20]*8+[22]
  body=struct.pack('>10H',*offsets)+b'\xf1\x00'+data+voice
  blob=(self.name+' OPM TIMING TEST').encode('ascii')+b'\r\n\x1a\x00'+body
  assert len(body)<65536
  (ROOT/'mdx'/f'{self.name}.MDX').write_bytes(blob)
  with (ROOT/'schedule'/f'{self.name}.csv').open('w',newline='',encoding='utf-8-sig') as f:
   writer=csv.DictWriter(f,fieldnames=list(self.sections[0]));writer.writeheader();writer.writerows(self.sections)
  (ROOT/'traces'/f'{self.name}.trace').write_text('# Nominal 4MHz timing; MDX bus-write latencies are not modeled\n'+''.join(f'{t*TICK_CLOCKS} 0x{r:02x} 0x{v:02x}\n' for t,r,v in self.events))
  return {'file':self.name+'.MDX','seconds_4MHz':self.tick*TICK_CLOCKS/CLOCK,'ticks':self.tick,'writes':len(self.events)}
def main():
 for d in ['mdx','schedule','traces']:(ROOT/d).mkdir(exist_ok=True)
 tests=[]
 t=Test('01SOLO')
 for slots in [(1,2,3),(1,),(2,),(3,)]:t.fresh(0,0x48,slots)
 tests.append(t)
 t=Test('02LIVE');t.voice(0,flat=True);t.w(8,0x78)
 for slots in [(1,2,3),(1,),(1,2,3),(2,),(1,2,3),(3,),(1,2,3)]:
  t.mask(0,slots);t.section('TL only; M1 D1R=0; NO re-key',512,0,0x48,slots)
 tests.append(t)
 t=Test('03CHSCAN')
 for ch in range(8):
  for slots in [(1,2,3),(1,),(2,),(3,)]:t.fresh(ch,0x48,slots,384)
 tests.append(t)
 t=Test('04PITCH')
 for kc in [0x38,0x48,0x58,0x68]:
  for slots in [(1,2,3),(1,),(2,),(3,)]:t.fresh(0,kc,slots,384)
 tests.append(t)
 t=Test('05SINE')
 for ch in range(8):
  for op in range(4):t.fresh(ch,0x48,(op,),384,alg=7,sine=True)
 tests.append(t)
 t=Test('06PAIR')
 for zero in [False,True]:
  for slots in [(1,2,3),(1,2),(1,3),(2,3)]:t.fresh(0,0x48,slots,512,zero=zero)
 tests.append(t)
 t=Test('07LOAD');t.voice(0,flat=True);t.w(8,0x78);t.section('ch0 only',512,0,0x48,(1,2,3))
 for ch in range(1,8):
  t.voice(ch,0x30+ch,flat=True,gain_tl=24);t.w(0x20+ch,0x3d);t.w(8,0x78|ch)
 t.section('other channels running; pan OFF',512,0,0x48,(1,2,3))
 for ch in range(1,8):t.w(0x20+ch,0xfd)
 t.section('other channels also audible; +24 TL',512,0,0x48,(1,2,3))
 for ch in range(1,8):t.w(0x20+ch,0x3d)
 t.section('other channels running; pan OFF again',512,0,0x48,(1,2,3));tests.append(t)
 summary=[t.save() for t in tests];(ROOT/'manifest.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
