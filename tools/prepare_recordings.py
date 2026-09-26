# SPDX-License-Identifier: 0BSD
# Copyright (C) 2026 by I.C.KaZe
"""Copy recordings to MDX-aligned names by content hash. Original files are untouched."""
from pathlib import Path
import argparse,hashlib,json,shutil
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);p.add_argument('--copy',action='store_true');a=p.parse_args()
rows=json.loads((Path(__file__).resolve().parents[1]/'docs/RECORDING_INDEX.json').read_text())
lookup={r['sha256']:r['recording'] for r in rows}
for f in a.source.rglob('*'):
 if not f.is_file() or f.suffix.lower() not in ['.wav','.flac']:continue
 h=hashlib.sha256()
 with f.open('rb') as s:
  for b in iter(lambda:s.read(8*1024*1024),b''):h.update(b)
 name=lookup.get(h.hexdigest())
 if name is None:print('Unrecognized:',f);continue
 dst=a.output/name;print(f,'->',dst)
 if a.copy:
  if dst.exists():raise FileExistsError(dst)
  dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dst)
