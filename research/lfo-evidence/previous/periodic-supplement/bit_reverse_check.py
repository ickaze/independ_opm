from pathlib import Path
import json,numpy as np
R=Path(__file__).resolve().parent
v=json.loads((R/'results.json').read_text());out=[]
for row in v['sections']:
 if not row['full']:continue
 bits=(np.array(row['jumps_db'])>1.5*v['quantum_db']).astype(int);low=row['frequency']%16;n=len(bits)
 candidates=[]
 for phase in range(16):
  i=np.arange(n);rev=np.array([int(f"{(phase+j)%16:04b}"[::-1],2) for j in range(n)]);pred=(rev<low).astype(int)
  candidates.append((int(sum(pred[:16]!=bits[:16])),phase,pred))
 best=min(candidates,key=lambda x:(x[0],x[1]));pred=best[2]
 out.append(dict(frequency=row['frequency'],phase=best[1],train_bits=16,train_errors=best[0],test_bits=n-16,test_errors=int(sum(pred[16:]!=bits[16:]))))
(R/'carry_check_bit_reverse.json').write_text(json.dumps(out,indent=2));print('segments',len(out),'train errors',sum(x['train_errors'] for x in out),'test',sum(x['test_bits'] for x in out),'test errors',sum(x['test_errors'] for x in out))
print('quantum',v['quantum_db'])
