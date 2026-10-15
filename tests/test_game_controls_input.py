"""Menu input routing edge and suppression contract. Original project work: djultra64."""
from pathlib import Path
import subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
HARNESS=r'''
#include "runtime/game_controls_input.hpp"
#include <cassert>
using namespace iss2000;using namespace iss2000::platform;
int main(){ControlsMenuInputRouter router;ControlsMenuInputFrame frame;frame.port=2;frame.active=true;
 auto& p=frame.controllers[2];p.held=1u<<SDL_CONTROLLER_BUTTON_A;frame.any_input=true;
 auto result=router.route(frame);assert(result.suppress&&result.command==ControlsMenuCommand::None);
 result=router.route(frame);assert(result.command==ControlsMenuCommand::None);
 p.held=0;frame.any_input=false;router.route(frame);
 frame.controllers[0].held=1u<<SDL_CONTROLLER_BUTTON_B;frame.any_input=true;result=router.route(frame);assert(result.command==ControlsMenuCommand::None);
 p.held=1u<<SDL_CONTROLLER_BUTTON_A;result=router.route(frame);assert(result.command==ControlsMenuCommand::Accept);
 result=router.route(frame);assert(result.command==ControlsMenuCommand::None);
 p.held=0;frame.controllers[0].held=0;frame.any_input=false;router.route(frame);
 p.y=.8f;frame.any_input=true;result=router.route(frame);assert(result.command==ControlsMenuCommand::Up);assert(router.route(frame).command==ControlsMenuCommand::None);
 p.y=0;frame.any_input=false;router.route(frame);p.preferences.bindings[0]=SDL_CONTROLLER_BUTTON_X;p.held=1u<<SDL_CONTROLLER_BUTTON_X;frame.any_input=true;assert(router.route(frame).command==ControlsMenuCommand::Accept);
 frame.capturing=true;frame.keyboard_command=ControlsMenuCommand::Cancel;frame.escape=false;result=router.route(frame);assert(result.command==ControlsMenuCommand::None&&result.held==p.held);
 frame.capturing=false;frame.keyboard_command=ControlsMenuCommand::None;assert(router.route(frame).command==ControlsMenuCommand::None);
 frame.escape=true;assert(router.route(frame).command==ControlsMenuCommand::Cancel);
 frame.escape=false;frame.capturing=true;frame.focused=false;assert(!router.route(frame).deliver);
 frame.focused=true;assert(!router.route(frame).deliver);p.held=0;frame.controllers[0].held=0;frame.any_input=false;assert(!router.route(frame).deliver);assert(router.route(frame).deliver);
 frame.active=false;frame.capturing=false;frame.any_input=true;frame.escape=false;frame.keyboard_command=ControlsMenuCommand::None;assert(router.route(frame).suppress);
 p.held=0;frame.any_input=true;assert(router.route(frame).suppress);frame.any_input=false;assert(!router.route(frame).suppress);
 frame.active=true;frame.any_input=false;router.route(frame);frame.keyboard_command=ControlsMenuCommand::Accept;frame.any_input=true;result=router.route(frame);assert(result.command==ControlsMenuCommand::Accept&&result.keyboard_navigation);
 frame.active=false;assert(router.route(frame).suppress);frame.any_input=false;frame.focused=false;assert(router.route(frame).suppress);frame.focused=true;assert(!router.route(frame).suppress);
}
'''
@unittest.skipUnless((ROOT/'.local/deps/N64Recomp/include/recomp.h').exists(),'Pinned native headers required')
class ControlsMenuInputTests(unittest.TestCase):
 def test_open_release_edges_capture_escape_port_isolation_and_close_release(self):
  with tempfile.TemporaryDirectory() as temp:
   d=Path(temp);(d/'test.cpp').write_text(HARNESS)
   includes=['src','.local/deps/N64Recomp/include','.local/deps/N64ModernRuntime/librecomp/include','.local/deps/N64ModernRuntime/ultramodern/include','.local/deps/N64ModernRuntime/thirdparty','.local/deps/N64ModernRuntime/thirdparty/concurrentqueue']
   result=subprocess.run(['c++','-std=c++20','-Wall','-Wextra','-Werror','-pthread',*['-I'+str(ROOT/i) for i in includes],'-I/home/linuxbrew/.linuxbrew/include/SDL2',str(d/'test.cpp'),'-o',str(d/'test')],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
   result=subprocess.run([str(d/'test')],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
