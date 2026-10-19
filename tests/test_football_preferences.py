"""Football scheme persistence is independent of legacy menu remapping. Work by djultra64."""
from pathlib import Path
import subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
CODE=r'''#include "runtime/input_preferences.hpp"
#include "json/json.hpp"
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <algorithm>
using namespace iss2000;using Json=nlohmann::json;
namespace iss2000::platform {
 std::array<PortPreferences,4> current{};unsigned applies=0;
 std::array<PortPreferences,4> port_preferences(){return current;}
 void apply_port_preferences(const std::array<PortPreferences,4>& p){current=p;++applies;}
}
void require(bool b,const char*why){if(!b)throw std::runtime_error(why);}
template<class F>void rejects(F f){bool threw=false;try{f();}catch(...){threw=true;}require(threw,"invalid football preferences accepted");}
Json controls(){return Json::array({"south","east","west","north","l1","r1","l2","r2"});}
Json legacy(bool vibration){
 auto j=Json::parse(serialize_input_preferences(default_input_preferences()));
 for(unsigned p=0;p<4;++p){j["ports"][p].erase("footballScheme");j["ports"][p].erase("freeFootballBindings");if(!vibration)j["ports"][p].erase("vibration");}
 return j;
}
Json configured(){auto j=legacy(true);for(unsigned p=0;p<4;++p){j["ports"][p]["footballScheme"]="type"+std::to_string(p+1);auto b=controls();std::rotate(b.begin(),b.begin()+p,b.end());j["ports"][p]["freeFootballBindings"]=b;}
 j["ports"][2]["manualFamily"]="switch";j["ports"][2]["vibration"]=false;j["ports"][1]["buttons"][0]=SDL_CONTROLLER_BUTTON_X;return j;
}
std::string bytes(const std::filesystem::path&p){std::ifstream in(p);return {(std::istreambuf_iterator<char>(in)),{}};}
int main(int,char**argv){try{
 const std::string mode=argv[1];std::filesystem::path folder=argv[2];std::filesystem::create_directories(folder);
 if(mode=="legacy"){
  for(bool v:{false,true}){auto old=legacy(v);auto value=parse_input_preferences(old.dump());auto normalized=Json::parse(serialize_input_preferences(value));
   for(unsigned p=0;p<4;++p){require(normalized["ports"][p].at("footballScheme")=="type1","legacy did not selectType1");require(normalized["ports"][p].at("freeFootballBindings").size()==8,"legacy default free map missing");require(value.ports[p].football_scheme==ControllerScheme::Type1&&value.ports[p].free_football_bindings==default_football_bindings,"legacy Type1/Free default matrix changed");require(normalized["ports"][p]["buttons"]==old["ports"][p]["buttons"],"legacy raw menu controls mutated");require(normalized["ports"][p]["vibration"]==true,"legacy vibration default changed");}
  }
 }else if(mode=="roundtrip"){
  for(auto scheme:{"type1","type2","type3","type4","type5","free"}){auto j=configured();j["ports"][3]["footballScheme"]=scheme;auto p=parse_input_preferences(j.dump());auto out=Json::parse(serialize_input_preferences(p));require(out==j,"scheme/custom map/rawmenu/family/vibration roundtrip differs");apply_input_preferences(p);require(capture_input_preferences()==p,"apply/capture dropped fields");}
 }else if(mode=="reject"){
  auto original=configured();auto good=parse_input_preferences(original.dump());apply_input_preferences(good);const auto live=capture_input_preferences();const auto applied=platform::applies;
  for(unsigned n=0;n<11;++n){auto j=original;auto&p=j["ports"][3];
   if(n==0)p.erase("footballScheme");if(n==1)p.erase("freeFootballBindings");if(n==2)p["footballScheme"]="modern";
   if(n==3)p["footballScheme"]=1;if(n==4)p["freeFootballBindings"][0]="east";if(n==5)p["freeFootballBindings"][0]="a";
   if(n==6)p["freeFootballBindings"][0]=0;if(n==7)p["freeFootballBindings"].erase(0);if(n==8)p["freeFootballBindings"].push_back("south");
   if(n==9)p["unknown"]=true;if(n==10)p["freeFootballBindings"]=Json::object();
   rejects([&]{apply_input_preferences(parse_input_preferences(j.dump()));});require(capture_input_preferences()==live&&platform::applies==applied,"invalidport partially changed live otherports");
  }
  std::string duplicate=original.dump();auto at=duplicate.find("\"footballScheme\":");require(at!=std::string::npos,"missingfield");duplicate.insert(at,"\"footballScheme\":\"type1\",");rejects([&]{parse_input_preferences(duplicate);});
 }else if(mode=="storage"){
  auto j=configured();auto p=parse_input_preferences(j.dump());save_input_preferences(folder,p);const auto before=bytes(folder/"input-preferences.json");require(load_input_preferences(folder)==p,"storage roundtrip lost football map");
  auto bad=j;bad["ports"][0]["freeFootballBindings"][1]="south";rejects([&]{save_input_preferences(folder,parse_input_preferences(bad.dump()));});require(bytes(folder/"input-preferences.json")==before,"invalid save changed original bytes");
  auto changed=p;changed.ports[0].vibration=false;save_input_preferences(folder,changed);require(load_input_preferences(folder)==changed,"vibration merge lost football fields");
 }else if(mode=="partial-vibration"){
  auto j=configured();for(auto&p:j["ports"])p.erase("vibration");auto out=Json::parse(serialize_input_preferences(parse_input_preferences(j.dump())));for(unsigned p=0;p<4;++p){require(out["ports"][p]["vibration"]==true,"new fields require unrelated vibration migration");out["ports"][p].erase("vibration");}require(out==j,"optional vibration changednewfields");
 }else return 2;
 return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
'''
class FootballPreferencesTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.tmp.cleanup);cls.folder=Path(cls.tmp.name);(cls.folder/'test.cpp').write_text(CODE);cls.binary=cls.folder/'test'
  inc=['src','.local/deps/N64Recomp/include','.local/deps/N64ModernRuntime/librecomp/include','.local/deps/N64ModernRuntime/ultramodern/include','.local/deps/N64ModernRuntime/thirdparty','.local/deps/N64ModernRuntime/thirdparty/concurrentqueue']
  sources=[ROOT/'src/runtime/input_preferences.cpp'];module=ROOT/'src/runtime/controller_schemes.cpp'
  if module.is_file():sources.append(module)
  q=subprocess.run(['c++','-std=c++20','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-pthread',*['-I'+str(ROOT/a)for a in inc],'-I/home/linuxbrew/.linuxbrew/include/SDL2',str(cls.folder/'test.cpp'),*map(str,sources),'-o',str(cls.binary)],capture_output=True,text=True)
  if q.returncode:raise RuntimeError(q.stderr)
 def run_case(self,name):
  q=subprocess.run([str(self.binary),name,str(self.folder/name)],capture_output=True,text=True,timeout=8);self.assertEqual(q.returncode,0,q.stderr)
 def test_legacy_two_and_three_key_ports_preserve_raw_controls_and_default_type1(self):self.run_case('legacy')
 def test_all_six_schemes_custom_maps_family_vibration_and_four_ports_roundtrip(self):self.run_case('roundtrip')
 def test_incomplete_duplicate_foreign_fields_reject_without_live_mutation(self):self.run_case('reject')
 def test_atomic_storage_and_unrelated_vibration_save_preserve_football_fields(self):self.run_case('storage')
 def test_new_complete_pair_allows_legacy_missing_vibration(self):self.run_case('partial-vibration')
if __name__=='__main__':unittest.main()
