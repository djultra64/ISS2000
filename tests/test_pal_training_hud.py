"""Original project work: djultra64. Genuine Training radar closure, CPU only."""
from pathlib import Path
import json,re,shutil,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class TrainingHudOriginalTests(unittest.TestCase):
 def test_training_radar_background_and_all_world_markers_share_visible_bottom_anchor(self):
  g=ROOT/'.local/pal-map-bound-01/functions';h=ROOT/'.local/deps/N64Recomp/include';snap=ROOT/'.local/training-timing-01/free-training-high43-completed.rdram'
  if not shutil.which('c++') or not snap.is_file():self.skipTest('Private completed High fixture required')
  paths={pc:g/f'func_{pc:08X}_overlay_376010_802a4380.c'for pc in [0x802A4DC0,0x802A4F78,0x802A5180,0x802A5230,0x802A5290]}
  code=r'''#include "recomp.h"
#include "runtime/pal_hud_widescreen.hpp"
#include <vector>
#include <cstring>
#include <cassert>
#include <cstdio>
#include <cstdlib>
ORIGINALS
using Bytes=std::vector<uint8_t>;
static bool enhanced;static unsigned markers;
static uint32_t w(const uint8_t*r,uint32_t a){uint32_t v;std::memcpy(&v,r+(a&0x7fffff),4);return v;}
static void put(Bytes&r,uint32_t a,uint32_t v){std::memcpy(r.data()+(a&0x7fffff),&v,4);}
static void byte(Bytes&r,uint32_t a,uint8_t v){r[(a&0x7fffff)^3]=v;}
namespace iss2000 {
enum class AspectRatio {Wide16x9,Original4x3};
namespace platform {struct Settings {AspectRatio aspect_ratio;};Settings render_settings(){return {enhanced?AspectRatio::Wide16x9:AspectRatio::Original4x3};}}
ACTUAL_WRAPPERS
}
static void marker(uint8_t*r,recomp_context*c){iss2000::align_training_radar_marker(r,c);++markers;}
static void projected_marker(uint8_t*r,recomp_context*c){iss2000::align_projected_radar_marker(r,c);++markers;}
extern "C" recomp_func_t* get_function(int32_t a){switch(uint32_t(a)){
 case 0x802A4DC0:return marker;
 case 0x802A4F78:return projected_marker;
 LOOKUPS
 default:std::abort();}}
int main(int argc,char**argv){assert(argc==3);Bytes base(0x800000);auto*f=std::fopen(argv[1],"rb");assert(f&&std::fread(base.data(),1,base.size(),f)==base.size());std::fclose(f);
 auto p=iss2000::pal_hud_placement(base,true,iss2000::PalHudDraw::Sprite,0x8013C47C);
 assert(p && p.y_offset==224 && p.x_offset==0); // Radar bottom452 +56 =508 of524 visible rows.
 auto l=iss2000::pal_hud_placement(base,true,iss2000::PalHudDraw::Sprite,0x8013C4B8);
 assert(l && l.x_offset==-744 && l.y_offset==168); // Original -7 +28logical, no horizontal change.
 auto ordinary=base;byte(ordinary,0x8012DE74,0);
 assert(iss2000::pal_hud_placement(ordinary,true,iss2000::PalHudDraw::Sprite,0x8013C47C).y_offset==224&&"Ordinary field radar must use the same proven visible bottom anchor");
 assert(iss2000::pal_hud_placement(ordinary,true,iss2000::PalHudDraw::Sprite,0x8013C4B8).y_offset==168);
 CLOSURE
}
'''
  # First assertion alone is meaningful against the original helper, before the marker API exists.
  code=code.replace('ORIGINALS','\n'.join('#include '+json.dumps(str(p))for p in paths.values())).replace('LOOKUPS','\n'.join(f'case 0x{pc:08X}:return {p.stem};'for pc,p in paths.items()if pc not in (0x802A4DC0,0x802A4F78)))
  native=(ROOT/'src/runtime/native_game.cpp').read_text()
  wrappers='\n'.join(re.search(r'void '+name+r'\(.*?\n\}',native,re.S).group()for name in ('align_training_radar_marker','align_projected_radar_marker'))
  self.assertIn('func_802A4DC0_overlay_376010_802a4380',wrappers)
  self.assertIn('func_802A4F78_overlay_376010_802a4380',wrappers)
  code=code.replace('ACTUAL_WRAPPERS',wrappers)
  code=code.replace('CLOSURE',r'''
 Bytes low(0x800000);f=std::fopen(argv[2],"rb");assert(f&&std::fread(low.data(),1,low.size(),f)==low.size());std::fclose(f);
 for(unsigned high=0;high<2;++high)for(unsigned training=0;training<2;++training)for(unsigned projected=0;projected<2;++projected)for(unsigned buffer=0;buffer<2;++buffer){
 auto input=high?base:low;byte(input,0x8012DE74,training?4:0);byte(input,0x8012E6A3,projected);byte(input,0x8013B418,0);byte(input,0x8013B419,buffer);
 const int shift=high?224:-4;
 const auto p=iss2000::pal_hud_placement(input,true,iss2000::PalHudDraw::Sprite,0x8013C47C);
 const auto left=iss2000::pal_hud_placement(input,true,iss2000::PalHudDraw::Sprite,0x8013C4B8);
 assert(p&&p.x_offset==0&&p.y_offset==shift&&left.y_offset==(high?168:-32));
 auto before=input,after=input,four=input;const auto object=w(input.data(),0x802B2950);assert(object);
 auto run=[&](Bytes&r,bool wide){recomp_context c{};c.r4=int32_t(object);c.r29=int32_t(0x800A4200);c.f_odd=&c.f0.u32h;enhanced=wide;markers=0;func_802A5290_overlay_376010_802a4380(r.data(),&c);assert(markers>=12);return markers;};
 auto n=run(before,false);assert(run(after,true)==n&&run(four,false)==n&&before==four);
 const auto start=w(before.data(),object+0x24),end=w(before.data(),0x802B4400);assert(start==0x802B4408+buffer*0x960&&end<=start+0x960);
 unsigned shifted=0;for(uint32_t a=start;a<end;a+=8){auto x=w(before.data(),a),y=w(before.data(),a+4);
  if(x>>24==0xE4){assert(w(after.data(),a)==((x&~0xFFFu)|unsigned(int(x&0xFFFu)+shift)));assert(w(after.data(),a+4)==((y&~0xFFFu)|unsigned(int(y&0xFFFu)+shift)));++shifted;}
  else if(x==0xE1000000){assert(x==w(after.data(),a)&&w(after.data(),a+4)==(((y>>16)+7)<<16|((y&0xffffu)+7)));}
  else if(x==0xF1000000){assert(x==w(after.data(),a)&&w(after.data(),a+4)==(high?0x01f001f0u:0x03e003e0u));}
  else {assert(x==w(after.data(),a)&&y==w(after.data(),a+4));}}
 assert(shifted==n); // All player dots, selected-player highlights, target and ball through either real emitter.
 for(size_t i=0;i<before.size();++i)if(i<(start&0x7fffff)||i>=(end&0x7fffff))assert(before[i]==after[i]);
 for(unsigned variant=0;variant<7;++variant){auto bad=after;const uint32_t at=start+56;
  if(variant==0)byte(bad,0x8013B44C,7);if(variant==1)byte(bad,0x8013B42A,2);
  if(variant==2)byte(bad,0x8012E6A3,2);if(variant==3)put(bad,at,0xF6000000);
  if(variant==4)put(bad,0x802B4400,at+32);if(variant==5)put(bad,at+16,0xF2000000);
  auto old=bad;assert(!iss2000::align_pal_training_radar_marker(bad,variant!=6,at));assert(bad==old);}
 }
''')
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);(p/'fixture.cpp').write_text(code)
   cmd=['c++','-std=c++20','-O2','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-I'+str(ROOT/'src'),'-I'+str(h),'-I'+str(ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz'),'-I'+str(ROOT/'.local/runtime-deps-build/librecomp/miniz'),str(p/'fixture.cpp'),str(ROOT/'src/runtime/pal_hud_widescreen.cpp'),str(ROOT/'src/runtime/pal_sky_widescreen.cpp'),str(ROOT/'src/runtime/rom_image.cpp'),'-o',str(p/'fixture')]
   result=subprocess.run(cmd,capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
   result=subprocess.run([str(p/'fixture'),str(snap),str(ROOT/'.local/training-timing-01/free-training-low.rdram')],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
