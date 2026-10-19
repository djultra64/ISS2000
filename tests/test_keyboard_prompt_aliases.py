"""Default keyboard names from the production SDL prompt path reach original UI.
Original project work: djultra64. CPU snapshots only; no game or OS input.
"""
from pathlib import Path
import os
import re
import shlex
import shutil
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
MINIZ=ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz'
MINIZ_BUILD=ROOT/'.local/runtime-deps-build/librecomp/miniz'
SDL_CONFIG=os.environ.get('ISS2000_SDL_CONFIG',shutil.which('sdl2-config') or '/home/linuxbrew/.linuxbrew/bin/sdl2-config')
def function(source,marker):
 start=source.index(marker);opening=source.index('{',start);depth=1;end=opening+1
 while depth:
  depth+=(source[end]=='{')-(source[end]=='}');end+=1
 return source[start:end]
class KeyboardPromptAliasTests(unittest.TestCase):
 def test_production_default_names_adapt_team_shoulders_and_original_p1_pause(self):
  team=ROOT/'.local/hidden-test-01/team16-completed.rdram';pause=ROOT/'.local/hidden-test-01/field16-pause-controls-completed.rdram'
  if not all(p.is_file() for p in [team,pause,MINIZ_BUILD/'libminiz.a',Path(SDL_CONFIG)]) or not shutil.which('c++'):self.skipTest('Private original PAL snapshots, C++ and pinned SDL/miniz required')
  platform=(ROOT/'src/platform.cpp').read_text();header=(ROOT/'src/platform.hpp').read_text()
  declarations='\n'.join(re.search(pattern,header).group() for pattern in [r'enum class Family \{[^}]+\};',r'enum class Action \{[^}]+\};',r'struct Prompt \{[^}]+\};'])
  keys=re.search(r'constexpr std::array<SDL_Scancode,[^;]+;',platform).group()
  code=r'''#define SDL_MAIN_HANDLED
#include <SDL.h>
#include "runtime/prompt_textures.hpp"
#include <fstream>
#include <iostream>
#include <source_location>
#include <stdexcept>
#include <vector>
namespace iss2000::platform {
DECLARATIONS
FACE
LABEL
struct Port{SDL_GameController* controller{};Family detected{Family::Xbox},manual{Family::Automatic};bool keyboard{true};std::array<SDL_GameControllerButton,static_cast<size_t>(Action::Count)> bindings{};};
KEYS
PROMPT
}
using namespace iss2000;
void check(bool b,const std::source_location p=std::source_location::current()){if(!b)throw std::runtime_error("line "+std::to_string(p.line()));}
std::vector<uint8_t> load(const char* p){std::vector<uint8_t> r(0x800000);std::ifstream f(p,std::ios::binary);f.read(reinterpret_cast<char*>(r.data()),r.size());check(bool(f));return r;}
int main(int argc,char** argv){try{
 check(argc==3);using platform::Action;using platform::Family;platform::Port keyboard;
 std::array<platform::Prompt,unsigned(Action::Count)> names;
 const char* expected[]={"Z","X","Return","Left Shift","Q","E","I","K","J","L","T","G","F","H"};
 for(unsigned i=0;i<names.size();++i){names[i]=platform::prompt_locked(keyboard,Action(i));check(names[i].family==Family::Keyboard&&names[i].name==expected[i]&&names[i].glyph==expected[i]);}
 auto request=[&](Action a){return PromptGlyphRequest{PromptGlyphFamily::Keyboard,names[unsigned(a)].glyph,0};};
 const std::array<PromptGlyphRequest,2> ab{{request(Action::A),request(Action::B)}};
 const std::array<PromptGlyphRequest,4> directions{{request(Action::CLeft),request(Action::CRight),request(Action::CUp),request(Action::CDown)}};
 const std::array<PromptGlyphRequest,3> shoulders{{request(Action::L),request(Action::Z),request(Action::R)}};
 prompt_detail::TextureGuard guard(pal_en_prompt_texture_layout());
 auto team=load(argv[1]);const auto team_before=team;
 auto result=guard.prepare_sprite(team.data(),0x8013d9d0,ab,directions,request(Action::Start),shoulders);
 check(result.status==PromptSpriteStatus::TextFallback&&result.icon_count==4&&result.line_count==0&&team==team_before);
 for(unsigned n=0;n<4;++n)check(result.icons[n].label==(n%2==0?"Q":"E")&&result.icons[n].width==16);
 // Every other requested default is already an uppercase letter with genuine
 // keyboard art. Use the captured original font palette for availability only.
 std::array<uint8_t,32> palette{};for(unsigned n=0;n<32;++n)palette[n]=team[(0x87460+n)^3];
 for(Action a:{Action::L,Action::R,Action::CUp,Action::CDown,Action::CLeft,Action::CRight,Action::DUp,Action::DDown,Action::DLeft,Action::DRight})check(prompt_detail::glyph_pixels(request(a),palette).has_value());
 auto paused=load(argv[2]);const auto pause_before=paused;
 check(guard.sprite_port(paused.data(),0x8013d8e0)==0);
 result=guard.prepare_sprite(paused.data(),0x8013d8e0,ab,directions,request(Action::Start),shoulders);
 check(result.status==PromptSpriteStatus::TextFallback&&result.line_count==4&&paused==pause_before);
 check(result.lines[0].text=="LS"&&result.lines[1].text=="E"&&result.lines[2].text=="1 2 Pass Button"&&result.lines[3].text=="T Pass Button");
 for(unsigned n=0;n<result.line_count;++n)check(result.lines[n].height==8&&result.lines[n].palette==0);
 for(unsigned n=result.line_count;n<result.lines.size();++n)check(result.lines[n].text.empty());
 // This is a default keyboard alias, not permission to accept arbitrary
 // controller labels which happen to contain a key name.
 auto foreign=shoulders;foreign[1].family=PromptGlyphFamily::Xbox;
 check(guard.prepare_sprite(paused.data(),0x8013d8e0,ab,directions,request(Action::Start),foreign).status==PromptSpriteStatus::RejectedKnown&&paused==pause_before);
 // The alternative Z action is deliberately absent from region prompts.
 check(guard.prepare_sprite(team.data(),0x8013d9d0,ab,directions,request(Action::Start),foreign).status==PromptSpriteStatus::TextFallback&&team==team_before);
 return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
'''.replace('DECLARATIONS',declarations).replace('FACE',function(header,'constexpr std::string_view face_label(')).replace('LABEL',function(header,'constexpr std::string_view button_label(')).replace('KEYS',keys).replace('PROMPT',function(platform,'Prompt prompt_locked('))
  flags=shlex.split(subprocess.check_output([SDL_CONFIG,'--cflags','--libs'],text=True))
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'probe.cpp';path.write_text(code);binary=Path(d)/'probe'
   built=subprocess.run(['c++','-std=c++20','-O1','-Wall','-Wextra','-Werror','-pthread','-I'+str(ROOT/'src'),'-I'+str(MINIZ),'-I'+str(MINIZ_BUILD),str(path),str(ROOT/'src/runtime/prompt_textures.cpp'),str(ROOT/'src/runtime/rom_image.cpp'),str(MINIZ_BUILD/'libminiz.a'),'-o',str(binary),*flags],capture_output=True,text=True)
   self.assertEqual(built.returncode,0,built.stderr)
   run=subprocess.run([str(binary),str(team),str(pause)],capture_output=True,text=True,timeout=10);self.assertEqual(run.returncode,0,run.stderr)
