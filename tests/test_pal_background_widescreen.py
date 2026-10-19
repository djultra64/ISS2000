"""Original project work: djultra64. Original PAL background chains; no gameplay."""
from pathlib import Path
import hashlib,json,re,shutil,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
RT64=ROOT/'.local/deps/rt64'
CODE=r'''#include "recomp.h"
#include "runtime/pal_background_widescreen.hpp"
#include "runtime/pal_sky_widescreen.hpp"
#include <array>
#include <algorithm>
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#define F3DEX_GBI_2
#include "rt64_extended_gbi.h"
ORIGINAL_DECLARATIONS
using namespace iss2000;using Bytes=std::vector<uint8_t>;
extern "C" recomp_func_t* get_function(int32_t a){switch(uint32_t(a)){
ORIGINAL_LOOKUP
default:std::fprintf(stderr,"Unknown original call %08X\n",uint32_t(a));std::abort();}}
static uint32_t word(const Bytes& r,uint32_t a){uint32_t v;std::memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
static void put(Bytes& r,uint32_t a,uint32_t v){std::memcpy(r.data()+(a&0x7fffff),&v,4);}
static void byte(Bytes& r,uint32_t a,uint8_t v){r[(a&0x7fffff)^3]=v;}
struct Draw {std::array<uint32_t,6> original;unsigned aspect;bool wide;int xoffset,yoffset;};
struct Audit {
 const Bytes& r;std::vector<Draw> draws;std::vector<bool> scissor;
 unsigned aspect=0;bool wide=false;int xoffset=0,yoffset=0;unsigned budget=8192;std::vector<std::array<uint32_t,6>> edges;
 void list(uint32_t begin,uint32_t end=0){
  for(auto p=begin;!end||p<end;p+=8){
   assert(budget--&&p>=0x80000400&&p<=0x807ffff8);const auto a=word(r,p),b=word(r,p+4);
   if(a==0x64000017)scissor.push_back(wide);
   else if(a==0x64000018){assert(!scissor.empty());wide=scissor.back();scissor.pop_back();}
   else if(a==0x64000005){assert(b==0x01000000&&word(r,p+8)==0&&word(r,p+12)==960);wide=true;p+=8;}
   else if(a==0x64000006){assert(b==0x00800800&&word(r,p+8)==word(r,p+12));xoffset=int16_t(word(r,p+8)>>16);yoffset=int16_t(word(r,p+8));p+=8;}
   else if(a==0x64000033){assert(b<3);aspect=b;}
   else if(a==0x64000002){assert(aspect==2&&wide);std::array<uint32_t,6> edge{};for(unsigned i=0;i<6;++i)edge[i]=word(r,p+4*i);edges.push_back(edge);p+=16;}
   else if(a>>24==0xDE){assert(a==0xDE000000);list(b);}
   else if(a>>24==0xDF){assert(!end);return;}
   else if(a>>24==0xED){wide=false;}
   else if(a>>24==0xE4){Draw draw{{},aspect,wide,xoffset,yoffset};for(unsigned n=0;n<6;++n)draw.original[n]=word(r,p+4*n);assert(draw.original[2]==0xE1000000&&draw.original[4]==0xF1000000);draws.push_back(draw);p+=16;}
  }
 }
};
static auto context(uint32_t object){recomp_context c{};c.r4=(int32_t)object;c.r29=(int32_t)0x807ff000;return c;}
static Bytes emit(const Bytes& base,uint32_t object,bool scope,bool wide){
 auto r=base;auto c=context(object);c.f_odd=&c.f0.u32h;
 if(scope){PalBackgroundScope s(r,wide,c.r4);assert(bool(s)==wide);func_80041B50_resident(r.data(),&c);}
 else func_80041B50_resident(r.data(),&c);
 return r;
}
int main(int argc,char**argv){
 assert(argc==4);Bytes base(0x800000);auto*f=std::fopen(argv[1],"rb");assert(f);assert(std::fread(base.data(),1,base.size(),f)==base.size());std::fclose(f);
 const uint32_t object=uint32_t(std::strtoul(argv[2],nullptr,16));const auto kind=std::atoi(argv[3]);
 const auto b=pal_gfx_bounds(base);assert(b);const auto begin=b.begin;put(base,0x8009E0C8,begin);
 if(kind==3||kind==5||kind==6){auto c=context(object);func_80047558_resident(base.data(),&c);}
 if(kind==4){auto c=context(object);c.r4=(int32_t)0x801F684C;func_80007BE0_resident(base.data(),&c);
  c=context(object);func_801ECC08_overlay_2b0e60_801eb960(base.data(),&c);
  auto raw=emit(base,object,false,false);assert(word(raw,0x8009E0C8)-begin==4880);
 }
 if(kind==5){
  auto call=[&](uint32_t fn,uint32_t arg,uint32_t arg2=0){auto ctx=context(arg);ctx.r5=int32_t(arg2);ctx.f_odd=&ctx.f0.u32h;get_function(fn)(base.data(),&ctx);};
  // Original initialized pool record plus an isolated original script-context
  // fixture; genuine AA/E9/8D/E5 handlers consume the untouched scene script.
  call(0x80008A54,object);put(base,object+0x38,0x807f0000);call(0x801AD90C,0x807f0000);put(base,0x801e3430,0);
  call(0x80007BE0,0x802BB80C);
  for(auto [fn,p]:{std::pair{0x801B0044u,0x802BB9FDu},std::pair{0x801AF818u,0x802BBA01u},std::pair{0x801AFDB0u,0x802BBA05u},std::pair{0x801B1818u,0x802BBA09u}}){
   put(base,0x807f0008,p);call(fn,object,0x807f0000);
  }
  auto raw=emit(base,object,false,false);assert(word(raw,0x8009E0C8)-begin==5496);
 }
 if(kind==6){
  auto call=[&](uint32_t fn,uint32_t arg,uint32_t arg2=0){auto ctx=context(arg);ctx.r5=int32_t(arg2);ctx.f_odd=&ctx.f0.u32h;get_function(fn)(base.data(),&ctx);};
  const auto table=word(base,0x80143d6c);const bool first=table==0x802b926c;assert(first||table==0x802ba394);
  call(0x80008A54,object);put(base,object+0x38,0x807f0000);call(0x801AD90C,0x807f0000);put(base,0x801e3430,0);
  call(0x80007BE0,table);
  put(base,0x807f0008,first?0x802b933d:0x802ba659);call(0x801AF818,object,0x807f0000);
  put(base,0x807f0008,first?0x802b9341:0x802ba65d);call(0x801B0044,object,0x807f0000);
  call(first?0x802b5db4:0x802b6800,object);
  auto raw=emit(base,object,false,false);assert(word(raw,0x8009E0C8)-begin==2888);
 }
 if(kind==7){
  auto call=[&](uint32_t fn,uint32_t arg,uint32_t arg2=0){auto ctx=context(arg);ctx.r5=int32_t(arg2);ctx.f_odd=&ctx.f0.u32h;get_function(fn)(base.data(),&ctx);if(fn==0x8021cee0)assert(ctx.r2==0);};
  call(0x80008A54,object);put(base,object+0x38,0x807f0000);call(0x801AD90C,0x807f0000);put(base,0x801e3430,0);
  call(0x8021cee0,0); // The original scene guard accepts supplied mode2.
  put(base,0x807f0008,0x80252899);call(0x801AF954,object,0x807f0000);
  put(base,0x807f0008,0x8025289d);call(0x801AFD40,object,0x807f0000);
  auto raw=emit(base,object,false,false);assert(word(raw,0x8009e0c8)-begin==3000);
 }
 if(kind==8){
  auto c=context(0);c.f_odd=&c.f0.u32h;func_80008940_resident(base.data(),&c);
  c=context(0x80261e68);func_80007BE0_resident(base.data(),&c);
  c=context(0);func_80235C50_overlay_4a6820_80230590(base.data(),&c);
  assert(object==0x8013dd90&&word(base,object+8)==0x26026642);
  auto raw=emit(base,object,false,false);assert(word(raw,0x8009e0c8)-begin==5840);
 }
 assert(int(pal_background_kind(base,true,object))==kind);
 assert(pal_background_kind(base,true,uint64_t(int64_t(int32_t(object))))==PalBackgroundKind(kind));
 assert(pal_background_kind(base,true,0x123456788013c47cULL)==PalBackgroundKind::None);
 assert(pal_background_kind(base,true,object+4)==PalBackgroundKind::None);
 assert(pal_background_kind(base,false,object)==PalBackgroundKind::None);
 auto original=emit(base,object,false,false),four=emit(base,object,true,false);
 assert(four==original); // Whole8MiB, including original caches/stack, remains identical.
 auto changed=emit(base,object,true,true);const auto final=word(changed,0x8009E0C8);
 assert(final==word(original,0x8009E0C8)+(kind==6?344:(kind==3||kind==5)?440:kind==1?88:56));
 Audit a{original,{},{}},c{changed,{},{}};
 a.list(begin,word(original,0x8009E0C8));c.list(begin,final);
 assert(a.draws.size()==unsigned(kind==4?150:kind==8?180:kind==7?90:kind==5?38:kind==6?20:40)&&c.draws.size()==a.draws.size()&&c.scissor.empty()&&!c.aspect&&!c.wide&&c.xoffset==0);
 for(unsigned i=0;i<a.draws.size();++i){auto expected=a.draws[i].original;
  if(kind==1){auto&lr=expected[0];if(((lr>>12)&4095)==1276)lr+=16<<12;if((lr&4095)==956)lr+=8;}
  assert(expected==c.draws[i].original&&a.draws[i].aspect==0&&c.draws[i].aspect==unsigned((kind==3||kind==5||kind==6)?2:1)&&c.draws[i].wide&&c.draws[i].xoffset==(kind==1?-16:0)&&c.draws[i].yoffset==(kind==1?-8:0));}
 if(kind==3||kind==5||kind==6){
  assert(c.edges.size()==unsigned(kind==6?12:16));
  // Exact public per-rectangle origins stretch only the zero-U-step outer
  // column; original center draw immediately overwrites their 1px overlap.
  for(unsigned i=0;i<c.edges.size();++i){
   const auto&e=c.edges[i];const unsigned y=e[2]&65535;const bool right=(e[1]&0x7ff8)==0x4000;
   const unsigned height=kind==6?std::min(right?256u:128u,960-y):y==896?64:128;
   assert(y%(kind==6&&right?256:128)==0&&y<960&&(e[3]&65535)==y+height);
   assert(e[4]==(right?(0x07e00000u|(kind>=5?0:y==896?0x7e00:0x7c00)):(kind>=5?0u:y==896?0x7e00u:0x7c00u)));assert(e[5]==0x00000400);
   GfxCommand edgeCommands[3]{};auto ec=edgeCommands;
   gEXTextureRectangle(ec++,right?G_EX_ORIGIN_NONE:G_EX_ORIGIN_LEFT,
    right?G_EX_ORIGIN_RIGHT:G_EX_ORIGIN_NONE,right?1276:-4,y,4,y+height,0,right?2016:0,kind>=5?0:y==896?32256:31744,0,1024);
   for(unsigned w=0;w<3;++w){assert(e[2*w]==edgeCommands[w].values.word0);assert(e[2*w+1]==edgeCommands[w].values.word1);}
  }
 }else assert(c.edges.empty());
 if(kind==3||kind==5||kind==6){
  // If a different original draw path changes UV or texture ownership, never
  // derive side strips from it. Keep the emitted center and balanced state.
  for(unsigned mutation:{0u,1u}){
   auto mismatch=base;auto ctx=context(object);ctx.f_odd=&ctx.f0.u32h;
   uint32_t originalEnd=0;
   {PalBackgroundScope scope(mismatch,true,object);assert(scope);
    func_80041B50_resident(mismatch.data(),&ctx);originalEnd=word(mismatch,0x8009E0C8);
    for(auto p=begin+40;p<originalEnd;p+=8){auto op=word(mismatch,p);
     if((mutation==0&&op==0xE1000000)||(mutation==1&&op==uint32_t(kind>=5?0xFD500000:0xFD100000))){put(mismatch,p+4,word(mismatch,p+4)^32);break;}
    }
   }
   assert(word(mismatch,0x8009E0C8)==originalEnd+16);
   Audit rejected{mismatch,{},{}};rejected.list(begin,originalEnd+16);
   assert(rejected.edges.empty()&&rejected.draws.size()==unsigned(kind==5?38:kind==6?20:40)&&rejected.aspect==0&&rejected.scissor.empty());
  }
 }
 if(kind==4){
  // Cover ownership includes color/material/layer/slot. Its 150 records bind
  // exactly one descriptor, so neighboring descriptor data is not our extent.
  for(auto offset:{0xeu,0xfu,0x10u,5u}){auto altered=base;byte(altered,object+offset,1);auto before=altered;
   {PalBackgroundScope scope(altered,true,object);assert(!scope);}assert(altered==before);}
  auto altered=base;put(altered,object+8,(word(altered,object+8)&0x01ffffff)|0x06000000);assert(pal_background_kind(altered,true,object)==PalBackgroundKind::None);
  altered=base;byte(altered,word(base,object+0x30)+1799,255);assert(pal_background_kind(altered,true,object)==PalBackgroundKind::None);
  altered=base;std::memcpy(altered.data()+(object&0x7fffff)+120,altered.data()+(object&0x7fffff),60);
  assert(pal_background_kind(altered,true,object+120)==PalBackgroundKind::None);
  altered=base;byte(altered,word(base,object+0x14)+12,255);assert(pal_background_kind(altered,true,object)==PalBackgroundKind::ScreenCover);
  for(uint8_t alpha:{uint8_t(0),uint8_t(127),uint8_t(255)}){altered=base;byte(altered,object+0x11,alpha);
   assert(pal_background_kind(altered,true,object)==PalBackgroundKind::ScreenCover);
   {PalBackgroundScope scope(altered,true,object);assert(scope);}assert(altered[((object+0x11)&0x7fffff)^3]==alpha);
  }
 }
 if(kind==5){
  // The actual emitter omits DE when material2 is already cached. Its FA/E2
  // setup still precedes the same38texture groups; edges must remain present.
  auto cached=base;byte(cached,0x800bdb26,0);byte(cached,0x800bdb27,2);
  auto raw=emit(cached,object,false,false),wide=emit(cached,object,true,true);
  assert(word(raw,begin)==0xfa000000&&word(wide,0x8009e0c8)==word(raw,0x8009e0c8)+440);
  Audit cachedAudit{wide,{},{}};cachedAudit.list(begin,word(wide,0x8009e0c8));
  assert(cachedAudit.edges.size()==16&&cachedAudit.draws.size()==38&&cachedAudit.scissor.empty()&&!cachedAudit.aspect);
 }
 if(kind==5){
  // The same metadata in a foreign original resource owner is declined.
  for(auto [address,value]:{std::pair{0x80143d6cu,0x801f684cu},std::pair{0x802bb89cu,0x0040001du},
      std::pair{0x802bb9fcu,0xaa000001u},std::pair{object+0x34,0x803d5110u},std::pair{object+8,0x06026642u}}){
   auto altered=base;put(altered,address,value);auto before=altered;
   {PalBackgroundScope scope(altered,true,object);assert(!scope);}assert(altered==before);
  }
  for(auto address:{0x803d6428u+455,0x802bb640u+455}){auto altered=base;byte(altered,address,255);
   assert(pal_background_kind(altered,true,object)==PalBackgroundKind::None);}
 }
 if(kind==6){
  for(auto [address,value]:{std::pair{0x80143d6cu,0x802bb80cu},std::pair{0x802b92fcu,0x00350001u},
      std::pair{0x802ba58cu,0x00350001u},std::pair{0x802b933cu,0xe900000du},std::pair{0x802ba658u,0xe900002bu},
      std::pair{object+0x34,0x803d3f10u},std::pair{object+8,0x04026642u}}){
   const auto table=word(base,0x80143d6c);
   if((address==0x802b92fc||address==0x802b933c)&&table!=0x802b926c)continue;
   if((address==0x802ba58c||address==0x802ba658)&&table!=0x802ba394)continue;
   auto altered=base;put(altered,address,value);auto before=altered;
   {PalBackgroundScope scope(altered,true,object);assert(!scope);}assert(altered==before);
  }
  for(auto address:{0x803d5b58u+239,0x802b8d40u+239}){auto altered=base;byte(altered,address,255);
   assert(pal_background_kind(altered,true,object)==PalBackgroundKind::None);}
 }
 if(kind==7){
  for(auto [address,value]:{std::pair{0x80077164u,0x802464bcu},std::pair{0x8024660cu,0x00660019u},
      std::pair{0x80252898u,0xec711e00u},std::pair{0x802537a8u,0xaa000001u},
      std::pair{object+0x34,0x8022c6d0u},std::pair{object+8,0x04026642u},std::pair{0x801fd5f0u,0u}}){
   auto altered=base;put(altered,address,value);auto before=altered;
   {PalBackgroundScope scope(altered,true,object);assert(!scope);}assert(altered==before);
  }
  auto other=base;byte(other,word(base,0x801fd5f0)+0x1e,1);assert(pal_background_kind(other,true,object)==PalBackgroundKind::None);
  for(auto address:{0x8022fc8cu+11,0x802406fcu+1079,0x80267e80u+1535}){auto altered=base;byte(altered,address,255);
   assert(pal_background_kind(altered,true,object)==PalBackgroundKind::None);}
 }
 if(kind==8){
  for(auto offset:{0xeu,0xfu,0x10u,0x11u,5u}){auto altered=base;byte(altered,object+offset,1);auto before=altered;
   {PalBackgroundScope scope(altered,true,object);assert(!scope);}assert(altered==before);}
  for(auto [address,value]:{std::pair{0x80143d6cu,0x802bb80cu},std::pair{0x80263434u,0x00020098u},std::pair{object+8,0x04026642u}}){auto altered=base;put(altered,address,value);assert(pal_background_kind(altered,true,object)==PalBackgroundKind::None);}
  for(auto address:{0x8025a014u+11,0x80260848u+2159,0x80212580u+2047}){auto altered=base;byte(altered,address,altered[(address&0x7fffff)^3]^255);
   assert(pal_background_kind(altered,true,object)==PalBackgroundKind::None);}
  auto copy=base;std::memcpy(copy.data()+((object+60)&0x7fffff),copy.data()+(object&0x7fffff),60);
  assert(pal_background_kind(copy,true,object+60)==PalBackgroundKind::None);
 }
 // Exact pinned public GBI macros prove scope encoding, not private opcode guesses.
 GfxCommand commands[8]{};auto cmd=commands;gEXEnable(cmd++);gEXPushScissor(cmd++);
 gEXSetScissor(cmd++,0,G_EX_ORIGIN_LEFT,G_EX_ORIGIN_RIGHT,0,0,0,240);gEXSetRectAspect(cmd++,(kind==3||kind==5||kind==6)?G_EX_ASPECT_ADJUST:G_EX_ASPECT_STRETCH);
 if(kind==1)gEXSetRectAlign(cmd++,G_EX_ORIGIN_NONE,G_EX_ORIGIN_NONE,-16,-8,-16,-8);
 for(unsigned i=0;i<unsigned(kind==1?7:5);++i){assert(word(changed,begin+8*i)==commands[i].values.word0);assert(word(changed,begin+8*i+4)==commands[i].values.word1);}
 cmd=commands;if(kind==1)gEXSetRectAlign(cmd++,G_EX_ORIGIN_NONE,G_EX_ORIGIN_NONE,0,0,0,0);gEXSetRectAspect(cmd++,G_EX_ASPECT_AUTO);gEXPopScissor(cmd++);
 for(unsigned i=0;i<unsigned(kind==1?4:2);++i){assert(word(changed,final-(kind==1?32:16)+8*i)==commands[i].values.word0);assert(word(changed,final-(kind==1?28:12)+8*i)==commands[i].values.word1);}
 // Every nonbackground pool entry, including real foreground widgets/portraits,
 // is rejected with no writes. Do not stretch a layer merely because it is2D.
 for(unsigned i=0;i<273;++i){auto candidate=0x8013c47c+i*0x3c;if(candidate==object)continue;
  const auto additional=pal_background_kind(base,true,candidate);
  if(additional==PalBackgroundKind::MenuHorizontalWatermark||additional==PalBackgroundKind::MenuVerticalWatermark){assert(candidate==0x8013C530||candidate==0x8013C56C);continue;}
  auto saved=base;{PalBackgroundScope scope(base,true,candidate);assert(!scope);}assert(saved==base);
 }
 // Original metadata alteration, position/scale/view changes, capacity and nesting fail closed.
 for(auto address:{word(base,object+0x14),word(base,object+0x30)}){auto altered=base;byte(altered,address,0xff);auto before=altered;{PalBackgroundScope scope(altered,true,object);assert(!scope);}assert(before==altered);}
 for(auto offset:{0x20u,0x24u,0x28u,0x2cu}){auto altered=base;put(altered,object+offset,0x40000000);auto before=altered;{PalBackgroundScope scope(altered,true,object);assert(!scope);}assert(before==altered);}
 auto short_space=base;put(short_space,0x8009E0C8,b.end-64);auto saved=short_space;{PalBackgroundScope scope(short_space,true,object);assert(!scope);}assert(saved==short_space);
 auto nested=base;{PalBackgroundScope scope(nested,true,object);assert(scope);auto before=nested;{PalBackgroundScope second(nested,true,object);assert(!second);}assert(nested==before);}
}
'''
@unittest.skipUnless(shutil.which('c++') and (RT64/'include/rt64_extended_gbi.h').is_file(),'C++ compiler and pinned RT64 GBI required')
class BackgroundOriginalTests(unittest.TestCase):
 def test_original_common_and_career_draw_chains_scope_only_the_background(self):
  generated=ROOT/'.local/pal-map-bound-01/functions';header=ROOT/'.local/deps/N64Recomp/include'
  names=['80041B50','800419F8','800423FC','8004250C','80042D0C','80047558','80047500','80007BE0','80007BF8','80007C2C','80043D90','80043D80','8000FACC','80043C74','80008A54','80043BD8','80043430','800433E0','80043710','80007C90','80008940','800089C0','8004C59C','8004C608'];originals=[generated/f'func_{n}_resident.c' for n in names]
  names+=['801ECC08','801EBF40','801EBB14'];originals +=[generated/f'func_{n}_overlay_2b0e60_801eb960.c' for n in names[-3:]]
  extra=['801B0044','801AE2F8','801B0000','801B0038','801AF818','801AE2B0','801AE2D4','801AF910','801AE4A8','801AFDB0','801AFEA4','801B1818','801B189C','801AE354','801AD90C','801AF954','801AF9C4','801AFD40']
  names+=extra;originals +=[generated/f'func_{n}_overlay_2dee70_801ad820.c' for n in extra]
  names+=['802B5DB4','802B6800'];originals +=[generated/f'func_{n}_overlay_4689a0_802b4b10.c' for n in names[-2:]]
  names+=['8021CEE0'];originals +=[generated/'func_8021CEE0_overlay_523120_80212700.c']
  names+=['80235C50','801DE4FC'];originals +=[generated/'func_80235C50_overlay_4a6820_80230590.c',generated/'func_801DE4FC_overlay_287ab0_801db100.c']
  symbols=[path.stem for path in originals]
  snapshots=[('mainmenu09',0x8013C47C,1),('career-final08',0x8013C5E4,2),('mainmenu09',0x8013C47C,3)]
  paths=[ROOT/f'.local/pal-acceptance/{n}.rdram' for n,_,_ in snapshots]
  if not all(p.is_file() for p in [header/'recomp.h',*originals,*paths]):self.skipTest('Private original PAL drawchain and snapshots required')
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);objects=[]
   for name,source in zip(names,originals):
    obj=p/(name+'.o');built=subprocess.run(['cc','-O2','-I'+str(header),'-c',str(source),'-o',str(obj)],capture_output=True,text=True);self.assertEqual(built.returncode,0,built.stderr);objects.append(obj)
   code=CODE.replace('ORIGINAL_DECLARATIONS','\n'.join('extern "C" void '+symbol+'(uint8_t*,recomp_context*);' for symbol in symbols)).replace('ORIGINAL_LOOKUP','\n'.join('case 0x'+n+':return '+symbol+';' for n,symbol in zip(names,symbols)))
   (p/'chain.cpp').write_text(code)
   source=ROOT/'src/runtime/rom_image.cpp';miniz=ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz';miniz_build=ROOT/'.local/runtime-deps-build/librecomp/miniz'
   built=subprocess.run(['c++','-std=c++20','-O2','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-I'+str(ROOT/'src'),'-I'+str(header),'-I'+str(RT64/'include'),'-I'+str(miniz),'-I'+str(miniz_build),str(p/'chain.cpp'),str(ROOT/'src/runtime/pal_background_widescreen.cpp'),str(ROOT/'src/runtime/pal_sky_widescreen.cpp'),str(source),*[str(x)for x in objects],'-o',str(p/'chain')],capture_output=True,text=True)
   self.assertEqual(built.returncode,0,built.stderr)
   # Exact original overlay data populates the ordinary fixture; the actual
   # original phase-0 callback constructs both cover and accompanying text.
   sections=json.loads((ROOT/'.local/pal-map-bound-01/section-analysis.json').read_text())
   sections=sections if isinstance(sections,list) else sections['sections']
   section=next(s for s in sections if s['rom']==0x2b0e60)
   rom=(ROOT/'.local/inputs/pal-en-de/rom.z64').read_bytes();self.assertEqual(hashlib.sha256(rom).hexdigest(),'6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf')
   cover=bytearray(paths[0].read_bytes());raw=rom[section['rom']:section['rom']+section['load_size']]
   for i,value in enumerate(raw):cover[((section['vram']+i)&0x7fffff)^3]=value
   for a in [0x801f7220,0x801f7224,0x801f722c]:cover[a&0x7fffff:(a&0x7fffff)+4]=bytes(4)
   (p/'cover.rdram').write_bytes(cover);snapshots.append(('cover',0x8013c47c,4));paths.append(p/'cover.rdram')
   scene=bytearray(paths[0].read_bytes())
   for offset in [0x4689a0,0x2dee70]:
    section=next(s for s in sections if s['rom']==offset)
    for i,value in enumerate(rom[offset:offset+section['load_size']]):scene[((section['vram']+i)&0x7fffff)^3]=value
   (p/'scene.rdram').write_bytes(scene);snapshots.append(('scene',0x8013c47c,5));paths.append(p/'scene.rdram')
   for table,selector,states in [(0x802b926c,0x802bbe11,range(5)),(0x802ba394,0x802ba36c,range(2))]:
    for state in states:
     globe=bytearray(scene);globe[0x143d6c:0x143d70]=table.to_bytes(4,'little');globe[(selector&0x7fffff)^3]=state
     path=p/f'globe-{table:x}-{state}.rdram';path.write_bytes(globe);snapshots.append(('globe',0x8013c47c,6));paths.append(path)
   # The original asset request fixes the gradient art's real ownership,
   # rather than reusing currentCareer RAM occupied by language scripts.
   import ast,struct
   decoder=next(n for n in ast.parse((ROOT/'.local/team-visual-assets-01/probe_assets.py').read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='decode');env={};exec(compile(ast.Module(body=[decoder],type_ignores=[]),'originaldecoder','exec'),env)
   start,end=struct.unpack_from('>II',rom,0x972bc+(0x112-1)*8);start&=0x7fffffff;art,_=env['decode'](rom[start:end],start)
   self.assertEqual(hashlib.sha256(art).hexdigest(),'9e74f95ee7237b5676a786ec4e1fafb370dd597d7563fbf52075538e7a1a9656')
   gradient=bytearray(scene);section=next(s for s in sections if s['rom']==0x523120)
   for i,value in enumerate(rom[section['rom']:section['rom']+section['load_size']]):gradient[((section['vram']+i)&0x7fffff)^3]=value
   for i,value in enumerate(art):gradient[((0x80265b80+i)&0x7fffff)^3]=value
   weekly=(ROOT/'.local/pal-acceptance/career-week04-10.rdram').read_bytes();ctx=int.from_bytes(weekly[0x1fd5f0:0x1fd5f4],'little');self.assertEqual(ctx,0x801fd4c0)
   gradient[ctx&0x7fffff:(ctx&0x7fffff)+0x100]=weekly[ctx&0x7fffff:(ctx&0x7fffff)+0x100]
   gradient[0x1fd5f0:0x1fd5f4]=ctx.to_bytes(4,'little');gradient[((ctx+0x1e)&0x7fffff)^3]=2
   (p/'gradient.rdram').write_bytes(gradient);snapshots.append(('gradient',0x8013c47c,7));paths.append(p/'gradient.rdram')
   result=bytearray(paths[0].read_bytes());section=next(s for s in sections if s['rom']==0x4a6820)
   for i,value in enumerate(rom[section['rom']:section['rom']+section['load_size']]):result[((section['vram']+i)&0x7fffff)^3]=value
   start,end=struct.unpack_from('>II',rom,0x972bc+(0x55-1)*8);start&=0x7fffffff;art,_=env['decode'](rom[start:end],start)
   self.assertEqual(hashlib.sha256(art).hexdigest(),'a7c2c2f52b61af42027e04953be7911ab9e0f0b363e525537202c3f0df580b12')
   for i,value in enumerate(art):result[((0x80201280+i)&0x7fffff)^3]=value
   (p/'result.rdram').write_bytes(result);snapshots.append(('result',0x8013dd90,8));paths.append(p/'result.rdram')
   for (_,address,kind),snapshot in zip(snapshots,paths):
    run=subprocess.run([str(p/'chain'),str(snapshot),f'{address:X}',str(kind)],capture_output=True,text=True)
    self.assertEqual(run.returncode,0,snapshot.name+': '+run.stderr)

CLEAR_CODE=r'''#include "recomp.h"
#include "runtime/pal_background_widescreen.hpp"
#include "runtime/pal_sky_widescreen.hpp"
#include <array>
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#define F3DEX_GBI_2
#include "rt64_extended_gbi.h"
extern "C" void func_800017C0_resident(uint8_t*,recomp_context*);
extern "C" void func_800019FC_resident(uint8_t*,recomp_context*);
extern "C" void func_80001B2C_resident(uint8_t*,recomp_context*);
extern "C" recomp_func_t* get_function(int32_t a){assert(uint32_t(a)==0x80001b2c);return func_80001B2C_resident;}
using namespace iss2000;using Bytes=std::vector<uint8_t>;
uint32_t word(const Bytes&r,uint32_t a){uint32_t v;memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
void put(Bytes&r,uint32_t a,uint32_t v){memcpy(r.data()+(a&0x7fffff),&v,4);}
void half(Bytes&r,uint32_t a,uint16_t v){memcpy(r.data()+((a&0x7fffff)^2),&v,2);}
Bytes emit(const Bytes&base,bool wrap,bool wide){auto r=base;recomp_context ctx{};ctx.r29=int32_t(0x807ff000);ctx.f_odd=&ctx.f0.u32h;
 func_800017C0_resident(r.data(),&ctx);
 if(wrap){PalScreenFillScope scope(r,wide);assert(bool(scope)==wide);func_800019FC_resident(r.data(),&ctx);}
 else func_800019FC_resident(r.data(),&ctx);return r;
}
int main(int argc,char**argv){assert(argc==2);Bytes source(0x800000);auto*f=fopen(argv[1],"rb");assert(f);assert(fread(source.data(),1,source.size(),f)==source.size());fclose(f);
 const auto arena=pal_gfx_bounds(source);assert(arena);const auto begin=arena.begin,limit=arena.end+0x54,patch=limit-4;
 for(bool registerFF:{false,true})for(auto color:{std::array<unsigned,4>{255,255,255,1},{0,0,0,0},{21,137,242,1}}){
  auto base=source;put(base,0x8009e0c8,begin);put(base,limit,registerFF?patch:limit);
  for(unsigned i=0;i<4;++i)half(base,0x8013b41eu+2*i,color[i]);
  auto original=emit(base,false,false),four=emit(base,true,false);assert(four==original);
  auto wide=emit(base,true,true);const auto oldEnd=word(original,0x8009e0c8),newEnd=word(wide,0x8009e0c8);
  assert(newEnd==oldEnd+56&&oldEnd-begin==unsigned(registerFF?64:56));
  // The actual caller emits its ED-bearing setup list before the scope.
  assert(word(wide,begin)==0xde000000&&word(wide,begin+4)==0x8006ce18);
  const auto fillBegin=begin+8;
  for(auto p=fillBegin;p<oldEnd;p+=4)assert(word(original,p)==word(wide,p+40));
  if(registerFF){assert(word(original,patch)==fillBegin+16&&word(wide,patch)==fillBegin+56);assert(word(wide,word(wide,patch))==0xff10013f);}
  assert(word(wide,limit)==word(original,limit));
  unsigned fills=0,colorWords=0;for(auto p=fillBegin+40;p<newEnd-16;p+=8){
   auto a=word(wide,p),b=word(wide,p+4);assert(a>>24!=0xed);
   if(a==0xf7000000){const auto c=((color[0]<<8)&0xf800)|((color[1]<<3)&0x7c0)|((color[2]>>2)&0x3e)|(color[3]&1);assert(b==(c<<16|c));++colorWords;}
   if(a>>24==0xf6){assert(a==0xf64fc3bc&&b==0);++fills;}
  }assert(fills==1&&colorWords==1);
  // Exact publicGBI scope encoding restores AUTO and the prior real scissor;
  // the next ordinary UI draw therefore has no inherited stretch or clip.
  GfxCommand commands[7]{};auto cmd=commands;gEXEnable(cmd++);gEXPushScissor(cmd++);gEXSetScissor(cmd++,0,G_EX_ORIGIN_LEFT,G_EX_ORIGIN_RIGHT,0,0,0,240);gEXSetRectAspect(cmd++,G_EX_ASPECT_STRETCH);gEXSetRectAspect(cmd++,G_EX_ASPECT_AUTO);gEXPopScissor(cmd++);
  for(unsigned i=0;i<5;++i){assert(word(wide,fillBegin+8*i)==commands[i].values.word0);assert(word(wide,fillBegin+8*i+4)==commands[i].values.word1);}
  for(unsigned i=5;i<7;++i){assert(word(wide,newEnd-16+8*(i-5))==commands[i].values.word0);assert(word(wide,newEnd-12+8*(i-5))==commands[i].values.word1);}
 }
 auto limited=source;put(limited,0x8009e0c8,arena.end-120);auto before=limited;{PalScreenFillScope scope(limited,true);assert(!scope);}assert(before==limited);
 for(auto [a,v]:{std::pair{0x8009e02cu,0x8013b400u},std::pair{0x8013b42cu,0x00f00180u},std::pair{0x800a4aa4u,0x800e0300u}}){auto other=source;put(other,a,v);before=other;{PalScreenFillScope scope(other,true);assert(!scope);}assert(before==other);}
 auto nested=source;{PalScreenFillScope first(nested,true);assert(first);before=nested;{PalScreenFillScope second(nested,true);assert(!second);}assert(before==nested);}
}
'''
@unittest.skipUnless(shutil.which('c++') and (RT64/'include/rt64_extended_gbi.h').is_file(),'C++ compiler and pinned RT64 GBI required')
class BackgroundScreenFillTests(unittest.TestCase):
 def test_actual_original_frame_clear_widens_without_touching_logos_or_patch_lists(self):
  generated=ROOT/'.local/pal-map-bound-01/functions';header=ROOT/'.local/deps/N64Recomp/include';snapshot=ROOT/'.local/pal-acceptance/mainmenu09.rdram'
  originals=[generated/f'func_{name}_resident.c' for name in ['800017C0','800019FC','80001B2C']]
  if not all(p.is_file() for p in [header/'recomp.h',snapshot,*originals]):self.skipTest('Private original PAL full-frame clear and snapshot required')
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);objects=[]
   for source in originals:
    obj=p/(source.stem+'.o');built=subprocess.run(['cc','-O2','-I'+str(header),'-c',str(source),'-o',str(obj)],capture_output=True,text=True);self.assertEqual(built.returncode,0,built.stderr);objects.append(obj)
   (p/'clear.cpp').write_text(CLEAR_CODE)
   miniz=ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz';miniz_build=ROOT/'.local/runtime-deps-build/librecomp/miniz'
   built=subprocess.run(['c++','-std=c++20','-O2','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-I'+str(ROOT/'src'),'-I'+str(header),'-I'+str(RT64/'include'),'-I'+str(miniz),'-I'+str(miniz_build),str(p/'clear.cpp'),str(ROOT/'src/runtime/pal_background_widescreen.cpp'),str(ROOT/'src/runtime/pal_sky_widescreen.cpp'),str(ROOT/'src/runtime/rom_image.cpp'),*[str(x)for x in objects],'-o',str(p/'clear')],capture_output=True,text=True);self.assertEqual(built.returncode,0,built.stderr)
   run=subprocess.run([str(p/'clear'),str(snapshot)],capture_output=True,text=True);self.assertEqual(run.returncode,0,run.stderr)

