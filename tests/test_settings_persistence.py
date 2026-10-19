"""PC Settings publishes both files or preserves exact original bytes. Work by djultra64."""
from pathlib import Path
import subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]

def function(source,marker):
 start=source.index(marker);opening=source.index('{',start);depth=1;end=opening+1
 while depth:
  depth+=(source[end]=='{')-(source[end]=='}');end+=1
 return source[start:end]

class SettingsPersistenceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.temp.cleanup);p=Path(cls.temp.name)
  platform=(ROOT/'src/platform.cpp').read_text()
  start=platform.index('            [](const GameSettingsDraft& draft){')
  callback=function(platform[start:],'[](const GameSettingsDraft& draft)')
  code=r'''#include "runtime/game_settings_menu.hpp"
#include "runtime/input_preferences.hpp"
#if __has_include("runtime/settings_persistence.hpp")
#include "runtime/settings_persistence.hpp"
#endif
#include <cassert>
#include <fstream>
#include <iostream>
#include <cerrno>
using namespace iss2000;
std::filesystem::path folder;
std::string fail_destination;
unsigned failures=0;
extern "C" int __real_rename(const char*,const char*);
extern "C" int __wrap_rename(const char* from,const char* to){
 if(failures && std::string(to)==fail_destination){--failures;errno=EIO;return -1;}
 return __real_rename(from,to);
}
namespace recomp {std::filesystem::path get_config_path(){return folder;}}
namespace iss2000::platform {
 std::array<PortPreferences,4> live{};
 std::array<PortPreferences,4> port_preferences(){return live;}
 void apply_port_preferences(const std::array<PortPreferences,4>& value){live=value;}
}
GraphicsSettings live_graphics;
void set_render_settings(const GraphicsSettings& value){live_graphics=value;}
std::string bytes(const std::filesystem::path& p){std::ifstream in(p,std::ios::binary);return {(std::istreambuf_iterator<char>(in)),{}};}
void require(bool v,const char* msg){if(!v)throw std::runtime_error(msg);}
int main(int,char**argv){try{
 folder=argv[1];std::filesystem::create_directories(folder);std::string mode=argv[2];
 InputPreferences original;original.ports[2].vibration=false;original.ports[3].manual_family=platform::Family::Nintendo;
 original.ports[1].bindings[0]=SDL_CONTROLLER_BUTTON_X;
 original.ports[3].football_scheme=ControllerScheme::Free;std::swap(original.ports[3].free_football_bindings[0],original.ports[3].free_football_bindings[5]);platform::live=original.ports;
 const bool absent=mode=="absent";
 std::string old_g="  \n"+serialize_graphics_settings(live_graphics),old_i="\n "+serialize_input_preferences(original);
 if(!absent){std::ofstream(folder/"graphics.json")<<old_g;std::ofstream(folder/"input-preferences.json")<<old_i;}
 if(mode=="malformed"){old_i="original damaged preferences";std::ofstream(folder/"input-preferences.json")<<old_i;}
 GameSettingsDraft desired;desired.graphics=live_graphics;desired.graphics.resolution=RenderResolution::P1080;desired.graphics.fullscreen=true;
 desired.families={platform::Family::PlayStation,platform::Family::Xbox,platform::Family::Automatic,platform::Family::Nintendo};
 desired.vibration={false,true,true,false};auto initial_live=platform::live;auto initial_graphics=live_graphics;
 auto save=CALLBACK;
 if(mode!="success"){fail_destination=(folder/"input-preferences.json").string();failures=1;}
 bool threw=false;try{save(desired);}catch(...){threw=true;}
 if(mode=="success"){
  auto expected=original;for(unsigned n=0;n<4;++n){expected.ports[n].vibration=desired.vibration[n];expected.ports[n].manual_family=desired.families[n];}
  require(load_graphics_settings(folder)==desired.graphics&&load_input_preferences(folder)==expected,"both saved values missing");
  require(platform::live==expected.ports&&live_graphics==desired.graphics,"live state not applied after success");
 }else{
  require(threw,"injected storage failure ignored");
  require(platform::live==initial_live&&live_graphics==initial_graphics,"failed save changed live preferences");
  if(absent)require(!std::filesystem::exists(folder/"graphics.json")&&!std::filesystem::exists(folder/"input-preferences.json"),"failed first save left partial files");
  else require(bytes(folder/"graphics.json")==old_g&&bytes(folder/"input-preferences.json")==old_i,"failed second save changed original file bytes");
 }
 for(auto& p:std::filesystem::directory_iterator(folder))require(!p.path().filename().string().starts_with(".pc-settings.transaction."),"completed rollback left staging");
 return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
'''.replace('CALLBACK',callback)
  (p/'test.cpp').write_text(code);cls.binary=p/'test';cls.folder=p
  includes=['src','.local/deps/N64Recomp/include','.local/deps/N64ModernRuntime/librecomp/include','.local/deps/N64ModernRuntime/ultramodern/include','.local/deps/N64ModernRuntime/thirdparty','.local/deps/N64ModernRuntime/thirdparty/concurrentqueue']
  command=['c++','-std=c++20','-Wall','-Wextra','-Werror','-pthread',*['-I'+str(ROOT/i)for i in includes],'-I/home/linuxbrew/.linuxbrew/include/SDL2',str(p/'test.cpp'),str(ROOT/'src/runtime/input_preferences.cpp'),str(ROOT/'src/runtime/controller_schemes.cpp'),str(ROOT/'src/runtime/graphics_settings.cpp'),str(ROOT/'src/runtime/settings_persistence.cpp'),'-Wl,--wrap=rename','-o',str(cls.binary)]
  result=subprocess.run(command,capture_output=True,text=True)
  if result.returncode:raise RuntimeError(result.stderr)
 def run_case(self,name):
  result=subprocess.run([str(self.binary),str(self.folder/name),name],capture_output=True,text=True,timeout=8)
  self.assertEqual(result.returncode,0,result.stderr)
 def test_second_publication_failure_preserves_both_exact_files_and_live_state(self):self.run_case('existing')
 def test_failed_first_save_restores_absent_files(self):self.run_case('absent')
 def test_invalid_existing_input_does_not_publish_graphics(self):self.run_case('malformed')
 def test_success_merges_fresh_remap_and_football_with_family_and_vibration(self):self.run_case('success')
if __name__=='__main__':unittest.main()
