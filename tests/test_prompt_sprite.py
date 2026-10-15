"""Original work: djultra64. Synthetic original-engine sprite transactions only."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
MINIZ=ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz'
MINIZ_BUILD=ROOT/'.local/runtime-deps-build/librecomp/miniz'
@unittest.skipUnless(shutil.which('c++') and (MINIZ_BUILD/'libminiz.a').is_file(),'Compiler and pinned miniz required')
class PromptSpriteTests(unittest.TestCase):
 def test_c_row_interleaving_ownership_and_bounded_text_fallback(self):
  with tempfile.TemporaryDirectory() as directory:
   folder=Path(directory);source=folder/'main.cpp'
   source.write_text(r'''
#include "runtime/prompt_textures.hpp"
#include "runtime/rom_image.hpp"
#include <algorithm>
#include <iostream>
#include <source_location>
#include <stdexcept>
#include <vector>
using namespace iss2000;
using namespace iss2000::prompt_detail;
void check(bool b,const std::source_location p=std::source_location::current()){if(!b)throw std::runtime_error("line "+std::to_string(p.line()));}
int main(){try{
 std::vector<uint8_t> ram(0x800000);auto* m=ram.data();
 auto byte=[&](uint32_t a,uint8_t v){m[(a&0x7fffff)^3]=v;};
 auto half=[&](uint32_t a,uint16_t v){byte(a,v>>8);byte(a+1,v);};
 auto word=[&](uint32_t a,uint32_t v){half(a,v>>16);half(a+2,v);};
 auto put=[&](uint32_t a,auto const& bytes){for(size_t n=0;n<bytes.size();++n)byte(a+n,bytes[n]);};
 auto get=[&](uint32_t a,size_t size){std::vector<uint8_t> v(size);for(size_t n=0;n<size;++n)v[n]=m[((a+n)&0x7fffff)^3];return v;};
 constexpr uint32_t bank=0x80300000,sprite=0x80100000,tex=0x80200000,pal=0x80210000,segments=0x80220000;
 std::array<uint8_t,128> ab{};std::array<uint8_t,640> c{};
 for(size_t n=0;n<ab.size();++n)ab[n]=n*3;
 for(size_t n=0;n<c.size();++n)c[n]=n*7+11;
 std::array<uint8_t,32> palette{};for(unsigned n=1;n<16;++n){unsigned v=n*2;half(pal+n*2,(v<<11)|(v<<6)|(v<<1)|1);}for(unsigned n=0;n<32;++n)palette[n]=m[((pal+n)&0x7fffff)^3];
 auto profile=pal_en_prompt_texture_layout();
 for(auto& h:profile.expected)h={rom_detail::sha256_hex(ab),rom_detail::sha256_hex(palette)};
 check(profile.c_directions.has_value());profile.c_directions->expected={rom_detail::sha256_hex(c),rom_detail::sha256_hex(palette)};
 std::array<uint8_t,32> font{};font[1]=0xAA;put(0x80230000,font);
 profile.text_fallback->font_address=0x230000;profile.text_fallback->font_bytes=32;profile.text_fallback->font_sha256=rom_detail::sha256_hex(font);
 const std::array<std::array<uint16_t,2>,4> positions{{{136,169},{211,187},{211,169},{136,187}}};
 for(unsigned n=0;n<4;++n){auto at=segments+n*12;byte(at,n==0?0x10:n==3?0x80:0);byte(at+1,16);byte(at+2,16);half(at+4,positions[n][0]);half(at+6,positions[n][1]);half(at+8,n*512);}
 profile.c_directions->fallback_segments_sha256=rom_detail::sha256_hex(get(segments,48));
 word(0x8009E02C,0x8013B418);half(0x8013B42C,320);half(0x8013B42E,240);
 TextureGuard guard(profile);
 word(0x80076B30,bank);word(sprite+0x34,pal);word(sprite+0x30,segments);
 for(unsigned i=0;i<2;++i){word(bank+(5+i)*12,0x00100010);word(bank+(5+i)*12+4,0x01060000+i*0x10000);word(bank+(5+i)*12+8,tex+i*128);put(tex+i*128,ab);}
 word(bank+8*12,0x00500010);word(bank+8*12+4,0x010A0000);word(bank+8*12+8,tex+256);put(tex+256,c);
 std::array<PromptGlyphRequest,2> labels{{{PromptGlyphFamily::Xbox,"A"},{PromptGlyphFamily::Nintendo,"A"}}};
 std::array<PromptGlyphRequest,4> directions{{{PromptGlyphFamily::Xbox,"R←"},{PromptGlyphFamily::PlayStation,"R→"},{PromptGlyphFamily::Nintendo,"R↑"},{PromptGlyphFamily::Keyboard,"C"}}};
 word(sprite+0x14,bank+8*12);auto before=ram;
 auto applied=guard.prepare_sprite(m,sprite,labels,directions);check(applied.status==PromptSpriteStatus::Applied);check(applied.action==PromptSpriteAction::CDirections);
 auto actual=get(tex+256,640);
 for(unsigned cell=0;cell<5;++cell)for(unsigned row=0;row<16;++row)for(unsigned b=0;b<8;++b){
  const unsigned index=row*40+cell*8+b;
  if(cell==4)check(actual[index]==c[index]);
  else {auto glyph=glyph_pixels(directions[cell],palette);check(glyph&&actual[index]==(*glyph)[row*8+b]);}
 }
 for(size_t n=0;n<ram.size();++n)if(n<0x200100||n>=0x200380)check(ram[n]==before[n]);
 guard.restore(m);check(ram==before);
 // Family and each action's binding are independent, including a genuine reload.
 check(guard.prepare_sprite(m,sprite,labels,directions).status==PromptSpriteStatus::Applied);put(tex+256,c);
 std::swap(directions[0],directions[3]);check(guard.prepare_sprite(m,sprite,labels,directions).status==PromptSpriteStatus::Applied);
 guard.restore(m);check(ram==before);
 // Failure is atomic across four icons; no old C image can be mistaken for a new binding.
 check(guard.prepare_sprite(m,sprite,labels,directions).status==PromptSpriteStatus::Applied);
 directions[2]={PromptGlyphFamily::Xbox,"Paddle 1"};
 auto cText=guard.prepare_sprite(m,sprite,labels,directions);check(cText.status==PromptSpriteStatus::TextFallback&&cText.line_count==4);check(ram==before);
 const std::array<std::string,4> names{{"C","RR","P1","RL"}};
 for(unsigned n=0;n<4;++n)check(cText.lines[n].text==names[n]&&cText.lines[n].x==positions[n][0]&&cText.lines[n].y==positions[n][1]+2);
 // Every member must fit: no partial fallback, wrong font, or altered consumer.
 byte(0x80230001,0xBB);auto wrongFont=ram;check(guard.prepare_sprite(m,sprite,labels,directions).status==PromptSpriteStatus::RejectedKnown);check(ram==wrongFont);put(0x80230000,font);
 byte(segments+24,0x10);auto wrongConsumer=ram;check(guard.prepare_sprite(m,sprite,labels,directions).status==PromptSpriteStatus::RejectedKnown);check(ram==wrongConsumer);byte(segments+24,0);
 auto oldDirection=directions[1];directions[1]={PromptGlyphFamily::Xbox,"Unknown binding"};check(guard.prepare_sprite(m,sprite,labels,directions).status==PromptSpriteStatus::RejectedKnown);directions[1]=oldDirection;

 directions[2]={PromptGlyphFamily::Nintendo,"R↑"};check(guard.prepare_sprite(m,sprite,labels,directions).status==PromptSpriteStatus::Applied);
 byte(tex+300,0xEE);auto foreign=ram;check(guard.prepare_sprite(m,sprite,labels,directions).status==PromptSpriteStatus::RejectedKnown);guard.restore(m);check(ram==foreign);
 put(tex+256,c);byte(pal+2,0xFE);auto changed_palette=ram;check(guard.prepare_sprite(m,sprite,labels,directions).status==PromptSpriteStatus::RejectedKnown);check(ram==changed_palette);put(pal,palette);
 // A missing-art prompt is distinct from an ordinary sprite. Fallback reports
 // only a validated original terminal 16x16 icon, with source-pixel coordinates.
 word(sprite+0x14,bank+5*12);byte(segments,0x90);byte(segments+1,16);byte(segments+2,16);
 half(segments+4,40);half(segments+6,100);half(sprite+0x20,24);half(sprite+0x24,8);
 half(sprite+0x1c,0);word(sprite+8,0);half(segments+8,0);half(segments+10,0);
 labels[0]={PromptGlyphFamily::Xbox,"Paddle 1"};before=ram;
 auto fallback=guard.prepare_sprite(m,sprite,labels,directions);
 check(fallback.status==PromptSpriteStatus::TextFallback&&fallback.action==PromptSpriteAction::A&&fallback.line_count==1);
 check(fallback.lines[0].x==64&&fallback.lines[0].y==110&&fallback.lines[0].text=="P1");check(ram==before);
 // Host upscaling is allowed, but an unproven original640x480 mode is not.
 byte(0x8013B42A,1);auto highResolution=ram;
 check(guard.prepare_sprite(m,sprite,labels,directions).status==PromptSpriteStatus::RejectedKnown);check(ram==highResolution);byte(0x8013B42A,0);
 half(0x8013B42C,640);check(guard.prepare_sprite(m,sprite,labels,directions).status==PromptSpriteStatus::RejectedKnown);half(0x8013B42C,320);
 word(0x8009E02C,0x807ffff0);check(guard.prepare_sprite(m,sprite,labels,directions).status==PromptSpriteStatus::RejectedKnown);word(0x8009E02C,0x8013B418);
 // Two viewport anchors are subtracted exactly like original 80041B50.
 half(sprite+0x1c,0x0302);half(0x8013c37c+2*16,10);half(0x8013c37c+2*16+4,20);
 fallback=guard.prepare_sprite(m,sprite,labels,directions);check(fallback.status==PromptSpriteStatus::TextFallback&&fallback.lines[0].x==54&&fallback.lines[0].y==90);
 // Unsafe scale, multi-icon list, nonzero UV, offscreen text and no short alias
 // each reject without a mutation or an inferred fallback location.
 auto rejected=[&]{auto snapshot=ram;check(guard.prepare_sprite(m,sprite,labels,directions).status==PromptSpriteStatus::RejectedKnown);check(ram==snapshot);};
 word(sprite+8,1u<<22);word(sprite+0x28,0x40000000);word(sprite+0x2c,0x3f800000);rejected();
 word(sprite+8,0);byte(segments,0x10);rejected();byte(segments,0x90);half(segments+8,32);rejected();half(segments+8,0);
 half(sprite+0x20,320);rejected();half(sprite+0x20,24);labels[0]={PromptGlyphFamily::Xbox,"Unknown binding"};rejected();
 labels[0]={PromptGlyphFamily::PlayStation,"PS"};fallback=guard.prepare_sprite(m,sprite,labels,directions);check(fallback.status==PromptSpriteStatus::TextFallback&&fallback.lines[0].text=="PS");
 word(sprite+0x14,bank+2*12);before=ram;check(guard.prepare_sprite(m,sprite,labels,directions).status==PromptSpriteStatus::Unrelated);check(ram==before);
 // PAL C proof is never silently enabled for the US compatibility profile.
 check(!us_prompt_texture_layout().c_directions.has_value());
 return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
''')
   executable=folder/'probe';result=subprocess.run(['c++','-std=c++20','-O1','-Wall','-Wextra','-Werror','-pthread','-I'+str(ROOT/'src'),'-I'+str(MINIZ),'-I'+str(MINIZ_BUILD),str(source),str(ROOT/'src/runtime/prompt_textures.cpp'),str(ROOT/'src/runtime/rom_image.cpp'),str(MINIZ_BUILD/'libminiz.a'),'-o',str(executable)],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
   result=subprocess.run([str(executable)],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
