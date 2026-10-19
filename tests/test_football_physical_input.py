"""Real SDL positions and genuine production get_input sampling. Work by djultra64.
Virtual controllers only: no window, game, OS input injection, or audio device.
"""
from pathlib import Path
import os,shlex,shutil,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
SDL_CONFIG=os.environ.get('ISS2000_SDL_CONFIG',shutil.which('sdl2-config') or '/home/linuxbrew/.linuxbrew/bin/sdl2-config')
def function(source,marker):
 start=source.index(marker);opening=source.index('{',start);end=opening+1;depth=1
 while depth:
  depth+=(source[end]=='{')-(source[end]=='}');end+=1
 return source[start:end]
CODE=r'''#include "platform.hpp"
#include "runtime/football_controller_editor.hpp"
#include "runtime/main_exit_menu.hpp"
#include <atomic>
#include <algorithm>
#include <cassert>
#include <iostream>
#include <mutex>
#include <stdexcept>
using namespace iss2000;
namespace iss2000::platform {
PORT
std::array<Port,4> ports;std::mutex input_mutex;std::atomic<bool> controls_menu_release{false};
struct FakeMenu{bool showing=false;bool active()const{return showing;}} controls,settings;
FakeMenu& game_controls_menu(){return controls;}FakeMenu& game_settings_menu(){return settings;}
SAMPLE
GET
PHYSICAL
SI
}
using namespace iss2000::platform;
void require(bool b,const char*m){if(!b)throw std::runtime_error(m);}
std::array<Uint8,SDL_NUM_SCANCODES> keyboard{};
std::array<int,4> devices{};
void poll(unsigned p,bool focus=true){SDL_GameControllerUpdate();ports[p].football_physical=sample_football_physical(ports[p],keyboard.data(),focus);}
void button(unsigned p,SDL_GameControllerButton b,bool held){require(SDL_JoystickSetVirtualButton(SDL_GameControllerGetJoystick(ports[p].controller),int(b),held)==0,"virtualbutton");}
void axis(unsigned p,SDL_GameControllerAxis a,int16_t v){require(SDL_JoystickSetVirtualAxis(SDL_GameControllerGetJoystick(ports[p].controller),int(a),v)==0,"virtualaxis");}
FootballSiInput sample(unsigned p){uint16_t b=0;float x=0,y=0;require(get_input(int(p),&b,&x,&y),"get_input rejectedconnectedport");return football_si_input(p);}
void setup(){
 require(SDL_Init(SDL_INIT_GAMECONTROLLER|SDL_INIT_EVENTS)==0,"SDL_Init");
 for(unsigned p=0;p<4;++p){devices[p]=SDL_JoystickAttachVirtual(SDL_JOYSTICK_TYPE_GAMECONTROLLER,SDL_CONTROLLER_AXIS_MAX,SDL_CONTROLLER_BUTTON_MAX,0);require(devices[p]>=0,"attach");ports[p].controller=SDL_GameControllerOpen(devices[p]);require(ports[p].controller,"open");ports[p].connected=true;
  axis(p,SDL_CONTROLLER_AXIS_TRIGGERLEFT,-32768);axis(p,SDL_CONTROLLER_AXIS_TRIGGERRIGHT,-32768);poll(p);
 }
}
void cleanup(){for(int p=3;p>=0;--p){if(ports[p].controller)SDL_GameControllerClose(ports[p].controller);ports[p].controller=nullptr;if(SDL_JoystickIsVirtual(devices[p]))SDL_JoystickDetachVirtual(devices[p]);}SDL_Quit();}
int main(int,char**argv){try{setup();const std::string mode=argv[1];
 if(mode=="positions"){
  const SDL_GameControllerButton face[]{SDL_CONTROLLER_BUTTON_A,SDL_CONTROLLER_BUTTON_B,SDL_CONTROLLER_BUTTON_X,SDL_CONTROLLER_BUTTON_Y,SDL_CONTROLLER_BUTTON_LEFTSHOULDER,SDL_CONTROLLER_BUTTON_RIGHTSHOULDER};
  for(unsigned f=0;f<6;++f){button(2,face[f],true);poll(2);auto v=football_physical_input(2);require(v.gamepad&&v.held==(1u<<f)&&!v.cancel,"positionmappingorEastcancelwrong");require(football_physical_input(1).held==0,"portleak");button(2,face[f],false);poll(2);}
  axis(2,SDL_CONTROLLER_AXIS_TRIGGERLEFT,-12767);poll(2);require(SDL_GameControllerGetAxis(ports[2].controller,SDL_CONTROLLER_AXIS_TRIGGERLEFT)==10000,"thresholdfixture");require(football_physical_input(2).held==0,"thresholdnotstrict");
  axis(2,SDL_CONTROLLER_AXIS_TRIGGERLEFT,-12765);poll(2);require(SDL_GameControllerGetAxis(ports[2].controller,SDL_CONTROLLER_AXIS_TRIGGERLEFT)==10001,"thresholdfixture");require(football_physical_input(2).held==physical_control_mask(PhysicalControl::L2),"lefttriggernotphysicalL2");
  axis(2,SDL_CONTROLLER_AXIS_TRIGGERRIGHT,32767);poll(2);require(football_physical_input(2).held==0xc0,"righttriggernotphysicalR2");
  ports[2].manual=Family::Nintendo;ports[2].bindings.fill(SDL_CONTROLLER_BUTTON_INVALID);poll(2);require(football_physical_input(2).held==0xc0,"familyorrawremapchangedpositions");
 }else if(mode=="timing"){
  auto before=football_si_input(3);button(3,SDL_CONTROLLER_BUTTON_A,true);poll(3);poll(3);require(football_si_input(3)==before,"polladvancedSIsample");
  ports[3].buttons=0xa123;ports[3].x=.25f;ports[3].y=-.75f;uint16_t raw=0;float x=0,y=0;require(get_input(3,&raw,&x,&y)&&raw==0xa123&&x==.25f&&y==-.75f,"footballchangedrawmenupacket");auto a=football_si_input(3);require(a.sequence==1&&a.held==1&&a.pressed==1&&a.gamepad,"firstSIedgewrong");
  require(football_si_input(3)==a&&football_si_input(3)==a,"getterconsumededge");auto b=sample(3);require(b.sequence==2&&b.held==1&&b.pressed==0,"repeatedSIaccumulatededge");
  button(3,SDL_CONTROLLER_BUTTON_A,false);poll(3);auto c=sample(3);require(c.sequence==3&&!c.held&&!c.pressed&&c.gamepad,"releasewrong");
  button(3,SDL_CONTROLLER_BUTTON_X,true);poll(3);button(3,SDL_CONTROLLER_BUTTON_X,false);poll(3);auto d=sample(3);require(d.sequence==4&&!d.held&&!d.pressed,"betweenSIpressaccumulated");
  button(3,SDL_CONTROLLER_BUTTON_A,true);poll(3);auto e=sample(3);require(e.pressed==1&&e.sequence==5,"represslost");
  for(unsigned p=0;p<3;++p)require(football_si_input(p).sequence==0,"otherportSIadvanced");require(football_si_input(4)==FootballSiInput{}&&football_physical_input(100)==FootballPhysicalInput{},"invalidgetter");
 }else if(mode=="suppression"){
  button(0,SDL_CONTROLLER_BUTTON_B,true);poll(0);require(sample(0).pressed==2,"initialedge");controls.showing=true;
  uint16_t raw=9;float x=1,y=1;require(get_input(0,&raw,&x,&y)&&raw==0&&x==0&&y==0,"oldmenusuppresschanged");auto s=football_si_input(0);require(!s.gamepad&&!s.held&&!s.pressed&&s.sequence==2,"oldmenudidnotsuppressSI");
  controls.showing=false;controls_menu_release=false;require(sample(0).pressed==2,"suppressiondidnotresetprevious");settings.showing=true;sample(0);require(!football_si_input(0).gamepad,"settingsSIleak");settings.showing=false;controls_menu_release=false;
  ports[0].keyboard=true;poll(0);require(!sample(0).gamepad&&!football_si_input(0).held,"keyboardprojectedfootball");ports[0].keyboard=false;poll(0);require(sample(0).pressed==2,"keyboardresetlost");
  poll(0,false);require(football_physical_input(0)==FootballPhysicalInput{}&&!sample(0).gamepad,"focuslossexposedphysical");poll(0);require(sample(0).pressed==2,"focusresetlost");
  ports[0].connected=false;poll(0);raw=9;require(!get_input(0,&raw,&x,&y),"disconnectchangedreturn");require(!football_si_input(0).gamepad&&!football_si_input(0).held&&!football_si_input(0).pressed,"disconnectleftstaleSI");
  ports[0].connected=true;poll(0);require(sample(0).pressed==2,"reconnectlostedge");auto seq=football_si_input(0).sequence;require(!get_input(-1,&raw,&x,&y)&&!get_input(4,&raw,&x,&y)&&football_si_input(0).sequence==seq,"invalidportmutatedsample");
 }else if(mode=="navigation"){
  button(1,SDL_CONTROLLER_BUTTON_B,true);button(1,SDL_CONTROLLER_BUTTON_START,true);button(1,SDL_CONTROLLER_BUTTON_DPAD_UP,true);poll(1);auto s=football_physical_input(1);require(s.held==2&&s.start&&s.up&&!s.cancel&&!s.down,"gamepadnavigationorassignableBwrong");
  keyboard[SDL_SCANCODE_ESCAPE]=keyboard[SDL_SCANCODE_RETURN]=keyboard[SDL_SCANCODE_DOWN]=1;ports[0].keyboard=true;poll(0);auto k=football_physical_input(0);require(!k.gamepad&&!k.held&&k.cancel&&k.start&&k.down&&!k.up,"keyboardnavigationwrong");
  poll(1);require(football_physical_input(1).cancel,"EscapecannotcancelP2editor");poll(1,false);require(football_physical_input(1)==FootballPhysicalInput{},"unfocusedkeyboardleak");
 }else return 2;
 cleanup();return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';cleanup();return 1;}}
'''
class FootballPhysicalTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if not shutil.which('c++')or not Path(SDL_CONFIG).is_file():raise unittest.SkipTest('C++/SDL2 required')
  cls.temp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.temp.cleanup);d=Path(cls.temp.name)
  source=(ROOT/'src/platform.cpp').read_text()
  code=CODE.replace('PORT',function(source,'struct Port {')+';').replace('SAMPLE',function(source,'FootballPhysicalInput sample_football_physical(')).replace('GET',function(source,'bool get_input(')).replace('PHYSICAL',function(source,'FootballPhysicalInput football_physical_input(')).replace('\nSI\n','\n'+function(source,'FootballSiInput football_si_input(')+'\n')
  (d/'test.cpp').write_text(code);cls.binary=d/'test'
  includes=['src','.local/deps/N64Recomp/include','.local/deps/N64ModernRuntime/librecomp/include','.local/deps/N64ModernRuntime/ultramodern/include','.local/deps/N64ModernRuntime/thirdparty','.local/deps/N64ModernRuntime/thirdparty/concurrentqueue']
  flags=shlex.split(subprocess.check_output([SDL_CONFIG,'--cflags','--libs'],text=True))
  cmd=['c++','-std=c++20','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-pthread',*['-I'+str(ROOT/p)for p in includes],str(d/'test.cpp'),'-o',str(cls.binary),*flags]
  p=subprocess.run(cmd,capture_output=True,text=True)
  if p.returncode:raise RuntimeError(p.stderr)
 def case(self,name):
  p=subprocess.run([str(self.binary),name],capture_output=True,text=True,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),timeout=10);self.assertEqual(p.returncode,0,p.stderr)
 def test_physical_positions_and_real_trigger_threshold_are_independent_of_family_and_raw_remap(self):self.case('positions')
 def test_only_genuine_get_input_advances_nonconsuming_per_port_SI_edges(self):self.case('timing')
 def test_keyboard_focus_disconnect_and_old_menu_suppression_reset_SI_edges(self):self.case('suppression')
 def test_Start_Dpad_and_keyboard_navigation_keep_East_assignable(self):self.case('navigation')

