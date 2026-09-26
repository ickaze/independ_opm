"""Measurement stimulus only. No LFO waveform/clock/depth emulator is used."""
from pathlib import Path
import json,math
import mdx_writer as m
R=Path(__file__).resolve().parent;m.ROOT=R
for d in ['mdx','schedule','traces']:(R/d).mkdir(exist_ok=True)
files=[]
def section(t,label,seconds):t.section(label,max(1,math.ceil(seconds*4000000/32768)))
def finish(t,group):
 item=t.finish();item['group']=group;files.append(item)
def pair(name,purpose):
 t=m.Test(name,purpose);t.am_pair();t.w(0x60,16);t.w(0x61,16);t.lfo(0xb0,0);return t
def pm_pair(name,purpose):
 t=pair(name,purpose);t.w(0x19,0);t.w(0x38,0x50);t.w(0xa0,0);return t

t=pair('13CAL','Amplitude, pitch, SRC and baseline calibration');t.w(0x19,0)
for tl in [8,16,24,32,40,48,64,80,96,112,127,16]:
 t.w(0x60,tl);section(t,f'TL={tl}, right TL=16',1)
for kc in [0x28,0x48,0x68]:
 t.w(0x28,kc);t.w(0x29,kc)
 for kf in [0,4,8,16,32,64,128,252]:
  t.w(0x30,kf);section(t,f'KC={kc:02X} left KF={kf} right KF=0',.5)
t.w(0x30,0)
for i in range(16):
 t.w(0x20,0x47 if i%2 else 7);section(t,'pan step '+str(i),.131)
finish(t,'primary')

t=pair('14WAVE','AM/PM waveform shape, endpoints and carrier independence')
for kc in [0x48,0x68]:
 t.w(0x28,kc);t.w(0x29,kc)
 for w in [0,1,2]:
  for mode in ['AM','PM','BOTH']:
   t.w(0x38,1 if mode=='AM' else 0x50 if mode=='PM' else 0x51)
   t.w(0x19,127 if mode!='PM' else 0);t.w(0x19,128|(64 if mode!='AM' else 0))
   t.w(1,2);t.lfo(0xa0,w);section(t,f'wave={w} mode={mode} KC={kc:02X} AMD/PMD endpoints',10)
finish(t,'primary')

t=pair('15AMDEP','All 128 AMD values x all four AMS values, square extrema');t.lfo(0xc0,1)
for ams in range(4):
 t.w(0x38,ams)
 for amd in range(128):
  t.w(0x19,amd);section(t,f'AMD={amd} AMS={ams} AME=1',.4)
t.w(0xa0,0);t.w(0x38,3);t.w(0x19,127);section(t,'AME=0 negative control',3)
finish(t,'primary')

t=pm_pair('16PMDEP','All 128 PMD values x all eight PMS values, square extrema');t.lfo(0xc0,1)
for pms in range(8):
 t.w(0x38,pms<<4)
 for pmd in range(128):
  t.w(0x19,128|pmd);section(t,f'PMD={pmd} PMS={pms}, AMD=0',.4)
finish(t,'primary')

# Timings below are observation budgets, not expected hardware periods.
for high in range(8,16):
 t=pair(f'{17+high-8:02d}F{high:X}0','Every high-range LFRQ value, saw AM transition timing')
 t.w(0x38,1);t.w(0x19,127);t.w(0x19,128)
 for low in range(16):
  f=high*16+low;t.w(1,2);t.lfo(f,0);section(t,f'LFRQ={f:02X} saw AM; measure transition times and increment sizes',12)
 finish(t,'primary')
for high,seconds in enumerate([180,90,48,26,15,10,10,10]):
 t=pair(f'{25+high:02d}F{high:X}0','Low-range LFRQ long step observation, not necessarily a whole cycle')
 for low in range(16):
  f=high*16+low;t.w(1,2);t.lfo(f,0);section(t,f'LFRQ={f:02X} saw AM; partial-cycle steps; budget={seconds}s',seconds)
 finish(t,'slow')

t=pair('33STATE','LFO register state transitions and depth-latch independence')
for w in range(3):
 t.w(1,2);t.lfo(0xa7,w);t.w(0x38,0x51);t.w(0x19,80);t.w(0x19,128|64)
 section(t,f'wave={w} baseline',5)
 for label,changes in [('same LFRQ',[(0x18,0xa7)]),('new LFRQ',[(0x18,0xa9)]),('hold 01h',[(1,2)]),('release 01h',[(1,0)]),('AMD only',[(0x19,37)]),('PMD only',[(0x19,128|99)]),('key off',[(8,0)]),('key on',[(8,8)]),('wave select',[(0x1b,(w+1)%3)]),('wave restore',[(0x1b,w)]),('frequency restore',[(0x18,0xa7)])]:
  for a,v in changes:t.w(a,v)
  section(t,f'wave={w}: {label}',3.137)
finish(t,'primary')

t=m.Test('34CHAN','AM operator enable and sensitivity channel mapping')
for ch in range(8):
 ref=(ch+1)%8
 for op in range(4):
  for c in range(8):t.w(8,c);t.w(0x20+c,0)
  # Initialize target using the standard voice writer; key mask extended to all slots.
  t.voice(ch,op,0x40,tl=16,ame=True);t.voice(ref,0,0x80,tl=16)
  t.w(8,0x78|ch);t.w(8,8|ref);t.w(0x38+ch,0x51)
  t.w(0x19,64);t.w(0x19,128|64);t.lfo(0xb0,2)
  section(t,f'ch={ch+1} register-slot={op} AME=1 AM+PM',2)
  t.w(0xa0+op*8+ch,0);section(t,f'ch={ch+1} slot={op} AME=0 PM remains',2)
finish(t,'primary')

t=pair('35JOINT','Combined depths and waveform interaction, held-out non-grid cases')
for w in [0,1,2]:
 for amd,pmd,ams,pms in [(1,1,1,1),(17,29,2,3),(63,65,3,5),(126,127,1,7),(95,37,2,6)]:
  t.w(0x19,amd);t.w(0x19,128|pmd);t.w(0x38,(pms<<4)|ams);t.lfo(0xb3,w)
  section(t,f'wave={w} AMD={amd} PMD={pmd} AMS={ams} PMS={pms}; validation holdout',4)
finish(t,'primary')
t=pair('36CLOCK','Cross-waveform timing checks at high-range octave endpoints')
for w in range(3):
 for high in range(8,16):
  for low in [0,15]:
   f=high*16+low;t.w(1,2);t.lfo(f,w)
   section(t,f'wave={w} LFRQ={f:02X} cross-wave timing',8)
finish(t,'primary')
(R/'manifest.json').write_text(json.dumps(dict(clock_hz=4000000,recording_hz=96000,recording_bits=24,tick_master_clocks=32768,files=files),indent=2))
for group in ['primary','slow']:
 items=[i for i in files if i['group']==group]
 (R/(group+'.m3u')).write_text(''.join('mdx/'+i['name']+'.MDX\n' for i in items))
 print(group,len(items),sum(i['seconds'] for i in items)/60,'minutes')
