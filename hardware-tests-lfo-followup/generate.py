"""SPDX-License-Identifier: 0BSD
Copyright (C) 2026 by I.C.KaZe
Stimulus generation only; no expected waveform or emulator formula is embedded.
"""
from pathlib import Path
import json,math
import mdx_writer as m
R=Path(__file__).resolve().parent;m.ROOT=R
for folder in ['mdx','schedule','traces']:(R/folder).mkdir(exist_ok=True)
files=[]
def duration(t,label,seconds):t.section(label,math.ceil(seconds/.008192))
def setup(name,purpose):
 t=m.Test(name,purpose);t.am_pair();t.w(0x60,0);t.w(0x61,0);return t
for name,w in [('37AMSAW',0),('38AMSQR',1),('39AMTRI',2)]:
 t=setup(name,'Slow full AMD sweep; stable waveform levels at AMS1, TL0')
 for amd in range(128):
  t.w(0x19,amd);t.w(0x19,128);t.w(0x38,1);t.w(1,2);t.lfo(0x80,w)
  duration(t,f'wave={w} AMD={amd} AMS=1 TL=0 PMD=0; steady level recovery',6)
 files.append(t.finish())
depths=[1,2,3,7,15,16,17,31,32,33,63,64,65,95,126,127]
for name,w in [('40PMSAW',0),('41PMTRI',2)]:
 t=setup(name,'Slow PM intermediate values without AM; selected depth boundaries')
 t.w(0xa0,0);t.w(0x19,0)
 for pms in range(8):
  for pmd in depths:
   t.w(0x19,128|pmd);t.w(0x38,pms<<4);t.w(1,2);t.lfo(0x80,w)
   duration(t,f'wave={w} PMD={pmd} PMS={pms} AMD=0 TL=0',6)
 files.append(t.finish())
t=setup('42STATE','Repeat state transitions at varied nominal MDX phases')
for freq in [0x81,0x87,0x8f]:
 for kind in ['same_freq','new_freq','hold','wave_select']:
  for delay in [1,2,3,5,7,11,17,31]:
   t.w(0x19,127);t.w(0x19,128);t.w(1,2);t.lfo(freq,0)
   t.section(f'f={freq:02X} {kind} delay={delay}; baseline',128)
   t.section('vary event phase in driver ticks',delay)
   if kind=='same_freq':t.w(0x18,freq)
   elif kind=='new_freq':t.w(0x18,freq^2)
   elif kind=='hold':t.w(1,2)
   else:t.w(0x1b,2)
   t.section(f'{kind} during',delay)
   if kind=='hold':t.w(1,0)
   elif kind=='wave_select':t.w(0x1b,0)
   t.section(f'{kind} after event',128)
files.append(t.finish())
(R/'manifest.json').write_text(json.dumps(dict(clock_hz=4000000,recording_hz=96000,recording_bits=24,files=files),indent=2))
(R/'followup.m3u').write_text(''.join('mdx/'+v['name']+'.MDX\n' for v in files))
for v in files:print(v['name'],v['seconds'])
