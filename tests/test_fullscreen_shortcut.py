"""Execute host Alt+Enter routing without game, window, audio or OS input.
Original project work: djultra64.
"""
from pathlib import Path
import re,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
def function(source,marker):
 start=source.index(marker);opening=source.index('{',start);depth=1;end=opening+1
 while depth:
  depth+=(source[end]=='{')-(source[end]=='}');end+=1
 return source[start:end]
class FullscreenShortcutTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.temp.cleanup);p=Path(cls.temp.name)
  source=(ROOT/'src/platform.cpp').read_text();update=function(source,'void update(void*)')
  event_start=update.index('    SDL_Event event;')
  if '    unsigned fullscreen_toggles=0;'in update:event_start=update.index('    unsigned fullscreen_toggles=0;')
  events=update[event_start:update.index('    int keyboard_count=0;')]
  keyboard=update[update.index('    int keyboard_count=0;'):update.index('    for(int k=0;k<keyboard_count;++k)')]
  deferred=update.split('    lock.unlock();',1)[1].split('    for(unsigned i=0;i<connected.size();++i)',1)[0]
  toggle=function(source,'void toggle_fullscreen(')if 'void toggle_fullscreen('in source else ''
  code=r'''#include "runtime/game_settings_menu.hpp"
#include "runtime/main_exit_menu.hpp"
#include "runtime/game_controls_input.hpp"
#if __has_include("runtime/fullscreen_shortcut.hpp")
#include "runtime/fullscreen_shortcut.hpp"
#endif
#include <algorithm>
#include <array>
#include <atomic>
#include <cstdio>
#include <stdexcept>
#include <string>
#include <vector>
using namespace iss2000;
using namespace iss2000::platform;
#if __has_include("runtime/fullscreen_shortcut.hpp")
FullscreenShortcut fullscreen_shortcut;
#endif
GameSettingsMenu& menu=iss2000::game_settings_menu();
struct FakeControls {bool active()const{return false;}} controls;
FakeControls& game_controls_menu(){return controls;}
struct Port {SDL_GameController* controller{};bool rumble=false,rumble_capable=false;};
std::array<Port,4> ports;
std::atomic<bool> controls_menu_release{false};
unsigned observed=0,sets=0;bool football_free=false;
GraphicsSettings applied;
GraphicsSettings render_settings(){return applied;}
void set_render_settings(const GraphicsSettings& g){applied=g;++sets;}
void observe_prompt_input(const SDL_Event&){++observed;}
void stop_motors(){}
void add_controllers(){}
namespace ultramodern {void quit(){throw std::runtime_error("unexpectedquit");}}
std::array<Uint8,SDL_NUM_SCANCODES> raw{},sampled{};
std::vector<SDL_Event> queue;size_t cursor=0;
int SDL_PollEvent(SDL_Event* e){if(cursor==queue.size())return 0;*e=queue[cursor++];return 1;}
const Uint8* SDL_GetKeyboardState(int* count){*count=int(raw.size());return raw.data();}
SDL_Joystick* SDL_GameControllerGetJoystick(SDL_GameController*){return nullptr;}
SDL_JoystickID SDL_JoystickInstanceID(SDL_Joystick*){return -1;}
int SDL_GameControllerRumble(SDL_GameController*,Uint16,Uint16,Uint32){return 0;}
void SDL_GameControllerClose(SDL_GameController*){}
TOGGLE
ControlsMenuInputFrame frame(){auto& controls_menu=controls;auto& settings_menu=menu;ControlsMenuInputFrame menu_frame;menu_frame.active=menu.active();
EVENTS
KEYBOARD
 sampled.fill(0);std::copy_n(keyboard,keyboard_count,sampled.begin());
DEFERRED
 queue.clear();cursor=0;return menu_frame;
}
void event(SDL_Scancode key,Uint16 mod=KMOD_NONE,bool repeat=false,bool up=false){
 SDL_Event e{};e.type=up?SDL_KEYUP:SDL_KEYDOWN;e.key.keysym.scancode=key;e.key.keysym.mod=mod;e.key.repeat=repeat;
 queue.push_back(e);raw[key]=!up;
}
void require(bool b,const char*m){if(!b)throw std::runtime_error(m);}
int main(int,char**argv){try{
 const std::string mode=argv[1];
 applied={AspectRatio::Original4x3,RenderResolution::P1440,RenderRefresh::Hz120,false};
 if(mode=="toggle"){
  event(SDL_SCANCODE_RETURN,KMOD_LALT);auto f=frame();
  require(applied.fullscreen&&sets==1,"Alt+Enter did not toggle fullscreen");
  require(applied.aspect_ratio==AspectRatio::Original4x3&&applied.resolution==RenderResolution::P1440&&applied.refresh_rate==RenderRefresh::Hz120,"Shortcut changed other graphics options");
  require(!sampled[SDL_SCANCODE_RETURN]&&raw[SDL_SCANCODE_RETURN],"Shortcut leaked Start or mutated SDL state");
  require(observed==0&&f.keyboard_command==ControlsMenuCommand::None,"Shortcut leaked into prompt or menu routing");
  event(SDL_SCANCODE_RETURN,KMOD_LALT,true);frame();require(sets==1,"Auto-repeat toggled fullscreen");
  event(SDL_SCANCODE_RETURN,KMOD_LALT);frame();require(sets==1,"Duplicate keydown toggled one held chord twice");
  event(SDL_SCANCODE_LALT,KMOD_NONE,false,true);frame();require(!sampled[SDL_SCANCODE_RETURN],"Alt release leaked held Enter");
  event(SDL_SCANCODE_RETURN,KMOD_NONE,true);frame();require(sets==1&&!sampled[SDL_SCANCODE_RETURN],"Repeat without Alt leaked Start");
  event(SDL_SCANCODE_RETURN,KMOD_NONE,false,true);frame();
  event(SDL_SCANCODE_RETURN);frame();require(sampled[SDL_SCANCODE_RETURN]&&sets==1,"Plain Enter lost Start");
  event(SDL_SCANCODE_RETURN,KMOD_NONE,false,true);frame();
  event(SDL_SCANCODE_RETURN,KMOD_RALT);frame();require(!applied.fullscreen&&sets==2,"Right Alt did not toggle back");
 }else if(mode=="keypad"){
  event(SDL_SCANCODE_KP_ENTER,KMOD_RALT);frame();require(applied.fullscreen&&sets==1&&!sampled[SDL_SCANCODE_KP_ENTER],"Keypad Alt+Enter failed");
  event(SDL_SCANCODE_KP_ENTER,KMOD_RALT,true);frame();require(sets==1,"Keypad auto-repeat toggled fullscreen");
 }else if(mode=="save"){
  GameSettingsDraft initial;initial.graphics=applied;initial.families[2]=Family::Nintendo;initial.vibration[3]=false;require(menu.open(0,initial),"open");
  menu.command(ControlsMenuCommand::Accept);menu.command(ControlsMenuCommand::Down);menu.command(ControlsMenuCommand::PreviousPage);
  event(SDL_SCANCODE_RETURN,KMOD_LALT);frame();
  unsigned saves=0;GameSettingsDraft saved;
  menu.command(ControlsMenuCommand::ApplySave,[&](const GameSettingsDraft& draft){saved=draft;++saves;return true;});
  require(saves==1&&saved.graphics.fullscreen&&saved.graphics.resolution==RenderResolution::P1080,"Explicit Save lost shortcut or pending resolution");
  require(saved.families[2]==Family::Nintendo&&!saved.vibration[3],"Explicit Save lost controller fields");
  require(applied.resolution==RenderResolution::P1440&&sets==1,"Shortcut implicitly applied other draft fields");
 }else if(mode=="draft"){
  GameSettingsDraft initial;initial.graphics=applied;initial.families[2]=Family::Nintendo;initial.vibration[3]=false;require(menu.open(0,initial),"open");
  menu.command(ControlsMenuCommand::Accept);menu.command(ControlsMenuCommand::Down);menu.command(ControlsMenuCommand::PreviousPage);
  require(menu.draft().graphics.resolution==RenderResolution::P1080,"draftsetup");
  event(SDL_SCANCODE_RETURN,KMOD_LALT);frame();
  require(applied.fullscreen&&menu.draft().graphics.fullscreen,"Active draft did not synchronize shortcut");
  require(menu.draft().graphics.resolution==RenderResolution::P1080&&applied.resolution==RenderResolution::P1440,"Shortcut committed or discarded unsaved draft");
  require(menu.draft().families[2]==Family::Nintendo&&!menu.draft().vibration[3],"Shortcut lost controller preferences");
  menu.command(ControlsMenuCommand::Cancel);menu.command(ControlsMenuCommand::Cancel);
  require(!menu.active()&&menu.draft().graphics.fullscreen&&menu.draft().graphics.resolution==RenderResolution::P1440,"Cancel undid the shortcut baseline");
  require(sets==1,"Shortcut implicitly applied the draft");
 }else return 2;
 return 0;
}catch(const std::exception&e){std::fprintf(stderr,"%s\n",e.what());return 1;}}
'''.replace('TOGGLE',toggle).replace('EVENTS',events).replace('KEYBOARD',keyboard).replace('DEFERRED',deferred)
  (p/'test.cpp').write_text(code);cls.binary=p/'test'
  includes=['src','.local/deps/N64Recomp/include','.local/deps/N64ModernRuntime/librecomp/include','.local/deps/N64ModernRuntime/ultramodern/include','.local/deps/N64ModernRuntime/thirdparty','.local/deps/N64ModernRuntime/thirdparty/concurrentqueue']
  result=subprocess.run(['c++','-std=c++20','-O1','-pthread',*['-I'+str(ROOT/i)for i in includes],'-I/home/linuxbrew/.linuxbrew/include/SDL2',str(p/'test.cpp'),str(ROOT/'src/runtime/game_settings_menu.cpp'),'-o',str(cls.binary)],capture_output=True,text=True)
  if result.returncode:raise RuntimeError(result.stderr)
 def run_case(self,name):
  result=subprocess.run([str(self.binary),name],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
 def test_alt_enter_consumes_entire_chord_and_preserves_other_options(self):self.run_case('toggle')
 def test_keypad_enter_and_right_alt_are_supported(self):self.run_case('keypad')
 def test_shortcut_updates_only_fullscreen_in_live_draft_and_cancel_baseline(self):self.run_case('draft')
 def test_explicit_save_keeps_shortcut_and_pending_edits(self):self.run_case('save')
if __name__=='__main__':unittest.main()
