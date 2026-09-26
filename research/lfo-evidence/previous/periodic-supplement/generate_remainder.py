from pathlib import Path
import sys,json,shutil
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R.parent/'lfo-independent-tests'))
import mdx_writer as m
out=R/'remaining-mdx';m.ROOT=out
for folder in ['mdx','schedule','traces']:(out/folder).mkdir(parents=True,exist_ok=True)
files=[]
for name,lo,hi in [('25R1',6,10),('25R2',10,14),('25R3',14,16)]:
 t=m.Test(name,'Remaining slow LFO settings, under 20 minutes per file')
 t.am_pair();t.w(0x60,16);t.w(0x61,16)
 for frequency in range(lo,hi):
  t.w(1,2);t.lfo(frequency,0)
  t.section(f'LFRQ={frequency:02X}; saw AM AMD=127 AMS=1',21973)
 files.append(t.finish())
(out/'manifest.json').write_text(json.dumps(dict(clock_hz=4000000,files=files),indent=2))
shutil.copyfile(R.parent/'lfo-independent-tests/verify.py',out/'verify.py')
for f in files:print(f['name'],f['seconds'])
