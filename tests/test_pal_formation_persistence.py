"""Original PAL formation persistence regression. Original work: djultra64."""
import importlib.util,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SYMBOL='func_802A3464_overlay_3e83d0_8029eea0'
class FormationPersistenceTests(unittest.TestCase):
 def module(self):
  spec=importlib.util.spec_from_file_location('formation',ROOT/'tools/prepare_pal_formation_persistence.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 def test_original_probe_and_worker_are_used_for_every_accessory_choice(self):
  source=ROOT/'.local/pal-map-02/functions'/f'{SYMBOL}.c'
  if not source.is_file():self.skipTest('Private original PAL functions required')
  m=self.module()
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);derived=p/'save.cpp';derived.write_bytes(m.derive(source.read_bytes()).replace(m.ENTRY.encode(),SYMBOL.encode()))
   inc='-I'+str(ROOT/'.local/deps/N64Recomp/include');objects=[]
   worker=ROOT/'.local/pal-map-02/functions/func_802A3720_overlay_3e83d0_8029eea0.c'
   for n,path in enumerate((derived,worker)):
    obj=p/f'{n}.o';compiler='c++' if n==0 else 'cc';std='c++20' if n==0 else 'c17'
    subprocess.run([compiler,'-std='+std,'-O1',inc,'-c',str(path),'-o',str(obj)],check=True,capture_output=True);objects.append(str(obj))
   subprocess.run(['c++','-std=c++20','-O1',inc,str(ROOT/'tests/fixtures/pal_formation_persistence.cpp'),*objects,'-o',str(p/'test')],check=True,capture_output=True)
   result=subprocess.run([str(p/'test')],text=True,capture_output=True)
   self.assertEqual(result.returncode,0,result.stdout+result.stderr)
   self.assertIn('54 storage-route cases and 8 original write-result cases passed',result.stdout)
  with self.assertRaises(ValueError):m.derive(source.read_bytes()+b'\n')
 def test_rom_binding_and_immutable_output(self):
  rom=ROOT/'.local/inputs/pal-en-de/rom.z64';source=ROOT/'.local/pal-map-02/functions'/f'{SYMBOL}.c'
  if not rom.is_file() or not source.is_file():self.skipTest('Private original PAL inputs required')
  m=self.module()
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);r=m.prepare(rom,source,p/'out');self.assertEqual(r,m.prepare(rom,source,p/'out'))
   (p/'out/extra').write_text('preserve')
   with self.assertRaises(ValueError):m.prepare(rom,source,p/'out')
   (p/'bad').write_bytes(bytes(0x1000000))
   with self.assertRaises(ValueError):m.prepare(p/'bad',source,p/'bad-out')
   self.assertFalse((p/'bad-out').exists())
