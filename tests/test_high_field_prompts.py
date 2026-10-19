"""Original project work: djultra64. Genuine PAL High field prompt/font chains.

CPU-only original constructors and font calls against private saved RAM. The High
video context comes from an actual High capture; no running game is modified.
"""
from pathlib import Path
import hashlib,json,shutil,struct,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
MINIZ=ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz'
MINIZ_BUILD=ROOT/'.local/runtime-deps-build/librecomp/miniz'
CODE=r'''
#include "runtime/prompt_textures.hpp"
#include "runtime/game_controls_menu.hpp"
#include <cassert>
#include <cstring>
#include <cstdio>
#include <cstdlib>
#include <vector>
DECLS
using namespace iss2000;using Bytes=std::vector<uint8_t>;
extern "C" recomp_func_t* get_function(int32_t a){switch(uint32_t(a)){LOOKUP default:std::abort();}}
extern "C" void do_break(uint32_t){std::abort();}
extern "C" void switch_error(const char*,uint32_t,uint32_t){std::abort();}
uint32_t word(const Bytes&r,uint32_t a){uint32_t v;memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
void put(Bytes&r,uint32_t a,uint32_t v){memcpy(r.data()+(a&0x7fffff),&v,4);}
void byte(Bytes&r,uint32_t a,uint8_t v){r[(a&0x7fffff)^3]=v;}
Bytes load(const char*p){Bytes r(0x800000);FILE*f=fopen(p,"rb");assert(f&&fread(r.data(),1,r.size(),f)==r.size());fclose(f);return r;}
struct Rect {int x0,y0,x1,y1;uint32_t uv,derivatives;};
std::vector<Rect> draw(Bytes ram,const PromptSpriteResult& proposal){
 put(ram,0x800A4AA4,0x800D0320);put(ram,0x8009E0C8,0x800D0328);
 recomp_context c{};c.r29=int32_t(0x800A4000);c.f_odd=&c.f0.u32h;const auto before=c;
 std::array<EngineTextLine,4>lines;for(unsigned n=0;n<proposal.line_count;++n){const auto&l=proposal.lines[n];lines[n]={l.x,l.y,l.text,l.height,l.palette};}
 assert(draw_pal_engine_text(ram,c,{lines.data(),proposal.line_count},&func_80048660_resident));assert(memcmp(&before,&c,sizeof(c))==0);
 std::vector<Rect>rects;const auto end=word(ram,0x8009E0C8);
 for(uint32_t a=0x800D0328;a<end;a+=8){const auto x=word(ram,a),y=word(ram,a+4);if((x>>24)==0xe4){assert(word(ram,a+8)==0xe1000000&&word(ram,a+16)==0xf1000000);rects.push_back({int(y>>12&4095),int(y&4095),int(x>>12&4095),int(x&4095),word(ram,a+12),word(ram,a+20)});a+=16;}}
 assert(!rects.empty());return rects;
}
void construct(Bytes&r,bool pause){recomp_context c{};c.r29=int32_t(0x800A4000);c.f_odd=&c.f0.u32h;
 if(pause){c.r4=0x159;c.r5=0x223;c.r6=0x221;func_801DF89C_overlay_287ab0_801db100(r.data(),&c);}
 else func_801DFB8C_overlay_287ab0_801db100(r.data(),&c);
}
int main(int argc,char**argv){assert(argc==4);const auto video=load(argv[3]);
 for(unsigned pause=0;pause<2;++pause){const auto saved=load(argv[1+pause]);const uint32_t object=pause?0x8013d8e0:0x8013cf08,action=pause?0x8013d958:0x8013d160;
  auto low=saved,high=saved;
  for(auto a:{0x13b428u,0x13b42cu,0x13b430u})memcpy(high.data()+a,video.data()+a,4);
  memcpy(high.data()+0x7aa008,video.data()+0x7aa008,0x2b4);
  construct(low,pause);construct(high,pause);
  assert(word(low,object+20)==word(high,object+20)&&word(low,object+48)==word(high,object+48));
  assert(word(high,object+20)==(pause?0x80259f9cu:0x80259fa8u));assert(word(high,object+48)==(pause?0x8025ea00u:0x8025fc90u));
  assert(high[(object&0x7fffff)+4^3]==1&&high[(object&0x7fffff)+5^3]==(pause?9:11));
  std::array<PromptGlyphRequest,2>ab{};std::array<PromptGlyphRequest,4>directions{};
  prompt_detail::TextureGuard guard(pal_en_prompt_texture_layout());
  auto proposal=[&](Bytes&r,PromptGlyphFamily family,std::string_view start,unsigned port){
   std::array<PromptGlyphRequest,3>shoulders{{{family,"L1",port},{family,"LT",port},{family,"RB",port}}};
   return guard.prepare_sprite(r.data(),object,ab,directions,PromptGlyphRequest{family,start,port},shoulders);
  };
  for(const auto& family:{std::pair{PromptGlyphFamily::Xbox,"Menu"},std::pair{PromptGlyphFamily::PlayStation,"Options"},std::pair{PromptGlyphFamily::Nintendo,"+"},std::pair{PromptGlyphFamily::Keyboard,"Return"}}){
   const auto beforeLow=low,beforeHigh=high;const auto a=proposal(low,family.first,family.second,0),b=proposal(high,family.first,family.second,0);
   assert(a.status==PromptSpriteStatus::TextFallback&&b.status==PromptSpriteStatus::TextFallback&&a.line_count==b.line_count&&a.action==b.action&&low==beforeLow&&high==beforeHigh);
   for(unsigned n=0;n<a.line_count;++n)assert(a.lines[n].x==b.lines[n].x&&a.lines[n].y==b.lines[n].y&&a.lines[n].text==b.lines[n].text&&a.lines[n].height==b.lines[n].height);
   auto lr=draw(low,a),hr=draw(high,b);assert(lr.size()==hr.size());
   for(unsigned n=0;n<lr.size();++n){const auto&l=lr[n];const auto&h=hr[n];assert(h.x0==2*l.x0&&h.x1==2*l.x1&&h.y0==2*l.y0&&h.y1==2*l.y1&&h.uv==l.uv);assert((h.derivatives>>16)==((l.derivatives>>16)/2)&&(h.derivatives&65535)==((l.derivatives&65535)/2));}
  }
  for(unsigned port=0;port<4;++port){auto r=high;if(pause)byte(r,0x8012de37,port+1);
   assert(guard.sprite_port(r.data(),object,port)==port);
   assert(proposal(r,PromptGlyphFamily::Xbox,"Menu",port).status==PromptSpriteStatus::TextFallback);
   assert(!guard.sprite_port(r.data(),action,port));
   if(pause)assert(proposal(r,PromptGlyphFamily::Xbox,"Menu",(port+1)%4).status==PromptSpriteStatus::RejectedKnown);
  }
  // All hashes, owner scene/layer/object, working video fields and both genuine
  // High emitters must agree. A mode-bit-only bypass fails these cases.
  for(unsigned change=0;change<11;++change){auto r=high;
   if(change==0)put(r,0x8013b42c,0x028001e0);
   if(change==1)put(r,0x8013b430,0x802e2000);
   if(change==2)put(r,0x807aa008,0);
   if(change==3)put(r,0x80049158,0);
   if(change==4)byte(r,0x8013b44c,7);
   if(change==5)byte(r,0x8013b452,pause?0:1);
   if(change==6)byte(r,object+5,8);
   if(change==7)byte(r,0x8013b42a,2);
   if(change==8){const auto a=word(r,word(r,object+20)+8);byte(r,a,r[(a&0x7fffff)^3]^1);}
   if(change==9)byte(r,pause?0x8025ea00:0x8025fc90,0);
   if(change==10)put(r,0x8009e02c,0x8013b410);
   const auto before=r;if(guard.sprite_port(r.data(),object,0))fprintf(stderr,"variant %u pause %u unexpectedly owned\n",change,pause);assert(!guard.sprite_port(r.data(),object,0));assert(proposal(r,PromptGlyphFamily::Xbox,"Menu",0).status==PromptSpriteStatus::RejectedKnown&&r==before);
  }
  std::array<PromptGlyphRequest,3>shoulders{};
  auto unrelated=guard.prepare_sprite(high.data(),action,ab,directions,PromptGlyphRequest{PromptGlyphFamily::Xbox,"Menu",0},shoulders);assert(unrelated.status==PromptSpriteStatus::Unrelated);
 }
}
'''

