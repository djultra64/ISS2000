"""PAL framebuffer ownership regression. Original work: djultra64."""
import hashlib,importlib.util,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HARNESS=(ROOT/'tests/fixtures/pal_framebuffer_ownership.py').read_text()
class FramebufferOwnershipTests(unittest.TestCase):
 def test_original_scheduler_does_not_reallocate_displayed_slot(self):
  path=ROOT/'tools/prepare_pal_framebuffer_ownership.py'
  self.assertTrue(path.is_file(), 'Missing framebuffer ownership correction')
  spec=importlib.util.spec_from_file_location('fb_ownership',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  source=ROOT/'.local/pal-map-bound-01/functions/func_8001D480_resident.c'
  if not source.exists():self.skipTest('Private original PAL functions required')
  with tempfile.TemporaryDirectory() as d:
   derived=Path(d)/'allocator.cpp';derived.write_bytes(m.derive(source.read_bytes()).replace(b'iss2000_pal_framebuffer_allocator', b'func_8001D480_resident'))
   harness=Path(d)/'run.py';harness.write_text(HARNESS)
   env=dict(os.environ,ISS_FB_ROOT=str(ROOT));env.pop('ISS_FB_DERIVATIVE',None)
   baseline=subprocess.run([sys.executable,str(harness)],env=env,text=True,capture_output=True)
   self.assertEqual(baseline.returncode,0,baseline.stdout+baseline.stderr)
   self.assertIn('same_current_first=1 completed=3',baseline.stdout)
   self.assertIn('foreign_current_burst completed=3',baseline.stdout)
   env['ISS_FB_DERIVATIVE']=str(derived)
   result=subprocess.run([sys.executable,str(harness)],env=env,text=True,capture_output=True)
   self.assertEqual(result.returncode,0,result.stdout+result.stderr)
   self.assertIn('same_current_first=1 completed=10',result.stdout)
   self.assertIn('foreign_current_burst completed=10',result.stdout)
  with self.assertRaises(ValueError):m.derive(source.read_bytes()+b'\n')

 def test_derivative_output_is_bound_to_rom_and_immutable(self):
  spec=importlib.util.spec_from_file_location('fb_ownership',ROOT/'tools/prepare_pal_framebuffer_ownership.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  rom=ROOT/'.local/inputs/pal-en-de/rom.z64';source=ROOT/'.local/pal-map-bound-01/functions/func_8001D480_resident.c'
  if not rom.exists() or not source.exists():self.skipTest('Private PAL inputs required')
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);receipt=m.prepare(rom,source,p/'out');self.assertEqual(receipt,m.prepare(rom,source,p/'out'))
   (p/'out/extra').write_text('preserve')
   with self.assertRaises(ValueError):m.prepare(rom,source,p/'out')
   (p/'bad-rom').write_bytes(bytes(0x1000000))
   with self.assertRaises(ValueError):m.prepare(p/'bad-rom',source,p/'bad-out')
   self.assertFalse((p/'bad-out').exists())
