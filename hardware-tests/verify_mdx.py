"""Decode MDX bytes independently of the generator; compare to the trace schedule."""
from pathlib import Path
import struct,json
root=Path(__file__).resolve().parent
for path in sorted((root/'mdx').glob('*.MDX')):
 data=path.read_bytes();base=data.index(b'\r\n\x1a')+3;assert data[base]==0;base+=1
 offsets=struct.unpack_from('>10H',data,base);assert min(offsets)==20
 start=base+offsets[9];end=base+offsets[0];assert len(data)-end==27
 tick=0;events=[];pos=start
 while pos<end:
  op=data[pos];pos+=1
  if op<128:tick+=op+1
  elif op==255:assert data[pos]==224;pos+=1
  elif op==254:events.append((tick*32768,data[pos],data[pos+1]));pos+=2
  elif op==241:assert data[pos]==0;pos+=1;break
  else:raise AssertionError('unexpected MDX command')
 assert pos==end
 expected=[]
 for line in (root/'traces'/f'{path.stem}.trace').read_text().splitlines():
  if not line.startswith('#'):expected.append(tuple(int(v,0) for v in line.split()))
 assert events==expected
 if path.stem=='02LIVE':
  # Exactly one all-OP key-on; all middle changes are TL writes.
  ons=[v for t,r,v in events if r==8 and v&0x78];assert ons==[0x78]
 print('PASS',path.name,'MDX/trace identical',len(events),'writes',tick,'ticks')
