"""Requires original source ZIP and g++; extracts reference only into a temporary directory."""
import pathlib,subprocess,tempfile,zipfile,argparse
p=argparse.ArgumentParser();p.add_argument('source_zip');a=p.parse_args()
root=pathlib.Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as d:
 d=pathlib.Path(d)
 with zipfile.ZipFile(a.source_zip) as z:
  (d/'original_lfo.h').write_text(z.read('X68Sound/lfo.h').decode('cp932'))
 subprocess.run(['g++','-std=c++17','-O2','-fsigned-char','-I'+str(root/'include'),'-I'+str(d),str(root/'tests/reference_lfo.cpp'),'-o',str(d/'check')],check=True)
 subprocess.run([str(d/'check')],check=True)
