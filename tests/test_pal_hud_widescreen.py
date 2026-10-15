"""Original project work: djultra64. Original-engine HUD scope; CPU only."""
from pathlib import Path
import shutil,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
RT64=ROOT/'.local/deps/rt64'
@unittest.skipUnless(shutil.which('c++') and (RT64/'include/rt64_extended_gbi.h').is_file(),
 'Compiler and pinned RT64 GBI header required')
class PalHudTests(unittest.TestCase):
 def test_exact_objects_phase_guards_balanced_commands_and_unmodified_original_rectangles(self):
  source=r'''#include "runtime/pal_hud_widescreen.hpp"
#include "runtime/pal_sky_widescreen.hpp"
#include <cassert>
#include <cstring>
#include <vector>
#define F3DEX_GBI_2
#include "rt64_extended_gbi.h"
using namespace iss2000;
void put(std::vector<uint8_t>& r,uint32_t a,uint32_t v){std::memcpy(r.data()+(a&0x7fffff),&v,4);}
uint32_t word(const std::vector<uint8_t>& r,uint32_t a){uint32_t v;std::memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
void byte(std::vector<uint8_t>& r,uint32_t a,uint8_t v){r[(a&0x7fffff)^3]=v;}
int main(){
 std::vector<uint8_t> r(0x800000);
 put(r,0x800A4AA4,0x800D0320);put(r,0x8009E0C8,0x800D0328);
 put(r,0x8009E02C,0x8013B418);put(r,0x80143D6C,0x80261E68);
 byte(r,0x8013B446,6);byte(r,0x8013B44C,4);
 auto object=[&](unsigned id,uint32_t descriptor){uint32_t a=0x8013C47C+id*0x3c;
  byte(r,a+4,1);byte(r,a+5,11);put(r,a+0x14,descriptor);
  put(r,a+0x28,0x3f800000);put(r,a+0x2c,0x3f800000);put(r,a+0x30,0x80261AFC);
  byte(r,0x80261AFC,0x90);return a;};
 auto score=object(30,0x80076F7C),clock=object(38,0x80076F1C);
 auto left=object(1,0x80076F70),right=object(2,0x80076F70);
 auto radar=object(0,0x80259918),unknown=object(50,0x80076F70);
 auto p=pal_hud_placement(r,true,PalHudDraw::Sprite,score);assert(p&&p.group==PalHudGroup::Score&&p.origin==G_EX_ORIGIN_LEFT);
 assert(p.x_offset==-24&&p.y_offset==4); // Original22,15 -> safe16,16.
 p=pal_hud_placement(r,true,PalHudDraw::Sprite,clock);assert(p&&p.group==PalHudGroup::Clock&&p.origin==G_EX_ORIGIN_RIGHT);
 assert(p.x_offset==-1284&&p.y_offset==12); // Right305 ->304; top13 ->16.
 assert(pal_hud_placement(r,true,PalHudDraw::Sprite,left).x_offset==-40);
 assert(pal_hud_placement(r,true,PalHudDraw::Sprite,right).x_offset==-1240);
 assert(pal_hud_placement(r,true,PalHudDraw::Sprite,left).y_offset==-28);
 assert(!pal_hud_placement(r,true,PalHudDraw::Sprite,radar));
 assert(!pal_hud_placement(r,true,PalHudDraw::Sprite,unknown));
 assert(!pal_hud_placement(r,true,PalHudDraw::Sprite,score+4));
 assert(!pal_hud_placement(r,true,PalHudDraw::Sprite,0x123456788013CB84ull));
 assert(pal_hud_placement(r,true,PalHudDraw::Sprite,0xFFFFFFFF8013CB84ull));
 assert(pal_hud_placement(r,true,PalHudDraw::ScoreFlags).group==PalHudGroup::Score);
 for(unsigned i=0;i<2;++i){auto t=0x801650DC+i*0x28;byte(r,t+4,2);byte(r,t+6,11);put(r,t+0x14,0x801A6984);
  assert(pal_hud_placement(r,true,PalHudDraw::Text,t).group==(i?PalHudGroup::RightPlayer:PalHudGroup::LeftPlayer));}
 assert(!pal_hud_placement(r,true,PalHudDraw::Text,0x8016512C));
 auto pristine=r;
 {PalHudScope scope(r,false,PalHudDraw::Sprite,score);assert(!scope);}assert(r==pristine);
 for(auto a:{0x8013B446u,0x8013B44Cu,0x8013B452u,0x8012DE27u,0x8013B42Au}){
  byte(r,a,9);auto saved=r;{PalHudScope scope(r,true,PalHudDraw::Sprite,score);assert(!scope);}assert(r==saved);r=pristine;
 }
 put(r,score+0x14,0x80076EF8);assert(!pal_hud_placement(r,true,PalHudDraw::Sprite,score));r=pristine;
 put(r,0x80143D6C,0x80261E6C);assert(!pal_hud_placement(r,true,PalHudDraw::Sprite,score));r=pristine;
 // Compare complete scope encoding against the real pinned public GBI macros.
 GfxCommand commands[16]{};auto cmd=commands;
 gEXEnable(cmd++);gEXPushScissor(cmd++);gEXSetScissor(cmd++,0,G_EX_ORIGIN_LEFT,G_EX_ORIGIN_RIGHT,0,0,0,240);
 gEXSetRectAlign(cmd++,G_EX_ORIGIN_LEFT,G_EX_ORIGIN_LEFT,-24,4,-24,4);
 const auto begin=word(r,0x8009E0C8);
 {PalHudScope scope(r,true,PalHudDraw::Sprite,score);assert(scope);
  assert(word(r,0x8009E0C8)==begin+48);
  for(unsigned n=0;n<6;++n){assert(word(r,begin+n*8)==commands[n].values.word0);assert(word(r,begin+n*8+4)==commands[n].values.word1);}
  auto saved=r;{PalHudScope nested(r,true,PalHudDraw::Sprite,clock);assert(!nested);}assert(r==saved);
  // Original game emitter writes its own unchanged geometry/UV words here.
  uint32_t original[]={0xE41B809C,0x005803C,0xE1000000,0,0xF1000000,0x04000400};
  for(unsigned n=0;n<6;++n){put(r,begin+48+4*n,original[n]);}
  put(r,0x8009E0C8,begin+72);
 }
 cmd=commands;gEXSetRectAlign(cmd++,G_EX_ORIGIN_NONE,G_EX_ORIGIN_NONE,0,0,0,0);gEXPopScissor(cmd++);
 for(unsigned n=0;n<3;++n){assert(word(r,begin+72+n*8)==commands[n].values.word0);assert(word(r,begin+76+n*8)==commands[n].values.word1);}
 assert(word(r,0x8009E0C8)==begin+96);assert(word(r,begin+48)==0xE41B809C);assert(word(r,begin+68)==0x04000400);
 for(unsigned a=0;a<r.size();++a)if((a<((begin&0x7fffff))||a>=((begin&0x7fffff)+96))&&(a<0x9e0c8||a>=0x9e0cc))assert(r[a]==pristine[a]);
 r=pristine;put(r,0x8009E0C8,0x800E0328-16);auto saved=r;{PalHudScope scope(r,true,PalHudDraw::Sprite,score);assert(!scope);}assert(r==saved);
 r=pristine;put(r,0x800A4AA4,0x800D0324);saved=r;{PalHudScope scope(r,true,PalHudDraw::Sprite,score);assert(!scope);}assert(r==saved);
}
'''
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder);(p/'test.cpp').write_text(source)
   result=subprocess.run(['c++','-std=c++20','-O2','-Wall','-Wextra','-Werror','-I'+str(ROOT/'src'),'-I'+str(RT64/'include'),str(p/'test.cpp'),str(ROOT/'src/runtime/pal_hud_widescreen.cpp'),str(ROOT/'src/runtime/pal_sky_widescreen.cpp'),'-o',str(p/'test')],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
   result=subprocess.run([str(p/'test')],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)

@unittest.skipUnless(shutil.which('c++') and (RT64/'src/render/rt64_framebuffer_renderer.cpp').is_file(),
 'Compiler and pinned RT64 renderer source required')
class PalHudViewportTests(unittest.TestCase):
 def test_actual_rt64_viewport_preserves_size_and_untagged_center_when_origins_expand(self):
  import re
  original=(RT64/'src/render/rt64_framebuffer_renderer.cpp').read_text()
  body=re.search(r'    RenderViewport convertViewportRect\(.*?\n    \}',original,re.S).group()
  code=r'''#include <cassert>
#include <cmath>
#include <cstdint>
#include <initializer_list>
#include <hlsl++.h>
#include "rt64_extended_gbi.h"
struct FixedRect {
 int a,b,c,d;
 int left(bool)const{return (a+3)>>2;}int top(bool)const{return (b+3)>>2;}
 int right(bool)const{return (c+3)>>2;}int bottom(bool)const{return (d+3)>>2;}
};
struct RenderViewport {float x,y,width,height;};
''' + body + r'''
int main(){
 for(float scale:{1.f,3.f,3.75f,4.5f,6.f,7.5f,9.f,1080.f/296,1080.f/232}){
  const hlslpp::float2 wideScale(scale*4.f/3.f,scale);
  FixedRect original{88,60,440,156};
  auto noneBefore=convertViewportRect(original,wideScale,320,.75f,0,0,G_EX_ORIGIN_NONE,G_EX_ORIGIN_NONE);
  auto noneAfter=convertViewportRect(original,wideScale,320,.75f,1,0,G_EX_ORIGIN_NONE,G_EX_ORIGIN_NONE);
  assert(noneBefore.x==noneAfter.x&&noneBefore.y==noneAfter.y&&noneBefore.width==noneAfter.width&&noneBefore.height==noneAfter.height);
  // Score envelope moves to16,16; both origins equal preserves scale.
  // Upstream rounds explicit origins to its native pixel grid, allowing
  // at most one original pixel of edge quantization at fractional scales.
  FixedRect left{64,64,416,160};
  auto score=convertViewportRect(left,wideScale,320,.75f,1,0,G_EX_ORIGIN_LEFT,G_EX_ORIGIN_LEFT);
  assert(std::abs(score.x-16*scale)<=scale+.51f&&std::abs(score.y-16*scale)<=scale+.51f);
  assert(std::abs(score.width-88*scale)<=scale+.51f&&std::abs(score.height-24*scale)<=scale+.51f);
  // Clock envelope ends at304; physical right safe margin stays16.
  FixedRect right{1056,64,1216,244};
  auto clock=convertViewportRect(right,wideScale,320,.75f,1,0,G_EX_ORIGIN_RIGHT,G_EX_ORIGIN_RIGHT);
  assert(std::abs(320*wideScale.x-(clock.x+clock.width)-16*scale)<=scale+.51f);
  assert(std::abs(clock.width-40*scale)<=scale+.51f);
  // At4:3, enabling extended origins cannot move ordinary untagged draws.
  const hlslpp::float2 normalScale(scale,scale);
  auto fourBefore=convertViewportRect(original,normalScale,320,1,0,0,G_EX_ORIGIN_NONE,G_EX_ORIGIN_NONE);
  auto fourAfter=convertViewportRect(original,normalScale,320,1,1,0,G_EX_ORIGIN_NONE,G_EX_ORIGIN_NONE);
  assert(fourBefore.x==fourAfter.x&&fourBefore.y==fourAfter.y&&fourBefore.width==fourAfter.width&&fourBefore.height==fourAfter.height);
 }
}
'''
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder);(p/'viewport.cpp').write_text(code)
   result=subprocess.run(['c++','-std=c++20','-O2','-Wall','-Wextra','-Werror','-isystem',str(RT64/'src/contrib/hlslpp/include'),'-I'+str(RT64/'include'),str(p/'viewport.cpp'),'-o',str(p/'viewport')],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
   result=subprocess.run([str(p/'viewport')],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)

@unittest.skipUnless(shutil.which('c++'),'C++ compiler required')
class PalHudOriginalFlagTests(unittest.TestCase):
 def test_actual_original_flag_chain_keeps_scissor_wide_after_original_setup(self):
  import hashlib,json,re
  generated=ROOT/'.local/pal-map-bound-01/functions'
  snapshot=ROOT/'.local/pal-acceptance/field06.rdram'
  header=ROOT/'.local/deps/N64Recomp/include'
  names=['func_800017C0_resident','func_8023A890_overlay_4a6820_80230590','func_8023A510_overlay_4a6820_80230590']
  paths=[generated/(n+'.c') for n in names]
  if not all(p.is_file() for p in [snapshot,header/'recomp.h',*paths]):
   self.skipTest('Private original PAL flag chain and saved field snapshot required')
  self.assertEqual(hashlib.sha256(snapshot.read_bytes()).hexdigest(),'89b3851a060992b4f747a6fb1a06ebed2b7abc306dd6482579373d11726dd970')
  native=(ROOT/'src/runtime/native_game.cpp').read_text()
  wrapper=re.search(r'void draw_widescreen_score_flags\(.*?\n\}',native,re.S).group()
  # Exercise the real integration wrapper, not a hand-copied replacement.
  self.assertIn('0x8023A510',wrapper,'Scope must begin inside the original flag compositor, after800017C0 resets the scissor')
  self.assertRegex(native,r'if\(uint32_t\(address\)==0x8023A510u[^\n]*\n?\s*return &iss2000::draw_widescreen_score_flags;')
  code=r'''#include "recomp.h"
#include "runtime/pal_hud_widescreen.hpp"
#include "runtime/pal_sky_widescreen.hpp"
#include <array>
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
ORIGINAL_INCLUDES
using Bytes=std::vector<uint8_t>;
using namespace iss2000;
static bool inner_scopes,wide=true;
static unsigned inner_calls;
static uint32_t word(const Bytes& r,uint32_t a){uint32_t v;std::memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
static void put(Bytes& r,uint32_t a,uint32_t v){std::memcpy(r.data()+(a&0x7fffff),&v,4);}
namespace iss2000 {
enum class AspectRatio {Wide16x9,Original4x3};
namespace platform {
struct Settings {AspectRatio aspect_ratio;};
Settings render_settings(){return {wide?AspectRatio::Wide16x9:AspectRatio::Original4x3};}
}
static void run_original_guest(uint32_t a,uint8_t* r,recomp_context* c){
 assert(a==0x8023A510);func_8023A510_overlay_4a6820_80230590(r,c);
}
ACTUAL_WRAPPER
}
static void inner(uint8_t* r,recomp_context* c){
 ++inner_calls;
 assert(uint32_t(c->r4)==0x8009E0C8&&uint16_t(c->r5)<2);
 if(inner_scopes)iss2000::draw_widescreen_score_flags(r,c);
 else func_8023A510_overlay_4a6820_80230590(r,c);
}
extern "C" recomp_func_t* get_function(int32_t a){switch(uint32_t(a)){
 case 0x800017C0:return func_800017C0_resident;
 case 0x8023A510:return inner;
 default:std::abort();}}
struct Flag {std::array<uint32_t,6> original;bool wide_scissor,aligned;};
// Bounded display-list state audit: follow the actual emitted original DE
// sublists, including the original ED scissor reset. This does not render.
struct Audit {
 const Bytes& ram;std::vector<Flag> flags;std::vector<bool> stack;
 bool scissor=false,aligned=false;unsigned budget=512;
 void list(uint32_t begin,uint32_t end=0){
  for(uint32_t p=begin;!end||p<end;p+=8){
   assert(budget--&&p>=0x80000400&&p<=0x807ffff8);
   auto a=word(ram,p),b=word(ram,p+4);
   if(a==0x64000017){stack.push_back(scissor);}
   else if(a==0x64000018){assert(!stack.empty());scissor=stack.back();stack.pop_back();}
   else if(a==0x64000005){
    assert(b==0x01000000&&word(ram,p+8)==0&&word(ram,p+12)==960);
    scissor=true;p+=8;
   }
   else if(a==0x64000006){
    aligned=b==0; // G_EX_ORIGIN_LEFT for both rectangle edges.
    if(aligned)assert(word(ram,p+8)==0xffe80004&&word(ram,p+12)==0xffe80004);
    else assert(b==0x00800800&&word(ram,p+8)==0&&word(ram,p+12)==0);
    p+=8;
   }
   else if((a>>24)==0xED){assert(a==0xED000000&&b==0x005003C0);scissor=false;}
   else if((a>>24)==0xDE){assert(a==0xDE000000);list(b);}
   else if((a>>24)==0xDF){assert(!end);return;}
   else if((a>>24)==0xE4){
    Flag f{{},scissor,aligned};for(unsigned n=0;n<6;++n)f.original[n]=word(ram,p+4*n);
    assert(f.original[2]==0xE1000000&&f.original[4]==0xF1000000);
    flags.push_back(f);p+=16;
   }
  }
 }
};
struct Result {Bytes ram;std::vector<Flag> flags;};
static Result emit(const Bytes& base,int mode){
 auto r=base;const uint32_t begin=0x800D0328;
 put(r,0x800A4AA4,0x800D0320);put(r,0x8009E0C8,begin);
 recomp_context c{};c.r29=(int32_t)0x807ff000;c.f_odd=&c.f0.u32h;
 inner_scopes=mode==2;inner_calls=0;
 wide=mode!=3;
 if(mode==1){ // Reproduce the rejected outer-only integration.
  PalHudScope outer(r,true,PalHudDraw::ScoreFlags);assert(outer);
  func_8023A890_overlay_4a6820_80230590(r.data(),&c);
 }else{
  if(mode==3)inner_scopes=true;
  func_8023A890_overlay_4a6820_80230590(r.data(),&c);
 }
 assert(inner_calls==2);
 Audit audit{r,{},{} };audit.list(begin,word(r,0x8009E0C8));
 assert(audit.flags.size()==2&&audit.stack.empty()&&!audit.aligned&&!audit.scissor);
 return {std::move(r),std::move(audit.flags)};
}
int main(int argc,char** argv){
 assert(argc==2);Bytes base(0x800000);FILE* f=std::fopen(argv[1],"rb");assert(f);
 assert(std::fread(base.data(),1,base.size(),f)==base.size());std::fclose(f);
 auto original=emit(base,0),old=emit(base,1),fixed=emit(base,2),four=emit(base,3);
 assert(four.ram==original.ram); // Original4:3 chain remains byte-identical.
 for(unsigned i=0;i<2;++i){
  assert(old.flags[i].original==original.flags[i].original&&fixed.flags[i].original==original.flags[i].original);
  assert(old.flags[i].aligned&&!old.flags[i].wide_scissor);
  assert(fixed.flags[i].aligned&&fixed.flags[i].wide_scissor);
 }
 // First actual flag23..48, shifted to17..42, must lie outside the old
 // centered320-wide scissor's left53.33 in a426.67-wide16:9 frame.
 const auto left=(original.flags[0].original[1]>>12&0xfff)/4.0-6;
 const auto right=(original.flags[0].original[0]>>12&0xfff)/4.0-6;
 assert(left>=16&&right<(320.0*4/3-320)/2);
}
'''
  code=code.replace('ORIGINAL_INCLUDES','\n'.join('#include '+json.dumps(str(p)) for p in paths)).replace('ACTUAL_WRAPPER',wrapper)
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder);(p/'chain.cpp').write_text(code)
   built=subprocess.run(['c++','-std=c++20','-O2','-I'+str(ROOT/'src'),'-I'+str(header),str(p/'chain.cpp'),str(ROOT/'src/runtime/pal_hud_widescreen.cpp'),str(ROOT/'src/runtime/pal_sky_widescreen.cpp'),'-o',str(p/'chain')],capture_output=True,text=True)
   self.assertEqual(built.returncode,0,built.stderr)
   run=subprocess.run([str(p/'chain'),str(snapshot)],capture_output=True,text=True)
   self.assertEqual(run.returncode,0,run.stderr)

if __name__=='__main__':unittest.main()
