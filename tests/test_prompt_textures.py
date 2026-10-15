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
#include <vector>
using namespace iss2000;
using namespace iss2000::prompt_detail;
void check(bool b){if(!b)throw std::runtime_error("Prompt texture contract failed");}
int main(){try{
 std::vector<uint8_t> ram(0x800000);auto* mem=ram.data();
 auto byte=[&](uint32_t a,uint8_t v){mem[(a&0x7fffff)^3]=v;};
 auto word=[&](uint32_t a,uint32_t v){for(int n=0;n<4;++n)byte(a+n,uint8_t(v>>(24-n*8)));};
 auto put=[&](uint32_t a,auto bytes){for(size_t n=0;n<bytes.size();++n)byte(a+uint32_t(n),bytes[n]);};
 auto get=[&](uint32_t a,size_t count){std::vector<uint8_t> result(count);for(size_t n=0;n<count;++n)result[n]=mem[((a+uint32_t(n))&0x7fffff)^3];return result;};
 constexpr uint32_t bank=0x80300000,sprite=0x80100000,tex=0x80200000,pal=0x80210000;
 PixelBytes original{};for(size_t n=0;n<original.size();++n)original[n]=uint8_t(n*3);
 std::array<uint8_t,32> palette{};for(size_t n=0;n<palette.size();++n)palette[n]=uint8_t(n*7);
 ExpectedHashes hashes{};for(auto& h:hashes){h.texture=rom_detail::sha256_hex(original);h.palette=rom_detail::sha256_hex(palette);}
 auto profile=us_prompt_texture_layout();profile.expected=hashes;TextureGuard guard(profile);std::array<std::string_view,2> labels{"Z","X"};
 word(0x80079650,bank);word(sprite+0x14,bank+5*12);word(sprite+0x34,pal);
 for(unsigned slot=0;slot<2;++slot){auto d=bank+(5+slot)*12;word(d,0x00100010);word(d+4,0x01060000+slot*0x10000);word(d+8,tex+slot*128);put(tex+slot*128,original);}
 put(pal,palette);auto before=ram;
 check(!prepare_prompt_textures(mem,sprite,labels));restore_prompt_textures(mem);check(ram==before);
 check(guard.prepare(mem,sprite,labels));check(ram!=before);
 auto expected=glyph_pixels("Z");check(expected.has_value());check(get(tex,128)==std::vector<uint8_t>(expected->begin(),expected->end()));
 // Only the one selected icon changes. Its palette, other icon and all other RAM remain exact.
 for(size_t n=0;n<ram.size();++n)if(n<0x200000||n>=0x200080)check(ram[n]==before[n]);
 auto patched=ram;check(guard.prepare(mem,sprite,labels));check(ram==patched);
 labels[0]="B";check(guard.prepare(mem,sprite,labels));check(get(tex,128)!=std::vector<uint8_t>(expected->begin(),expected->end()));
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
 auto z=glyph_pixels("Z"),x=glyph_pixels("X"),a=glyph_pixels("A"),b=glyph_pixels("B");
 check(z&&x&&a&&b&&z!=x&&a!=b);
 check(glyph_pixels("×")==glyph_pixels("Cross"));check(glyph_pixels("○")==glyph_pixels("Circle"));
 check(glyph_pixels("□")==glyph_pixels("Square"));check(glyph_pixels("△")==glyph_pixels("Triangle"));
 check(glyph_pixels("Enter").has_value());check(glyph_pixels("LT").has_value());check(!glyph_pixels("Unbound"));
 for(auto label:{"↑","↓","←","→","dpup","dpdown","dpleft","dpright","dpadup","dpad_down","dpad-left","D-pad right","dpad","leftshoulder","rightshoulder","leftstick","rightstick","back","start","guide","LB","RB","L1","R1","L","R","LS","RS","L3","R3","Menu","Options","+","-","View","Share","Home","PS","misc1","paddle1","paddle2","paddle3","paddle4","touchpad","D↑","D↓","D←","D→","R↑","R↓","R←","R→","Left stick","Right stick","Xbox","Microphone","Capture","Touchpad","Paddle 1","Paddle 2","Paddle 3","Paddle 4"}){
  auto pixels=glyph_pixels(label);check(pixels.has_value());check(pixels->size()==128);
  check(std::any_of(pixels->begin(),pixels->end(),[](auto v){return v!=0;}));
  for(auto value:*pixels)check((value>>4)==0||(value>>4)==1||(value>>4)==15);
  for(auto value:*pixels)check((value&15)==0||(value&15)==1||(value&15)==15);
 }
 check(glyph_pixels("↑")==glyph_pixels("dpup"));check(glyph_pixels("→")==glyph_pixels("dpright"));
 check(glyph_pixels("leftshoulder")==glyph_pixels("LB"));check(glyph_pixels("rightstick")==glyph_pixels("RS"));
 check(glyph_pixels("start")==glyph_pixels("Menu"));check(glyph_pixels("back")==glyph_pixels("View"));
 check(glyph_pixels("guide")==glyph_pixels("Home"));check(glyph_pixels("↑")!=glyph_pixels("↓"));
 check(glyph_pixels("L1")!=glyph_pixels("L3"));check(glyph_pixels("+")!=glyph_pixels("-"));
 // PAL selects its own pointer table, while retaining verified descriptor/hash guards.
 auto palProfile=pal_en_prompt_texture_layout();palProfile.expected=hashes;
 TextureGuard palGuard(palProfile);palProfile.bank_pointer=0x79650; // observer owns a const copy
 word(0x80079650,0);word(0x80076B30,bank);word(sprite+0x14,bank+5*12);
 word(bank+5*12,0x00100010);put(tex,original);put(pal,palette);
 labels={"B","A"};auto palBefore=ram;
 check(palGuard.prepare(mem,sprite,labels));
 auto physicalB=glyph_pixels("B");check(get(tex,128)==std::vector<uint8_t>(physicalB->begin(),physicalB->end()));
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
