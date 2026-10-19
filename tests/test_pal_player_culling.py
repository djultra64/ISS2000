"""Original work: djultra64. Real PAL player AABB visibility and exact rig ownership."""
from pathlib import Path
import json,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
CODE=r'''#include "runtime/widescreen_culling.hpp"
#include "recomp.h"
#include <cassert>
#include <cstdio>
#include <cstring>
#include <vector>
DECLS
extern "C" recomp_func_t*get_function(int32_t a){switch(uint32_t(a)){ROUTES default:assert(false);return nullptr;}}
using Bytes=std::vector<uint8_t>;
uint32_t word(const Bytes&r,uint32_t a){uint32_t v;memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
void put(Bytes&r,uint32_t a,uint32_t v){memcpy(r.data()+(a&0x7fffff),&v,4);}
void fp(Bytes&r,uint32_t a,float f){uint32_t v;memcpy(&v,&f,4);put(r,a,v);}
Bytes load(const char*p){FILE*f=fopen(p,"rb");assert(f);Bytes b(0x800000);assert(fread(b.data(),1,b.size(),f)==b.size());fclose(f);return b;}
namespace iss2000 {
unsigned original_calls;
void run_original_guest(uint32_t pc,uint8_t* ram,recomp_context* c){assert(pc==0x80023344);++original_calls;func_80023344_resident(ram,c);}
NATIVE_WRAPPER
}
bool enabled(const Bytes&r,uint32_t root){return iss2000::pal_player_culling_disabled(r,root);}
void exercise(Bytes r,uint32_t root,float x,bool player){
 // Original actual player AABB gate in a controlled orthonormal camera.
 put(r,0x8009e0b4,0);for(unsigned p=0x800a7800;p<0x800a7838;p+=4)fp(r,p,0);fp(r,0x800a7800,1);fp(r,0x800a7810,1);fp(r,0x800a7820,1);
 fp(r,0x800a7824,100);fp(r,0x800a7828,75);fp(r,0x8009debc,1000);fp(r,0x8009e114,.1f);fp(r,root,x);fp(r,root+4,0);fp(r,root+8,-100);
 auto original=r;recomp_context c{};c.r4=int32_t(root);c.r29=int32_t(0x800a4000);c.f_odd=&c.f0.u32h;func_80023344_resident(original.data(),&c);
 if(player)assert(c.r2==(x==0?0:1)); // Visible center, entirely offscreen left and right.
 const auto before=r;assert(enabled(r,root)==player&&r==before);
 auto adapted=r;recomp_context d{};d.r4=int32_t(root);d.r29=int32_t(0x800a4000);d.f_odd=&d.f0.u32h;iss2000::original_calls=0;iss2000::retain_football_player(adapted.data(),&d);
 assert(iss2000::original_calls==1&&adapted==original);
 if(player)c.r2=0;c.f_odd=d.f_odd;assert(memcmp(&c,&d,sizeof(c))==0); // Every register/FPU word and RAM side effect except player return are original.
}
int main(int argc,char**argv){assert(argc==5);
 for(unsigned frame=0;frame<4;++frame){const auto base=load(argv[frame+1]);const unsigned count=frame==1?11:22;
  for(unsigned n=0;n<count;++n){const auto state=0x801a07cc+n*256,root=word(base,state);assert(root>=0x80145624&&word(base,root+0x84)==state);
   for(float x:{-300.f,0.f,300.f})exercise(base,root,x,true);
   assert(!enabled(base,word(base,state+4))); // An articulated limb cannot authorize another object.
   for(unsigned variant=0;variant<8;++variant){auto bad=base;if(variant==0)put(bad,root+0x84,state+1);if(variant==1)put(bad,state,root+0x98);if(variant==2)put(bad,root+0x28,word(bad,root+0x28)&0x7fffffff);if(variant==3)bad[0x13b44c^3]=7;if(variant==4)put(bad,0x8009e02c,0);if(variant==5)put(bad,state+4,root);if(variant==6)put(bad,root+0x48,0);if(variant==7)put(bad,0x8013b42c,0);const auto same=bad;assert(!enabled(bad,root)&&bad==same);}
  }
  for(unsigned n=count;n<26;++n){const auto root=word(base,0x801a07cc+n*256);assert(!enabled(base,root));if(root>=0x80145624&&root<0x8014ff5c)exercise(base,root,300,false);} // Actual referee/staff roots retain their original rejection.
 }
}'''
class PalPlayerCullingTests(unittest.TestCase):
 def test_actual_original_player_gate_preserves_all_22_players_and_other_owners(self):
  g=ROOT/'.local/pal-map-bound-01/functions';h=ROOT/'.local/deps/N64Recomp/include';field=ROOT/'.local/hidden-test-01/field16-tooltip-completed.rdram';training=ROOT/'.local/training-timing-01/free-training-high43-completed.rdram';paused=ROOT/'.local/hidden-test-01/field16-pause-controls-completed.rdram';live=ROOT/'.local/corrections-r55/baseline/field-b.rdram';names=['80023344','800231CC','80022F00','80022D90','80022B38','8002286C']
  paths=[g/('func_'+n+'_resident.c')for n in names]
  if not all(p.is_file()for p in [*paths,h/'recomp.h',field,training,paused,live]):self.skipTest('Private PAL originals required')
  native=(ROOT/'src/runtime/native_game.cpp').read_text();a=native.index('void retain_football_player(');opening=native.index('{',a);end=opening+1;depth=1
  while depth:
   depth+=(native[end]=='{')-(native[end]=='}');end+=1
  wrapper=native[a:end]
  code=CODE.replace('NATIVE_WRAPPER',wrapper).replace('DECLS','\n'.join('extern "C" void '+p.stem+'(uint8_t*,recomp_context*);'for p in paths)).replace('ROUTES','\n'.join('case 0x'+n+':return func_'+n+'_resident;'for n in names))
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);(p/'test.cpp').write_text(code);(p/'original.c').write_text('\n'.join('#include '+json.dumps(str(f))for f in paths))
   q=subprocess.run(['cc','-O1','-fno-strict-aliasing','-I'+str(h),'-c',str(p/'original.c'),'-o',str(p/'original.o')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
   q=subprocess.run(['c++','-std=c++20','-O1','-I'+str(ROOT/'src'),'-I'+str(h),str(p/'test.cpp'),str(p/'original.o'),str(ROOT/'src/runtime/widescreen_culling.cpp'),'-o',str(p/'test')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
   q=subprocess.run([str(p/'test'),str(field),str(training),str(paused),str(live)],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
