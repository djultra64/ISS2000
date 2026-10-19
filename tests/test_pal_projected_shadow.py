"""Original project work: djultra64. Pose-driven simplified projected silhouettes."""
from pathlib import Path
import subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
CODE=r'''
#include "runtime/pal_projected_shadow.hpp"
#include "runtime/pal_shadow_vertices.hpp"
#include <cassert>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <vector>
using namespace iss2000;using Bytes=std::vector<uint8_t>;
uint32_t w(const Bytes&r,uint32_t p){uint32_t v;memcpy(&v,r.data()+(p&0x7fffff),4);return v;}
void put(Bytes&r,uint32_t p,uint32_t v){memcpy(r.data()+(p&0x7fffff),&v,4);}
float f(const Bytes&r,uint32_t p){float v;memcpy(&v,r.data()+(p&0x7fffff),4);return v;}
void fp(Bytes&r,uint32_t p,float v){memcpy(r.data()+(p&0x7fffff),&v,4);}
int main(int argc,char**argv){assert(argc==2);Bytes base(0x800000);auto*file=fopen(argv[1],"rb");assert(file&&fread(base.data(),1,base.size(),file)==base.size());fclose(file);
 const unsigned players=base[0x12de74^3]==4?11:25;
 for(unsigned lighting=0;lighting<4;++lighting)for(unsigned bank=0;bank<2;++bank)for(unsigned player=0;player<players;++player){auto r=base;const auto root=w(r,0x801a07cc+player*256),object=w(r,root+0x4c);assert(object);
  put(r,0x8009ded0,bank);put(r,object+0x5c,w(r,w(r,object+0x80))+bank*640);put(r,object+0x24,lighting==3?0x80083ce0:lighting==2?0x80083d60:lighting?0x80083bc8:0x80083b90);put(r,0x800839e0,lighting>=2?2:lighting);put(r,object+0x28,w(r,object+0x28)|0x80004000);
  const float dx=f(r,root)-f(r,0x8012aaf0+4*12),dz=f(r,root+8)-f(r,0x8012aaf0+4*12+8);
  for(unsigned n=0;n<11;++n){fp(r,0x8012aaf0+n*12,f(r,0x8012aaf0+n*12)+dx);fp(r,0x8012aaf0+n*12+8,f(r,0x8012aaf0+n*12+8)+dz);}
  if(lighting>=2){
   const auto v=w(r,object+0x5c);auto sh=[&](uint32_t p,int16_t h){memcpy(r.data()+((p&0x7fffff)^2),&h,2);};
   const float cx=f(r,0x8012aaf0+5*12)*10,cz=f(r,0x8012aaf0+5*12+8)*10,cy=f(r,0x8012aaf0+5*12+4)*20;
   for(unsigned n=0;n<(lighting==3?16u:8u);++n){sh(v+n*16,int16_t(cx+(n<4?-cy:cy)));sh(v+n*16+4,int16_t(cz+cy));r[((v+n*16+15)&0x7fffff)^3]=n<4?100:40;}
   // Far-edge midpoint of the first original floodlight quad is(-2,+2).
  }
  const auto before=r;assert(project_pal_shadow(r,object));auto mesh=pal_projected_shadow(r,object,bank);assert(mesh&&mesh->vertices>=0x807e0000+bank*0x10000&&mesh->vertices+80*16<=0x807f0000+bank*0x10000);
  assert(!pal_projected_shadow(r,object,1-bank));assert(w(r,object+0x5c)==mesh->vertices&&w(r,object+0x24)==mesh->display_list);
  assert(memcmp(r.data()+0x7c0000,before.data()+0x7c0000,0x20000)==0);assert(memcmp(r.data()+0x12aaf0,before.data()+0x12aaf0,132)==0);
  unsigned triangles=0,loads=0,mode=0;for(auto pc=mesh->display_list;pc<mesh->display_list+352;pc+=8){auto a=w(r,pc),b=w(r,pc+4);if(a==0xe200001c)mode=(mode&0xf0000000u)|(b&0x0fffffffu);if(a==0xe2001d00)mode=(mode&~4u)|(b&4u);if(a>>24==1){assert(!(mode&4u));++loads;assert((b&0x1fffffff)>=(mesh->vertices&0x1fffffff));}if(a>>24==6)triangles+=2;assert(a>>24!=0xee);if(a>>24==0xfa)assert(b==(lighting?64u:96u));}assert(triangles==60&&loads==4);
  for(unsigned n=0;n<80;++n){int16_t y;memcpy(&y,r.data()+(((mesh->vertices+n*16+2)&0x7fffff)^2),2);assert(y==1);}
  auto pre_match=before;pre_match[0x13b44c^3]=16;assert(project_pal_shadow(pre_match,object));
  // One immutable task tag per player covers all four real vertex loads.
  PalShadowVertices tags;tags.allocation(object);put(r,0x800b1a48,0x800a7848+bank*0x5100);put(r,0x800b1a4c,0x800ac948+bank*0x5100);tags.begin_frame(r);assert(tags.capture(r,object));
  // Actual new silhouette is pose dependent and keeps the same topology.
  auto changed=before;fp(changed,0x8012aaf0+7*12,f(changed,0x8012aaf0+7*12)+2);assert(project_pal_shadow(changed,object));assert(memcmp(r.data()+(mesh->vertices&0x7fffff),changed.data()+(mesh->vertices&0x7fffff),1280)!=0);
  for(unsigned variant=0;variant<7;++variant){if(variant==6&&lighting<2)continue;auto bad=before;if(variant==0)put(bad,object+0x7c,0);if(variant==1)put(bad,root+0x84,0);if(variant==2)put(bad,object+0x24,0x80083c70);if(variant==3)fp(bad,0x8012aaf0,NAN);if(variant==4)bad[0x13b44c^3]=7;if(variant==5)put(bad,0x80083ad0,0);if(variant==6)put(bad,lighting==3?0x80083d00:0x80083d80,0);const auto original=bad;assert(!project_pal_shadow(bad,object)&&bad==original);}
 }
}
'''
class ProjectedShadowTests(unittest.TestCase):
 def test_original_pose_drives_banked_mesh_with_owned_interpolation(self):
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);(p/'test.cpp').write_text(CODE)
   q=subprocess.run(['c++','-std=c++20','-O1','-pthread','-I'+str(ROOT/'src'),str(p/'test.cpp'),*[str(ROOT/'src/runtime'/x)for x in ['pal_projected_shadow.cpp','pal_shadow_vertices.cpp','graphics_task_bank.cpp']],'-o',str(p/'test')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
   for snapshot in ['.local/training-timing-01/free-training-high43-completed.rdram','.local/hidden-test-01/field16-tooltip-completed.rdram']:
    q=subprocess.run([str(p/'test'),str(ROOT/snapshot)],capture_output=True,text=True);self.assertEqual(q.returncode,0,snapshot+':'+q.stderr)


BALL_CODE=r'''
#include "runtime/pal_projected_shadow.hpp"
#include "runtime/pal_shadow_vertices.hpp"
#include <cassert>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <vector>
using namespace iss2000;using Bytes=std::vector<uint8_t>;
uint32_t w(const Bytes&r,uint32_t p){uint32_t v;memcpy(&v,r.data()+(p&0x7fffff),4);return v;}
void put(Bytes&r,uint32_t p,uint32_t v){memcpy(r.data()+(p&0x7fffff),&v,4);}
float f(const Bytes&r,uint32_t p){float v;memcpy(&v,r.data()+(p&0x7fffff),4);return v;}
void fp(Bytes&r,uint32_t p,float v){memcpy(r.data()+(p&0x7fffff),&v,4);}
int16_t h(const Bytes&r,uint32_t p){int16_t v;memcpy(&v,r.data()+((p&0x7fffff)^2),2);return v;}
int main(int argc,char**argv){assert(argc==2);Bytes base(0x800000);auto*file=fopen(argv[1],"rb");assert(file&&fread(base.data(),1,base.size(),file)==base.size());fclose(file);
 const auto root=w(base,0x802b57d0),child=w(base,0x802b43f4);assert(root&&child);
 for(unsigned lighting=0;lighting<3;++lighting)for(unsigned bank=0;bank<2;++bank)for(float height:{1.4f,20.f,100.f}){
  auto r=base;put(r,0x8009ded0,bank);put(r,0x800839e0,lighting);fp(r,root+4,height);const auto before=r;
  assert(project_pal_shadow(r,root));const auto mesh=pal_projected_shadow(r,root,bank);assert(mesh&&!pal_projected_shadow(r,root,1-bank));
  assert(w(r,child+0x24)==mesh->display_list&&w(r,root+0x24)==w(before,root+0x24));
  unsigned triangles=0,loads=0;for(auto pc=mesh->display_list;pc<mesh->display_list+144;pc+=8){const auto a=w(r,pc),b=w(r,pc+4);
   if(a>>24==1){assert(a==0x01010020&&b==mesh->vertices);++loads;}if(a>>24==6)triangles+=2;
   if(a>>24==0xfa)assert(b==(lighting?64u:96u));assert(a>>24!=0xee&&a>>24!=0xfd);
  }assert(loads==1&&triangles==14);
  float cx=0,cz=0;for(unsigned n=0;n<16;++n){cx+=h(r,mesh->vertices+n*16);cz+=h(r,mesh->vertices+n*16+4);assert(h(r,mesh->vertices+n*16+2)==1);}
  cx/=16;cz/=16;const float lx=lighting==2?2.f:-.5f,lz=lighting==2?(f(before,root+8)>0?-2.f:2.f):.5f;assert(std::abs(cx-(f(before,root)+height*lx)*10)<1);assert(std::abs(cz-(f(before,root+8)+height*lz)*10)<1);
  const auto slot=mesh->display_list-0x580;assert(slot==0x807e0000+bank*0x10000+25*0x800);
  for(unsigned n=0;n<r.size();++n)if(r[n]!=before[n])assert((n>=(slot&0x7fffff)&&n<(slot&0x7fffff)+0x800)||(n>=((child+0x24)&0x7fffff)&&n<((child+0x28)&0x7fffff)));
  PalShadowVertices tags;tags.allocation(root);put(r,0x800b1a48,0x800a7848+bank*0x5100);put(r,0x800b1a4c,0x800ac948+bank*0x5100);tags.begin_frame(r);assert(tags.capture(r,root));
  TransformTaskFingerprint task{0x80001000,0x80069ad0,0x80099ef0,16};put(r,0x80001000,0xda380007);put(r,0x80001004,0x800c1ac0+bank*64);put(r,0x80001008,0xdf000000);put(r,0x8000100c,0);
  tags.submit(r,1,task);auto snapshot=tags.consume(task);assert(snapshot&&snapshot->tags.size()==1);const auto id=snapshot->tags[0].first_id;
  assert(snapshot->lookup(mesh->vertices,16,0)==id);assert(!snapshot->lookup(mesh->vertices,24,0)&&!snapshot->lookup(mesh->vertices,16,1));
  tags.release(root);assert(!tags.capture(r,root));assert(snapshot->lookup(mesh->vertices,16,0)==id);
  restore_pal_ball_shadow(r,root);assert(w(r,child+0x24)==0x802b2780);assert(!pal_projected_shadow(r,root,bank));
  r[0x13b44c^3]=7;const auto foreign=r;assert(!project_pal_shadow(r,root)&&r==foreign);
 }
 for(unsigned variant=0;variant<8;++variant){auto r=base;
  if(variant==0)put(r,root+0x7c,0);if(variant==1)put(r,child+0x44,0);if(variant==2)put(r,0x802b2788,0);
  if(variant==3)fp(r,root+4,NAN);if(variant==4)put(r,0x8009ded0,2);if(variant==5)r[0x13b44c^3]=7;
  if(variant==6)put(r,0x802b57d0,root+0x98);if(variant==7)put(r,0x802a472c,0);const auto before=r;
  assert(!project_pal_shadow(r,root)&&r==before);
 }
}
'''
class BallShadowTests(unittest.TestCase):
 def test_ball_uses_player_material_ground_projection_and_owned_banked_interpolation(self):
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);(p/'test.cpp').write_text(BALL_CODE)
   q=subprocess.run(['c++','-std=c++20','-O1','-pthread','-I'+str(ROOT/'src'),str(p/'test.cpp'),*[str(ROOT/'src/runtime'/x)for x in ['pal_projected_shadow.cpp','pal_shadow_vertices.cpp','graphics_task_bank.cpp']],'-o',str(p/'test')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
   for snapshot in ['.local/training-timing-01/free-training-high43-completed.rdram','.local/hidden-test-01/field16-tooltip-completed.rdram']:
    q=subprocess.run([str(p/'test'),str(ROOT/snapshot)],capture_output=True,text=True);self.assertEqual(q.returncode,0,snapshot+':'+q.stderr)
