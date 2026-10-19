"""Original work: djultra64. Exact PAL set-play physical prefixes and logical action preservation."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
MINIZ=ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz'
MINIZ_BUILD=ROOT/'.local/runtime-deps-build/librecomp/miniz'
@unittest.skipUnless(shutil.which('c++') and (MINIZ_BUILD/'libminiz.a').is_file(),'Compiler and pinned miniz required')
class FieldPausePromptTests(unittest.TestCase):
 def test_actual_pause_prefixes_preserve_logical_actions_and_fit_original_panel(self):
  snapshot=ROOT/'.local/hidden-test-01/field16-pause-controls-completed.rdram'
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
int main(int argc,char**argv){try{
 check(argc==2);std::vector<uint8_t> ram(0x800000);std::ifstream f(argv[1],std::ios::binary);f.read(reinterpret_cast<char*>(ram.data()),ram.size());check(bool(f));
 auto byte=[&](uint32_t p){return ram[(p&0x7fffff)^3];};
 auto word=[&](uint32_t p){return uint32_t(byte(p))<<24|uint32_t(byte(p+1))<<16|uint32_t(byte(p+2))<<8|byte(p+3);};
 auto put=[&](uint32_t p,uint32_t v){for(unsigned n=0;n<4;++n)ram[((p+n)&0x7fffff)^3]=uint8_t(v>>(24-8*n));};
 const auto original=ram;constexpr uint32_t sprite=0x8013d8e0,action=0x8013d958;
 const auto descriptor=word(sprite+20),texture=word(descriptor+8);
 std::array<PromptGlyphRequest,2> ab{};std::array<PromptGlyphRequest,4> c{};
 std::array<PromptGlyphRequest,3> shoulders{{{PromptGlyphFamily::Xbox,"LB"},{PromptGlyphFamily::Xbox,"LT"},{PromptGlyphFamily::Xbox,"RB"}}};
 prompt_detail::TextureGuard guard(pal_en_prompt_texture_layout());
 check(guard.prepare_sprite(ram.data(),sprite,ab,c).status==PromptSpriteStatus::Unrelated);
 auto r=guard.prepare_sprite(ram.data(),sprite,ab,c,std::nullopt,shoulders);
 check(r.status==PromptSpriteStatus::TextFallback&&r.line_count==4&&ram==original);
 const char* labels[]={"LT","RB","1 2 Pass Button","T Pass Button"};const int xs[]{123,123,74,86};
 for(unsigned n=0;n<4;++n){check(r.lines[n].text==labels[n]&&r.lines[n].x==xs[n]&&r.lines[n].y==191+int(n)*8&&r.lines[n].height==8);const int right=r.lines[n].x+int(r.lines[n].text.size())*6;check(r.lines[n].x>=74&&right<=(n<2?149:164));}
 check(guard.sprite_port(ram.data(),sprite)==0);
 check(!guard.sprite_port(ram.data(),action));
 check(!physical_prompt_sprite_port(ram.data(),sprite));
 configure_prompt_textures(pal_en_prompt_texture_layout());
 check(physical_prompt_sprite_port(ram.data(),sprite)==0);
 for(unsigned port=0;port<4;++port){ram=original;ram[0x12de37^3]=uint8_t(port+1);
  check(guard.sprite_port(ram.data(),sprite)==port&&guard.sprite_port(ram.data(),sprite,3)==port);
  if(port)check(guard.prepare_sprite(ram.data(),sprite,ab,c,std::nullopt,shoulders).status==PromptSpriteStatus::RejectedKnown);
  shoulders[1].port=shoulders[2].port=port;
  const auto before=ram;check(guard.prepare_sprite(ram.data(),sprite,ab,c,std::nullopt,shoulders).status==PromptSpriteStatus::TextFallback&&ram==before);
  shoulders[1].port=shoulders[2].port=0;
 }
 ram=original;
 // Real completed command samples prove panelleft72 and bodybottom226.
 check(word(0x800e2378)==0xe41802c8&&word(0x800e237c)==0x001202a8);
 check(word(0x800e23f8)==0xe4140388&&word(0x800e23fc)==0x00120348);
 // Original action consumers have distinct x153/x167 origins. Keep all bytes.
 check(word(action+48)==0x8025fe1c&&byte(0x8025fe40+5)==153&&byte(0x8025fe34+5)==167);
 check(guard.prepare_sprite(ram.data(),action,ab,c,std::nullopt,shoulders).status==PromptSpriteStatus::Unrelated&&ram==original);
 for(unsigned variant=0;variant<8;++variant){ram=original;
  if(variant==0)ram[(texture&0x7fffff)^3]^=1;
  if(variant==1)ram[0x25ea00^3]^=1;
  if(variant==2)ram[0x352800^3]^=1;
  if(variant==3)put(sprite+32,0x10000);
  if(variant==4){put(sprite+8,word(sprite+8)|(1u<<22));put(sprite+40,0x40000000);}
  if(variant==5)ram[((word(0x9e02c)&0x7fffff)+18)^3]=1;
  if(variant==6)ram[0x12de37^3]=0;
  if(variant==7)ram[0x12de37^3]=5;
  const auto foreign=ram;check(!guard.sprite_port(ram.data(),sprite)&&guard.prepare_sprite(ram.data(),sprite,ab,c,std::nullopt,shoulders).status==PromptSpriteStatus::RejectedKnown&&ram==foreign);
 }
 ram=original;put(sprite+52,0xffffffff);const auto unused=ram;check(guard.prepare_sprite(ram.data(),sprite,ab,c,std::nullopt,shoulders).status==PromptSpriteStatus::TextFallback&&ram==unused);
 ram=original;shoulders[1]={PromptGlyphFamily::Xbox,"Unsupported"};check(guard.prepare_sprite(ram.data(),sprite,ab,c,std::nullopt,shoulders).status==PromptSpriteStatus::RejectedKnown&&ram==original);
 return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
'''
  with tempfile.TemporaryDirectory() as d:
   folder=Path(d);path=folder/'probe.cpp';path.write_text(source);exe=folder/'probe'
   built=subprocess.run(['c++','-std=c++20','-O1','-Wall','-Wextra','-Werror','-pthread','-I'+str(ROOT/'src'),'-I'+str(MINIZ),'-I'+str(MINIZ_BUILD),str(path),str(ROOT/'src/runtime/prompt_textures.cpp'),str(ROOT/'src/runtime/rom_image.cpp'),str(MINIZ_BUILD/'libminiz.a'),'-o',str(exe)],capture_output=True,text=True)
   self.assertEqual(built.returncode,0,built.stderr)
   run=subprocess.run([str(exe),str(snapshot)],capture_output=True,text=True);self.assertEqual(run.returncode,0,run.stderr)
