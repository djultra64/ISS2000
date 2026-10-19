"""Original work: djultra64. Bounded live-context football input CPU fixtures."""
from pathlib import Path
import hashlib,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class PalFootballInputTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  rom=ROOT/'.local/inputs/pal-en-de/rom.z64';g=ROOT/'.local/pal-map-bound-01/functions';h=ROOT/'.local/deps/N64Recomp/include'
  if not rom.exists()or not(g/'func_801D4880_overlay_25aaf0_801ad820.c').exists():raise unittest.SkipTest('Private original PAL input/translation required')
  assert hashlib.sha256(rom.read_bytes()).hexdigest()=='6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf'
  cls.temp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.temp.cleanup);d=Path(cls.temp.name);objects=[]
  for name in ['801D4880','801D4540','801D5FE8','80014A74','802C53A4']:
   suffix='resident'if name=='80014A74'else 'overlay_40c7a0_802c3490'if name=='802C53A4'else 'overlay_25aaf0_801ad820'
   source=g/f'func_{name}_{suffix}.c';obj=d/(name+'.o')
   r=subprocess.run(['cc','-O1','-I'+str(h),'-c',str(source),'-o',str(obj)],capture_output=True,text=True);assert r.returncode==0,r.stderr;objects.append(str(obj))
  (d/'test.cpp').write_text(r'''
#include "pal_football_input.hpp"
#include <array>
#include <cassert>
#include <cstring>
#include <stdexcept>
#include <string>
#include <vector>
using namespace iss2000;
extern "C" void func_801D4880_overlay_25aaf0_801ad820(uint8_t*,recomp_context*);
extern "C" void func_801D4540_overlay_25aaf0_801ad820(uint8_t*,recomp_context*);
extern "C" void func_801D5FE8_overlay_25aaf0_801ad820(uint8_t*,recomp_context*);
extern "C" void func_80014A74_resident(uint8_t*,recomp_context*);
extern "C" void func_802C53A4_overlay_40c7a0_802c3490(uint8_t*,recomp_context*);
bool project_initializer=false;unsigned initializer_calls=0;uint16_t initializer_held=0;
void initializer_normalize(uint8_t*r,recomp_context*c){
 ++initializer_calls;
 if(project_initializer){auto b=*scheme_bindings(ControllerScheme::Type5);assert(apply_pal_football_input({r,0x800000},*c,initializer_held,initializer_held,b,func_801D4880_overlay_25aaf0_801ad820));}
 else func_801D4880_overlay_25aaf0_801ad820(r,c);
}
unsigned calls=0,tailcalls=0;bool throwing=false;uint32_t object,packet;uint64_t entry_sp;std::array<uint8_t,10> source_bytes;
uint8_t byte(const uint8_t*r,uint32_t p){return r[(p&0x7fffff)^3];}
void sb(uint8_t*r,uint32_t p,uint8_t v){r[(p&0x7fffff)^3]=v;}
uint16_t half(const uint8_t*r,uint32_t p){uint16_t v;std::memcpy(&v,r+((p&0x7fffff)^2),2);return v;}
void sh(uint8_t*r,uint32_t p,uint16_t v){std::memcpy(r+((p&0x7fffff)^2),&v,2);}
uint32_t word(const uint8_t*r,uint32_t p){uint32_t v;std::memcpy(&v,r+(p&0x7fffff),4);return v;}
void sw(uint8_t*r,uint32_t p,uint32_t v){std::memcpy(r+(p&0x7fffff),&v,4);}
void nested(uint8_t*r,recomp_context*c){++tailcalls;func_801D4540_overlay_25aaf0_801ad820(r,c);}
extern "C" recomp_func_t* get_function(int32_t p){switch(uint32_t(p)){
 case 0x801d4540:return nested;case 0x801d4880:return initializer_normalize;case 0x80014a74:return func_80014A74_resident;
 default:assert(false);return nullptr;}}
extern "C" void do_break(uint32_t){assert(false);}
extern "C" void switch_error(const char*,uint32_t,uint32_t){assert(false);}
void original(uint8_t*r,recomp_context*c){++calls;
 assert(c->r29==entry_sp-0x20);const auto scratch=word(r,object+0x24);assert(scratch==uint32_t(entry_sp)-0x10);
 for(unsigned n:{0u,1u,6u,7u,8u,9u})assert(byte(r,scratch+n)==source_bytes[n]);
 for(unsigned n=0;n<10;++n)assert(byte(r,packet+n)==source_bytes[n]);
 if(throwing){sw(r,scratch,0x12345678);sw(r,object+0x24,0x807ffff0);c->r29=0xffffffffdeadbeefull;c->r2=0x1234;*c->f_odd=0xabcdef01;throw std::runtime_error("original failure");}
 func_801D4880_overlay_25aaf0_801ad820(r,c);
}
constexpr uint16_t profiles[3][6]={{1,8,4,0x8000,0x4000,2},{1,8,0x4000,0x8000,2,4},{0x8000,0x4000,2,4,8,1}};
constexpr uint16_t normalized[6]={0x8000,0x4000,2,4,8,1};
// Primary N64 manual: Dash C-down, Lob C-left, OneTwo C-right.
constexpr uint16_t action[8]={4,8,2,1,0x4000,0x8000,0x2000,0x10};
void setup(std::vector<uint8_t>&m,recomp_context&c,unsigned port=0,unsigned profile=0){auto*r=m.data();
 object=0x80127468+port*0xa8;packet=0x8013b454+port*10;entry_sp=0xffffffff800a3f80ull;
 std::memset(r+(object&0x7fffff),0,0xa8);sw(r,object+0x24,packet);sw(r,object,4);
 for(unsigned i=0;i<6;++i){sh(r,object+0x72+i*2,profiles[profile][i]);sh(r,0x801d9a70+i*2,normalized[i]);}
 for(unsigned n=0;n<10;++n)sb(r,packet+n,uint8_t(17+n*19+port));
 // Raw face/modifier inputs deliberately disagree with the football sidecar.
 sh(r,packet+2,0xff3f);sh(r,packet+4,0xdf3f);
 for(unsigned n=0;n<10;++n)source_bytes[n]=byte(r,packet+n);
 for(unsigned n=0;n<32;++n)sb(r,uint32_t(entry_sp)-32+n,uint8_t(n*7+port));
 sb(r,0x8013b44c,4);sb(r,0x8009df78,0);
 c={};c.r4=int32_t(object);c.r29=entry_sp;c.r31=0xffffffff80123450ull;c.f_odd=&c.f0.u32h;calls=tailcalls=0;throwing=false;
}
std::array<uint8_t,32> stack(const uint8_t*r){std::array<uint8_t,32>s;std::memcpy(s.data(),r+((uint32_t(entry_sp)-32)&0x7fffff),32);return s;}
void preserved(const std::vector<uint8_t>&m,const recomp_context&c,const std::array<uint8_t,32>&saved){assert(c.r29==entry_sp);assert(word(m.data(),object+0x24)==packet);assert(stack(m.data())==saved);for(unsigned n=0;n<10;++n)assert(byte(m.data(),packet+n)==source_bytes[n]);}
int main(int argc,char**argv){assert(argc==2);std::vector<uint8_t>m(0x800000);recomp_context c{};const std::string mode=argv[1];
 if(mode=="frames"){
 for(unsigned type=0;type<6;++type)for(unsigned profile=0;profile<3;++profile)for(unsigned port=0;port<4;++port)for(unsigned a=0;a<8;++a){setup(m,c,port,profile);const auto saved=stack(m.data());auto bindings=type<5?*scheme_bindings(ControllerScheme(type)):default_football_bindings;if(type==5){assert(assign_free(bindings,FootballAction::Pass,PhysicalControl::R2));assert(assign_free(bindings,FootballAction::Curve,PhysicalControl::South));}const auto bit=physical_control_mask(bindings[a]);
  const uint16_t held[4]={0,bit,bit,0},pressed[4]={0,bit,0,0};
  for(unsigned f=0;f<4;++f){c.r4=int32_t(object);assert(apply_pal_football_input(m,c,held[f],pressed[f],bindings,original));assert(calls==f+1);preserved(m,c,saved);
   assert(half(m.data(),object+0x66)==uint16_t(0x1f00|(pressed[f]?action[a]:0)));
   assert(half(m.data(),object+0x68)==uint16_t(0x1f00|(held[f]?action[a]:0)));
   assert(half(m.data(),object+0x6c)==half(m.data(),object+0x66));assert(half(m.data(),object+0x6a)==half(m.data(),object+0x68));
   assert(half(m.data(),object+0x6e)==uint16_t(f==3?action[a]:0));
  }
 }
 }else if(mode=="initializer"){
 for(unsigned profile=0;profile<3;++profile)for(unsigned pressed=0;pressed<2;++pressed){
  std::fill(m.begin(),m.end(),0);for(unsigned port=0;port<4;++port){const auto o=0x80127468+port*0xa8;sh(m.data(),o+0x64,1);sb(m.data(),0x802d21e4+port,profile);}
  for(unsigned i=0;i<3;++i)for(unsigned j=0;j<6;++j)sh(m.data(),0x800774f0+i*12+j*2,profiles[i][j]);
  for(unsigned j=0;j<6;++j)sh(m.data(),0x801d9a70+j*2,normalized[j]);
  c={};c.r29=0xffffffff800a3f80ull;c.r31=0xffffffff80123450ull;c.f_odd=&c.f0.u32h;
  // Genuine Ready applies all four saved profiles, then genuine first input
  // initializer rebuilds every packet pointer and invokes the hooked normalizer.
  func_802C53A4_overlay_40c7a0_802c3490(m.data(),&c);
  for(unsigned port=0;port<4;++port)for(unsigned j=0;j<6;++j)assert(half(m.data(),0x80127468+port*0xa8+0x72+j*2)==profiles[profile][j]);
  auto expected=m;recomp_context e=c;e.f_odd=&e.f0.u32h;
  initializer_held=pressed?physical_control_mask(PhysicalControl::South):0;
  const auto raw=*football_guest_pad(*scheme_bindings(ControllerScheme::Type5),initializer_held,profile);
  for(unsigned port=0;port<4;++port){sh(expected.data(),0x8013b454+port*10+2,raw);sh(expected.data(),0x8013b454+port*10+4,raw);}
  project_initializer=false;initializer_calls=0;func_801D5FE8_overlay_25aaf0_801ad820(expected.data(),&e);assert(initializer_calls==4);
  project_initializer=true;initializer_calls=0;func_801D5FE8_overlay_25aaf0_801ad820(m.data(),&c);assert(initializer_calls==4&&c.r29==0xffffffff800a3f80ull);
  for(unsigned port=0;port<4;++port){const auto o=0x80127468+port*0xa8;assert(word(m.data(),o+0x24)==0x8013b454+port*10);assert(memcmp(m.data()+(o&0x7fffff),expected.data()+(o&0x7fffff),0xa8)==0);}
 }
 }else if(mode=="guards"){
 for(unsigned bad=0;bad<15;++bad){setup(m,c);auto bindings=default_football_bindings;uint16_t held=1,pressed=1;auto fn=&original;std::span<uint8_t>ram=m;
 switch(bad){case0:c.r4=0xffffffff80127469ull;break;case1:c.r4=0x1234567880127468ull;break;case2:c.r4=int32_t(0x80127708);break;case3:sw(m.data(),object+0x24,packet+10);break;case4:sh(m.data(),object+0x72,0x10);break;case5:c.r29=0xffffffff800a02e8ull;break;case6:c.r29=0xffffffff800a42e0ull;break;case7:c.r29=entry_sp+1;break;case8:c.r29=0x12345678800a3f80ull;break;case9:ram=ram.first(0x7fffff);break;case10:bindings[0]=bindings[1];break;case11:held=0x100;break;case12:pressed=2;break;case13:fn=nullptr;break;case14:sh(m.data(),0x801d9a70,0);break;}
 const auto before=m;const auto ctx=c;assert(!apply_pal_football_input(ram,c,held,pressed,bindings,fn));assert(calls==0);assert(m==before);assert(std::memcmp(&c,&ctx,sizeof c)==0);
 }
 }else if(mode=="throw"){
 setup(m,c);const auto saved=stack(m.data());throwing=true;try{apply_pal_football_input(m,c,1,1,default_football_bindings,original);assert(false);}catch(const std::runtime_error&){}
 assert(calls==1);preserved(m,c,saved);assert(c.r2==0x1234&&c.f0.u32h==0xabcdef01);assert(c.f_odd==&c.f0.u32h);
 }else if(mode=="tail"){
 setup(m,c,3,2);const auto saved=stack(m.data());sw(m.data(),object,0);sw(m.data(),object+0x38,0x80200000);sw(m.data(),0x801a44e4,0x80200000);sw(m.data(),0x802d7904,0x80200000);sh(m.data(),0x802000e8,0x10);
 sw(m.data(),0x801a4504,0x20000);sw(m.data(),0x800c1a10,0x800);sb(m.data(),0x8009df78,6);
 const auto curve=physical_control_mask(default_football_bindings[unsigned(FootballAction::Curve)]);
 assert(apply_pal_football_input(m,c,curve,curve,default_football_bindings,original));assert(calls==1&&tailcalls==1);preserved(m,c,saved);
 }else assert(false);
}
'''.replace('case0:','case 0:').replace('case1:','case 1:').replace('case2:','case 2:').replace('case3:','case 3:').replace('case4:','case 4:').replace('case5:','case 5:').replace('case6:','case 6:').replace('case7:','case 7:').replace('case8:','case 8:').replace('case9:','case 9:').replace('case10:','case 10:').replace('case11:','case 11:').replace('case12:','case 12:').replace('case13:','case 13:').replace('case14:','case 14:'))
  cls.binary=d/'test';r=subprocess.run(['c++','-std=c++20','-O1','-Wall','-Wextra','-Werror','-I'+str(ROOT/'src/runtime'),'-I'+str(h),str(d/'test.cpp'),str(ROOT/'src/runtime/controller_schemes.cpp'),str(ROOT/'src/runtime/pal_football_input.cpp'),*objects,'-o',str(cls.binary)],capture_output=True,text=True);assert r.returncode==0,r.stderr
 def run_case(self,case):
  r=subprocess.run([str(self.binary),case],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
 def test_genuine_Ready_profiles_and_all_four_first_neutral_or_Begin_confirm_inputs(self):self.run_case('initializer')
 def test_press_hold_release_all_schemes_profiles_and_ports(self):self.run_case('frames')
 def test_foreign_packet_profile_stack_and_physical_input_fail_unchanged(self):self.run_case('guards')
 def test_live_context_effects_survive_but_scratch_restores_on_exception(self):self.run_case('throw')
 def test_original_nested_special_action_closure_runs_once(self):self.run_case('tail')
