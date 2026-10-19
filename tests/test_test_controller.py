"""App-owned SDL virtual controller fixture; no game, window or OS input injection."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
SDL_CONFIG=os.environ.get('ISS2000_SDL_CONFIG',shutil.which('sdl2-config') or '/home/linuxbrew/.linuxbrew/bin/sdl2-config')
class TestControllerTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if not shutil.which('c++'):raise unittest.SkipTest('virtual controller checks require C++20')
  cls.temp=tempfile.TemporaryDirectory(prefix='iss2000-virtual-controller-');cls.addClassCleanup(cls.temp.cleanup)
  cls.folder=Path(cls.temp.name)
  (cls.folder/'off.cpp').write_text('''#include "runtime/test_controller.hpp"
int main(){iss2000::test_controller::initialize();iss2000::test_controller::pump();iss2000::test_controller::shutdown();return iss2000::test_controller::device_instance()==-1?0:1;}
''')
  cls.off=cls.folder/'off'
  subprocess.run(['c++','-std=c++20','-Wall','-Wextra','-Werror','-I'+str(ROOT/'src'),str(cls.folder/'off.cpp'),str(ROOT/'src/runtime/test_controller.cpp'),'-o',str(cls.off)],check=True,capture_output=True,text=True)
 def test_disabled_build_is_inert_even_when_environment_is_set(self):
  result=subprocess.run([str(self.off)],env=dict(os.environ,ISS2000_TEST_CONTROLLER='/nonexistent/snapshot'),capture_output=True)
  self.assertEqual(result.returncode,0,result.stderr)

class EnabledTestControllerTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if not Path(SDL_CONFIG).is_file() or not shutil.which('c++'):raise unittest.SkipTest('enabled virtual controller checks require SDL2 development files and C++20')
  import shlex
  cls.temp=tempfile.TemporaryDirectory(prefix='iss2000-sdl-controller-');cls.addClassCleanup(cls.temp.cleanup);cls.folder=Path(cls.temp.name)
  (cls.folder/'harness.cpp').write_text(r'''
#include "runtime/test_controller.hpp"
#include <SDL.h>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
void require(bool b){if(!b)throw std::runtime_error("SDL virtual controller assertion failed");}
int main(int,char** argv){try{
 require(SDL_Init(SDL_INIT_GAMECONTROLLER|SDL_INIT_EVENTS)==0);
 int before=SDL_NumJoysticks();iss2000::test_controller::initialize();iss2000::test_controller::initialize();
 std::string mode=argv[1];std::filesystem::path path=argv[2];
 if(mode=="relative"||mode=="unset") {require(SDL_NumJoysticks()==before);iss2000::test_controller::shutdown();SDL_Quit();return 0;}
 require(SDL_NumJoysticks()==before+1);
 int device=SDL_NumJoysticks()-1;require(iss2000::test_controller::device_instance()==SDL_JoystickGetDeviceInstanceID(device));require(SDL_JoystickIsVirtual(device));require(SDL_IsGameController(device));
 auto* controller=SDL_GameControllerOpen(device);require(controller!=nullptr);
 auto snapshot=[&](const std::string& s){std::ofstream f(path,std::ios::binary|std::ios::trunc);f<<s;f.close();iss2000::test_controller::pump();SDL_PumpEvents();};
 auto released=[&](){for(auto b:{SDL_CONTROLLER_BUTTON_X,SDL_CONTROLLER_BUTTON_Y,SDL_CONTROLLER_BUTTON_LEFTSHOULDER,SDL_CONTROLLER_BUTTON_RIGHTSHOULDER})require(!SDL_GameControllerGetButton(controller,b));for(auto a:{SDL_CONTROLLER_AXIS_TRIGGERLEFT,SDL_CONTROLLER_AXIS_TRIGGERRIGHT,SDL_CONTROLLER_AXIS_RIGHTX,SDL_CONTROLLER_AXIS_RIGHTY})require(SDL_GameControllerGetAxis(controller,a)==0);require(!SDL_GameControllerGetButton(controller,SDL_CONTROLLER_BUTTON_A));require(!SDL_GameControllerGetButton(controller,SDL_CONTROLLER_BUTTON_B));require(!SDL_GameControllerGetButton(controller,SDL_CONTROLLER_BUTTON_START));require(SDL_GameControllerGetAxis(controller,SDL_CONTROLLER_AXIS_LEFTX)==0);require(SDL_GameControllerGetAxis(controller,SDL_CONTROLLER_AXIS_LEFTY)==0);for(auto b:{SDL_CONTROLLER_BUTTON_DPAD_UP,SDL_CONTROLLER_BUTTON_DPAD_DOWN,SDL_CONTROLLER_BUTTON_DPAD_LEFT,SDL_CONTROLLER_BUTTON_DPAD_RIGHT})require(!SDL_GameControllerGetButton(controller,b));};
 if(mode=="football"){
  // The descriptor and initial neutral state must be real SDL device state,
  // including before the first file pump/controller sample.
  require(SDL_JoystickNumAxes(SDL_GameControllerGetJoystick(controller))==SDL_CONTROLLER_AXIS_MAX);
  for(int a=0;a<SDL_CONTROLLER_AXIS_MAX;++a)require(SDL_GameControllerHasAxis(controller,SDL_GameControllerAxis(a)));
  for(auto a:{SDL_CONTROLLER_AXIS_TRIGGERLEFT,SDL_CONTROLLER_AXIS_TRIGGERRIGHT}){
   require(SDL_JoystickGetAxis(SDL_GameControllerGetJoystick(controller),int(a))==-32768);
   require(SDL_GameControllerGetAxis(controller,a)==0);
  }
  snapshot("a b x y l1 r1 l2 r2");
  for(auto b:{SDL_CONTROLLER_BUTTON_A,SDL_CONTROLLER_BUTTON_B,SDL_CONTROLLER_BUTTON_X,SDL_CONTROLLER_BUTTON_Y,SDL_CONTROLLER_BUTTON_LEFTSHOULDER,SDL_CONTROLLER_BUTTON_RIGHTSHOULDER})require(SDL_GameControllerGetButton(controller,b));
  for(auto a:{SDL_CONTROLLER_AXIS_TRIGGERLEFT,SDL_CONTROLLER_AXIS_TRIGGERRIGHT})require(SDL_GameControllerGetAxis(controller,a)==32767);
  snapshot("");released();
  const char* names[]{"x","y","l1","r1"};
  const SDL_GameControllerButton buttons[]{SDL_CONTROLLER_BUTTON_X,SDL_CONTROLLER_BUTTON_Y,SDL_CONTROLLER_BUTTON_LEFTSHOULDER,SDL_CONTROLLER_BUTTON_RIGHTSHOULDER};
  for(unsigned n=0;n<4;++n){snapshot(names[n]);for(unsigned j=0;j<4;++j)require(bool(SDL_GameControllerGetButton(controller,buttons[j]))==(j==n));snapshot("");released();}
  snapshot("l2");require(SDL_GameControllerGetAxis(controller,SDL_CONTROLLER_AXIS_TRIGGERLEFT)==32767&&SDL_GameControllerGetAxis(controller,SDL_CONTROLLER_AXIS_TRIGGERRIGHT)==0);
  snapshot("r2");require(SDL_GameControllerGetAxis(controller,SDL_CONTROLLER_AXIS_TRIGGERLEFT)==0&&SDL_GameControllerGetAxis(controller,SDL_CONTROLLER_AXIS_TRIGGERRIGHT)==32767);
  snapshot("a b x y l1 r1 l2 r2 start dpad_up right");snapshot("l2 r2 x unknown");released();
  SDL_GameControllerClose(controller);iss2000::test_controller::shutdown();require(SDL_NumJoysticks()==before);SDL_Quit();return 0;
 }
 snapshot("start a b up right");require(SDL_GameControllerGetButton(controller,SDL_CONTROLLER_BUTTON_A));require(SDL_GameControllerGetButton(controller,SDL_CONTROLLER_BUTTON_B));require(SDL_GameControllerGetButton(controller,SDL_CONTROLLER_BUTTON_START));require(SDL_GameControllerGetAxis(controller,SDL_CONTROLLER_AXIS_LEFTX)==32767);require(SDL_GameControllerGetAxis(controller,SDL_CONTROLLER_AXIS_LEFTY)==-32767);
 if(mode=="dpad"){
  snapshot("dpad_up dpad_right");require(SDL_GameControllerGetButton(controller,SDL_CONTROLLER_BUTTON_DPAD_UP));require(SDL_GameControllerGetButton(controller,SDL_CONTROLLER_BUTTON_DPAD_RIGHT));require(!SDL_GameControllerGetButton(controller,SDL_CONTROLLER_BUTTON_DPAD_DOWN));require(!SDL_GameControllerGetButton(controller,SDL_CONTROLLER_BUTTON_DPAD_LEFT));require(SDL_GameControllerGetAxis(controller,SDL_CONTROLLER_AXIS_LEFTX)==0);require(SDL_GameControllerGetAxis(controller,SDL_CONTROLLER_AXIS_LEFTY)==0);require(!SDL_GameControllerGetButton(controller,SDL_CONTROLLER_BUTTON_A));
  snapshot("dpad_down dpad_left up right a");require(SDL_GameControllerGetButton(controller,SDL_CONTROLLER_BUTTON_DPAD_DOWN));require(SDL_GameControllerGetButton(controller,SDL_CONTROLLER_BUTTON_DPAD_LEFT));require(!SDL_GameControllerGetButton(controller,SDL_CONTROLLER_BUTTON_DPAD_UP));require(!SDL_GameControllerGetButton(controller,SDL_CONTROLLER_BUTTON_DPAD_RIGHT));require(SDL_GameControllerGetAxis(controller,SDL_CONTROLLER_AXIS_LEFTX)==32767);require(SDL_GameControllerGetAxis(controller,SDL_CONTROLLER_AXIS_LEFTY)==-32767);require(SDL_GameControllerGetButton(controller,SDL_CONTROLLER_BUTTON_A));
  snapshot("");released();snapshot("dpad_up dpad_down dpad_left dpad_right");for(auto b:{SDL_CONTROLLER_BUTTON_DPAD_UP,SDL_CONTROLLER_BUTTON_DPAD_DOWN,SDL_CONTROLLER_BUTTON_DPAD_LEFT,SDL_CONTROLLER_BUTTON_DPAD_RIGHT})require(SDL_GameControllerGetButton(controller,b));
  snapshot("dpad_up invalid");
 }
 else if(mode=="release")snapshot("");
 else if(mode=="boundary")snapshot(std::string(255,' '));
 else if(mode=="symlink"){std::filesystem::remove(path);std::ofstream other(path.string()+".other");other<<"a";other.close();std::filesystem::create_symlink(path.string()+".other",path);iss2000::test_controller::pump();SDL_PumpEvents();}
 else if(mode=="invalid")snapshot("a quit");
 else if(mode=="oversized")snapshot(std::string(256,' ')+"a");
 else if(mode=="missing"){std::filesystem::remove(path);iss2000::test_controller::pump();SDL_PumpEvents();}
 else if(mode=="opposites")snapshot("up down left right");
 else if(mode=="directory"){std::filesystem::remove(path);std::filesystem::create_directory(path);iss2000::test_controller::pump();SDL_PumpEvents();}
 else if(mode=="negative"){snapshot("down left");require(SDL_GameControllerGetAxis(controller,SDL_CONTROLLER_AXIS_LEFTX)==-32767);require(SDL_GameControllerGetAxis(controller,SDL_CONTROLLER_AXIS_LEFTY)==32767);snapshot("");}
 else return 2;
 released();require(SDL_NumJoysticks()==before+1);
 SDL_GameControllerClose(controller);iss2000::test_controller::shutdown();iss2000::test_controller::shutdown();require(SDL_NumJoysticks()==before);require(iss2000::test_controller::device_instance()==-1);SDL_Quit();
}catch(const std::exception& e){std::cerr<<e.what()<<":"<<SDL_GetError();return 1;}}
''')
  flags=shlex.split(subprocess.check_output([SDL_CONFIG,'--cflags','--libs'],text=True))
  cls.binary=cls.folder/'enabled'
  command=['c++','-std=c++20','-Wall','-Wextra','-Werror','-DISS2000_ENABLE_INPUT_TESTING','-I'+str(ROOT/'src'),str(cls.folder/'harness.cpp'),str(ROOT/'src/runtime/test_controller.cpp'),'-o',str(cls.binary)]+flags
  subprocess.run(command,check=True,capture_output=True,text=True)
 def run_case(self,mode):
  with tempfile.TemporaryDirectory(prefix='iss2000-controller-snapshot-') as folder:
   path=Path(folder)/'snapshot';env=dict(os.environ,ISS2000_TEST_CONTROLLER=str(path),SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
   if mode=='unset':env.pop('ISS2000_TEST_CONTROLLER')
   if mode=='relative':env['ISS2000_TEST_CONTROLLER']='relative-snapshot'
   r=subprocess.run([str(self.binary),mode,str(path)],env=env,capture_output=True,text=True,timeout=10)
   self.assertEqual(r.returncode,0,r.stderr)
   if mode=='boundary':self.assertNotIn('controls released',r.stderr)
   if mode=='invalid':self.assertIn('invalid snapshot token',r.stderr)
 def test_all_eight_physical_positions_and_real_trigger_rest_full_and_invalid_release(self):self.run_case('football')
 def test_explicit_dpad_buttons_are_independent_of_analog_and_release_atomically(self):self.run_case('dpad')
 def test_release_snapshot(self):self.run_case('release')
 def test_255_byte_boundary_is_accepted(self):self.run_case('boundary')
 def test_symlink_snapshot_is_rejected(self):
  if os.name=='nt':self.skipTest('Windows symlinks require extra privileges')
  self.run_case('symlink')
 def test_unknown_token_releases_every_control(self):self.run_case('invalid')
 def test_bounded_snapshot_releases(self):self.run_case('oversized')
 def test_missing_snapshot_releases_and_preserves_controller(self):self.run_case('missing')
 def test_opposite_axes_cancel(self):self.run_case('opposites')
 def test_regular_file_required(self):self.run_case('directory')
 def test_negative_axes(self):self.run_case('negative')
 def test_relative_environment_path_is_rejected(self):self.run_case('relative')
 def test_no_environment_creates_no_controller(self):self.run_case('unset')
