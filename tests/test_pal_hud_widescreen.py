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
 assert(p.x_offset==-1284&&p.y_offset==0); // Right305 ->304; top13 ->16.
 assert(pal_hud_placement(r,true,PalHudDraw::Sprite,left).x_offset==-372);
 assert(pal_hud_placement(r,true,PalHudDraw::Sprite,left).origin==0x100);
 assert(pal_hud_placement(r,true,PalHudDraw::Sprite,right).x_offset==-904);
 assert(pal_hud_placement(r,true,PalHudDraw::Sprite,right).origin==0x300);
 assert(pal_hud_placement(r,true,PalHudDraw::Sprite,left).y_offset==-32);
 // Original801DBD88 numeric-clock branch replaces37/38 with native black
 // panels,39 with the separator and43 with the period label (BD/BE resources).
 for(auto item:{std::pair{37u,0x80076F7Cu},std::pair{38u,0x80076F7Cu},
                std::pair{39u,0x80076EF8u},std::pair{43u,0x80076F28u}}){
  const auto a=object(item.first,item.second);
  const uint32_t segment=item.first==37?0x80261C70:item.first==38?0x80261C7C:
                         item.first==39?0x80261C88:0x80261D30;
  put(r,a+0x30,segment);byte(r,segment,0x90);
  p=pal_hud_placement(r,true,PalHudDraw::Sprite,a);
  assert(p&&p.group==PalHudGroup::Clock&&p.origin==G_EX_ORIGIN_RIGHT);
  assert(p.x_offset==-1284&&p.y_offset==0);
  assert(!pal_hud_placement(r,false,PalHudDraw::Sprite,a));
  if(item.first==43){put(r,a+0x30,0x80261D3C);byte(r,0x80261D3C,0x90);
   assert(pal_hud_placement(r,true,PalHudDraw::Sprite,a).group==PalHudGroup::Clock);
   put(r,a+0x30,0x80261D48);byte(r,0x80261D48,0x90);
   assert(!pal_hud_placement(r,true,PalHudDraw::Sprite,a));}
 }
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
   result=subprocess.run(['c++','-std=c++20','-O2','-Wall','-Wextra','-Werror','-I'+str(ROOT/'src'),'-I'+str(RT64/'include'),str(p/'test.cpp'),str(ROOT/'src/runtime/pal_hud_widescreen.cpp'),str(ROOT/'src/runtime/pal_sky_widescreen.cpp'),str(ROOT/'src/runtime/rom_image.cpp'),'-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-I'+str(ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz'),'-I'+str(ROOT/'.local/runtime-deps-build/librecomp/miniz'),'-o',str(p/'test')],capture_output=True,text=True)
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
  rdp=(RT64/'src/hle/rt64_rdp.cpp').read_text()
  move=re.search(r'    int32_t RDP::movedFromOrigin\(.*?\n    \}',rdp,re.S).group().replace('RDP::','')
  code=r'''#include "runtime/pal_hud_widescreen.hpp"
#include <vector>
#include <cstring>
#include <cassert>
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
struct {uint32_t width=320;} colorImage;
''' + body + '\n' + move + r'''
int main(){
 std::vector<uint8_t> ram(0x800000);
 auto put=[&](uint32_t a,uint32_t v){std::memcpy(ram.data()+(a&0x7fffff),&v,4);};
 auto byte=[&](uint32_t a,uint8_t v){ram[(a&0x7fffff)^3]=v;};
 put(0x8009E02C,0x8013B418);put(0x80143D6C,0x80261E68);
 byte(0x8013B446,6);byte(0x8013B44C,4);
 for(auto a:{0x801650DCu,0x80165104u}){byte(a+4,2);byte(a+6,11);put(a+0x14,0x801A6984);}
 const auto leftPlayer=iss2000::pal_hud_placement(ram,true,iss2000::PalHudDraw::Text,0x801650DC);
 const auto rightPlayer=iss2000::pal_hud_placement(ram,true,iss2000::PalHudDraw::Text,0x80165104);
 assert(leftPlayer&&rightPlayer);
 for(float scale:{1.f,3.f,3.75f,4.5f,6.f,7.5f,9.f,1080.f/296,720.f/232,900.f/232,1080.f/232,1440.f/232,1800.f/232,2160.f/232}){
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
  // Complete original player envelopes center in the space between the
  // untouched radar and the respective edge, including PAL VI crop ratios.
  for(float inverseAspect:{.75f,232.f*4.f/3.f/(232.f*16.f/9.f),.77586f}){
   const hlslpp::float2 profileScale(scale/inverseAspect,scale);
   FixedRect radarRect{120*4,170*4,200*4,226*4};
   auto radar=convertViewportRect(radarRect,profileScale,320,inverseAspect,1,0,G_EX_ORIGIN_NONE,G_EX_ORIGIN_NONE);
   FixedRect leftRect{movedFromOrigin(26*4+leftPlayer.x_offset,leftPlayer.origin),200*4,movedFromOrigin(120*4+leftPlayer.x_offset,leftPlayer.origin),224*4};
   FixedRect rightRect{movedFromOrigin(199*4+rightPlayer.x_offset,rightPlayer.origin),200*4,movedFromOrigin(293*4+rightPlayer.x_offset,rightPlayer.origin),224*4};
   auto lp=convertViewportRect(leftRect,profileScale,320,inverseAspect,1,0,leftPlayer.origin,leftPlayer.origin);
   auto rp=convertViewportRect(rightRect,profileScale,320,inverseAspect,1,0,rightPlayer.origin,rightPlayer.origin);
   const float width=320*profileScale.x;
   assert(std::abs((lp.x+lp.width/2)-radar.x/2)<=scale+1);
   assert(std::abs((rp.x+rp.width/2)-(width+radar.x+radar.width)/2)<=scale+1);
   assert(lp.x>=0&&lp.x+lp.width<radar.x&&rp.x>radar.x+radar.width&&rp.x+rp.width<=width);
   assert(std::abs(lp.width-94*scale)<=scale+1&&std::abs(rp.width-94*scale)<=scale+1);
  }
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
   result=subprocess.run(['c++','-std=c++20','-O2','-Wall','-Wextra','-Werror','-isystem',str(RT64/'src/contrib/hlslpp/include'),'-I'+str(RT64/'include'),'-I'+str(ROOT/'src'),str(p/'viewport.cpp'),str(ROOT/'src/runtime/pal_hud_widescreen.cpp'),str(ROOT/'src/runtime/pal_sky_widescreen.cpp'),str(ROOT/'src/runtime/rom_image.cpp'),'-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-I'+str(ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz'),'-I'+str(ROOT/'.local/runtime-deps-build/librecomp/miniz'),'-o',str(p/'viewport')],capture_output=True,text=True)
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
  if not all(p.is_file() for p in [snapshot,header/'recomp.h',ROOT/'.local/training-timing-01/free-training-high.rdram',*paths]):
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
#include "runtime/menu_sprite_runtime.hpp"
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
static unsigned inner_calls,original_calls;
static uint32_t word(const Bytes& r,uint32_t a){uint32_t v;std::memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
static void put(Bytes& r,uint32_t a,uint32_t v){std::memcpy(r.data()+(a&0x7fffff),&v,4);}
namespace iss2000 {
enum class AspectRatio {Wide16x9,Original4x3};
namespace platform {
struct Settings {AspectRatio aspect_ratio;};
Settings render_settings(){return {wide?AspectRatio::Wide16x9:AspectRatio::Original4x3};}
}
static void run_original_guest(uint32_t a,uint8_t* r,recomp_context* c){
 assert(a==0x8023A510);++original_calls;func_8023A510_overlay_4a6820_80230590(r,c);
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
    assert(b==0x01000000&&word(ram,p+8)==0&&word(ram,p+12)==(ram[0x13b42a^3]?2176u:960u));
    scissor=true;p+=8;
   }
   else if(a==0x64000006){
    aligned=b==0; // G_EX_ORIGIN_LEFT for both rectangle edges.
    if(aligned){const auto packed=ram[0x13b42a^3]?0xffd00008u:0xffe80004u;assert(word(ram,p+8)==packed&&word(ram,p+12)==packed);}
    else assert(b==0x00800800&&word(ram,p+8)==0&&word(ram,p+12)==0);
    p+=8;
   }
   else if((a>>24)==0xED){assert(a==0xED000000&&b==(ram[0x13b42a^3]?0x00a00880u:0x005003c0u));scissor=false;}
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
struct Result {Bytes ram;std::vector<Flag> flags;std::shared_ptr<const MenuSpriteTaskSnapshot> metadata;};
static Result emit(const Bytes& base,int mode,unsigned expected=2){
 auto r=base;const uint32_t begin=0x800D0328;
 put(r,0x800A4AA4,0x800D0320);put(r,0x8009E0C8,begin);
 recomp_context c{};c.r29=(int32_t)0x807ff000;c.f_odd=&c.f0.u32h;
 inner_scopes=mode==2;inner_calls=original_calls=0;
 if(mode>=2)begin_menu_sprite_frame(r);
 wide=mode!=3;
 if(mode==1){ // Reproduce the rejected outer-only integration.
  PalHudScope outer(r,true,PalHudDraw::ScoreFlags);assert(outer);
  func_8023A890_overlay_4a6820_80230590(r.data(),&c);
 }else{
  if(mode==3)inner_scopes=true;
  func_8023A890_overlay_4a6820_80230590(r.data(),&c);
 }
 assert(inner_calls==2&&original_calls==(mode>=2?2u:0u));
 Audit audit{r,{},{} };audit.list(begin,word(r,0x8009E0C8));
 assert(audit.flags.size()==expected&&audit.stack.empty()&&!audit.aligned&&!audit.scissor);
 std::shared_ptr<const MenuSpriteTaskSnapshot> metadata;
 if(mode>=2){auto unchanged=r;TransformTaskFingerprint task{begin,0x80069AD0,0x80099EF0,word(r,0x8009E0C8)-begin};submit_menu_sprite_metadata(1,task);metadata=consume_menu_sprite_metadata(task);assert(r==unchanged&&metadata&&metadata->commands.size()==expected&&"Both genuine score flag rectangles need shared interpolation metadata");
  for(auto [pc,id]:metadata->commands)assert(id&&pc>=(begin&0x7fffff)&&pc<(word(r,0x8009E0C8)&0x7fffff)&&word(r,pc)>>24==0xE4);
 }
 return {std::move(r),std::move(audit.flags),std::move(metadata)};
}
int main(int argc,char** argv){
 assert(argc==4);{FILE*f=std::fopen(argv[3],"rb");assert(f);std::vector<uint8_t>rom(0x1000000);assert(std::fread(rom.data(),1,rom.size(),f)==rom.size());std::fclose(f);assert(configure_menu_sprite_runtime(rom));}Bytes base(0x800000);FILE* f=std::fopen(argv[1],"rb");assert(f);
 assert(std::fread(base.data(),1,base.size(),f)==base.size());std::fclose(f);
 Bytes high(0x800000);f=std::fopen(argv[2],"rb");assert(f&&std::fread(high.data(),1,high.size(),f)==high.size());std::fclose(f);
 for(unsigned high_mode=0;high_mode<2;++high_mode){
 // Isolated original field fixture with the separately captured genuine High
 // video context and complete High leaf, never a live guest RAM write.
 if(high_mode){for(auto a:{0x13b428u,0x13b42cu,0x13b430u})std::memcpy(base.data()+a,high.data()+a,4);std::memcpy(base.data()+0x7aa008,high.data()+0x7aa008,0x2b4);}
 auto original=emit(base,0),old=emit(base,1),fixed=emit(base,2),four=emit(base,3);
 assert(four.ram==original.ram);
 auto ordered=[](const Result&v){std::array<uint32_t,2>ids{};unsigned n=0;for(auto pc=0x800D0328u;pc<word(v.ram,0x8009E0C8);pc+=8)if(word(v.ram,pc)>>24==0xE4)ids[n++]=v.metadata->commands.at(pc&0x7fffff);assert(n==2&&ids[0]&&ids[1]&&ids[0]!=ids[1]);return ids;};
 assert(ordered(fixed)==ordered(four));
 auto moved_base=base;auto xy=word(moved_base,0x802698B0);put(moved_base,0x802698B0,xy+4);auto moved=emit(moved_base,2);assert(ordered(moved)==ordered(fixed));
 auto one_base=base;one_base[0x2698B0^3]=0;auto only_right=emit(one_base,2,1);
 assert(only_right.metadata->commands.begin()->second==ordered(fixed)[1]&&"Hiding the left flag must not lend its identity to the right flag");
 // Already queued metadata remains immutable across later moved emissions.
 assert(ordered(fixed)==ordered(four)); // Original4:3 chain remains byte-identical.
 for(unsigned i=0;i<2;++i){
  assert(old.flags[i].original==original.flags[i].original&&fixed.flags[i].original==original.flags[i].original);
  assert(old.flags[i].aligned&&!old.flags[i].wide_scissor);
  assert(fixed.flags[i].aligned&&fixed.flags[i].wide_scissor);
 }
 // First actual flag23..48, shifted to17..42, must lie outside the old
 // centered320-wide scissor's left53.33 in a426.67-wide16:9 frame.
 const unsigned factor=high_mode?2:1;
 const auto left=(original.flags[0].original[1]>>12&0xfff)/4.0-6*factor;
 const auto right=(original.flags[0].original[0]>>12&0xfff)/4.0-6*factor;
 assert(left>=16*factor&&right<(320.0*factor*4/3-320*factor)/2);
 }

}
'''
  code=code.replace('ORIGINAL_INCLUDES','\n'.join('#include '+json.dumps(str(p)) for p in paths)).replace('ACTUAL_WRAPPER',wrapper)
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder);(p/'chain.cpp').write_text(code)
   built=subprocess.run(['c++','-std=c++20','-O2','-I'+str(ROOT/'src'),'-I'+str(header),str(p/'chain.cpp'),str(ROOT/'src/runtime/pal_hud_widescreen.cpp'),str(ROOT/'src/runtime/pal_sky_widescreen.cpp'),str(ROOT/'src/runtime/rom_image.cpp'),str(ROOT/'src/runtime/menu_sprite_runtime.cpp'),str(ROOT/'src/runtime/pal_radar_interpolation.cpp'),str(ROOT/'src/runtime/graphics_task_bank.cpp'),'-pthread','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-I'+str(ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz'),'-I'+str(ROOT/'.local/runtime-deps-build/librecomp/miniz'),'-o',str(p/'chain')],capture_output=True,text=True)
   self.assertEqual(built.returncode,0,built.stderr)
   run=subprocess.run([str(p/'chain'),str(snapshot),str(ROOT/'.local/training-timing-01/free-training-high.rdram'),str(ROOT/'.local/inputs/pal-en-de/rom.z64')],capture_output=True,text=True)
   self.assertEqual(run.returncode,0,run.stderr)



@unittest.skipUnless(shutil.which('c++') and (RT64/'src/render/rt64_framebuffer_renderer.cpp').is_file(),'Compiler and pinned RT64 viewport source required')
class PalHudHighOriginalTests(unittest.TestCase):
 def test_genuine_high_sprite_font_chains_scaled_scope_original_uv_and_full_four_three(self):
  import hashlib,json,struct,re
  renderer=(RT64/"src/render/rt64_framebuffer_renderer.cpp").read_text()
  viewport=re.search(r"    RenderViewport convertViewportRect\(.*?\n    \}",renderer,re.S).group()
  move=re.search(r"    int32_t RDP::movedFromOrigin\(.*?\n    \}",(RT64/"src/hle/rt64_rdp.cpp").read_text(),re.S).group().replace("RDP::","")
  generated=ROOT/'.local/pal-map-bound-01/functions';analysis=ROOT/'.local/pal-map-bound-01/section-analysis.json'
  high=ROOT/'.local/training-timing-01/free-training-high.rdram';low=ROOT/'.local/training-timing-01/free-training-low.rdram';rom=ROOT/'.local/inputs/pal-en-de/rom.z64';header=ROOT/'.local/deps/N64Recomp/include'
  if not all(p.is_file()for p in [high,low,rom,analysis,header/'recomp.h']):self.skipTest('Private genuine PAL High/Low originals required')
  image=rom.read_bytes();self.assertEqual(hashlib.sha256(image).hexdigest(),'6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf')
  sections=json.loads(analysis.read_text());functions={f['vram']:(section,f)for section in sections for f in section['functions']};pending=[0x80041B50,0x80048660];seen=set()
  while pending:
   pc=pending.pop()
   if pc in seen:continue
   seen.add(pc);section,f=functions[pc];offset=section['rom']+pc-section['vram']
   for instruction in struct.unpack_from('>'+str(f['size']//4)+'I',image,offset):
    if instruction>>26==3:pending.append(0x80000000|((instruction&0x3ffffff)<<2))
  paths={pc:next(generated.glob(f'func_{pc:08X}_*.c'))for pc in seen}
  code=r"""#include "recomp.h"
#include "runtime/pal_hud_widescreen.hpp"
#include <cassert>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <vector>
#include <algorithm>
#include <cmath>
#include <hlsl++.h>
#include "rt64_extended_gbi.h"
struct FixedRect {int a,b,c,d;int left(bool)const{return(a+3)>>2;}int top(bool)const{return(b+3)>>2;}int right(bool)const{return(c+3)>>2;}int bottom(bool)const{return(d+3)>>2;}};
struct RenderViewport {float x,y,width,height;};
struct {uint32_t width=640;}colorImage;
VIEWPORT_FUNCTIONS
DECLS
using namespace iss2000;using Bytes=std::vector<uint8_t>;
extern "C" void do_break(uint32_t){std::abort();}
extern "C" recomp_func_t* get_function(int32_t a){switch(uint32_t(a)){LOOKUP default:std::abort();}}
uint32_t word(const Bytes&r,uint32_t a){uint32_t v;memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
void put(Bytes&r,uint32_t a,uint32_t v){memcpy(r.data()+(a&0x7fffff),&v,4);}
void byte(Bytes&r,uint32_t a,uint8_t v){r[(a&0x7fffff)^3]=v;}
struct Result {Bytes ram;std::vector<uint32_t> commands;};
Result emit(const Bytes&base,uint32_t object,PalHudDraw draw,int scope){
 auto r=base;put(r,0x800A4AA4,0x800D0320);put(r,0x8009E0C8,0x800D0328);
 recomp_context c{};c.r4=int32_t(object);c.r29=int32_t(0x807ff000);c.f_odd=&c.f0.u32h;
 {PalHudScope h(r,scope==2,draw,object);assert(bool(h)==(scope==2));
  if(draw==PalHudDraw::Text)func_80048660_resident(r.data(),&c);else func_80041B50_resident(r.data(),&c);
 }
 const uint32_t begin=0x800D0328,end=word(r,0x8009E0C8),prefix=scope==2?48:0,suffix=scope==2?24:0;
 std::vector<uint32_t> commands;for(uint32_t a=begin+prefix;a<end-suffix;a+=4)commands.push_back(word(r,a));
 assert(!commands.empty());
 if(scope==2){
  assert(word(r,begin)==0xE0525464&&word(r,begin+16)==0x64000005);
  assert(word(r,begin+28)==(r[0x13b42a^3]?544u:240u)*4);
  const auto p=pal_hud_placement(r,true,draw,object);
  assert(word(r,begin+40)==((uint32_t(uint16_t(p.x_offset))<<16)|uint16_t(p.y_offset)));
  assert(word(r,end-24)==0x64000006&&word(r,end-20)==0x00800800&&word(r,end-8)==0x64000018);
 }
 return {std::move(r),std::move(commands)};
}
Bytes load(const char*path){Bytes r(0x800000);FILE*f=fopen(path,"rb");assert(f&&fread(r.data(),1,r.size(),f)==r.size());fclose(f);return r;}
int main(int argc,char**argv){assert(argc==3);auto low=load(argv[1]),high=load(argv[2]);
 assert(high[0x13b42a^3]==1&&word(high,0x8013b42c)==0x02800220&&word(high,0x8013b430)==0x80700000);
 for(auto object:{0x8013c47cu,0x8013c4b8u,0x8013c530u,0x8013c56cu,0x8013c620u,0x8013c698u,0x8013c74cu,0x8013c92cu,0x801650dcu}){
  const auto draw=object==0x801650dc?PalHudDraw::Text:PalHudDraw::Sprite;
  auto lp=pal_hud_placement(low,true,draw,object),hp=pal_hud_placement(high,true,draw,object);
  assert(lp&&hp&&hp.group==lp.group&&hp.origin==lp.origin&&hp.x_offset==2*lp.x_offset&&hp.y_offset==2*lp.y_offset+232);
  for(const auto*base:{&low,&high}){
   const auto original=emit(*base,object,draw,0),four=emit(*base,object,draw,1),wide=emit(*base,object,draw,2);
   assert(original.ram==four.ram);
   if(object==0x8013c47cu && (*base)[0x13b42a^3]){
    auto expected=original.commands;unsigned quads=0;
    for(unsigned n=0;n+5<expected.size();n+=2)if(expected[n]>>24==0xe4){if(quads%3)expected[n]=0xe4000000u|(expected[n+1]&0xffffffu);++quads;n+=4;}
    assert(quads==42&&expected==wide.commands); // Only redundant repair rectangles become empty.
    auto coverage=[](const auto&commands,int x,int y){unsigned count=0;for(unsigned n=0;n+5<commands.size();n+=2)if(commands[n]>>24==0xe4){auto a=commands[n],b=commands[n+1];count+=x>=int((b>>12&4095)+3)/4&&x<int((a>>12&4095)+3)/4&&y>=int((b&4095)+3)/4&&y<int((a&4095)+3)/4;n+=4;}return count;};
    unsigned doubled=0;for(int y=340;y<452;++y)for(int x=240;x<400;++x){doubled+=coverage(original.commands,x,y)>1;assert(coverage(wide.commands,x,y)==1);}
    assert(doubled>300); // Complete160x112 radar, single alpha coverage on BOTH halves.
   }else assert(original.commands==wide.commands);
   bool rectangle=false;for(auto w:original.commands)rectangle|=(w>>24)==0xE4;assert(rectangle);
  }
 }
 auto p=pal_hud_placement(high,true,PalHudDraw::Sprite,0x8013c4b8);assert(p.x_offset==-744&&p.y_offset==168); // Training: +28logical relative to prior -7.
 // Execute the pinned real RDP-origin and viewport code at High's640 width.
 const auto left=pal_hud_placement(high,true,PalHudDraw::Text,0x801650dc);
 const auto right=pal_hud_placement(high,true,PalHudDraw::Text,0x80165104);
 for(float scale:{.5f,1.f,1.5f,2.f,3.f,4.5f})for(float inverse:{.75f,.77586f}){
  const hlslpp::float2 resolution(scale/inverse,scale);
  auto radar=convertViewportRect({240*4,340*4,400*4,452*4},resolution,640,inverse,1,0,G_EX_ORIGIN_NONE,G_EX_ORIGIN_NONE);
  FixedRect a{movedFromOrigin(52*4+left.x_offset,left.origin),400*4,movedFromOrigin(240*4+left.x_offset,left.origin),448*4};
  FixedRect b{movedFromOrigin(398*4+right.x_offset,right.origin),400*4,movedFromOrigin(586*4+right.x_offset,right.origin),448*4};
  auto lp=convertViewportRect(a,resolution,640,inverse,1,0,left.origin,left.origin);
  auto rp=convertViewportRect(b,resolution,640,inverse,1,0,right.origin,right.origin);
  const float width=640*resolution.x;
  assert(std::abs(lp.x+lp.width/2-radar.x/2)<=scale+1);
  assert(std::abs(rp.x+rp.width/2-(width+radar.x+radar.width)/2)<=scale+1);
  assert(std::abs(lp.width-188*scale)<=scale+1&&std::abs(rp.width-188*scale)<=scale+1);
  assert(lp.x>=0&&lp.x+lp.width<radar.x&&rp.x>radar.x+radar.width&&rp.x+rp.width<=width);
 }
 // Decline inconsistent mode/dimensions/depth, wrong High code and phases.
 for(auto[a,v]:{std::pair{0x8013b42cu,0x028001e0u},std::pair{0x8013b430u,0x802e2000u},std::pair{0x807aa008u,0u}}){auto r=high;put(r,a,v);auto before=r;assert(!pal_hud_placement(r,true,PalHudDraw::Sprite,0x8013c4b8));{PalHudScope scope(r,true,PalHudDraw::Sprite,0x8013c4b8);assert(!scope);}assert(r==before);}
 for(auto[a,v]:{std::pair{0x8013b42au,2u},std::pair{0x8013b44cu,7u},std::pair{0x8013b452u,1u}}){auto r=high;byte(r,a,v);assert(!pal_hud_placement(r,true,PalHudDraw::Sprite,0x8013c4b8));}
 assert(pal_hud_placement(high,true,PalHudDraw::Sprite,0x8013c47c).x_offset==0); // Training radar stays centered while moving downward.
}
"""
  code=code.replace('VIEWPORT_FUNCTIONS',viewport+'\n'+move).replace('DECLS','\n'.join(f'extern "C" void {path.stem}(uint8_t*,recomp_context*);'for pc,path in sorted(paths.items()))).replace('LOOKUP','\n'.join(f'case 0x{pc:08X}:return {path.stem};'for pc,path in sorted(paths.items())))
  with tempfile.TemporaryDirectory()as folder:
   p=Path(folder);(p/'original.c').write_text('\n'.join('#include '+json.dumps(str(path))for pc,path in sorted(paths.items())));(p/'high.cpp').write_text(code)
   result=subprocess.run(['cc','-O1','-fno-strict-aliasing','-I'+str(header),'-c',str(p/'original.c'),'-o',str(p/'original.o')],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
   result=subprocess.run(['c++','-std=c++20','-O2','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-I'+str(ROOT/'src'),'-I'+str(header),'-I'+str(ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz'),'-I'+str(ROOT/'.local/runtime-deps-build/librecomp/miniz'),'-isystem',str(RT64/'src/contrib/hlslpp/include'),'-I'+str(RT64/'include'),str(p/'high.cpp'),str(p/'original.o'),str(ROOT/'src/runtime/pal_hud_widescreen.cpp'),str(ROOT/'src/runtime/pal_sky_widescreen.cpp'),str(ROOT/'src/runtime/rom_image.cpp'),'-o',str(p/'high')],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
   result=subprocess.run([str(p/'high'),str(low),str(high)],capture_output=True,text=True,timeout=15);self.assertEqual(result.returncode,0,result.stderr)
   old=p/'old-high-guard.cpp';old.write_text((ROOT/'src/runtime/pal_hud_widescreen.cpp').read_text().replace('if(mode!=1 ||','if(mode==1 ||'))
   command=['c++','-std=c++20','-O2','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-I'+str(ROOT/'src'),'-I'+str(ROOT/'src/runtime'),'-I'+str(header),'-I'+str(ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz'),'-I'+str(ROOT/'.local/runtime-deps-build/librecomp/miniz'),'-isystem',str(RT64/'src/contrib/hlslpp/include'),'-I'+str(RT64/'include'),str(p/'high.cpp'),str(p/'original.o'),str(old),str(ROOT/'src/runtime/pal_sky_widescreen.cpp'),str(ROOT/'src/runtime/rom_image.cpp'),'-o',str(p/'old-high')]
   built=subprocess.run(command,capture_output=True,text=True);self.assertEqual(built.returncode,0,built.stderr)
   failed=subprocess.run([str(p/'old-high'),str(low),str(high)],capture_output=True,text=True,timeout=15);self.assertNotEqual(failed.returncode,0,'Negative control must reproduce the rejected High HUD')


if __name__=='__main__':unittest.main()