@unittest.skipUnless(shutil.which('c++') and (MINIZ_BUILD/'libminiz.a').is_file(),'Compiler and pinned native miniz required')
class HighFieldPromptTests(unittest.TestCase):
 def test_original_constructors_font_scaled_geometry_physical_ports_and_strict_high_guards(self):
  generated=ROOT/'.local/pal-map-bound-01/functions';analysis=ROOT/'.local/pal-map-bound-01/section-analysis.json';rom=ROOT/'.local/inputs/pal-en-de/rom.z64';header=ROOT/'.local/deps/N64Recomp/include'
  snapshots=[ROOT/'.local/hidden-test-01/field16-tooltip-completed.rdram',ROOT/'.local/hidden-test-01/field16-pause-controls-completed.rdram',ROOT/'.local/training-timing-01/free-training-high.rdram']
  if not all(p.is_file()for p in [analysis,rom,header/'recomp.h',*snapshots]):self.skipTest('Private actual PAL Low field/pause and High video fixtures required')
  image=rom.read_bytes();self.assertEqual(hashlib.sha256(image).hexdigest(),'6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf')
  sections=json.loads(analysis.read_text());functions={f['vram']:(s,f)for s in sections for f in s['functions']};pending=[0x80048660,0x801DFB8C,0x801DF89C,*getattr(self,"extra_entries",[])];seen=set()
  while pending:
   pc=pending.pop()
   if pc in seen:continue
   seen.add(pc);section,f=functions[pc];offset=section['rom']+pc-section['vram']
   for op in struct.unpack_from('>'+str(f['size']//4)+'I',image,offset):
    if op>>26==3:pending.append(0x80000000|((op&0x3ffffff)<<2))
  paths={pc:next(generated.glob(f'func_{pc:08X}_*.c'))for pc in seen}
  code=CODE.replace('DECLS','\n'.join(f'extern "C" void {p.stem}(uint8_t*,recomp_context*);'for pc,p in sorted(paths.items()))).replace('LOOKUP','\n'.join(f'case 0x{pc:08X}:return {p.stem};'for pc,p in sorted(paths.items())))
  with tempfile.TemporaryDirectory()as temp:
   p=Path(temp);(p/'original.c').write_text('\n'.join('#include '+json.dumps(str(path))for pc,path in sorted(paths.items())));(p/'test.cpp').write_text(code)
   built=subprocess.run(['cc','-O1','-fno-strict-aliasing','-I'+str(header),'-c',str(p/'original.c'),'-o',str(p/'original.o')],capture_output=True,text=True);self.assertEqual(built.returncode,0,built.stderr)
   includes=['src','.local/deps/N64Recomp/include','.local/deps/N64ModernRuntime/librecomp/include','.local/deps/N64ModernRuntime/ultramodern/include','.local/deps/N64ModernRuntime/thirdparty','.local/deps/N64ModernRuntime/thirdparty/concurrentqueue']
   command=['c++','-std=c++20','-O1','-pthread',*['-I'+str(ROOT/i)for i in includes],'-I/home/linuxbrew/.linuxbrew/include/SDL2','-I'+str(MINIZ),'-I'+str(MINIZ_BUILD),str(p/'test.cpp'),str(p/'original.o'),str(ROOT/'src/runtime/prompt_textures.cpp'),str(ROOT/'src/runtime/game_controls_menu.cpp'),str(ROOT/'src/runtime/rom_image.cpp'),str(MINIZ_BUILD/'libminiz.a'),'-o',str(p/'test')]
   built=subprocess.run(command,capture_output=True,text=True);self.assertEqual(built.returncode,0,built.stderr)
   ran=subprocess.run([str(p/'test'),*[str(x)for x in snapshots]],capture_output=True,text=True,timeout=15);self.assertEqual(ran.returncode,0,ran.stderr)

if __name__=='__main__':unittest.main()
