"""Execute production input-activity observation with isolated SDL devices.
Original project work: djultra64. No game, window or OS input injection.
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
SDL_CONFIG=os.environ.get('ISS2000_SDL_CONFIG',shutil.which('sdl2-config') or '/home/linuxbrew/.linuxbrew/bin/sdl2-config')
def function(source,marker):
 start=source.index(marker);opening=source.index('{',start);depth=1;end=opening+1
 while depth:
  depth+=(source[end]=='{')-(source[end]=='}');end+=1
 return source[start:end]
class ActiveInputPortTests(unittest.TestCase):
 def test_real_device_ids_event_order_keyboard_noise_and_disconnect(self):
  if not shutil.which('c++') or not Path(SDL_CONFIG).is_file():self.skipTest('C++ and pinned SDL2 required')
  source=(ROOT/'src/platform.cpp').read_text()
  self.assertTrue('void observe_prompt_input(' in source,'Production input activity observer is missing')
  self.assertIn('observe_prompt_input(event);',function(source,'void update('))
  header=(ROOT/'src/platform.hpp').read_text();action=re.search(r'enum class Action \{[^}]+\};',header).group()
  keys=re.search(r'constexpr std::array<SDL_Scancode,[^;]+;',source).group()
  code=r'''#define SDL_MAIN_HANDLED
#include <SDL.h>
#include <array>
#include <algorithm>
#include <cassert>
#include <cmath>
#include <mutex>
struct Port{SDL_GameController* controller{};bool keyboard{};};
std::array<Port,4> ports;unsigned active_prompt_port{};std::mutex input_mutex;
ACTION
KEYS
OBSERVER
GETTER
int main(){
 assert(SDL_Init(SDL_INIT_GAMECONTROLLER|SDL_INIT_EVENTS)==0);
 std::array<int,4> devices;std::array<SDL_JoystickID,4> ids;
 for(unsigned n=0;n<4;++n){devices[n]=SDL_JoystickAttachVirtual(SDL_JOYSTICK_TYPE_GAMECONTROLLER,SDL_CONTROLLER_AXIS_MAX,SDL_CONTROLLER_BUTTON_MAX,0);assert(devices[n]>=0);ports[n].controller=SDL_GameControllerOpen(devices[n]);assert(ports[n].controller);ids[n]=SDL_JoystickInstanceID(SDL_GameControllerGetJoystick(ports[n].controller));}
 auto button=[&](unsigned n){SDL_Event e{};e.type=SDL_CONTROLLERBUTTONDOWN;e.cbutton.which=ids[n];e.cbutton.button=SDL_CONTROLLER_BUTTON_A;observe_prompt_input(e);};
 auto axis=[&](unsigned n,SDL_GameControllerAxis a,int16_t value){SDL_Event e{};e.type=SDL_CONTROLLERAXISMOTION;e.caxis.which=ids[n];e.caxis.axis=a;e.caxis.value=value;observe_prompt_input(e);};
 auto key=[&](SDL_Scancode scan,bool repeat=false){SDL_Event e{};e.type=SDL_KEYDOWN;e.key.keysym.scancode=scan;e.key.repeat=repeat;observe_prompt_input(e);};
 assert(active_input_port()==0);button(3);assert(active_input_port()==3&&!ports[3].keyboard);
 SDL_Event unrelated{};unrelated.type=SDL_CONTROLLERBUTTONDOWN;unrelated.cbutton.which=ids[3]+1000;observe_prompt_input(unrelated);assert(active_input_port()==3);
 axis(1,SDL_CONTROLLER_AXIS_LEFTX,12000);assert(active_input_port()==3);
 axis(1,SDL_CONTROLLER_AXIS_LEFTX,12001);assert(active_input_port()==1);
 axis(2,SDL_CONTROLLER_AXIS_RIGHTY,-12001);assert(active_input_port()==2);
 axis(1,SDL_CONTROLLER_AXIS_TRIGGERLEFT,-32768);assert(active_input_port()==2);
 axis(0,SDL_CONTROLLER_AXIS_TRIGGERRIGHT,12001);assert(active_input_port()==0);
 button(3);key(SDL_SCANCODE_F12);assert(active_input_port()==3);
 key(SDL_SCANCODE_RETURN,true);assert(active_input_port()==3);
 key(SDL_SCANCODE_RETURN);assert(active_input_port()==0&&ports[0].keyboard);
 button(2);key(SDL_SCANCODE_LEFT);assert(active_input_port()==0&&ports[0].keyboard);
 button(2);SDL_Event removed{};removed.type=SDL_CONTROLLERDEVICEREMOVED;removed.cdevice.which=ids[1];observe_prompt_input(removed);assert(active_input_port()==2);
 removed.cdevice.which=ids[2];observe_prompt_input(removed);assert(active_input_port()==0);
 button(3);assert(active_input_port()==3);assert(SDL_JoystickDetachVirtual(devices[3])==0);assert(active_input_port()==0);
 SDL_GameControllerClose(ports[3].controller);ports[3].controller=nullptr;
 for(int n=2;n>=0;--n){SDL_GameControllerClose(ports[n].controller);ports[n].controller=nullptr;assert(SDL_JoystickDetachVirtual(devices[n])==0);}
 SDL_Quit();
}
'''.replace('ACTION',action).replace('KEYS',keys).replace('OBSERVER',function(source,'void observe_prompt_input(')).replace('GETTER',function(source,'unsigned active_input_port('))
  flags=shlex.split(subprocess.check_output([SDL_CONFIG,'--cflags','--libs'],text=True))
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'probe.cpp';path.write_text(code);binary=Path(d)/'probe'
   result=subprocess.run(['c++','-std=c++20','-O1','-Wall','-Wextra','-Werror',str(path),'-o',str(binary),*flags],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
   env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
   result=subprocess.run([str(binary)],capture_output=True,text=True,env=env,timeout=10)
   self.assertEqual(result.returncode,0,result.stderr)
