"""Original project work: djultra64. PAL VI/projection and genuine frustum tests."""
from pathlib import Path
import json,re,shutil,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class PalCullingVideoTests(unittest.TestCase):
 def test_original_visibility_matches_pinned_rt64_pal_projection_and_retains_far_culling(self):
  h=ROOT/'.local/deps/N64Recomp/include';g=ROOT/'.local/pal-map-bound-01/functions/func_80023604_resident.c'
  high=ROOT/'.local/training-timing-01/free-training-high43-completed.rdram';low=ROOT/'.local/training-timing-01/free-training-low.rdram'
  if not shutil.which('c++') or not all(x.is_file()for x in [g,high,low,h/'recomp.h']):self.skipTest('Private PAL originals required')
  vi=(ROOT/'.local/deps/rt64/src/hle/rt64_vi.cpp').read_text();body=re.search(r'    hlslpp::uint2 VI::fbSize\(\) const \{.*?\n    \}',vi,re.S).group().replace('VI::','')
  code=r'''#include "recomp.h"
#include "runtime/widescreen_culling.hpp"
#include <vector>
#include <cstring>
#include <cmath>
#include <cassert>
#include <cstdio>
#include <cstdint>
ORIGINAL
namespace hlslpp {struct uint2 {unsigned x,y;uint2(unsigned a,unsigned b):x(a),y(b){}};}
struct VI {struct {bool serrate;}status;unsigned width;struct{unsigned hEnd,hStart;}hRegion;struct{unsigned vEnd,vStart;}vRegion;unsigned xs,ys;
 float xScaleFloat()const{return 1024.f/xs;}float yScaleFloat()const{return 1024.f/ys;}
 VI_FUNCTION
};
using Bytes=std::vector<uint8_t>;
uint32_t w(const Bytes&r,uint32_t a){uint32_t v;memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
void put(Bytes&r,uint32_t a,uint32_t v){memcpy(r.data()+(a&0x7fffff),&v,4);}
void fput(Bytes&r,uint32_t a,float f){uint32_t v;memcpy(&v,&f,4);put(r,a,v);}
Bytes load(const char*p){Bytes b(0x800000);auto*f=fopen(p,"rb");assert(f&&fread(b.data(),1,b.size(),f)==b.size());fclose(f);return b;}
int culled(Bytes&r,float x,float y,float z){const uint32_t sp=0x800A4000,obj=0x8014D000;
 fput(r,obj,x);fput(r,obj+4,y);fput(r,obj+8,z);for(unsigned i=0;i<36;i+=4)put(r,sp+0x10+i,0);
 fput(r,sp+0x18,1);fput(r,sp+0x20,1);fput(r,sp+0x28,1); // Original view basis depthZ,verticalY,horizontalX.
 r[((obj+0x6c)&0x7fffff)^3]=0;r[((obj+0x6d)&0x7fffff)^3]=0;
 recomp_context c{};c.r4=int32_t(obj);c.r29=int32_t(sp);c.f_odd=&c.f0.u32h;func_80023604_resident(r.data(),&c);return int(c.r2);}
int main(int argc,char**argv){assert(argc==3);
 for(int mode=0;mode<2;++mode){auto b=load(argv[mode?1:2]);auto base=mode?0x80099040u:0x80098DC0u;
  VI vi{};vi.status.serrate=w(b,base+4)&0x40;vi.width=w(b,base+8);vi.hRegion={w(b,base+28)&65535,w(b,base+28)>>16};vi.vRegion={w(b,base+48)&65535,w(b,base+48)>>16};vi.xs=w(b,base+32)&4095;vi.ys=w(b,base+44)&4095;
  auto size=vi.fbSize();assert(size.x==(mode?640u:320u)&&size.y==(mode?524u:264u));
  float scale=iss2000::pal_widescreen_projection_scale(b);
  if(!mode){assert(fabs(scale-4.f/3.f)<1e-6);continue;} // LowliveVIscale is not inferred from storedmode.
  auto layout=iss2000::verified_pal_widescreen_layout(scale);
  fput(b,0x8009DF00,4.f/3.f);fput(b,0x8009E09C,1);fput(b,0x8009DFE8,.75f);fput(b,0x800A7824,100);fput(b,0x800A7828,75);
  fput(b,0x8009E114,.1f);fput(b,0x8009DEBC,1000);
  auto legacy=b;assert(iss2000::apply_widescreen_culling(legacy,true,iss2000::verified_pal_widescreen_layout()));assert(culled(legacy,14,0,-10)==1);
  auto four=b;assert(iss2000::apply_widescreen_culling(four,false,layout));assert(four==b);
  assert(iss2000::apply_widescreen_culling(b,true,layout));assert(culled(b,14,0,-10)==0);assert(culled(b,-14,0,-10)==0);
  assert(culled(b,16,0,-10)==1&&culled(b,-16,0,-10)==1);assert(culled(b,0,8,-10)==1);assert(culled(b,0,0,-1100)==1);
  auto same=b;assert(iss2000::ensure_widescreen_far_extents(b,true,layout));assert(b==same);
  for(int bad=0;bad<4;++bad){auto r=b;if(bad==0)put(r,base+48,0);if(bad==1)put(r,0x8009E02C,0);if(bad==2)put(r,0x8013B42C,0);if(bad==3)r[0x13b42a^3]=2;auto old=r;
   assert(iss2000::pal_widescreen_projection_scale(r)==0);auto invalid=iss2000::verified_pal_widescreen_layout(0);assert(!iss2000::apply_widescreen_culling(r,true,invalid));assert(r==old);}
 }
}
'''.replace('ORIGINAL','#include '+json.dumps(str(g))).replace('VI_FUNCTION',body)
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);(p/'check.cpp').write_text(code)
   result=subprocess.run(['c++','-std=c++20','-O2','-I'+str(ROOT/'src'),'-I'+str(h),str(p/'check.cpp'),str(ROOT/'src/runtime/widescreen_culling.cpp'),'-o',str(p/'check')],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
   result=subprocess.run([str(p/'check'),str(high),str(low)],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
