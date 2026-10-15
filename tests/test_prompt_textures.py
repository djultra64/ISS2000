"""Synthetic bounds/reload tests for two original UI prompt texture overrides."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
MINIZ=ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz'
MINIZ_BUILD=ROOT/'.local/runtime-deps-build/librecomp/miniz'
@unittest.skipUnless(shutil.which('c++') and (MINIZ/'miniz.h').is_file() and (MINIZ_BUILD/'libminiz.a').is_file(),'Pinned miniz build and C++ compiler required for shared SHA256 implementation')
class PromptTextureTests(unittest.TestCase):
 def test_guarded_ui_pixels_reload_restore_and_glyphs(self):
  with tempfile.TemporaryDirectory(prefix='iss2000-prompt-textures-') as directory:
   folder=Path(directory);source=folder/'probe.cpp'
   source.write_text(r'''
#include "runtime/prompt_textures.hpp"
#include "runtime/rom_image.hpp"
#include <algorithm>
#include <iostream>
#include <stdexcept>
#include <source_location>
#include <vector>
using namespace iss2000;
using namespace iss2000::prompt_detail;
void check(bool b,const std::source_location where=std::source_location::current()){if(!b)throw std::runtime_error("Prompt texture contract failed at line "+std::to_string(where.line()));}
int main(){try{
 std::vector<uint8_t> ram(0x800000);auto* mem=ram.data();
 auto byte=[&](uint32_t a,uint8_t v){mem[(a&0x7fffff)^3]=v;};
 auto word=[&](uint32_t a,uint32_t v){for(int n=0;n<4;++n)byte(a+n,uint8_t(v>>(24-n*8)));};
 auto put=[&](uint32_t a,auto bytes){for(size_t n=0;n<bytes.size();++n)byte(a+uint32_t(n),bytes[n]);};
 auto get=[&](uint32_t a,size_t count){std::vector<uint8_t> result(count);for(size_t n=0;n<count;++n)result[n]=mem[((a+uint32_t(n))&0x7fffff)^3];return result;};
 constexpr uint32_t bank=0x80300000,sprite=0x80100000,tex=0x80200000,pal=0x80210000;
 PixelBytes original{};for(size_t n=0;n<original.size();++n)original[n]=uint8_t(n*3);
 std::array<uint8_t,32> palette{};for(unsigned n=1;n<16;++n){const unsigned c=n*2;const uint16_t rgba=(c<<11)|(c<<6)|(c<<1)|1;palette[n*2]=rgba>>8;palette[n*2+1]=rgba;}
 ExpectedHashes hashes{};for(auto& h:hashes){h.texture=rom_detail::sha256_hex(original);h.palette=rom_detail::sha256_hex(palette);}
 auto profile=us_prompt_texture_layout();profile.expected=hashes;TextureGuard guard(profile);std::array<PromptGlyphRequest,2> labels{{{PromptGlyphFamily::Keyboard,"Z"},{PromptGlyphFamily::Keyboard,"X"}}};
 word(0x80079650,bank);word(sprite+0x14,bank+5*12);word(sprite+0x34,pal);
 for(unsigned slot=0;slot<2;++slot){auto d=bank+(5+slot)*12;word(d,0x00100010);word(d+4,0x01060000+slot*0x10000);word(d+8,tex+slot*128);put(tex+slot*128,original);}
 put(pal,palette);auto before=ram;
 check(!prepare_prompt_textures(mem,sprite,labels));restore_prompt_textures(mem);check(ram==before);
 check(guard.prepare(mem,sprite,labels));check(ram!=before);
 auto expected=glyph_pixels(labels[0],palette);check(expected.has_value());check(get(tex,128)==std::vector<uint8_t>(expected->begin(),expected->end()));
 // Only the one selected icon changes. Its palette, other icon and all other RAM remain exact.
 for(size_t n=0;n<ram.size();++n)if(n<0x200000||n>=0x200080)check(ram[n]==before[n]);
 auto patched=ram;check(guard.prepare(mem,sprite,labels));check(ram==patched);
 labels[0]={PromptGlyphFamily::Xbox,"B"};check(guard.prepare(mem,sprite,labels));check(get(tex,128)!=std::vector<uint8_t>(expected->begin(),expected->end()));
 guard.restore(mem);check(ram==before);
 // A real reload of original pixels is recognized afresh, even after prior application.
 check(guard.prepare(mem,sprite,labels));put(tex,original);check(guard.prepare(mem,sprite,labels));guard.restore(mem);check(ram==before);
 // Foreign replacement must never be treated as our old image or overwritten on restore.
 check(guard.prepare(mem,sprite,labels));byte(tex,0x99);auto foreign=ram;check(!guard.prepare(mem,sprite,labels));guard.restore(mem);check(ram==foreign);
 put(tex,original);word(sprite+0x14,bank+6*12);check(guard.prepare(mem,sprite,labels));guard.restore(mem);check(get(tex+128,128)==std::vector<uint8_t>(original.begin(),original.end()));
 // Out-of-bounds, spoofed upper bits, bad dimensions and changed palettes are read-only failures.
 auto stable=ram;check(!guard.prepare(mem,0x807ffff0,labels));check(!guard.prepare(mem,0x180100000ull,labels));check(ram==stable);
 word(bank+6*12,0x00200010);stable=ram;check(!guard.prepare(mem,sprite,labels));check(ram==stable);
 word(bank+6*12,0x00100010);byte(pal,123);stable=ram;check(!guard.prepare(mem,sprite,labels));check(ram==stable);
 // Family-specific source tiles and aliases preserve genuine artwork.
 auto keyboardZ=glyph_pixels({PromptGlyphFamily::Keyboard,"Z"},palette);
 auto keyboardX=glyph_pixels({PromptGlyphFamily::Keyboard,"X"},palette);
 auto xboxA=glyph_pixels({PromptGlyphFamily::Xbox,"A"},palette);
 auto switchA=glyph_pixels({PromptGlyphFamily::Nintendo,"A"},palette);
 check(keyboardZ&&keyboardX&&xboxA&&switchA&&keyboardZ!=keyboardX&&xboxA!=switchA);
 for(auto pair:{std::pair{"×","Cross"},std::pair{"○","Circle"},std::pair{"□","Square"},std::pair{"△","Triangle"}})
  check(glyph_pixels({PromptGlyphFamily::PlayStation,pair.first},palette)==glyph_pixels({PromptGlyphFamily::PlayStation,pair.second},palette));
 check(!glyph_pixels({PromptGlyphFamily::Xbox,"Unbound"},palette));
 // Unsupported artwork restores only a texture that this guard still owns.
 put(pal,palette);word(sprite+0x14,bank+5*12);auto unavailable=labels;unavailable[0]={PromptGlyphFamily::Xbox,"Paddle 1"};
 check(guard.prepare(mem,sprite,labels));check(!guard.prepare(mem,sprite,unavailable));check(ram==before);
 // PAL selects its own pointer table, while retaining verified descriptor/hash guards.
 auto palProfile=pal_en_prompt_texture_layout();palProfile.expected=hashes;
 TextureGuard palGuard(palProfile);palProfile.bank_pointer=0x79650; // observer owns a const copy
 word(0x80079650,0);word(0x80076B30,bank);word(sprite+0x14,bank+5*12);
 word(bank+5*12,0x00100010);put(tex,original);put(pal,palette);
 labels={{{PromptGlyphFamily::Nintendo,"B"},{PromptGlyphFamily::Nintendo,"A"}}};auto palBefore=ram;
 check(palGuard.prepare(mem,sprite,labels));
 auto physicalB=glyph_pixels(labels[0],palette);check(get(tex,128)==std::vector<uint8_t>(physicalB->begin(),physicalB->end()));
 palGuard.restore(mem);check(ram==palBefore);
 // Bad PAL hash preserves every byte, including pixels cached from another revision.
 auto badProfile=pal_en_prompt_texture_layout();badProfile.expected=hashes;badProfile.expected[0].texture=std::string(64,'0');
 TextureGuard badGuard(badProfile);check(!badGuard.prepare(mem,sprite,labels));check(ram==palBefore);
 auto configured=pal_en_prompt_texture_layout();configured.expected=hashes;configure_prompt_textures(configured);
 check(prepare_prompt_textures(mem,sprite,labels));restore_prompt_textures(mem);check(ram==palBefore);

 return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
''')
   executable=folder/'probe'
   result=subprocess.run(['c++','-std=c++20','-O1','-Wall','-Wextra','-Werror','-pthread','-I',str(ROOT/'src'),'-I',str(MINIZ),'-I',str(MINIZ_BUILD),str(source),str(ROOT/'src/runtime/prompt_textures.cpp'),str(ROOT/'src/runtime/rom_image.cpp'),str(MINIZ_BUILD/'libminiz.a'),'-o',str(executable)],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
   result=subprocess.run([str(executable)],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