class FootballEscapeTests(unittest.TestCase):
 def test_actual_Escape_handler_cancels_Free_instead_of_quitting_without_changing_ordinary_Escape(self):
  source=(ROOT/'src/platform.cpp').read_text()
  block=function(source,'if(key==SDL_SCANCODE_ESCAPE)')
  code=r'''#define SDL_MAIN_HANDLED
#include <SDL.h>
#include "runtime/football_controller_editor.hpp"
#include "runtime/main_exit_menu.hpp"
#include <atomic>
#include <cassert>
using namespace iss2000;
unsigned stopped=0,quits=0;
namespace ultramodern{void quit(){++quits;}}
void stop_motors(){++stopped;}
enum class ControlsMenuCommand{None,Cancel};
struct Frame{bool escape=false;ControlsMenuCommand keyboard_command=ControlsMenuCommand::None;}menu_frame;
std::atomic<bool>controls_menu_release=false;
void event(bool menu_visible){
 bool exit_escape=false;
 const bool football_free=football_controller_editor().snapshot().editing_free;
 const auto key=SDL_SCANCODE_ESCAPE;
 BLOCK
 assert(!exit_escape);
}
int main(){
 auto&e=football_controller_editor();std::array<FootballPortConfig,4>initial{};initial[2].scheme=ControllerScheme::Free;
 assert(e.begin(initial,2)&&e.open_free());e.input({});event(false);
 assert(quits==0&&stopped==0&&!menu_frame.escape&&e.snapshot().editing_free);
 FootballEditorInput cancel;cancel.cancel=true;assert(e.input(cancel)&&!e.snapshot().editing_free);
 event(false);assert(quits==1&&stopped==1);event(true);assert(menu_frame.escape&&menu_frame.keyboard_command==ControlsMenuCommand::Cancel&&quits==1);
 controls_menu_release=true;event(false);assert(quits==1);e.end();
}
'''.replace('BLOCK',block)
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);(p/'test.cpp').write_text(code);binary=p/'test'
   cflags=shlex.split(subprocess.check_output([SDL_CONFIG,'--cflags'],text=True))
   result=subprocess.run(['c++','-std=c++20','-Wall','-Wextra','-Werror','-pthread','-I'+str(ROOT/'src'),*cflags,str(p/'test.cpp'),str(ROOT/'src/runtime/football_controller_editor.cpp'),str(ROOT/'src/runtime/controller_schemes.cpp'),'-o',str(binary)],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
   result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=10);self.assertEqual(result.returncode,0,result.stderr)

class FootballPublicLinkTests(unittest.TestCase):
 def test_public_getters_link_from_real_platform_translation_unit(self):
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);source=p/'caller.cpp';source.write_text(r'''#include "platform.hpp"
#include <cassert>
int main(){using namespace iss2000::platform;for(unsigned p=0;p<5;++p){assert(football_physical_input(p)==FootballPhysicalInput{});assert(football_si_input(p)==FootballSiInput{});}}
''')
   includes=['src','.local/deps/N64Recomp/include','.local/deps/N64ModernRuntime/librecomp/include','.local/deps/N64ModernRuntime/ultramodern/include','.local/deps/N64ModernRuntime/thirdparty','.local/deps/N64ModernRuntime/thirdparty/concurrentqueue']
   cflags=shlex.split(subprocess.check_output([SDL_CONFIG,'--cflags'],text=True))
   binary=p/'probe';command=['c++','-std=c++20','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-pthread',*['-I'+str(ROOT/i)for i in includes],*cflags,str(source),str(ROOT/'src/platform.cpp'),'-o',str(binary)]
   result=subprocess.run(command,capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
   result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=10);self.assertEqual(result.returncode,0,result.stderr)

if __name__=='__main__':unittest.main()
