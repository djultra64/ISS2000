"""Original full controller CPU stages, never a game session. Work by djultra64."""
from pathlib import Path
import hashlib,json,re,shutil,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
def function(s,marker):
 a=s.index(marker);b=s.index('{',a);end=b+1;depth=1
 while depth:depth+=(s[end]=='{')-(s[end]=='}');end+=1
 return s[a:end]
CODE=r'''#include "pal_football_input.hpp"
#include <array>
#include <cassert>
#include <cstring>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>
using namespace iss2000;
DECLS
unsigned si_reads=0,conversions=0,normalizations=0,raw_consumers=0;uint16_t observed_raw=0;
bool legacy=false,baseline=false;unsigned selected_port=0;uint16_t held=0,pressed=0;bool gamepad=true;
namespace platform {
struct Input{uint16_t held,pressed;uint64_t sequence;bool gamepad;};
struct Config{ControllerScheme football_scheme=ControllerScheme::Type5;FootballBindings free_football_bindings=default_football_bindings;};
Input football_si_input(unsigned p){assert(p==selected_port);++si_reads;return {::held,::pressed,1,::gamepad};}
std::array<Config,4>port_preferences(){return {};}
}
bool observed_apply(std::span<uint8_t>r,recomp_context&c,uint16_t h,uint16_t p,const FootballBindings&b,recomp_func_t*f){const bool applied=apply_pal_football_input(r,c,h,p,b,f);conversions+=applied;return applied;}
#define apply_pal_football_input observed_apply
WRAPPERS
#undef apply_pal_football_input
uint16_t half(uint8_t*r,uint32_t p){uint16_t v;memcpy(&v,r+((p&0x7fffff)^2),2);return v;}
uint32_t word(uint8_t*r,uint32_t p){uint32_t v;memcpy(&v,r+(p&0x7fffff),4);return v;}
void sw(uint8_t*r,uint32_t p,uint32_t v){memcpy(r+(p&0x7fffff),&v,4);}void sh(uint8_t*r,uint32_t p,uint16_t v){memcpy(r+((p&0x7fffff)^2),&v,2);}
void raw_consumer(uint8_t*r,recomp_context*c){++raw_consumers;observed_raw=half(r,word(r,uint32_t(c->r4)+0x24)+2);func_801D4B4C_overlay_25aaf0_801ad820(r,c);}
extern "C" recomp_func_t*get_function(int32_t a){
 if(uint32_t(a)==0x801d4880){++normalizations;return baseline?func_801D4880_overlay_25aaf0_801ad820:normalize_football_controller;}
 if(uint32_t(a)==0x801d4cc0)return baseline||legacy?func_801D4CC0_overlay_25aaf0_801ad820:process_special_football_controller;
 if(uint32_t(a)==0x801d4b4c)return raw_consumer;
 switch(uint32_t(a)){LOOKUP default:std::cerr<<"Uncovered original "<<std::hex<<uint32_t(a)<<'\n';throw std::runtime_error("uncovered original CPU branch");}}
extern "C"void do_break(uint32_t){throw std::runtime_error("original break");}
extern "C"void switch_error(const char*,uint32_t,uint32_t){throw std::runtime_error("original switch");}
void require(bool b,const char*m){if(!b)throw std::runtime_error(m);}
int main(int,char**argv){try{
 std::ifstream in(argv[1],std::ios::binary);std::vector<uint8_t>base((std::istreambuf_iterator<char>(in)),{});require(base.size()==0x800000,"fixture size");const std::string mode=argv[2];
 const auto entry=mode=="aux"?process_auxiliary_football_controller:mode=="special"?process_special_football_controller:process_football_controller;
 const auto original=mode=="aux"?func_801D5E1C_overlay_25aaf0_801ad820:mode=="special"?func_801D4CC0_overlay_25aaf0_801ad820:func_801D5A74_overlay_25aaf0_801ad820;
 if(mode=="legacy")legacy=true;
 const auto player=word(base.data(),0x801274a0);const auto actor=word(base.data(),player+0xa8);
 for(unsigned profile=0;profile<3;++profile)for(unsigned port=0;port<4;++port)for(unsigned phase=0;phase<4;++phase){
  selected_port=port;auto actual=base;const auto object=0x80127468+port*0xa8,packet=0x8013b454+port*10;
  // A valid original controlled-player object copied across port slots; its
  // real player/model/action data remain from the preserved Training capture.
  memcpy(actual.data()+(object&0x7fffff),base.data()+0x127468,0xa8);
  recomp_context setup{};setup.r4=port;setup.r5=int32_t(0x800774f0+profile*12);func_80014A74_resident(actual.data(),&setup);
  sw(actual.data(),object,word(actual.data(),object)|0x4000);
  actual[((actor+0xe01)&0x7fffff)^3]=1;
  actual[0x9dd22^3]=8;actual[0x9df78^3]=10; // exact auxiliary path, excludes an unrelated overlay callback
  held=phase==1||phase==2?physical_control_mask(PhysicalControl::R1):0;pressed=phase==1?held:0;
  const auto binding=*scheme_bindings(ControllerScheme::Type5);const auto expected_held=*football_guest_pad(binding,held,profile),expected_pressed=*football_guest_pad(binding,pressed,profile);
  sh(actual.data(),packet+2,held?0x10:0);sh(actual.data(),packet+4,pressed?0x10:0);
  auto expected=actual;sh(expected.data(),packet+2,expected_held);sh(expected.data(),packet+4,expected_pressed);
  recomp_context a{},e{};a.r4=e.r4=int32_t(object);a.r29=e.r29=int32_t(0x800a3f80);a.r31=e.r31=int32_t(0x80123450);a.f_odd=&a.f0.u32h;e.f_odd=&e.f0.u32h;
  baseline=true;normalizations=raw_consumers=0;original(expected.data(),&e);const auto baseline_normalizations=normalizations,baseline_consumers=raw_consumers;
  baseline=false;si_reads=conversions=normalizations=raw_consumers=0;
  if(legacy)original(actual.data(),&a);else entry(actual.data(),&a);
  require(raw_consumers==baseline_consumers,"special original call count changed");
  if(raw_consumers)require(observed_raw==expected_held,"post-normalizer consumer read ordinary menu packet");
  require(normalizations==baseline_normalizations,"normalizer repeated or skipped");
  if(!legacy)require(conversions==1&&si_reads==1,"nested stage converted or sampled twice");
  require(a.r29==uint64_t(int64_t(int32_t(0x800a3f80)))&&word(actual.data(),object+0x24)==packet,"scratch pointer/SP escaped");
  // Input remains original and every other port's complete object is isolated.
  sh(expected.data(),packet+2,held?0x10:0);sh(expected.data(),packet+4,pressed?0x10:0);
  for(unsigned i=0;i<actual.size();++i)if(i<0xa2f80||i>=0xa3f80)require(actual[i]==expected[i],"original full-stage RAM output diverged");
 }
 // Genuine keyboard and foreign-object paths call the ordinary CPU body once.
 auto actual=base;recomp_context c{};c.r4=int32_t(0x80127468);c.r29=int32_t(0x800a3f80);c.f_odd=&c.f0.u32h;selected_port=0;gamepad=false;conversions=0;entry(actual.data(),&c);require(conversions==0,"keyboard projected");
 gamepad=true;actual=base;const uint32_t foreign=0x80160000;memcpy(actual.data()+(foreign&0x7fffff),base.data()+0x127468,0xa8);c={};c.r4=int32_t(foreign);c.r29=int32_t(0x800a3f80);c.f_odd=&c.f0.u32h;conversions=si_reads=0;entry(actual.data(),&c);require(conversions==0&&si_reads==0,"foreign controller object projected");
 return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
'''
class FootballFullStageTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  g=ROOT/'.local/pal-map-bound-01/functions';snapshot=ROOT/'.local/training-timing-01/free-training-high43-completed.rdram';rom=ROOT/'.local/inputs/pal-en-de/rom.z64';h=ROOT/'.local/deps/N64Recomp/include'
  if not all(p.exists()for p in [g,snapshot,rom,h/'recomp.h'])or not shutil.which('c++'):raise unittest.SkipTest('Private original PAL CPU fixtures required')
  ram=snapshot.read_bytes();image=rom.read_bytes();assert hashlib.sha256(image).hexdigest()=='6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf';available={}
  for section in json.loads((g.parent/'section-analysis.json').read_text()):
   for f in section['functions']:
    pc=f['vram'];start=section['rom']+pc-section['vram'];data=image[start:start+f['size']]
    if data==bytes(ram[((pc+i)&0x7fffff)^3]for i in range(f['size'])):available[pc]=g/f"func_{pc:08X}_{section['name']}.c"
  seen=set();pending=[0x801d5a74,0x801d5e1c,0x801d5fe8,0x80014a74]
  while pending:
   pc=pending.pop()
   if pc in seen:continue
   seen.add(pc)
   if pc in available:pending.extend(int(x,16)for x in re.findall(r'LOOKUP_FUNC\(0x([0-9A-F]+)\)',available[pc].read_text()))
  paths={pc:available[pc]for pc in sorted(seen)if pc in available}
  native=(ROOT/'src/runtime/native_game.cpp').read_text();names=['run_football_controller_stage','normalize_football_controller','process_football_controller','process_auxiliary_football_controller','process_special_football_controller']
  wrappers='\n'.join(function(native,'void '+name+'(')for name in names)
  code=CODE.replace('DECLS','\n'.join('extern "C" void '+p.stem+'(uint8_t*,recomp_context*);'for p in paths.values())).replace('WRAPPERS',wrappers).replace('LOOKUP','\n'.join(f'case 0x{pc:x}:return {p.stem};'for pc,p in paths.items())).replace('extern "C"void','extern "C" void')
  cls.temp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.temp.cleanup);p=Path(cls.temp.name);(p/'test.cpp').write_text(code);(p/'original.c').write_text('\n'.join('#include '+json.dumps(str(v))for v in paths.values()));cls.binary=p/'test';cls.snapshot=snapshot
  q=subprocess.run(['cc','-O1','-fno-strict-aliasing','-I'+str(h),'-c',str(p/'original.c'),'-o',str(p/'original.o')],capture_output=True,text=True)
  if q.returncode:raise RuntimeError(q.stderr)
  q=subprocess.run(['c++','-std=c++20','-O1','-I'+str(ROOT/'src/runtime'),'-I'+str(h),str(p/'test.cpp'),str(ROOT/'src/runtime/pal_football_input.cpp'),str(ROOT/'src/runtime/controller_schemes.cpp'),str(p/'original.o'),'-o',str(cls.binary)],capture_output=True,text=True)
  if q.returncode:raise RuntimeError(q.stderr)
 def case(self,name):
  p=subprocess.run([str(self.binary),str(self.snapshot),name],capture_output=True,text=True,timeout=15);self.assertEqual(p.returncode,0,p.stderr)
 def test_full_original_controller_press_hold_release_all_profiles_and_ports(self):self.case('full')
 def test_auxiliary_original_stage_preserves_raw_consumers_until_return(self):self.case('aux')
 def test_direct_special_stage_preserves_raw_consumers_until_return(self):self.case('special')
 def test_old_inner_only_scope_is_a_negative_control(self):
  p=subprocess.run([str(self.binary),str(self.snapshot),'legacy'],capture_output=True,text=True,timeout=15);self.assertNotEqual(p.returncode,0);self.assertIn('post-normalizer consumer read ordinary menu packet',p.stderr)
if __name__=='__main__':unittest.main()
