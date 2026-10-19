"""Original work: djultra64. Career original sprite guard and CPU-only snapshot checks."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
MINIZ=ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz'
MINIZ_BUILD=ROOT/'.local/runtime-deps-build/librecomp/miniz'
@unittest.skipUnless(shutil.which('c++') and (MINIZ_BUILD/'libminiz.a').is_file(),'Compiler and pinned miniz required')
class CareerPromptTests(unittest.TestCase):
 def test_actual_private_career_prompt_uses_both_physical_glyphs_and_safe_text_fallback(self):
  snapshots=[ROOT/'.local/pal-acceptance'/name for name in ['career-files08.rdram','career-face08.rdram']]
  if not all(p.is_file() for p in snapshots):self.skipTest('Private visible Career snapshots required')
  with tempfile.TemporaryDirectory() as directory:
   folder=Path(directory);source=folder/'main.cpp';source.write_text(r'''
#include "runtime/prompt_textures.hpp"
#include <algorithm>
#include <fstream>
#include <iostream>
#include <source_location>
#include <stdexcept>
#include <vector>
using namespace iss2000;
void check(bool b,const std::source_location p=std::source_location::current()){if(!b)throw std::runtime_error("line "+std::to_string(p.line()));}
int main(int argc,char**argv){try{
 check(argc==4);std::vector<uint8_t> ram(0x800000);std::ifstream f(argv[1],std::ios::binary);f.read(reinterpret_cast<char*>(ram.data()),ram.size());check(bool(f));
 auto*m=ram.data();auto byte=[&](uint32_t p){return m[(p&0x7fffff)^3];};
 auto word=[&](uint32_t p){return uint32_t(byte(p))<<24|uint32_t(byte(p+1))<<16|uint32_t(byte(p+2))<<8|byte(p+3);};
 const uint32_t sprite=std::stoul(argv[2],nullptr,16),expectedAction=std::stoul(argv[3]);
 const uint32_t descriptor=word(sprite+0x14),texture=word(descriptor+8),pal=word(sprite+0x34);
 std::array<uint8_t,32> palette{};for(unsigned n=0;n<32;++n)palette[n]=byte(pal+n);
 std::array<PromptGlyphRequest,2> labels{{{PromptGlyphFamily::Xbox,"B"},{PromptGlyphFamily::Nintendo,"A"}}};std::array<PromptGlyphRequest,4> c{};
 prompt_detail::TextureGuard guard(pal_en_prompt_texture_layout());const auto original=ram;
 auto result=guard.prepare_sprite(m,sprite,labels,c);check(result.status==PromptSpriteStatus::Applied);check(unsigned(result.action)==expectedAction);
 for(unsigned cell=0;cell<2;++cell){prompt_detail::PixelBytes ink;for(unsigned y=0;y<16;++y)for(unsigned x=0;x<8;++x)ink[y*8+x]=original[((texture+y*16+cell*8+x)&0x7fffff)^3];auto glyph=prompt_detail::glyph_pixels(labels[cell],palette,ink);check(bool(glyph));for(unsigned row=0;row<16;++row)for(unsigned n=0;n<8;++n)check(byte(texture+row*16+cell*8+n)==(*glyph)[row*8+n]);}
 for(size_t n=0;n<ram.size();++n)if(n<(texture&0x7fffff)||n>=(texture&0x7fffff)+256)check(ram[n]==original[n]);
 guard.restore(m);check(ram==original);
 // A valid but unavailable artist binding falls back to the current cell's
 // exact original-font position; the entire two-cell strip remains untouched.
 labels[expectedAction-1]={PromptGlyphFamily::Xbox,"Paddle 1"};result=guard.prepare_sprite(m,sprite,labels,c);
 check(result.status==PromptSpriteStatus::TextFallback&&result.line_count==1&&result.lines[0].text=="P1");check(ram==original);
 // Known original files/country/name geometry is exact, including right-cellUV.
 check(result.lines[0].x==(expectedAction==1?104:(sprite==0x8013c83c?20:168)));
 check(result.lines[0].y==(sprite==0x8013c83c?203:178));
 return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
''')
   executable=folder/'probe';built=subprocess.run(['c++','-std=c++20','-O1','-Wall','-Wextra','-Werror','-pthread','-I'+str(ROOT/'src'),'-I'+str(MINIZ),'-I'+str(MINIZ_BUILD),str(source),str(ROOT/'src/runtime/prompt_textures.cpp'),str(ROOT/'src/runtime/rom_image.cpp'),str(MINIZ_BUILD/'libminiz.a'),'-o',str(executable)],capture_output=True,text=True)
   self.assertEqual(built.returncode,0,built.stderr)
   for snapshot,sprite,action in [(snapshots[0],'8013c83c','2'),(snapshots[1],'8013c6d4','1'),(snapshots[1],'8013c710','2')]:
    with self.subTest(snapshot=snapshot.name,sprite=sprite):
     run=subprocess.run([str(executable),str(snapshot),sprite,action],capture_output=True,text=True);self.assertEqual(run.returncode,0,run.stderr)
 def test_pair_hash_palette_reload_and_foreign_ownership_guards(self):
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
 auto byte=[&](uint32_t p,uint8_t v){m[(p&0x7fffff)^3]=v;};
 auto half=[&](uint32_t p,uint16_t v){byte(p,v>>8);byte(p+1,v);};
 auto word=[&](uint32_t p,uint32_t v){half(p,v>>16);half(p+2,v);};
 auto put=[&](uint32_t p,auto const& bytes){for(size_t n=0;n<bytes.size();++n)byte(p+n,bytes[n]);};
 constexpr uint32_t bank=0x80300000,sprite=0x80100000,texture=0x80200000,pal=0x80210000,seg=0x80220000;
 std::array<uint8_t,256> original{};for(unsigned n=0;n<256;++n)original[n]=n*13+5;
 std::array<uint8_t,32> palette{};for(unsigned n=1;n<16;++n){unsigned v=n*2;uint16_t rgba=(v<<11)|(v<<6)|(v<<1)|1;palette[n*2]=rgba>>8;palette[n*2+1]=rgba;}
 auto profile=pal_en_prompt_texture_layout();check(profile.ab_pair.has_value());check(!us_prompt_texture_layout().ab_pair);
 profile.ab_pair->expected={rom_detail::sha256_hex(original),rom_detail::sha256_hex(palette)};
 prompt_detail::TextureGuard guard(profile);profile.ab_pair->bank_pointer=0; // const copy
 word(0x80076c54,bank);word(sprite+0x14,bank+19*12);word(sprite+0x34,pal);word(sprite+0x30,seg);
 word(bank+19*12,0x00200010);word(bank+19*12+4,0x010a0000);word(bank+19*12+8,texture);put(texture,original);put(pal,palette);
 byte(seg,0x90);byte(seg+1,16);byte(seg+2,16);half(seg+8,512);
 std::array<PromptGlyphRequest,2> ab{{{PromptGlyphFamily::Xbox,"A"},{PromptGlyphFamily::Nintendo,"A"}}};std::array<PromptGlyphRequest,4> c{};
 const auto baseline=ram;
 check(guard.prepare_sprite(m,sprite,ab,c).status==PromptSpriteStatus::Applied);auto first=ram;
 check(guard.prepare_sprite(m,sprite,ab,c).status==PromptSpriteStatus::Applied&&ram==first);
 std::swap(ab[0],ab[1]);check(guard.prepare_sprite(m,sprite,ab,c).status==PromptSpriteStatus::Applied&&ram!=first);guard.restore(m);check(ram==baseline);
 check(guard.prepare_sprite(m,sprite,ab,c).status==PromptSpriteStatus::Applied);put(texture,original);check(guard.prepare_sprite(m,sprite,ab,c).status==PromptSpriteStatus::Applied);guard.restore(m);check(ram==baseline);
 check(guard.prepare_sprite(m,sprite,ab,c).status==PromptSpriteStatus::Applied);byte(texture+131,0xEE);auto foreign=ram;
 check(guard.prepare_sprite(m,sprite,ab,c).status==PromptSpriteStatus::RejectedKnown);guard.restore(m);check(ram==foreign);
 put(texture,original);byte(pal+2,0xFE);auto changed=ram;check(guard.prepare_sprite(m,sprite,ab,c).status==PromptSpriteStatus::RejectedKnown);guard.restore(m);check(ram==changed);put(pal,palette);
 // No patch is made to a different source cell or a multi-icon consumer.
 for(unsigned u:{1u,32u,1024u}){half(seg+8,u);changed=ram;check(guard.prepare_sprite(m,sprite,ab,c).status==PromptSpriteStatus::RejectedKnown);check(ram==changed);}half(seg+8,512);
 byte(seg,0x10);changed=ram;check(guard.prepare_sprite(m,sprite,ab,c).status==PromptSpriteStatus::RejectedKnown);check(ram==changed);byte(seg,0x90);
 word(bank+19*12,0x00400010);changed=ram;check(guard.prepare_sprite(m,sprite,ab,c).status==PromptSpriteStatus::RejectedKnown);check(ram==changed);word(bank+19*12,0x00200010);
 check(guard.prepare_sprite(m,sprite,ab,c).status==PromptSpriteStatus::Applied);
 // Missing either artist tile restores the complete owned pair. No font has
 // been loaded in this synthetic fixture, so it cannot claim a text fallback.
 ab[0]={PromptGlyphFamily::Xbox,"Paddle 1"};check(guard.prepare_sprite(m,sprite,ab,c).status==PromptSpriteStatus::RejectedKnown);check(ram==baseline);
 return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
''')
   executable=folder/'probe';built=subprocess.run(['c++','-std=c++20','-O1','-Wall','-Wextra','-Werror','-pthread','-I'+str(ROOT/'src'),'-I'+str(MINIZ),'-I'+str(MINIZ_BUILD),str(source),str(ROOT/'src/runtime/prompt_textures.cpp'),str(ROOT/'src/runtime/rom_image.cpp'),str(MINIZ_BUILD/'libminiz.a'),'-o',str(executable)],capture_output=True,text=True)
   self.assertEqual(built.returncode,0,built.stderr)
   run=subprocess.run([str(executable)],capture_output=True,text=True);self.assertEqual(run.returncode,0,run.stderr)
