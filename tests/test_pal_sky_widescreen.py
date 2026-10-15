"""Original project work: djultra64. Sky geometry and allocation invariants."""
from pathlib import Path
import shutil, subprocess, tempfile, unittest
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(shutil.which('c++'),'C++20 compiler required')
class PalSkyTests(unittest.TestCase):
 def test_sampling_coverage_and_guarded_guest_writes(self):
  source=r'''#include "runtime/pal_sky_widescreen.hpp"
#include <cassert>
#include <cstring>
#include <vector>
using namespace iss2000;
void put(std::vector<uint8_t>& r,uint32_t a,uint32_t v){std::memcpy(r.data()+(a&0x7fffff),&v,4);}
int main(){
 std::vector<uint8_t> r(0x800000);const uint32_t base=0x800D0320,dl=base+8;
 put(r,0x800A4AA4,base);put(r,0x8009E0C8,dl);
 auto b=pal_gfx_bounds(r);assert(b.begin==base+8&&b.end==base+0x10008&&b.cursor==dl);
 for(int phase=0;phase<64;++phase){
  int last=0,count=0;
  for(int col=0;col<8;++col){auto q=pal_sky_rectangle(-phase-64+col*64,0,0,false);if(!q.visible)continue;
   int left=(q.words[1]>>12)&4095,right=(q.words[0]>>12)&4095;
   assert(left==last&&right>left&&right<=1280);last=right;++count;
   assert((q.words[5]>>16)==5461);assert((q.words[5]&65535)==1024);
  }
  assert(last==1280&&count>=7);
 }
 auto q=pal_sky_rectangle(0,0,0,false);assert(q.visible);
 assert(((q.words[0]>>12)&4095)-((q.words[1]>>12)&4095)==192); // 48 guest px ->64 physical.
 auto hi=pal_sky_rectangle(0,0,0,true);assert(((hi.words[0]>>12)&4095)-((hi.words[1]>>12)&4095)==384);assert((hi.words[5]>>16)==2731);
 auto clip=pal_sky_rectangle(-64,-16,0x80,false);assert(clip.visible);assert(((clip.words[1]>>12)&4095)==0);assert((clip.words[3]>>16)==uint32_t(64*32+341));assert((clip.words[3]&65535)==48*32);
 assert(!pal_sky_rectangle(-128,0,0,false).visible);assert(!pal_sky_rectangle(400,0,0,false).visible);assert(!pal_sky_rectangle(0,240,0,false).visible);
 auto before=r;assert(!pal_sky_preflight(r,false));assert(r==before);
 // Original row table alternates a distinct texture pair: <=32 entries/texture.
 for(int row=0;row<24;++row)for(int col=0;col<14;++col)r[(0x8384c+row*14+col)^3]=uint8_t((row<10?0:row<17?(row-9)*2:14)+(col&1));
 assert(pal_sky_preflight(r,true));
 {
  auto initial=pal_gfx_bounds(r);PalSkyWriteScope scope(r,true);assert(scope);
  iss2000_pal_sky_aspect(r.data(),1);
  assert(append_pal_sky_rectangle(r,initial.cursor+16,initial.end,0,0,0,false)==initial.cursor+40);
  put(r,0x8009E0C8,initial.cursor+40);iss2000_pal_sky_aspect(r.data(),0);
  uint32_t v;std::memcpy(&v,r.data()+(initial.cursor&0x7fffff),4);assert(v==0xE0525464);
  std::memcpy(&v,r.data()+(initial.cursor&0x7fffff)+16-4,4);assert(v==1);
  std::memcpy(&v,r.data()+(initial.cursor&0x7fffff)+44,4);assert(v==0);
  put(r,0x8009E0C8,dl);
 }
 auto saved=r;r[(0x8384c+3)^3]=0;assert(!pal_sky_preflight(r,true));r=saved;
 put(r,0x8009E0C8,b.end-0x9f8);assert(!pal_sky_preflight(r,true));
 put(r,0x8009E0C8,dl);put(r,0x800A4AA4,base+0x10060);assert(!pal_gfx_bounds(r));
 put(r,0x800A4AA4,base);put(r,0x8009E0C8,dl+4);assert(!pal_gfx_bounds(r));
 put(r,0x8009E0C8,dl);saved=r;
 assert(append_pal_sky_rectangle(r,dl,b.end,0,0,0,false)==dl+24);
 for(unsigned i=0;i<6;++i){uint32_t w;std::memcpy(&w,r.data()+(dl&0x7fffff)+4*i,4);assert(w==q.words[i]);}
 for(size_t i=0;i<r.size();++i)if(i<(dl&0x7fffff)||i>=(dl&0x7fffff)+24)assert(r[i]==saved[i]);
 saved=r;assert(!append_pal_sky_rectangle(r,dl,dl+16,0,0,0,false));assert(r==saved);
}
'''
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'test.cpp').write_text(source)
   result=subprocess.run(['c++','-std=c++20','-O2','-Wall','-Wextra','-Werror','-I'+str(ROOT/'src'),str(p/'test.cpp'),str(ROOT/'src/runtime/pal_sky_widescreen.cpp'),'-o',str(p/'test')],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
   subprocess.run([str(p/'test')],check=True)

class PalSkyGeneratorGuards(unittest.TestCase):
 def test_wrong_rom_and_generated_source_are_rejected_before_output(self):
  from tools.prepare_pal_sky import prepare, derive
  with self.assertRaisesRegex(ValueError,'source digest mismatch'):
   derive(b'RECOMP_FUNC void unrelated_source() {}')
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'rom').write_bytes(b'wrong revision');(p/'source').write_bytes(b'wrong source')
   with self.assertRaisesRegex(ValueError,'ROM/sky body digest mismatch'):
    prepare(p/'rom',p/'source',p/'output')
   self.assertFalse((p/'output').exists())
