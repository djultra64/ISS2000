"""Original work: djultra64. Actual PAL Career packed prompt CPU snapshots."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
MINIZ=ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz'
MINIZ_BUILD=ROOT/'.local/runtime-deps-build/librecomp/miniz'
@unittest.skipUnless(shutil.which('c++') and (MINIZ_BUILD/'libminiz.a').is_file(),'Compiler and pinned miniz required')
class CareerPackedPromptTests(unittest.TestCase):
 def test_actual_name_direction_strip_preserves_cell_order_and_transaction(self):
  snapshot=ROOT/'.local/pal-acceptance/name10.rdram'
  if not snapshot.is_file():self.skipTest('Private original PAL name editor snapshot required')
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
 auto byte=[&](uint32_t a){return ram[(a&0x7fffff)^3];};
 auto word=[&](uint32_t a){return uint32_t(byte(a))<<24|uint32_t(byte(a+1))<<16|uint32_t(byte(a+2))<<8|byte(a+3);};
 constexpr uint32_t sprite=0x8013c9a4;const auto descriptor=word(sprite+20),texture=word(descriptor+8),palette=word(sprite+52),segments=word(sprite+48);
 std::array<uint8_t,32> colors{};for(unsigned n=0;n<32;++n)colors[n]=byte(palette+n);
 std::array<PromptGlyphRequest,2> ab{};std::array<PromptGlyphRequest,4> c{{{PromptGlyphFamily::Xbox,"R←"},{PromptGlyphFamily::Xbox,"R→"},{PromptGlyphFamily::Xbox,"R↑"},{PromptGlyphFamily::Xbox,"R↓"}}};
 prompt_detail::TextureGuard guard(pal_en_prompt_texture_layout());const auto original=ram;
 auto result=guard.prepare_sprite(ram.data(),sprite,ab,c);check(result.status==PromptSpriteStatus::Applied);
 const unsigned cell_action[]={1,0,2,3};
 for(unsigned cell=0;cell<4;++cell){prompt_detail::PixelBytes ink;for(unsigned y=0;y<16;++y)for(unsigned x=0;x<8;++x)ink[y*8+x]=original[((texture+y*32+cell*8+x)&0x7fffff)^3];auto expected=prompt_detail::glyph_pixels(c[cell_action[cell]],colors,ink);check(bool(expected));for(unsigned y=0;y<16;++y)for(unsigned x=0;x<8;++x)check(byte(texture+y*32+cell*8+x)==(*expected)[y*8+x]);}
 for(size_t n=0;n<ram.size();++n)if(n<(texture&0x7fffff)||n>=(texture&0x7fffff)+512)check(ram[n]==original[n]);
 guard.restore(ram.data());check(ram==original);
 // Name entry has its own single-cell A/B images in bank105; they do not
 // share the Career file/country32x16 strip from bank94.
 ab={{{PromptGlyphFamily::Nintendo,"B"},{PromptGlyphFamily::Nintendo,"A"}}};
 for(unsigned n=0;n<2;++n){
  const uint32_t object=0x8013C92C+n*0x3C,d=word(object+20),t=word(d+8),p=word(object+52);
  for(unsigned j=0;j<32;++j)colors[j]=byte(p+j);
  result=guard.prepare_sprite(ram.data(),object,ab,c);check(result.status==PromptSpriteStatus::Applied);
  prompt_detail::PixelBytes ink;for(unsigned j=0;j<128;++j)ink[j]=original[((t+j)&0x7fffff)^3];const auto expected=prompt_detail::glyph_pixels(ab[n],colors,ink);check(bool(expected));
  for(unsigned j=0;j<128;++j)check(byte(t+j)==(*expected)[j]);
  guard.restore(ram.data());check(ram==original);
  auto saved=ab[n];ab[n]={PromptGlyphFamily::Xbox,"Paddle 2"};
  result=guard.prepare_sprite(ram.data(),object,ab,c);check(result.status==PromptSpriteStatus::TextFallback&&result.line_count==1&&ram==original);
  check(result.lines[0].text=="P2"&&result.lines[0].x==(n?164:108)&&result.lines[0].y==179);ab[n]=saved;
 }
 c[0]={PromptGlyphFamily::Xbox,"Paddle 1"};result=guard.prepare_sprite(ram.data(),sprite,ab,c);
 check(result.status==PromptSpriteStatus::TextFallback&&result.line_count==4&&ram==original);
 const char* expected_text[]={"RR","P1","RD","RU"};const int expected_x[]={46,32,208,128};
 for(unsigned n=0;n<4;++n)check(result.lines[n].text==expected_text[n]&&result.lines[n].x==expected_x[n]&&result.lines[n].y==51);
 // Exact consumer and palette remain mandatory, including on owned data.
 c[0]={PromptGlyphFamily::Xbox,"R←"};check(guard.prepare_sprite(ram.data(),sprite,ab,c).status==PromptSpriteStatus::Applied);
 ram[((segments+7)&0x7fffff)^3]^=1;auto foreign=ram;check(guard.prepare_sprite(ram.data(),sprite,ab,c).status==PromptSpriteStatus::RejectedKnown&&ram==foreign);
 ram=original;ram[((palette+2)&0x7fffff)^3]^=1;foreign=ram;check(guard.prepare_sprite(ram.data(),sprite,ab,c).status==PromptSpriteStatus::RejectedKnown&&ram==foreign);
 return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
'''
  self.run_snapshot(source,snapshot)
 def test_actual_country_shoulders_offer_exact_original_font_transaction(self):
  snapshot=ROOT/'.local/pal-acceptance/country10.rdram'
  if not snapshot.is_file():self.skipTest('Private original PAL country snapshot required')
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
 std::array<PromptGlyphRequest,2> ab{};std::array<PromptGlyphRequest,4> c{};
 std::array<PromptGlyphRequest,3> shoulder{{{PromptGlyphFamily::Xbox,"LB"},{PromptGlyphFamily::Xbox,"LT"},{PromptGlyphFamily::Xbox,"RB"}}};
 constexpr uint32_t sprite=0x8013c878;prompt_detail::TextureGuard guard(pal_en_prompt_texture_layout());const auto original=ram;
 check(guard.prepare_sprite(ram.data(),sprite,ab,c).status==PromptSpriteStatus::Unrelated);
 auto result=guard.prepare_sprite(ram.data(),sprite,ab,c,std::nullopt,shoulder);
 check(result.status==PromptSpriteStatus::TextFallback&&result.action==PromptSpriteAction::Shoulders&&result.line_count==1);
 check(result.lines[0].text=="LB LT RB"&&result.lines[0].x==47&&result.lines[0].y==151&&ram==original);
 // The actual adjacent arrow rectangles are x39/70,y135,16x16.
 // The physical phrase must remain below both, and above A Select at176.
 auto byte=[&](uint32_t p){return ram[(p&0x7fffff)^3];};
 auto half=[&](uint32_t p){return unsigned(byte(p))*256+byte(p+1);};
 for(uint32_t p:{0x80241F8Cu,0x80241F98u}){
  const auto& line=result.lines[0];const int x=half(p+4),y=half(p+6);
  check(line.x+int(line.text.size())*6<=x||line.x>=x+byte(p+1)||line.y+12<=y||line.y>=y+byte(p+2));
 }
 check(result.lines[0].y+12<=176);
 shoulder={{{PromptGlyphFamily::PlayStation,"L1"},{PromptGlyphFamily::Nintendo,"ZL"},{PromptGlyphFamily::Xbox,"Paddle 3"}}};
 result=guard.prepare_sprite(ram.data(),sprite,ab,c,std::nullopt,shoulder);check(result.status==PromptSpriteStatus::TextFallback&&result.lines[0].text=="L1 ZL P3"&&ram==original);
 ram[0x241fa4^3]^=1;const auto foreign=ram;check(guard.prepare_sprite(ram.data(),sprite,ab,c,std::nullopt,shoulder).status==PromptSpriteStatus::RejectedKnown&&ram==foreign);
 ram=original;ram[(0x352800+7)^3]^=1;const auto changed=ram;check(guard.prepare_sprite(ram.data(),sprite,ab,c,std::nullopt,shoulder).status==PromptSpriteStatus::RejectedKnown&&ram==changed);
 return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
'''
  self.run_snapshot(source,snapshot)
 def run_snapshot(self,source,snapshot):
  with tempfile.TemporaryDirectory() as directory:
   folder=Path(directory);path=folder/'probe.cpp';path.write_text(source);exe=folder/'probe'
   result=subprocess.run(['c++','-std=c++20','-O1','-Wall','-Wextra','-Werror','-pthread','-I'+str(ROOT/'src'),'-I'+str(MINIZ),'-I'+str(MINIZ_BUILD),str(path),str(ROOT/'src/runtime/prompt_textures.cpp'),str(ROOT/'src/runtime/rom_image.cpp'),str(MINIZ_BUILD/'libminiz.a'),'-o',str(exe)],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
   result=subprocess.run([str(exe),str(snapshot)],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
