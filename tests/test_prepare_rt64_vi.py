"""Original project work: djultra64. Reviewed private RT64 VI adaptation."""
from pathlib import Path
import tempfile,unittest
from tools.prepare_rt64_vi import prepare
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'.local/deps/rt64/src/hle/rt64_vi.cpp'
@unittest.skipUnless(SOURCE.is_file(),'Pinned private RT64 VI source required')
class PrepareRt64ViTests(unittest.TestCase):
 def test_exact_source_keeps_origin_and_geometry_uses_host_identity_and_region_rate(self):
  original=SOURCE.read_bytes()
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'out';receipt=prepare(SOURCE,p);text=(p/'rt64_vi.cpp').read_text()
   self.assertIn('iss2000_resolve_vi_framebuffer(origin, width, siz)',text)
   self.assertIn('iss2000_vi_original_rate(top().vi.vSync)',text)
   self.assertIn('return origin - rowOffset;',text)
   self.assertNotIn('origin =',text)
   self.assertEqual(SOURCE.read_bytes(),original)
   self.assertEqual(prepare(SOURCE,p),receipt)
   (p/'rt64_vi.cpp').write_text('changed')
   with self.assertRaises(ValueError):prepare(SOURCE,p)
 def test_changed_source_rejected_before_output(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'vi.cpp').write_bytes(SOURCE.read_bytes()+b'\n')
   with self.assertRaises(ValueError):prepare(p/'vi.cpp',p/'out')
   self.assertFalse((p/'out').exists())
 def test_actual_rt64_vi_uses_registered_base_and_pal_factors(self):
  import subprocess
  source=r'''#include "hle/rt64_vi.h"
#include "runtime/vi_framebuffer.hpp"
#include <cassert>
int main(){
 RT64::VI vi{};vi.status.word=0x13012;vi.origin=0x27D899;vi.width=320;vi.vSync=625;
 iss2000_record_vi_framebuffer(vi.origin,vi.width,vi.status.word,0x27D380);
 assert(vi.fbAddress()==0x27D380);
 assert(vi.origin==0x27D899); // raw physical origin is preserved
 auto unknown=vi;unknown.origin=0x100280;assert(unknown.fbAddress()==0x100000);
 RT64::VIHistory history;history.pushVI(vi,320);history.factors.fill(1);
 assert(history.logicalRateFromFactors()==50);history.factors.fill(2);assert(history.logicalRateFromFactors()==25);
 vi.vSync=525;history.pushVI(vi,320);assert(history.logicalRateFromFactors()==30);
 history.factors.fill(1);assert(history.logicalRateFromFactors()==60);
}'''
  with tempfile.TemporaryDirectory() as d:
   folder=Path(d);(folder/'test.cpp').write_text(source);prepare(SOURCE,folder/'adapted')
   rt64=ROOT/'.local/deps/rt64/src'
   args=['c++','-std=c++20','-DHLSL_CPU','-DFFX_GCC','-I'+str(ROOT/'src'),'-I'+str(rt64),'-I'+str(rt64/'contrib'),'-I'+str(rt64/'contrib/plume'),'-I'+str(rt64/'contrib/hlslpp/include'),'-I'+str(rt64/'hle'),str(folder/'test.cpp'),str(ROOT/'src/runtime/vi_framebuffer.cpp')]
   for original in [True,False]:
    binary=folder/('original' if original else 'adapted-test')
    implementation=SOURCE if original else folder/'adapted/rt64_vi.cpp'
    result=subprocess.run([*args,str(implementation),'-o',str(binary)],capture_output=True,text=True)
    self.assertEqual(result.returncode,0,result.stderr)
    result=subprocess.run([str(binary)],capture_output=True,text=True)
    if original:self.assertNotEqual(result.returncode,0,'Unadapted VI must reproduce the wrong framebuffer base')
    else:self.assertEqual(result.returncode,0,result.stderr)
