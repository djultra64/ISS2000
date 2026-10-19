"""Original project work: djultra64. Original articulated shadow topology proof."""
from pathlib import Path
import json,shutil,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class OriginalShadowGeometryTests(unittest.TestCase):
 def test_genuine_near_shadow_deforms_forty_vertices_without_changing_matrix_or_depth(self):
  header=ROOT/'.local/deps/N64Recomp/include';folder=ROOT/'.local/pal-map-bound-01/functions';snap=ROOT/'.local/training-timing-01/free-training-high43-completed.rdram'
  if not shutil.which('c++')or not snap.is_file():self.skipTest('Private original PAL CPU and High snapshot required')
  paths=[folder/f'func_{n}_resident.c'for n in ['800368E8','80036820','80036610']]
  code=r'''#include "recomp.h"
#include <vector>
#include <cstring>
#include <cstdio>
#include <cassert>
#include <cstdlib>
ORIGINALS
using Bytes=std::vector<uint8_t>;
uint32_t word(const Bytes&r,uint32_t a){uint32_t v;memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
void put(Bytes&r,uint32_t a,uint32_t v){memcpy(r.data()+(a&0x7fffff),&v,4);}
extern "C" recomp_func_t*get_function(int32_t p){switch(uint32_t(p)){case 0x80036820:return func_80036820_resident;case 0x80036610:return func_80036610_resident;default:abort();}}
int main(int argc,char**argv){assert(argc==2);Bytes original(0x800000);auto*f=fopen(argv[1],"rb");assert(f&&fread(original.data(),1,original.size(),f)==original.size());fclose(f);
 constexpr uint32_t output=0x8039D000,pose=0x8012AAF0;
 auto render=[&](Bytes&r){put(r,0x800BD618,output);put(r,0x800BD61C,pose);recomp_context c{};c.r29=int32_t(0x800A4200);c.f_odd=&c.f0.u32h;func_800368E8_resident(r.data(),&c);assert(word(r,0x800BD618)==output+640);};
 auto a=original,b=original; // Pose changed one original endpoint, without changing playerworld/objectmatrix.
 float value;memcpy(&value,b.data()+(pose&0x7fffff),4);value+=2;uint32_t bits;memcpy(&bits,&value,4);put(b,pose,bits);
 render(a);render(b);unsigned changed=0;
 for(unsigned i=0;i<640;++i)if(a[(output&0x7fffff)+i]!=b[(output&0x7fffff)+i]){assert((i%16>=2&&i%16<4)||(i%16>=6&&i%16<8));++changed;}
 assert(changed>0); // CPU-deformed vertex data, not a changing rigid matrix.
 for(unsigned i=0;i<64;++i)assert(a[0x1A3F00+i]==original[0x1A3F00+i]&&b[0x1A3F00+i]==original[0x1A3F00+i]);
 for(uint32_t material:{0x80083B90u,0x80083BC8u}){assert(word(a,material)==0xE2001D00&&word(a,material+4)==4);assert(word(a,material+8)==0xEE000000&&word(a,material+12)==0x7FFF7FFF);}
 assert(word(a,0x80083AD0)==0xE200001C&&word(a,0x80083AD4)==0x005049F8);
 // Genuine40vertexdraw and triangle topology never change betweenposes.
 assert(word(a,0x80083B00)==0x0101C038);for(unsigned i=0;i<0xB0;++i)assert(a[0x83AD0+i]==b[0x83AD0+i]);
}
'''.replace('ORIGINALS','\n'.join('#include '+json.dumps(str(p))for p in paths))
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);(p/'shadow.cpp').write_text(code);q=subprocess.run(['c++','-std=c++20','-O2','-I'+str(header),str(p/'shadow.cpp'),'-o',str(p/'shadow')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
   q=subprocess.run([str(p/'shadow'),str(snap)],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