@unittest.skipUnless(shutil.which('c++') and shutil.which('cc'),'C/C++ compilers required')
class BackgroundMenuCompositeTests(unittest.TestCase):
 def test_actual_menu_base_and_both_moving_watermarks_share_wide_canvas_without_clipped_edges(self):
  snapshot=ROOT/'.local/select-teams-54-before/yellow.rdram'
  if not snapshot.is_file():self.skipTest('Private actual yellow Select Teams snapshot required')
  folder=ROOT/'.local/pal-map-bound-01/functions';header=ROOT/'.local/deps/N64Recomp/include'
  originals=[folder/f'func_{n}_resident.c'for n in ['80041B50','800419F8','800423FC','8004250C','80042D0C']]
  originals += [folder/f'func_{n}_overlay_32ae00_803ac000.c'for n in ['803C36C0','803C3978','803C3E20','803C3EA0']]
  code=CODE[:CODE.index('int main(int argc,char**argv)')]+r'''
extern "C" void switch_error(const char*,uint32_t,uint32_t){std::abort();}
static void shortput(Bytes&r,uint32_t a,int16_t v){std::memcpy(r.data()+((a&0x7fffff)^2),&v,2);}
int main(int argc,char**argv){assert(argc==2);Bytes base(0x800000);auto*f=fopen(argv[1],"rb");assert(f&&fread(base.data(),1,base.size(),f)==base.size());fclose(f);
 const auto begin=0x800D0328u;put(base,0x800A4AA4,0x800D0320);put(base,0x8009E0C8,begin);
 for(auto object:{0x8013C530u,0x8013C56Cu}){
  assert(pal_background_kind(base,true,object)!=PalBackgroundKind::None&&"Original moving background lettering must share the base background's widescreen mapping");
  auto old=emit(base,object,false,false),four=emit(base,object,true,false),wide=emit(base,object,true,true);assert(old==four);
  Audit a{old,{},{}},b{wide,{},{}};a.list(begin,word(old,0x8009E0C8));b.list(begin,word(wide,0x8009E0C8));assert(!a.draws.empty()&&a.draws.size()==b.draws.size());
  for(unsigned n=0;n<a.draws.size();++n)assert(a.draws[n].original==b.draws[n].original&&b.draws[n].aspect==1&&b.draws[n].wide);
  assert(!b.aspect&&!b.wide&&b.scissor.empty());
  const auto callback=object==0x8013C530?func_803C3E20_overlay_32ae00_803ac000:func_803C3EA0_overlay_32ae00_803ac000;
  auto moved=base;auto c=context(0);c.f_odd=&c.f0.u32h;callback(moved.data(),&c);assert(pal_background_kind(moved,true,object)!=PalBackgroundKind::None);
  assert(word(moved,object+0x20)!=word(base,object+0x20)||word(moved,object+0x24)!=word(base,object+0x24));
  for(unsigned fault=0;fault<6;++fault){auto bad=base;
   if(fault==0)byte(bad,object+5,3);if(fault==1)put(bad,object+8,0x04026642);if(fault==2)put(bad,object+0x28,0x40000000);
   if(fault==3)byte(bad,word(base,object+0x14)+35,255);if(fault==4)byte(bad,word(base,object+0x30)+143,255);
   if(fault==5)shortput(bad,object+(object==0x8013C530?0x20:0x24),1000);
   const auto before=bad;{PalBackgroundScope scope(bad,true,object);assert(!scope);}assert(bad==before);
  }
 }
 auto old=emit(base,0x8013C47C,false,false),wide=emit(base,0x8013C47C,true,true);Audit a{old,{},{}},b{wide,{},{}};
 a.list(begin,word(old,0x8009E0C8));b.list(begin,word(wide,0x8009E0C8));assert(a.draws.size()==40&&b.draws.size()==40);
 unsigned right=0,bottom=0;
 for(unsigned n=0;n<40;++n){const auto&before=a.draws[n];const auto&after=b.draws[n];
  auto expected=before.original;auto&lr=expected[0];if(((lr>>12)&4095)==1276){lr+=16<<12;++right;}if((lr&4095)==956){lr+=8;++bottom;}
  assert(after.original==expected&&"Background origin alignment must not leave the already-clipped right/bottom edge uncovered");
  assert(after.xoffset==-16&&after.yoffset==-8&&after.aspect==1&&after.wide);
 }
 assert(right==4&&bottom==10);
 // Altered original texture/UV output must not receive guessed edge geometry.
 for(unsigned fault=0;fault<2;++fault){auto bad=base;auto c=context(0x8013C47C);c.f_odd=&c.f0.u32h;
  unsigned originalEnd;{PalBackgroundScope scope(bad,true,c.r4);assert(scope);func_80041B50_resident(bad.data(),&c);originalEnd=word(bad,0x8009E0C8);
   for(auto pc=begin+56;pc<originalEnd;pc+=8)if(word(bad,pc)==(fault?0xE1000000u:0xFD500000u)){put(bad,pc+4,word(bad,pc+4)^32);break;}
  }
  Audit rejected{bad,{},{}};rejected.list(begin,word(bad,0x8009E0C8));assert(rejected.draws.size()==40);
  for(unsigned n=0;n<40;++n)assert(rejected.draws[n].original[0]==a.draws[n].original[0]);
 }
}
'''
  code=code.replace('ORIGINAL_DECLARATIONS','\n'.join('extern "C" void '+x.stem+'(uint8_t*,recomp_context*);'for x in originals)).replace('ORIGINAL_LOOKUP','\n'.join('case 0x'+x.stem[5:13]+':return '+x.stem+';'for x in originals))
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);objects=[]
   for original in originals:
    obj=p/(original.stem+'.o');q=subprocess.run(['cc','-O2','-I'+str(header),'-c',str(original),'-o',str(obj)],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr);objects.append(str(obj))
   (p/'composite.cpp').write_text(code);miniz=ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz';miniz_build=ROOT/'.local/runtime-deps-build/librecomp/miniz'
   q=subprocess.run(['c++','-std=c++20','-O2','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-I'+str(ROOT/'src'),'-I'+str(header),'-I'+str(RT64/'include'),'-I'+str(miniz),'-I'+str(miniz_build),str(p/'composite.cpp'),str(ROOT/'src/runtime/pal_background_widescreen.cpp'),str(ROOT/'src/runtime/pal_sky_widescreen.cpp'),str(ROOT/'src/runtime/rom_image.cpp'),*objects,'-o',str(p/'composite')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
   for fixture in [snapshot,ROOT/'.local/select-teams-54-before/blue-teams.rdram']:
    if fixture.is_file():
     q=subprocess.run([str(p/'composite'),str(fixture)],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)

@unittest.skipUnless(shutil.which('c++') and (RT64/'src/render/rt64_framebuffer_renderer.cpp').is_file(),'Compiler and pinned RT64 renderer source required')
class BackgroundViewportTests(unittest.TestCase):
 def test_actual_rt64_viewport_stretches_only_scoped_background_rectangles(self):
  original=(RT64/'src/render/rt64_framebuffer_renderer.cpp').read_text()
  body=re.search(r'    RenderViewport convertViewportRect\(.*?\n    \}',original,re.S).group()
  self.assertRegex(original,r'call\.callDesc\.rectAspect == G_EX_ASPECT_STRETCH\).*?\n\s*invRatioScale = 1\.0f;')
  code=r'''#include <cassert>
#include <cmath>
#include <cstdint>
#include <initializer_list>
#include <hlsl++.h>
#include "rt64_extended_gbi.h"
struct FixedRect {int a,b,c,d;int left(bool)const{return (a+3)>>2;}int top(bool)const{return (b+3)>>2;}int right(bool)const{return (c+3)>>2;}int bottom(bool)const{return (d+3)>>2;}};
struct RenderViewport {float x,y,width,height;};
'''+body+r'''
int main(){
 for(float scale:{1.f,3.f,3.75f,4.5f,6.f,7.5f,9.f,1080.f/232}){
  const hlslpp::float2 wide(scale*4.f/3.f,scale);
  // Genuine Career canvas; STRETCH uses the renderer's originalinvRatio1.
  auto background=convertViewportRect({0,0,1280,960},wide,320,1,1,0,G_EX_ORIGIN_NONE,G_EX_ORIGIN_NONE);
  assert(background.x==0&&background.y==0&&std::abs(background.width-320*wide.x)<1&&std::abs(background.height-240*scale)<1);

  // Genuine common-menu COPY rectangles were clipped before(-4,-2) align.
  // Apply the pinned RDP inclusive LR bits, then the actual alignment offsets.
  auto clipped=convertViewportRect({0,0,(1276|3)-16,(956|3)-8},wide,320,1,1,0,G_EX_ORIGIN_NONE,G_EX_ORIGIN_NONE);
  auto repaired=convertViewportRect({0,0,(1292|3)-16,(964|3)-8},wide,320,1,1,0,G_EX_ORIGIN_NONE,G_EX_ORIGIN_NONE);
  assert(clipped.width<background.width-3*float(wide.x)&&clipped.height<background.height-scale);
  assert(repaired.x==0&&repaired.y==0&&std::abs(repaired.width-background.width)<.01f&&std::abs(repaired.height-background.height)<.01f);

  // The original title center is exactly 4:3; new strips bridge each physical
  // side to that centered canvas. Their 1px overlap is redrawn by the original.
  auto center=convertViewportRect({0,0,1280,960},wide,320,.75f,1,0,G_EX_ORIGIN_NONE,G_EX_ORIGIN_NONE);
  assert(std::abs(center.width-320*scale)<1&&center.x>0);
  // Both original modes: title COPY applies inclusive low coordinate bits;
  // bank64 CI8 one-cycle does not. The same encoded strips bridge both sides.
  for(bool copy:{false,true}){
   auto left=convertViewportRect({-4,0,copy?7:4,copy?131:128},wide,320,.75f,1,0,G_EX_ORIGIN_LEFT,G_EX_ORIGIN_NONE);
   auto right=convertViewportRect({1276,0,copy?1287:1284,copy?131:128},wide,320,.75f,1,0,G_EX_ORIGIN_NONE,G_EX_ORIGIN_RIGHT);
   assert(left.x<=0&&left.x+left.width>=center.x);
   assert(right.x<=center.x+center.width&&right.x+right.width>=320*float(wide.x)-0.01f&&right.x+right.width-320*float(wide.x)<=2*scale+1);
  }
  // Direct introCI8 side strips meet center0/320 exactly. Unlike opaque
  // title strips, these must not overlap and apply fadealpha twice.
  auto whiteLeft=convertViewportRect({-4,0,0,960},wide,320,.75f,1,0,G_EX_ORIGIN_LEFT,G_EX_ORIGIN_NONE);
  auto whiteRight=convertViewportRect({1280,0,1284,960},wide,320,.75f,1,0,G_EX_ORIGIN_NONE,G_EX_ORIGIN_RIGHT);
  assert(whiteLeft.x<=0&&std::abs(whiteLeft.x+whiteLeft.width-center.x)<0.01f);
  assert(std::abs(whiteRight.x-center.x-center.width)<0.01f&&whiteRight.x+whiteRight.width>=320*float(wide.x)-0.01f);
  // Original-sized portrait/widget stays centered once AUTO is restored.
  FixedRect widget{96,192,224,320};
  auto foreground=convertViewportRect(widget,wide,320,.75f,1,0,G_EX_ORIGIN_NONE,G_EX_ORIGIN_NONE);
  assert(std::abs(foreground.width-32*scale)<1&&std::abs(foreground.height-32*scale)<1);
  assert(foreground.x>background.x);
  const hlslpp::float2 normal(scale,scale);
  auto four=convertViewportRect({0,0,1280,960},normal,320,1,1,0,G_EX_ORIGIN_NONE,G_EX_ORIGIN_NONE);
  assert(four.x==0&&std::abs(four.width-320*scale)<1&&std::abs(four.height-240*scale)<1);
 }
}
'''
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'viewport.cpp').write_text(code)
   built=subprocess.run(['c++','-std=c++20','-O2','-isystem',str(RT64/'src/contrib/hlslpp/include'),'-I'+str(RT64/'include'),str(p/'viewport.cpp'),'-o',str(p/'viewport')],capture_output=True,text=True)
   self.assertEqual(built.returncode,0,built.stderr)
   run=subprocess.run([str(p/'viewport')],capture_output=True,text=True)
   self.assertEqual(run.returncode,0,run.stderr)

INTRO_CODE=r'''#include "recomp.h"
#include "runtime/menu_sprite_runtime.hpp"
#include "runtime/pal_background_widescreen.hpp"
#include "runtime/pal_sky_widescreen.hpp"
#include <array>
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#define F3DEX_GBI_2
#include "rt64_extended_gbi.h"
extern "C" void func_801ADD44_overlay_2c99e0_801ad820(uint8_t*,recomp_context*);
extern "C" void func_801ADC7C_overlay_2c99e0_801ad820(uint8_t*,recomp_context*);
static bool route_wide=false,route_adapt=false;
namespace iss2000 {
enum class AspectRatio{Wide16x9,Original4x3};
namespace platform {struct Settings{AspectRatio aspect_ratio;};Settings render_settings(){return {route_wide?AspectRatio::Wide16x9:AspectRatio::Original4x3};}}
static recomp_context original_leaf_context;
static void run_original_guest(uint32_t a,uint8_t*r,recomp_context*c){assert(a==0x801add44);func_801ADD44_overlay_2c99e0_801ad820(r,c);original_leaf_context=*c;}
ACTUAL_INTRO_WRAPPER
}
extern "C" void verified_actual_route(uint8_t*r,recomp_context*c){iss2000::draw_widescreen_intro_canvas(r,c);assert(memcmp(c,&iss2000::original_leaf_context,sizeof(*c))==0);}
extern "C" recomp_func_t* get_function(int32_t a){assert(uint32_t(a)==0x801add44);return route_adapt?verified_actual_route:func_801ADD44_overlay_2c99e0_801ad820;}
using namespace iss2000;using Bytes=std::vector<uint8_t>;
uint32_t word(const Bytes&r,uint32_t a){uint32_t v;memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
void put(Bytes&r,uint32_t a,uint32_t v){memcpy(r.data()+(a&0x7fffff),&v,4);}
void byte(Bytes&r,uint32_t a,uint8_t v){r[(a&0x7fffff)^3]=v;}
struct Profile{uint32_t desc,palette,segments,rectangles,texels;};
constexpr Profile profiles[]={{0x801b7608,0x801ae080,0x801ae280,163,0x00200020},
 {0x801b7680,0x801b2bc8,0x801b2dc8,96,0x00400020},{0x801b76e0,0x801b7048,0x801b7248,80,0x00200020}};
Bytes emit(const Bytes&base,Profile p,unsigned alpha){auto r=base;recomp_context c{};c.r4=int32_t(p.desc);c.r5=int32_t(p.palette);c.r6=int32_t(p.segments);c.r7=alpha;c.r29=int32_t(0x807ff000);c.f_odd=&c.f0.u32h;func_801ADD44_overlay_2c99e0_801ad820(r.data(),&c);return r;}
int main(int argc,char**argv){assert(argc==3);Bytes source(0x800000);auto*f=fopen(argv[1],"rb");assert(f&&fread(source.data(),1,source.size(),f)==source.size());fclose(f);
 const auto bounds=pal_gfx_bounds(source);assert(bounds);const auto begin=bounds.begin;put(source,0x8009e0c8,begin);put(source,0x801b77c0,begin);
 // Dump authentic original streams for a reproducible pinned-output proof.
 for(unsigned k=0;k<3;++k){auto r=emit(source,profiles[k],255);auto end=word(r,0x801b77c0);char name[1024];snprintf(name,sizeof(name),"%s-%u.bin",argv[2],k);f=fopen(name,"wb");assert(f);for(auto p=begin;p<end;++p)fputc(r[(p&0x7fffff)^3],f);fclose(f);}
 for(auto profile:profiles)for(unsigned alpha:{0u,96u,255u}){
  // Full original caller supplies the exact arguments/private pointer and
  // consumes the post-adapter cursor through its unmodified return path.
  auto caller=[&](bool adapt,bool wide){auto r=source;put(r,0x801b770c,profile.desc==0x801b76e0);put(r,0x801b76f4,profile.desc==0x801b7608);put(r,0x801b7704,profile.desc==0x801b7680);byte(r,0x801b76f8,alpha);byte(r,0x801b7708,alpha);
   recomp_context c{};c.r5=int32_t(begin);c.r29=int32_t(0x807ff000);c.f_odd=&c.f0.u32h;route_wide=wide;route_adapt=adapt;func_801ADC7C_overlay_2c99e0_801ad820(r.data(),&c);assert(uint32_t(c.r2)==word(r,0x801b77c0));return r;};
  auto parentOriginal=caller(false,false),parentFour=caller(true,false),parentWide=caller(true,true);assert(parentFour==parentOriginal&&word(parentWide,0x801b77c0)==word(parentOriginal,0x801b77c0)+104);
  auto original=emit(source,profile,alpha),four=original;const auto oldEnd=word(original,0x801b77c0);auto originalGlobal=word(original,0x8009e0c8);
  assert(!extend_pal_intro_canvas(four,false,profile.desc,profile.palette,profile.segments,alpha,begin)&&four==original);
  auto r=original;assert(extend_pal_intro_canvas(r,true,profile.desc,profile.palette,profile.segments,alpha,begin));const auto end=word(r,0x801b77c0);assert(end==oldEnd+104&&word(r,0x8009e0c8)==originalGlobal);
  for(auto p=begin;p<oldEnd;p+=4)assert(word(r,p)==word(original,p));
  assert(word(r,begin)==0xde000000&&word(r,begin+4)==0x801b7710&&word(r,begin+8)==0xfa000000&&word(r,begin+12)==(0xffffff00|alpha));
  unsigned rectangles=0;for(auto p=begin;p<oldEnd;p+=8)if(word(r,p)>>24==0xe4){++rectangles;assert(word(r,p+8)==0xe1000000&&word(r,p+16)==0xf1000000&&word(r,p+20)==0x04000400);p+=16;}assert(rectangles==profile.rectangles);
  GfxCommand expected[13]{};auto c=expected;gEXEnable(c++);gEXPushScissor(c++);gEXSetScissor(c++,0,G_EX_ORIGIN_LEFT,G_EX_ORIGIN_RIGHT,0,0,0,240);gEXSetRectAspect(c++,G_EX_ASPECT_ADJUST);
  gEXTextureRectangle(c++,G_EX_ORIGIN_LEFT,G_EX_ORIGIN_NONE,-4,0,0,960,0,profile.texels>>16,profile.texels&65535,0,0);
  gEXTextureRectangle(c++,G_EX_ORIGIN_NONE,G_EX_ORIGIN_RIGHT,1280,0,4,960,0,profile.texels>>16,profile.texels&65535,0,0);
  gEXSetRectAspect(c++,G_EX_ASPECT_AUTO);gEXPopScissor(c++);
  for(unsigned i=0;i<13;++i){assert(word(r,oldEnd+8*i)==expected[i].values.word0&&word(r,oldEnd+8*i+4)==expected[i].values.word1);}
  auto preserved=r;memcpy(preserved.data()+(oldEnd&0x7fffff),original.data()+(oldEnd&0x7fffff),104);put(preserved,0x801b77c0,oldEnd);assert(preserved==original);
  auto again=r;assert(!extend_pal_intro_canvas(again,true,profile.desc,profile.palette,profile.segments,alpha,begin)&&again==r);
  for(auto [a,v]:{std::pair{begin,0xde000001u},std::pair{oldEnd-4,0x10000400u},std::pair{0x8009e02cu,0x8013b400u},std::pair{0x800a4aa4u,0x800e0300u}}){auto other=original;put(other,a,v);auto before=other;assert(!extend_pal_intro_canvas(other,true,profile.desc,profile.palette,profile.segments,alpha,begin)&&other==before);}
  for(auto a:{profile.desc+11,profile.palette+511,profile.segments+profile.rectangles*12-1,0x801add44u+815,0x801b7710u+143,(profile.desc==0x801b7608?0x801b27c8u:profile.desc==0x801b7680?0x801b6448u:0x801b6c48u)}){auto other=original;byte(other,a,other[(a&0x7fffff)^3]^255);auto before=other;assert(!extend_pal_intro_canvas(other,true,profile.desc,profile.palette,profile.segments,alpha,begin)&&other==before);}
  for(auto params:{std::array<uint64_t,5>{profile.desc+4,profile.palette,profile.segments,alpha,begin},{profile.desc,profile.palette+4,profile.segments,alpha,begin},{profile.desc,profile.palette,profile.segments+4,alpha,begin},{profile.desc,profile.palette,profile.segments,256,begin},{profile.desc,profile.palette,profile.segments,alpha,0x12345678800d0328ULL}}){auto other=original;assert(!extend_pal_intro_canvas(other,true,params[0],params[1],params[2],params[3],params[4])&&other==original);}
  auto space=original;put(space,0x801b77c0,bounds.end-96);auto before=space;assert(!extend_pal_intro_canvas(space,true,profile.desc,profile.palette,profile.segments,alpha,begin)&&space==before);
 }
}
'''
@unittest.skipUnless(shutil.which('c++') and (RT64/'include/rt64_extended_gbi.h').is_file(),'C++ compiler and pinnedRT64 required')
class BackgroundIntroCanvasTests(unittest.TestCase):
 def test_original_direct_ci8_logos_extend_only_white_sides_and_preserve_fades(self):
  generated=ROOT/'.local/pal-map-bound-01/functions';header=ROOT/'.local/deps/N64Recomp/include';original=generated/'func_801ADD44_overlay_2c99e0_801ad820.c';caller=generated/'func_801ADC7C_overlay_2c99e0_801ad820.c';snapshot=ROOT/'.local/pal-acceptance/mainmenu09.rdram';rom_path=ROOT/'.local/inputs/pal-en-de/rom.z64'
  if not all(p.is_file()for p in [original,caller,header/'recomp.h',snapshot,rom_path]):self.skipTest('PrivatePAL source andfixture required')
  with tempfile.TemporaryDirectory()as d:
   native=(ROOT/'src/runtime/native_game.cpp').read_text();wrapper=re.search(r'void draw_widescreen_intro_canvas\(.*?\n\}',native,re.S).group()
   self.assertRegex(native,r'if\(uint32_t\(address\)==0x801ADD44u && iss2000::registry.find\(uint32_t\(address\)\)==&func_801ADD44_overlay_2c99e0_801ad820\)\s*return &iss2000::draw_widescreen_intro_canvas;')
   p=Path(d);(p/'intro.cpp').write_text(INTRO_CODE.replace('ACTUAL_INTRO_WRAPPER',wrapper))
   built=subprocess.run(['cc','-O2','-I'+str(header),'-c',str(original),'-o',str(p/'original.o')],capture_output=True,text=True);self.assertEqual(built.returncode,0,built.stderr)
   built=subprocess.run(['cc','-O2','-I'+str(header),'-c',str(caller),'-o',str(p/'caller.o')],capture_output=True,text=True);self.assertEqual(built.returncode,0,built.stderr)
   miniz=ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz';miniz_build=ROOT/'.local/runtime-deps-build/librecomp/miniz'
   built=subprocess.run(['c++','-std=c++20','-O2','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-I'+str(ROOT/'src'),'-I'+str(header),'-I'+str(RT64/'include'),'-I'+str(miniz),'-I'+str(miniz_build),str(p/'intro.cpp'),str(ROOT/'src/runtime/menu_sprite_runtime.cpp'),str(ROOT/'src/runtime/pal_radar_interpolation.cpp'),str(ROOT/'src/runtime/graphics_task_bank.cpp'),str(ROOT/'src/runtime/pal_background_widescreen.cpp'),str(ROOT/'src/runtime/pal_sky_widescreen.cpp'),str(ROOT/'src/runtime/rom_image.cpp'),str(p/'original.o'),str(p/'caller.o'),'-o',str(p/'intro')],capture_output=True,text=True);self.assertEqual(built.returncode,0,built.stderr)
   rom=rom_path.read_bytes();self.assertEqual(hashlib.sha256(rom).hexdigest(),'6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf')
   base=bytearray(snapshot.read_bytes());sections=json.loads((ROOT/'.local/pal-map-bound-01/section-analysis.json').read_text());sections=sections if isinstance(sections,list)else sections['sections'];section=next(s for s in sections if s['rom']==0x2c99e0)
   for i,v in enumerate(rom[section['rom']:section['rom']+section['load_size']]):base[((section['vram']+i)&0x7fffff)^3]=v
   (p/'base.rdram').write_bytes(base);run=subprocess.run([str(p/'intro'),str(p/'base.rdram'),str(p/'original')],capture_output=True,text=True)
   for n,(length,pinned) in enumerate([(4536,'7c20ae859cf6c524f033714de52642e947b8c0c25b10ce708c81372c2bbcbe79'),(2816,'7116090a307b9c026e71787d7e384317f28204a6acdbefd8c058ced65bf4c8b2'),(2040,'caf89248faf39c25452d9994c50b8728b6bd4eebb60904e1eec35ff7adfb6acb')]):
    data=(p/f'original-{n}.bin').read_bytes();self.assertEqual(len(data),length);self.assertEqual(hashlib.sha256(data).hexdigest(),pinned)
   self.assertEqual(run.returncode,0,run.stderr)
