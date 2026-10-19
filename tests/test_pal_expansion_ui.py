"""Original project work: djultra64. Original PAL notice selector; no gameplay."""
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
HARNESS=r'''#include "recomp.h"
#include <cassert>
#include <cstdlib>
#include <cstdio>
#include <cstring>
#include <vector>
ORIGINALS
DERIVED
using Bytes=std::vector<uint8_t>;
static bool replacement;static int queued;
static void put(Bytes& r,uint32_t a,uint32_t v){std::memcpy(r.data()+(a&0x7fffff),&v,4);}
static void byte(Bytes& r,uint32_t a,uint8_t v){r[(a&0x7fffff)^3]=v;}
static uint8_t byte(const Bytes& r,uint32_t a){return r[(a&0x7fffff)^3];}
static void noop(uint8_t*,recomp_context*){}
static void queue(uint8_t* r,recomp_context* c){assert(uint32_t(c->r4)==0x802b4334);++queued;assert(r[0x2b4819^3]!=14);}
static void selector(uint8_t* r,recomp_context* c){if(replacement)iss2000_pal_skip_expansion_notice(r,c);else func_802B1FDC_overlay_481680_802b1070(r,c);}
extern "C" recomp_func_t* get_function(int32_t a){switch(uint32_t(a)){
 case 0x802b1fdc:return selector;
 case 0x801ae594:return queue;
 case 0x8000c174:case 0x8000c474:case 0x801b52d0:case 0x803c36a0:case 0x803c37b8:
 case 0x8000c5e4:case 0x8000cd3c:case 0x8000cc5c:return noop;
 default:std::fprintf(stderr,"Unexpected call %08X\n",uint32_t(a));std::abort();}}
static auto context(){recomp_context c{};c.r29=(int32_t)0x807ff000;return c;}
int main(){
 for(unsigned memory:{0u,1u,2u})for(unsigned sentinel:{0u,0xc9u})
 for(unsigned boot:{0u,1u})for(unsigned acknowledged:{0u,1u})for(unsigned pak=0;pak<8;++pak){
  Bytes initial(0x800000,0x5a);
  // These are original context inputs, never fabricated by the port helper.
  put(initial,0x8013b428,(memory<<16)|(acknowledged<<29));
  put(initial,0x8000030c,boot);byte(initial,0x803fffff,sentinel);byte(initial,0x8012e67a,pak);
  auto original=initial,changed=initial;auto c=context();func_802B1FDC_overlay_481680_802b1070(original.data(),&c);
  c=context();iss2000_pal_skip_expansion_notice(changed.data(),&c);
  if(memory==1){
   assert(byte(changed,0x802b4819)!=14);
   // Compare with the genuine already-seen continuation, then restore only
   // its fixture input differences. The whole8MiB must match that reference.
   auto reference=initial;byte(reference,0x803fffff,0xc9);put(reference,0x8000030c,1);
   c=context();func_802B1FDC_overlay_481680_802b1070(reference.data(),&c);
   byte(reference,0x803fffff,sentinel);put(reference,0x8000030c,boot);
   assert(reference==changed);
  }else assert(original==changed); // Includes the genuine noExpansion path.
  // Actual memory/detection/config state and every buffer remain unchanged.
  for(unsigned i=0;i<4;++i)assert(changed[0x13b428+i]==initial[0x13b428+i]&&changed[0x30c+i]==initial[0x30c+i]);
 }
 // Run the genuine parent initializer. The queue must never seeEnhanced14,
 // while the distinct ControllerPak insertion dialog15 remains intact.
 Bytes initial(0x800000);put(initial,0x8013b428,0x00010000);byte(initial,0x803fffff,0);
 auto c=context();replacement=true;queued=0;
 func_802B1CC8_overlay_481680_802b1070(initial.data(),&c);
 assert(queued==1&&byte(initial,0x802b4819)==15);
}
'''
@unittest.skipUnless(shutil.which('c++'),'C++ compiler required')
class ExpansionOriginalTests(unittest.TestCase):
 def test_only_enhanced_notice_uses_original_already_seen_continuation(self):
  from tools.prepare_pal_expansion_ui import derive,ROM_SHA256
  folder=ROOT/'.local/pal-map-bound-01/functions';header=ROOT/'.local/deps/N64Recomp/include';rom=ROOT/'.local/inputs/pal-en-de/rom.z64'
  originals=[folder/(n+'.c') for n in ['func_802B1FDC_overlay_481680_802b1070','func_802B1CC8_overlay_481680_802b1070']]
  if not all(p.is_file() for p in [rom,header/'recomp.h',*originals]):self.skipTest('Private original PAL selector/parent fixtures required')
  self.assertEqual(hashlib.sha256(rom.read_bytes()).hexdigest(),ROM_SHA256)
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'derived.cpp').write_bytes(derive(originals[0].read_bytes()))
   code=HARNESS.replace('ORIGINALS','\n'.join('#include '+json.dumps(str(x)) for x in originals)).replace('DERIVED','#include '+json.dumps(str(p/'derived.cpp')))
   (p/'check.cpp').write_text(code)
   built=subprocess.run(['c++','-std=c++20','-O2','-I'+str(header),str(p/'check.cpp'),'-o',str(p/'check')],capture_output=True,text=True)
   self.assertEqual(built.returncode,0,built.stderr)
   run=subprocess.run([str(p/'check')],capture_output=True,text=True)
   self.assertEqual(run.returncode,0,run.stderr)
class ExpansionIdentityTests(unittest.TestCase):
 def test_bad_inputs_rejected_before_output(self):
  from tools.prepare_pal_expansion_ui import derive,prepare
  with self.assertRaisesRegex(ValueError,'source digest mismatch'):derive(b'unrelated')
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'rom').write_bytes(b'not PAL')
   with self.assertRaisesRegex(ValueError,'ROM digest mismatch'):prepare(p/'rom',p/'missing',p/'out')
   self.assertFalse((p/'out').exists())
 def test_outputs_are_idempotent_and_tampering_is_rejected(self):
  from tools.prepare_pal_expansion_ui import prepare
  rom=ROOT/'.local/inputs/pal-en-de/rom.z64';source=ROOT/'.local/pal-map-bound-01/functions/func_802B1FDC_overlay_481680_802b1070.c'
  if not rom.is_file() or not source.is_file():self.skipTest('Private original PAL generation inputs required')
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'out';receipt=prepare(rom,source,out)
   self.assertEqual(prepare(rom,source,out),receipt)
   self.assertEqual(receipt['attribution'],'djultra64');self.assertNotIn(str(ROOT),json.dumps(receipt))
   target=out/'pal_skip_expansion_notice.cpp';target.write_bytes(target.read_bytes()+b'\n// changed\n')
   with self.assertRaisesRegex(ValueError,'Refusing to alter'):prepare(rom,source,out)
