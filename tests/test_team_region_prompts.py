"""Original work: djultra64. Exact PAL region-selector font transaction."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
MINIZ=ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz'
MINIZ_BUILD=ROOT/'.local/runtime-deps-build/librecomp/miniz'
@unittest.skipUnless(shutil.which('c++') and (MINIZ_BUILD/'libminiz.a').is_file(),'Compiler and pinned miniz required')
class TeamRegionPromptTests(unittest.TestCase):
 def test_actual_region_hint_uses_all_physical_actions_without_touching_atlas_or_neighbors(self):
  snapshot=ROOT/'.local/hidden-test-01/team16-completed.rdram'
  if not snapshot.is_file():self.skipTest('Private completed PAL team-selection snapshot required')
  source=r'''
#include "runtime/prompt_textures.hpp"
#include <fstream>
#include <iostream>
#include <source_location>
#include <stdexcept>
#include <vector>
using namespace iss2000;
void check(bool b,const std::source_location p=std::source_location::current()){if(!b)throw std::runtime_error("line "+std::to_string(p.line()));}
template<class Result> unsigned icons(const Result& result){if constexpr(requires{result.icon_count;})return result.icon_count;else return 0;}
template<class Line> unsigned tint(const Line& line){if constexpr(requires{line.palette;})return line.palette;else return 0;}
int main(int argc,char**argv){try{
 check(argc==2);std::vector<uint8_t> ram(0x800000);std::ifstream f(argv[1],std::ios::binary);f.read(reinterpret_cast<char*>(ram.data()),ram.size());check(bool(f));
 auto byte=[&](uint32_t p){return ram[(p&0x7fffff)^3];};
 auto word=[&](uint32_t p){return uint32_t(byte(p))<<24|uint32_t(byte(p+1))<<16|uint32_t(byte(p+2))<<8|byte(p+3);};
 auto put=[&](uint32_t p,uint32_t v){for(unsigned n=0;n<4;++n)ram[((p+n)&0x7fffff)^3]=uint8_t(v>>(24-8*n));};
 const auto original=ram;constexpr uint32_t sprite=0x8013d9d0;
 const auto descriptor=word(sprite+20),palette=word(sprite+52);
 std::array<PromptGlyphRequest,2> ab{};std::array<PromptGlyphRequest,4> c{};
 std::array<PromptGlyphRequest,3> shoulders{{{PromptGlyphFamily::Xbox,"LB"},{PromptGlyphFamily::Xbox,"LT"},{PromptGlyphFamily::Xbox,"RB"}}};
 prompt_detail::TextureGuard guard(pal_en_prompt_texture_layout());
 check(guard.prepare_sprite(ram.data(),sprite,ab,c).status==PromptSpriteStatus::Unrelated);
 auto result=guard.prepare_sprite(ram.data(),sprite,ab,c,std::nullopt,shoulders);
 check(result.status==PromptSpriteStatus::TextFallback&&result.action==PromptSpriteAction::Shoulders&&result.line_count==0&&ram==original);
 check(icons(result)==4); // Each physical shoulder is a native sprite, with its own authentic palette.
 const int xs[]{44,128,179,263};
 for(unsigned n=0;n<4;++n)check(result.icons[n].label==(n%2==0?"LB":"RB")&&result.icons[n].x==xs[n]&&result.icons[n].y>=50&&result.icons[n].y<=51&&result.icons[n].width==16&&result.icons[n].height==16);
 // Genuine completed Gfx samples region-label source80210F00. Its visible
 // EUROPEB ink ends before x123; EUROPEA before x258. Original quads contain
 // transparent padding, so validate actual ink rather than their loose bounds.
 auto ink=[&](unsigned u,unsigned width){int lo=999,hi=-1;for(unsigned y=0;y<16;++y)for(unsigned x=0;x<width;++x){auto b=byte(0x80210f00+y*64+(u+x)/2);const auto a=(u+x)%2?b&15:b>>4;if(a){lo=std::min(lo,int(x));hi=std::max(hi,int(x));}}return std::pair(lo,hi);};
 check(ink(0,48).second+67<123&&ink(64,16).second+115<123&&ink(0,56).second+202<258);
 // Native 16px buttons now flank the heading. Its authentic visible ink is
 // y54..63. Each tile's own transparent padding is accounted for by the adapter.
 for(unsigned n=0;n<4;++n){const auto& icon=result.icons[n];
  check(icon.y>=50&&icon.y<=51&&icon.width==16);
  const int offset=n<2?0:135;
  if(n%2==0)check(icon.x+16<=67+offset);
  else check(icon.x>=128+offset);
 }
 check(ram==original); // Original EUROPE B/A images and consumers remain unchanged.
 shoulders={{{PromptGlyphFamily::PlayStation,"L1"},{PromptGlyphFamily::Nintendo,"ZL"},{PromptGlyphFamily::Xbox,"Paddle 3"}}};
 result=guard.prepare_sprite(ram.data(),sprite,ab,c,std::nullopt,shoulders);
 check(result.status==PromptSpriteStatus::TextFallback&&result.line_count==4&&result.lines[0].text=="L1"&&result.lines[1].text=="P3"&&result.lines[0].x==46&&result.lines[0].y==53&&ram==original);
 for(unsigned variant=0;variant<9;++variant){ram=original;
  if(variant==0)ram[0x1be700^3]^=1;
  if(variant==1)ram[(word(descriptor+8)&0x7fffff)^3]^=1;
  if(variant==2)ram[(word(descriptor+20)&0x7fffff)^3]^=1;
  if(variant==3)ram[(palette&0x7fffff)^3]^=1;
  if(variant==4)ram[0x352800^3]^=1;
  if(variant==5){put(sprite+8,word(sprite+8)|(1u<<22));put(sprite+40,0x40000000);}
  if(variant==6)ram[(0x13b418+18)^3]=1;
  if(variant==7)ram[0x12de56^3]=2; // Multiplayer ownership is not yet proven.
  if(variant==8)ram[0x876bc^3]^=1; // Original font tint4 must remain black.
  const auto foreign=ram;check(guard.prepare_sprite(ram.data(),sprite,ab,c,std::nullopt,shoulders).status==PromptSpriteStatus::RejectedKnown&&ram==foreign);
 }
 ram=original;shoulders[0]={PromptGlyphFamily::Xbox,"Unsupported"};check(guard.prepare_sprite(ram.data(),sprite,ab,c,std::nullopt,shoulders).status==PromptSpriteStatus::RejectedKnown&&ram==original);
 ram=original;shoulders[0]={PromptGlyphFamily::Xbox,"LB",1};check(guard.prepare_sprite(ram.data(),sprite,ab,c,std::nullopt,shoulders).status==PromptSpriteStatus::RejectedKnown&&ram==original);shoulders[0].port=0;
 // Other consumers of the same two common atlas descriptors stay unrelated.
 shoulders[0]={PromptGlyphFamily::Xbox,"LB"};
 // Hidden Z alternatives cannot influence either visible bumper prompt.
 shoulders[1]={PromptGlyphFamily::Automatic,"Unsupported",3};
 const auto ignored=guard.prepare_sprite(ram.data(),sprite,ab,c,std::nullopt,shoulders);check(ignored.status==PromptSpriteStatus::TextFallback&&ignored.line_count==4&&ignored.lines[0].text=="LB"&&ignored.lines[1].text=="P3"&&ram==original);
 check(guard.prepare_sprite(ram.data(),0x8013cb0c,ab,c,std::nullopt,shoulders).status==PromptSpriteStatus::Unrelated&&ram==original);
 return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
'''
  with tempfile.TemporaryDirectory() as d:
   folder=Path(d);path=folder/'probe.cpp';path.write_text(source);exe=folder/'probe'
   built=subprocess.run(['c++','-std=c++20','-O1','-Wall','-Wextra','-Werror','-pthread','-I'+str(ROOT/'src'),'-I'+str(MINIZ),'-I'+str(MINIZ_BUILD),str(path),str(ROOT/'src/runtime/prompt_textures.cpp'),str(ROOT/'src/runtime/rom_image.cpp'),str(MINIZ_BUILD/'libminiz.a'),'-o',str(exe)],capture_output=True,text=True)
   self.assertEqual(built.returncode,0,built.stderr)
   run=subprocess.run([str(exe),str(snapshot)],capture_output=True,text=True);self.assertEqual(run.returncode,0,run.stderr)
