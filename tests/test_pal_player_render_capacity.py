"""Original work: djultra64. Actual22-player CPU traversal, no rendering stubs."""
from pathlib import Path
import json,re,struct,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
CODE=r'''
#include "recomp.h"
#include "runtime/widescreen_culling.hpp"
#include "runtime/pal_game_layout.hpp"
#include <vector>
#include <cstdio>
#include <cassert>
#include <cstring>
#include <cstdlib>
#include <set>
ORIGINALS
extern "C" void pause_self(uint8_t*){std::abort();}
static unsigned mode;static unsigned playergates,retained;
static uint32_t w(uint8_t*r,uint32_t a){uint32_t v;memcpy(&v,r+(a&0x7fffff),4);return v;}
static void put(uint8_t*r,uint32_t a,uint32_t v){memcpy(r+(a&0x7fffff),&v,4);}
void gate(uint8_t*r,recomp_context*c){auto obj=c->r4;func_80023344_resident(r,c);++playergates;if(mode&&iss2000::pal_player_culling_disabled({r,0x800000},obj)){c->r2=0;++retained;}}
void arena(uint8_t*r,recomp_context*c){func_80025910_resident(r,c);if(mode==2)assert(iss2000::extend_pal_field_matrix_arena({r,0x800000}));}
extern "C" void switch_error(const char*f,uint32_t p,uint32_t t){fprintf(stderr,"switch %s %x %x\n",f,p,t);abort();}
extern "C" void do_break(uint32_t p){fprintf(stderr,"break %x\n",p);abort();}
extern "C" recomp_func_t* get_function(int32_t a){switch(uint32_t(a)){ROUTES default:fprintf(stderr,"unknown %08x\n",uint32_t(a));abort();}}
int main(int argc,char**argv){assert(argc==2);std::vector<uint8_t>base(0x800000);FILE*f=fopen(argv[1],"rb");assert(f&&fread(base.data(),1,base.size(),f)==base.size());fclose(f);
 for(mode=0;mode<3;++mode){auto r=base;
 recomp_context c{};c.r29=int32_t(0x800a4200);c.f_odd=&c.f0.u32h;playergates=retained=0;func_8002B30C_resident(r.data(),&c);unsigned visible=0;for(unsigned n=0;n<22;++n)visible+=(w(r.data(),w(r.data(),0x801a07cc+n*256)+0x28)&0x400000)!=0;
 if(mode==1){assert(visible<22&&w(r.data(),0x8009df24)==1);}
 if(mode==2){assert(visible==22&&retained==22&&w(r.data(),0x8009df24)==0);const auto bank=w(r.data(),0x8009ded0),start=0x807c0000+bank*0x10000,cursor=w(r.data(),0x800b1a48);assert((cursor-start)/64>324&&cursor<=start+0x10000);
  std::set<uint32_t>matrices;for(unsigned n=0;n<22;++n)for(unsigned joint=0;joint<19;++joint){auto object=w(r.data(),0x801a07cc+n*256+joint*4);auto matrix=w(r.data(),object+0x18+bank*4);assert(matrix>=start&&matrix+64<=cursor&&(matrix-start)%64==0);matrices.insert(matrix);}assert(matrices.size()==418);
 }

 }
}'''
class PalPlayerRenderCapacityTests(unittest.TestCase):
 def test_all_22_high_detail_rigs_fit_and_original_small_pool_reproduces_drop(self):
  fixture=ROOT/'.local/corrections-r55/baseline/field-b.rdram'
  if not fixture.is_file():self.skipTest('Private captured live PAL field required')
  b=fixture.read_bytes();folder=ROOT/'.local/pal-map-bound-01/functions';pending=[0x8002B30C,0x802A4DC0,0x802A4F78];paths={}
  for n in range(285):
   v=struct.unpack_from('<I',b,0x145624+n*0x98+0x7c)[0]
   if v:pending.append(v)
  while pending:
   a=pending.pop()
   if a in paths:continue
   v=list(folder.glob(f'func_{a:08X}_*.c'))
   if not v:continue
   paths[a]=v[0];pending +=[int(x,16)for x in re.findall(r'LOOKUP_FUNC\(0x([0-9A-Fa-f]+)\)',v[0].read_text())]
  with tempfile.TemporaryDirectory()as directory:
   p=Path(directory);(p/'original.c').write_text('\n'.join('#include '+json.dumps(str(x))for x in paths.values()))
   code=CODE.replace('ORIGINALS','\n'.join('extern "C" void '+x.stem+'(uint8_t*,recomp_context*);'for x in paths.values())).replace('ROUTES','\n'.join(f'case 0x{a:08X}:return '+({0x80023344:'gate',0x80025910:'arena'}.get(a,x.stem))+';'for a,x in paths.items()))
   (p/'frame.cpp').write_text(code);inc=str(ROOT/'.local/deps/N64Recomp/include')
   for command in(["cc","-w","-O1","-fno-strict-aliasing","-I"+inc,"-c",str(p/'original.c'),"-o",str(p/'original.o')],["c++","-w","-std=c++20","-O1","-fno-strict-aliasing","-I"+str(ROOT/'src'),"-I"+inc,str(p/'frame.cpp'),str(p/'original.o'),str(ROOT/'src/runtime/widescreen_culling.cpp'),"-o",str(p/'frame')],[str(p/'frame'),str(fixture)]):
    q=subprocess.run(command,capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
