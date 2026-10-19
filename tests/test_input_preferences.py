"""Portable action preferences: real JSON/storage roundtrips and atomic apply.
Original project work: djultra64.
"""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless((ROOT/'.local/deps/N64Recomp/include/recomp.h').exists(),'Pinned headers required')
class InputPreferencesTests(unittest.TestCase):
 def test_preferences_contract(self):
  with tempfile.TemporaryDirectory(prefix='iss2000-input-') as directory:
   folder=Path(directory);source=folder/'input.cpp';source.write_text(r'''
#include "runtime/input_preferences.hpp"
#include <fstream>
#include <iostream>
#include <stdexcept>
#ifndef _WIN32
#include <cerrno>
bool fail_input_sync=false;
extern "C" int __real_fsync(int);
extern "C" int __wrap_fsync(int fd){if(fail_input_sync){errno=EIO;return -1;}return __real_fsync(fd);}
#endif
using namespace iss2000;
namespace iss2000::platform {
std::array<PortPreferences,4> current{};unsigned applies=0;
std::array<PortPreferences,4> port_preferences(){return current;}
void apply_port_preferences(const std::array<PortPreferences,4>& p){current=p;++applies;}
}
void require(bool v){if(!v)throw std::runtime_error("Input preferences contract failed");}
template<class F>void rejects(F f){bool failed=false;try{f();}catch(const std::exception&){failed=true;}require(failed);}
int main(int,char** argv){try{
 std::filesystem::path folder=argv[1];auto p=default_input_preferences();
 require(p.ports[0].bindings[0]==SDL_CONTROLLER_BUTTON_A);
 require(platform::axis_fallback(platform::Action::CUp,SDL_CONTROLLER_BUTTON_Y));
 require(!platform::axis_fallback(platform::Action::CUp,SDL_CONTROLLER_BUTTON_DPAD_UP));
 require(platform::axis_fallback(platform::Action::Z,SDL_CONTROLLER_BUTTON_INVALID));
 require(!platform::axis_fallback(platform::Action::Z,SDL_CONTROLLER_BUTTON_DPAD_UP));
 require(platform::button_label(platform::Family::Nintendo,SDL_CONTROLLER_BUTTON_A)=="B");
 require(platform::button_label(platform::Family::PlayStation,SDL_CONTROLLER_BUTTON_LEFTSHOULDER)=="L1");
 require(platform::button_label(platform::Family::Xbox,SDL_CONTROLLER_BUTTON_PADDLE2)=="Paddle 3");
 p.ports[2].vibration=false;p.ports[2].manual_family=platform::Family::Nintendo;p.ports[2].bindings[3]=SDL_CONTROLLER_BUTTON_DPAD_RIGHT;
 save_input_preferences(folder,p);auto restored=load_input_preferences(folder);require(restored==p);
 #ifndef _WIN32
 auto changed=p;changed.ports[0].bindings[0]=SDL_CONTROLLER_BUTTON_Y;fail_input_sync=true;
 rejects([&]{save_input_preferences(folder,changed);});fail_input_sync=false;require(load_input_preferences(folder)==p);
 for(const auto& entry:std::filesystem::directory_iterator(folder))require(entry.path().filename().string().find("input-preferences.json.tmp-")==std::string::npos);
#endif
 apply_input_preferences(restored);require(platform::applies==1&&platform::current[2].bindings[3]==SDL_CONTROLLER_BUTTON_DPAD_RIGHT);
 auto invalid=p;invalid.ports[3].bindings[0]=SDL_CONTROLLER_BUTTON_MAX;
 rejects([&]{apply_input_preferences(invalid);});require(platform::applies==1);
 for(const char* text:{"{}","{\"schemaVersion\":2,\"ports\":[]}","{\"schemaVersion\":1,\"schemaVersion\":1,\"ports\":[]}"})rejects([&]{parse_input_preferences(text);});
 std::string valid=serialize_input_preferences(p);
 auto bad=nlohmann::json::parse(valid);bad["ports"][0]["buttons"][0]=-2;rejects([&]{parse_input_preferences(bad.dump());});
 bad=nlohmann::json::parse(valid);bad["ports"][0]["manualFamily"]="keyboard";rejects([&]{parse_input_preferences(bad.dump());});
 auto path=folder/"input-preferences.json";{std::ofstream file(path);file<<"original malformed input prefs";}
 rejects([&]{save_input_preferences(folder,p);});std::ifstream file(path);std::string text((std::istreambuf_iterator<char>(file)),{});require(text=="original malformed input prefs");
 std::filesystem::remove(path);auto target=folder/"external.json";{std::ofstream out(target);out<<valid;}
#ifndef _WIN32
 std::filesystem::create_symlink(target,path);rejects([&]{save_input_preferences(folder,p);});require(std::filesystem::is_symlink(path));
#endif
 return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
'''.replace('#include <fstream>','#include <fstream>\n#include "json/json.hpp"'))
   includes=['src','.local/deps/N64Recomp/include','.local/deps/N64ModernRuntime/librecomp/include','.local/deps/N64ModernRuntime/ultramodern/include','.local/deps/N64ModernRuntime/thirdparty','.local/deps/N64ModernRuntime/thirdparty/concurrentqueue']
   command=['c++','-std=c++20','-Wall','-Wextra','-Werror','-pthread',*(['-Wl,--wrap=fsync'] if sys.platform!='win32' else [])]
   for inc in includes:command+=['-I',str(ROOT/inc)]
   command+=['-I/home/linuxbrew/.linuxbrew/include/SDL2',str(source),str(ROOT/'src/runtime/input_preferences.cpp'),str(ROOT/'src/runtime/controller_schemes.cpp'),'-o',str(folder/'test')]
   result=subprocess.run(command,capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
   result=subprocess.run([str(folder/'test'),str(folder)],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
 def test_actual_platform_snapshot_apply_and_invalid_rollback(self):
  with tempfile.TemporaryDirectory(prefix='iss2000-input-apply-') as directory:
   folder=Path(directory);source=folder/'apply.cpp';source.write_text(r'''
#include "platform.hpp"
#include <algorithm>
#include <stdexcept>
// No physical controller in this CPU-only snapshot fixture.
extern "C" int SDL_GameControllerRumble(SDL_GameController*,Uint16,Uint16,Uint32){return 0;}
using namespace iss2000::platform;
void require(bool value){if(!value)throw std::runtime_error("Platform mapping contract failed");}
int main(){try{
 auto initial=port_preferences();auto edited=initial;
 edited[3].vibration=false;edited[3].manual_family=Family::Nintendo;edited[3].bindings[size_t(Action::Z)]=SDL_CONTROLLER_BUTTON_DPAD_UP;
 edited[3].football_scheme=iss2000::ControllerScheme::Free;std::rotate(edited[3].free_football_bindings.begin(),edited[3].free_football_bindings.begin()+3,edited[3].free_football_bindings.end());edited[2].football_scheme=iss2000::ControllerScheme::Type4;
 apply_port_preferences(edited);require(port_preferences()==edited);require(get_binding(3,Action::Z)==SDL_CONTROLLER_BUTTON_DPAD_UP);require(controller_family(3)==Family::Nintendo);
 auto invalid=edited;invalid[0].manual_family=Family::PlayStation;invalid[3].bindings[1]=SDL_CONTROLLER_BUTTON_MAX;
 bool failed=false;try{apply_port_preferences(invalid);}catch(const std::exception&){failed=true;}require(failed&&port_preferences()==edited);
 invalid=edited;invalid[0].vibration=false;invalid[3].football_scheme=iss2000::ControllerScheme(255);failed=false;
 try{apply_port_preferences(invalid);}catch(const std::exception&){failed=true;}require(failed&&port_preferences()==edited);
 invalid=edited;invalid[0].manual_family=Family::Xbox;invalid[3].free_football_bindings[0]=invalid[3].free_football_bindings[1];failed=false;
 try{apply_port_preferences(invalid);}catch(const std::exception&){failed=true;}require(failed&&port_preferences()==edited);
 failed=false;try{bind_button(0,Action(-1),SDL_CONTROLLER_BUTTON_A);}catch(const std::exception&){failed=true;}require(failed);
 apply_port_preferences(initial);require(port_preferences()==initial);return 0;
}catch(...){return 1;}}
''')
   includes=['src','.local/deps/N64Recomp/include','.local/deps/N64ModernRuntime/librecomp/include','.local/deps/N64ModernRuntime/ultramodern/include','.local/deps/N64ModernRuntime/thirdparty','.local/deps/N64ModernRuntime/thirdparty/concurrentqueue']
   command=['c++','-std=c++20','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-pthread']
   for inc in includes:command+=['-I',str(ROOT/inc)]
   command+=['-I/home/linuxbrew/.linuxbrew/include/SDL2',str(source),str(ROOT/'src/platform.cpp'),str(ROOT/'src/runtime/controller_schemes.cpp'),'-o',str(folder/'apply')]
   result=subprocess.run(command,capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
   result=subprocess.run([str(folder/'apply')],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
if __name__=='__main__':unittest.main()
