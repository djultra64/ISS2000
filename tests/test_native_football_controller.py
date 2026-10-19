"""Exercise the native Controller Type handler; no game/window/OS input.
Original project work: djultra64.
"""
from pathlib import Path
import subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
def function(source,name,returns="void"):
 start=source.index(returns+' '+name+'(');opening=source.index('{',start);depth=1;end=opening+1
 while depth:
  depth+=(source[end]=='{')-(source[end]=='}');end+=1
 return source[start:end]
class NativeFootballControllerTests(unittest.TestCase):
 def test_type_accept_never_opens_raw_n64_remap(self):
  source=(ROOT/'src/runtime/native_game.cpp').read_text()
  handler=function(source,'select_original_controller_action')+'\n'+function(source,'cycle_original_controller_type','bool')+'\n'+function(source,'previous_original_controller_type')+'\n'+function(source,'next_original_controller_type')
  code=r'''
#include "recomp.h"
#include "runtime/football_controller_editor.hpp"
#include <array>
#include <vector>
#include <cassert>
using namespace iss2000;
unsigned raw_opens=0,original_calls=0,save_attempts=0;bool allow_save=true;
void ensure_controller_editor(){auto& e=football_controller_editor();if(!e.snapshot().active)e.begin({});}
bool save_original_controller_port(unsigned){++save_attempts;return allow_save;}
bool controller_save_failed=false;
bool owner=true;
namespace platform {struct Pref{};std::array<Pref,4> port_preferences(){return {};}}
struct RawMenu{void open(unsigned,platform::Pref){++raw_opens;}};
RawMenu& game_controls_menu(){static RawMenu menu;return menu;}
bool original_controller_screen(uint8_t*){return owner;}
void func_802C49B8_overlay_40c7a0_802c3490(uint8_t*,recomp_context*){++original_calls;}
unsigned original_type_events=0;
void original_type(uint8_t* ram,recomp_context* c){++original_type_events;const auto port=ram[0x2d21ef^3];ram[(0x2d21e4+port)^3]=(ram[(0x2d21e4+port)^3]+1)%3;c->r2=987;}
void func_802C4C40_overlay_40c7a0_802c3490(uint8_t* r,recomp_context* c){original_type(r,c);}
void func_802C4D88_overlay_40c7a0_802c3490(uint8_t* r,recomp_context* c){original_type(r,c);}

HANDLER
int main(){
 std::vector<uint8_t> ram(0x800000);recomp_context c{};
 for(unsigned port=0;port<4;++port){ram[0x2d21ef^3]=port;ram[(0x2d21e0+port)^3]=1;
  select_original_controller_action(ram.data(),&c);
  assert(raw_opens==0&&"Type must never open the rejected raw N64 remap screen");
 }
 assert(original_calls==4);
 auto& editor=football_controller_editor();editor.select_port(2);editor.cycle_scheme(-1);
 ram[0x2d21ef^3]=2;select_original_controller_action(ram.data(),&c);
 assert(editor.snapshot().editing_free&&raw_opens==0&&original_calls==5);
 editor.input({});editor.input({.cancel=true});
 ram[(0x2d21e0+2)^3]=0;allow_save=false;
 select_original_controller_action(ram.data(),&c);assert(save_attempts==1&&original_calls==5);
 allow_save=true;select_original_controller_action(ram.data(),&c);assert(save_attempts==2&&original_calls==6);
 ram[0x2d21ef^3]=3;ram[(0x2d21e0+3)^3]=1;ram[(0x2d21e4+3)^3]=2;
 for(unsigned n=0;n<6;++n){assert(cycle_original_controller_type(ram.data(),1));assert(ram[(0x2d21e4+3)^3]==2);}
 assert(editor.snapshot().draft[3].scheme==ControllerScheme::Type1);
 ram[(0x2d21e0+3)^3]=2;const auto before=editor.snapshot();assert(!cycle_original_controller_type(ram.data(),1));assert(editor.snapshot()==before);
 ram[(0x2d21e0+3)^3]=1;previous_original_controller_type(ram.data(),&c);
 assert(original_type_events==1&&ram[(0x2d21e4+3)^3]==2&&c.r2==987);
 next_original_controller_type(ram.data(),&c);assert(original_type_events==2&&ram[(0x2d21e4+3)^3]==2);
 owner=false;select_original_controller_action(ram.data(),&c);assert(original_calls==7&&save_attempts==2);
}
'''.replace('HANDLER',handler)
  with tempfile.TemporaryDirectory() as d:
   cpp=Path(d)/'check.cpp';cpp.write_text(code);exe=Path(d)/'check'
   r=subprocess.run(['c++','-std=c++20','-O1','-pthread','-I'+str(ROOT/'src'),'-I'+str(ROOT/'.local/deps/N64Recomp/include'),str(cpp),str(ROOT/'src/runtime/football_controller_editor.cpp'),str(ROOT/'src/runtime/controller_schemes.cpp'),'-o',str(exe)],capture_output=True,text=True)
   self.assertEqual(r.returncode,0,r.stderr)
   r=subprocess.run([str(exe)],capture_output=True,text=True)
   self.assertEqual(r.returncode,0,r.stderr)
if __name__=='__main__':unittest.main()
