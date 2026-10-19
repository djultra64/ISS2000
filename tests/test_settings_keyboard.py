"""Execute production keyboard mapping into the native settings draft.
Original project work: djultra64. CPU-only; no desktop or synthetic game input.
"""
from pathlib import Path
import subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class SettingsKeyboardTests(unittest.TestCase):
 def test_arrows_and_page_keys_change_graphics_through_real_router(self):
  source=(ROOT/'src/platform.cpp').read_text();start=source.index('switch(key){');opening=source.index('{',start);end=opening+1;depth=1
  while depth:
   depth+=(source[end]=='{')-(source[end]=='}');end+=1
  switch=source[start:end]
  code=r'''#include "runtime/game_settings_menu.hpp"
#include "runtime/game_controls_input.hpp"
#include <cassert>
using namespace iss2000;
ControlsMenuCommand keyboard(SDL_Scancode key,bool apply=false){ControlsMenuInputFrame menu_frame;menu_frame.apply_save_enabled=apply;SWITCH;return menu_frame.keyboard_command;}
int main(){
 assert(keyboard(SDL_SCANCODE_X)==ControlsMenuCommand::Cancel);
 assert(keyboard(SDL_SCANCODE_X,true)==ControlsMenuCommand::ApplySave);
 assert(keyboard(SDL_SCANCODE_LEFT)==ControlsMenuCommand::PreviousPage);
 assert(keyboard(SDL_SCANCODE_RIGHT)==ControlsMenuCommand::NextPage);
 assert(keyboard(SDL_SCANCODE_PAGEUP)==keyboard(SDL_SCANCODE_LEFT));
 assert(keyboard(SDL_SCANCODE_PAGEDOWN)==keyboard(SDL_SCANCODE_RIGHT));
 GameSettingsMenu menu;GameSettingsDraft draft;draft.graphics.resolution=RenderResolution::Original;draft.graphics.refresh_rate=RenderRefresh::Original;assert(menu.open(0,draft));
 ControlsMenuInputRouter router;ControlsMenuInputFrame f;f.active=true;f.owner_token=1;f.keyboard_active=true;
 router.route(f);router.route(f);
 auto press=[&](SDL_Scancode key){f.any_input=true;f.keyboard_command=keyboard(key);auto r=router.route(f);assert(r.deliver);menu.command(r.command);f.any_input=false;f.keyboard_command=ControlsMenuCommand::None;router.route(f);};
 press(SDL_SCANCODE_Z);press(SDL_SCANCODE_DOWN);
 press(SDL_SCANCODE_RIGHT);assert(menu.draft().graphics.resolution==RenderResolution::P720);
 press(SDL_SCANCODE_RIGHT);press(SDL_SCANCODE_RIGHT);assert(menu.draft().graphics.resolution==RenderResolution::P1080);
 press(SDL_SCANCODE_LEFT);assert(menu.draft().graphics.resolution==RenderResolution::P900);
 press(SDL_SCANCODE_PAGEDOWN);assert(menu.draft().graphics.resolution==RenderResolution::P1080);
 press(SDL_SCANCODE_DOWN);press(SDL_SCANCODE_RIGHT);press(SDL_SCANCODE_RIGHT);assert(menu.draft().graphics.refresh_rate==RenderRefresh::Hz120);
 // Physical WEST applies across families, with a neutral gate on page changes.
 for(auto family:{platform::Family::Xbox,platform::Family::PlayStation,platform::Family::Nintendo}){
  ControlsMenuInputRouter r;ControlsMenuInputFrame a;a.active=true;a.owner_token=1;a.controllers[0].preferences.manual_family=family;r.route(a);r.route(a);
  // Inherited raw menu remaps cannot steal the dedicated Graphics shortcut.
  a.controllers[0].preferences.bindings[size_t(platform::Action::B)]=SDL_CONTROLLER_BUTTON_X;
  a.controllers[0].preferences.bindings[size_t(platform::Action::CDown)]=SDL_CONTROLLER_BUTTON_B;
  a.any_input=true;a.controllers[0].held=1u<<SDL_CONTROLLER_BUTTON_X;a.apply_save_enabled=true;
  assert(r.route(a).command==ControlsMenuCommand::None);a.any_input=false;a.controllers[0].held=0;r.route(a);
  a.any_input=true;a.controllers[0].held=1u<<SDL_CONTROLLER_BUTTON_X;assert(r.route(a).command==ControlsMenuCommand::ApplySave);assert(r.route(a).command==ControlsMenuCommand::None);
  a.escape=true;assert(r.route(a).command==ControlsMenuCommand::Cancel);
 }

}
'''.replace('SWITCH',switch)
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);(p/'test.cpp').write_text(code);includes=['src','.local/deps/N64Recomp/include','.local/deps/N64ModernRuntime/librecomp/include','.local/deps/N64ModernRuntime/ultramodern/include','.local/deps/N64ModernRuntime/thirdparty','.local/deps/N64ModernRuntime/thirdparty/concurrentqueue'];built=subprocess.run(['c++','-std=c++20','-O1','-pthread',*['-I'+str(ROOT/i)for i in includes],'-I/home/linuxbrew/.linuxbrew/include/SDL2',str(p/'test.cpp'),str(ROOT/'src/runtime/game_settings_menu.cpp'),'-o',str(p/'test')],capture_output=True,text=True);self.assertEqual(built.returncode,0,built.stderr);run=subprocess.run([str(p/'test')],capture_output=True,text=True);self.assertEqual(run.returncode,0,run.stderr)
