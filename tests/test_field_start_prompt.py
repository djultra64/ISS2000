"""Original work: djultra64. Exact PAL on-field Start label transaction."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
MINIZ=ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz'
MINIZ_BUILD=ROOT/'.local/runtime-deps-build/librecomp/miniz'
@unittest.skipUnless(shutil.which('c++') and (MINIZ_BUILD/'libminiz.a').is_file(),'Compiler and pinned miniz required')
class FieldStartPromptTests(unittest.TestCase):
 def test_actual_start_hint_preserves_action_and_fails_closed_for_foreign_source(self):
  snapshot=ROOT/'.local/hidden-test-01/field16-tooltip-completed.rdram'
  if not snapshot.is_file():self.skipTest('Private completed PAL field tooltip snapshot required')
  source=r'''
#include "runtime/prompt_textures.hpp"
#include <fstream>
#include <iostream>
#include <source_location>
#include <stdexcept>
#include <vector>
using namespace iss2000;
void check(bool b,const std::source_location p=std::source_location::current()){if(!b)throw std::runtime_error("line "+std::to_string(p.line()));}
template<class Guard> std::optional<unsigned> active_owner(Guard& g,const uint8_t* ram,uint64_t sprite,unsigned port){
 if constexpr(requires {g.sprite_port(ram,sprite,std::optional<unsigned>{port});})return g.sprite_port(ram,sprite,std::optional<unsigned>{port});
 else return {};
}
int main(int argc,char**argv){try{
 check(argc==2);std::vector<uint8_t> ram(0x800000);std::ifstream f(argv[1],std::ios::binary);f.read(reinterpret_cast<char*>(ram.data()),ram.size());check(bool(f));
 auto byte=[&](uint32_t p){return ram[(p&0x7fffff)^3];};
 auto word=[&](uint32_t p){return uint32_t(byte(p))<<24|uint32_t(byte(p+1))<<16|uint32_t(byte(p+2))<<8|byte(p+3);};
 auto put=[&](uint32_t p,uint32_t v){for(unsigned n=0;n<4;++n)ram[((p+n)&0x7fffff)^3]=uint8_t(v>>(24-8*n));};
 const auto original=ram;constexpr uint32_t sprite=0x8013cf08,action=0x8013d160;
 const auto descriptor=word(sprite+20),texture=word(descriptor+8);
 std::array<PromptGlyphRequest,2> ab{};std::array<PromptGlyphRequest,4> c{};
 prompt_detail::TextureGuard guard(pal_en_prompt_texture_layout());
 check(guard.prepare_sprite(ram.data(),sprite,ab,c).status==PromptSpriteStatus::Unrelated);
 check(!guard.sprite_port(ram.data(),sprite));
 for(unsigned port=0;port<4;++port){check(active_owner(guard,ram.data(),sprite,port)==port);check(!active_owner(guard,ram.data(),action,port));}
 check(!active_owner(guard,ram.data(),sprite,4));
 check(!physical_prompt_sprite_port(ram.data(),sprite,2));
 configure_prompt_textures(pal_en_prompt_texture_layout());
 for(unsigned port=0;port<4;++port){
  check(physical_prompt_sprite_port(ram.data(),sprite,port)==port);
  check(guard.prepare_sprite(ram.data(),sprite,ab,c,PromptGlyphRequest{PromptGlyphFamily::Xbox,"Menu",port}).status==PromptSpriteStatus::TextFallback);
 }
 check(!physical_prompt_sprite_port(ram.data(),action,2));
 check(guard.prepare_sprite(ram.data(),sprite,ab,c,PromptGlyphRequest{PromptGlyphFamily::Xbox,"Menu",4}).status==PromptSpriteStatus::RejectedKnown);
 struct Example{PromptGlyphRequest request;const char* text;};
 const Example examples[]={{{PromptGlyphFamily::Xbox,"Menu"},"Menu"},{{PromptGlyphFamily::PlayStation,"Options"},"Options"},{{PromptGlyphFamily::Nintendo,"+"},"Plus"},{{PromptGlyphFamily::Keyboard,"Return"},"Return"},{{PromptGlyphFamily::Xbox,"Paddle 1"},"Paddle 1"}};
 for(auto e:examples){auto r=guard.prepare_sprite(ram.data(),sprite,ab,c,e.request);
  check(r.status==PromptSpriteStatus::TextFallback&&r.line_count==1&&r.lines[0].text==e.text&&ram==original);
  const int width=int(r.lines[0].text.size())*6;check(r.lines[0].x>=116&&r.lines[0].x+width<=164&&r.lines[0].y==17&&r.lines[0].y+12<=31);
  // GameControls source remains an unrelated original draw at x172,y19.
  check(guard.prepare_sprite(ram.data(),action,ab,c,e.request).status==PromptSpriteStatus::Unrelated&&ram==original);
 }
 for(unsigned variant=0;variant<7;++variant){ram=original;
  if(variant==0)ram[(texture&0x7fffff)^3]^=1;
  if(variant==1)ram[0x25fc90^3]^=1;
  if(variant==2)ram[0x352800^3]^=1;
  if(variant==3)put(sprite+32,0x00010000);
  if(variant==4){put(sprite+8,word(sprite+8)|(1u<<22));put(sprite+40,0x40000000);}
  if(variant==5)ram[((word(0x9e02c)&0x7fffff)+18)^3]=1;
  if(variant==6)put(descriptor+4,0x010f0000);
  const auto foreign=ram;check(!active_owner(guard,ram.data(),sprite,2));auto r=guard.prepare_sprite(ram.data(),sprite,ab,c,examples[0].request);if(r.status!=PromptSpriteStatus::RejectedKnown)std::cerr<<"variant "<<variant<<" status "<<unsigned(r.status)<<"\n";check(r.status==PromptSpriteStatus::RejectedKnown&&ram==foreign);
 }
 ram=original;put(sprite+52,0xffffffff);const auto unused=ram;check(guard.prepare_sprite(ram.data(),sprite,ab,c,examples[0].request).status==PromptSpriteStatus::TextFallback&&ram==unused);
 ram=original;check(guard.prepare_sprite(ram.data(),sprite,ab,c,PromptGlyphRequest{PromptGlyphFamily::Xbox,"Unsupported"}).status==PromptSpriteStatus::RejectedKnown&&ram==original);
 return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
'''
  with tempfile.TemporaryDirectory() as d:
   folder=Path(d);path=folder/'probe.cpp';path.write_text(source);exe=folder/'probe'
   built=subprocess.run(['c++','-std=c++20','-O1','-Wall','-Wextra','-Werror','-pthread','-I'+str(ROOT/'src'),'-I'+str(MINIZ),'-I'+str(MINIZ_BUILD),str(path),str(ROOT/'src/runtime/prompt_textures.cpp'),str(ROOT/'src/runtime/rom_image.cpp'),str(MINIZ_BUILD/'libminiz.a'),'-o',str(exe)],capture_output=True,text=True)
   self.assertEqual(built.returncode,0,built.stderr)
   run=subprocess.run([str(exe),str(snapshot)],capture_output=True,text=True);self.assertEqual(run.returncode,0,run.stderr)
