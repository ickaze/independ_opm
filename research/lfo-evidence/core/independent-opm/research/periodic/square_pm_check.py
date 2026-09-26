# SPDX-License-Identifier: 0BSD
# Copyright (C) 2026 by I.C.KaZe
from pathlib import Path
import json,math,statistics
r=Path(__file__).resolve().parent
rows=json.loads((r/'prior_square_depth.json').read_text())
t={int(k):v for k,v in json.loads((r/'pm_endpoint127.json').read_text())['pitch_table'].items()}
out=[]
for raw in [127,128]:
 errors=[]
 for row in rows:
  if not row['pmd']:continue
  q=(raw*row['pmd']//128)*(1<<(row['pms']-5))
  if q not in t or -q not in t:continue
  errors.append((row['cents_high']-row['cents_low'])-(t[q]-t[-q]))
 out.append(dict(endpoint=raw,conditions=len(errors),rms_cents=math.sqrt(sum(e*e for e in errors)/len(errors)),median_abs_cents=statistics.median(map(abs,errors)),max_abs_cents=max(map(abs,errors))))
(r/'square_pm_check.json').write_text(json.dumps(out,indent=2));print(out)
