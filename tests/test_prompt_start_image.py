"""Original work: djultra64. Guarded original-font Start-for-random proposals."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
MINIZ=ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz'
MINIZ_BUILD=ROOT/'.local/runtime-deps-build/librecomp/miniz'
@unittest.skipUnless(shutil.which('c++') and (MINIZ_BUILD/'libminiz.a').is_file(),'Compiler and pinned miniz required')
class PromptStartImageTests(unittest.TestCase):
 def test_exact_start_image_and_consumer_offer_only_bounded_physical_font_text(self):
  with tempfile.TemporaryDirectory() as directory:
   folder=Path(directory);source=folder/'main.cpp';source.write_text(r'''
#include "runtime/prompt_textures.hpp"
#include "runtime/rom_image.hpp"
#include <iostream>
#include <source_location>
#include <stdexcept>
#include <vector>
using namespace iss2000;
void check(bool b,const std::source_location p=std::source_location::current()){if(!b)throw std::runtime_error("line "+std::to_string(p.line()));}
int main(){try{
 std::vector<uint8_t> ram(0x800000);auto*m=ram.data();
 auto byte=[&](uint32_t a,uint8_t v){m[(a&0x7fffff)^3]=v;};
 auto half=[&](uint32_t a,uint16_t v){byte(a,v>>8);byte(a+1,v);};
 auto word=[&](uint32_t a,uint32_t v){half(a,v>>16);half(a+2,v);};
 auto put=[&](uint32_t a,auto const& bytes){for(size_t n=0;n<bytes.size();++n)byte(a+n,bytes[n]);};
 auto get=[&](uint32_t a,size_t size){std::vector<uint8_t> v(size);for(size_t n=0;n<size;++n)v[n]=m[((a+n)&0x7fffff)^3];return v;};
 constexpr uint32_t bank=0x80300000,sprite=0x80100000,tex=0x80200000,pal=0x80210000,seg=0x80220000,font=0x80230000;
 std::array<uint8_t,768> pixels{};for(unsigned n=0;n<pixels.size();++n)pixels[n]=n*11+19;
 std::array<uint8_t,32> palette{},letters{};letters[1]=0xAA;
 auto profile=pal_en_prompt_texture_layout();check(profile.start_random.has_value());check(!us_prompt_texture_layout().start_random);
 profile.start_random->expected={rom_detail::sha256_hex(pixels),rom_detail::sha256_hex(palette)};
 profile.text_fallback->font_address=font&0x7fffff;profile.text_fallback->font_bytes=letters.size();profile.text_fallback->font_sha256=rom_detail::sha256_hex(letters);
 put(tex,pixels);put(pal,palette);put(font,letters);word(0x80076B30,bank);
 word(bank+12,0x00600010);word(bank+16,0x03030000);word(bank+20,tex);
 word(sprite+0x14,bank+12);word(sprite+0x34,pal);word(sprite+0x30,seg);
 word(0x8009E02C,0x8013B418);half(0x8013B42C,320);half(0x8013B42E,240);
 byte(seg,0x90);byte(seg+1,96);byte(seg+2,16);half(seg+4,177);half(seg+6,213);
 check(rom_detail::sha256_hex(get(seg,12))==profile.start_random->consumer_sha256[0]);
 prompt_detail::TextureGuard guard(profile);std::array<PromptGlyphRequest,2> ab{};std::array<PromptGlyphRequest,4> c{};
 const auto before=ram;
 check(guard.prepare_sprite(m,sprite,ab,c).status==PromptSpriteStatus::Unrelated);check(ram==before);
 struct Case {PromptGlyphFamily family;const char* label;const char* text;};
 for(auto test:{Case{PromptGlyphFamily::Xbox,"Menu","Menu Random"},Case{PromptGlyphFamily::PlayStation,"Options","Options Random"},Case{PromptGlyphFamily::Nintendo,"+","Plus Random"},Case{PromptGlyphFamily::Keyboard,"Return","Enter Random"},Case{PromptGlyphFamily::PlayStation,"×","Cross Random"},Case{PromptGlyphFamily::Xbox,"Paddle 1","Paddle 1 Random"}}){
  auto result=guard.prepare_sprite(m,sprite,ab,c,PromptGlyphRequest{test.family,test.label});
  check(result.status==PromptSpriteStatus::TextFallback&&result.action==PromptSpriteAction::StartRandom&&result.line_count==1);
  check(result.lines[0].x==177&&result.lines[0].y==212&&result.lines[0].text==test.text);check(ram==before);
 }
 auto request=PromptGlyphRequest{PromptGlyphFamily::Xbox,"Menu"};
 auto reject=[&]{auto snapshot=ram;check(guard.prepare_sprite(m,sprite,ab,c,request).status==PromptSpriteStatus::RejectedKnown);check(ram==snapshot);};
 // Original I4 descriptor03030000 does not consume a palette. The normal
 // sprite initializer leaves its unused palette override pointer atFFFFFFFF.
 word(sprite+0x34,0xFFFFFFFF);
 auto unpaletted=guard.prepare_sprite(m,sprite,ab,c,request);
 check(unpaletted.status==PromptSpriteStatus::TextFallback&&unpaletted.lines[0].text=="Menu Random");
 word(sprite+0x34,pal);byte(pal,0xFF);
 check(guard.prepare_sprite(m,sprite,ab,c,request).status==PromptSpriteStatus::TextFallback);put(pal,palette);
 byte(tex+3,0xEE);reject();put(tex,pixels);byte(font+1,0xBB);reject();put(font,letters);
 byte(seg,0x10);reject();byte(seg,0x90);half(seg+8,32);reject();half(seg+8,0);
 half(seg+4,178);reject();half(seg+4,177);byte(0x8013B42A,1);reject();byte(0x8013B42A,0);
 request={PromptGlyphFamily::Xbox,"Definitely not a button"};reject();request={PromptGlyphFamily::Automatic,"Menu"};reject();
 guard.restore(m);check(ram==before);
 // The other two pinned original single-sprite consumers retain exact positions.
 for(auto xy:{std::pair{188,216},std::pair{182,214}}){half(seg+4,xy.first);half(seg+6,xy.second);auto result=guard.prepare_sprite(m,sprite,ab,c,PromptGlyphRequest{PromptGlyphFamily::Keyboard,"Return"});check(result.status==PromptSpriteStatus::TextFallback&&result.lines[0].x==xy.first&&result.lines[0].y==xy.second-1);}
 return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
''')
   executable=folder/'probe';result=subprocess.run(['c++','-std=c++20','-O1','-Wall','-Wextra','-Werror','-pthread','-I'+str(ROOT/'src'),'-I'+str(MINIZ),'-I'+str(MINIZ_BUILD),str(source),str(ROOT/'src/runtime/prompt_textures.cpp'),str(ROOT/'src/runtime/rom_image.cpp'),str(MINIZ_BUILD/'libminiz.a'),'-o',str(executable)],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
   result=subprocess.run([str(executable)],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
