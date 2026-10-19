"""Original PS1 football layouts preserve genuine PAL guest action conversion.
Original project work: djultra64. No complete game or controller execution.
"""
from pathlib import Path
import subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class ControllerSchemesTests(unittest.TestCase):
 def run_cpp(self,body,originals=()):
  with tempfile.TemporaryDirectory()as td:
   d=Path(td);(d/'test.cpp').write_text(body)
   extra=[]
   if originals:
    include='-I'+str(ROOT/'.local/deps/N64Recomp/include');extra.append(include)
    for source in originals:
     target=d/(source.stem+'.o');r=subprocess.run(['cc','-std=c17','-O1',include,'-c',str(source),'-o',str(target)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr);extra.append(str(target))
   r=subprocess.run(['c++','-std=c++20','-Wall','-Wextra','-Werror','-O1','-I'+str(ROOT/'src/runtime'),str(d/'test.cpp'),str(ROOT/'src/runtime/controller_schemes.cpp'),*extra,'-lm','-o',str(d/'test')],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
   r=subprocess.run([str(d/'test')],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)

 def test_primary_n64_manual_actions_match_all_three_real_guest_profiles(self):
  # Primary booklet printed20 (PDF22), read visually: Type1 Dash=C-down,
  # FlyBall=C-left, OneTwo=C-right. Standard raw C bits are down4/left2/right1.
  # Types2/3 independently establish each semantic slot in PAL's ROM table.
  self.run_cpp(r'''#include "controller_schemes.hpp"
#include <cassert>
using namespace iss2000;
int main(){
 const uint16_t manual_actions[3][8]={
  {0x8000,0x4000,0x0004,0x0002,0x0008,0x0001,0x2000,0x0010},
  {0x8000,0x0002,0x4000,0x0004,0x0008,0x0001,0x2000,0x0010},
  {0x0004,0x0008,0x0002,0x0001,0x4000,0x8000,0x2000,0x0010}};
 for(unsigned profile=0;profile<3;++profile)for(unsigned action=0;action<8;++action){
  const auto actual=football_guest_pad(default_football_bindings,physical_control_mask(default_football_bindings[action]),profile);
  assert(actual&&*actual==manual_actions[profile][action]&&"Football action must match the primary N64 manual, not a guessed ROM slot label");
 }
 auto type5=*scheme_bindings(ControllerScheme::Type5);
 assert(football_guest_pad(type5,physical_control_mask(PhysicalControl::R2),0)==0x0004);
 assert(football_guest_pad(type5,physical_control_mask(PhysicalControl::East),0)==0x0002);
 assert(football_guest_pad(type5,physical_control_mask(PhysicalControl::R1),0)==0x0001);
}
''')

 def test_recorded_ps1_types_drive_the_intended_guest_actions(self):
  # A misplaced face or shoulder assignment causes a different real guest bit.
  self.run_cpp(r'''#include "controller_schemes.hpp"
#include <cassert>
using namespace iss2000;
int main(){
 const uint16_t want[4][8]={{4,2,0x8000,0x4000,1,8,0x2000,0x10},
 {0x8000,4,0x4000,2,0x2000,0x10,1,8},
 {0x8000,2,4,0x4000,0x2000,0x10,1,8},
 {0x8000,2,0x4000,8,0x10,4,0x2000,1}};
 for(unsigned t=0;t<4;++t){auto b=scheme_bindings(ControllerScheme(t));assert(b&&valid_football_bindings(*b));
 for(unsigned p=0;p<8;++p){auto out=football_guest_pad(*b,physical_control_mask(PhysicalControl(p)),0);assert(out&&*out==want[t][p]);}
 assert(football_guest_pad(*b,0,0)==0);assert(football_guest_pad(*b,0xff,0)==0xe01f);}
 assert(*scheme_bindings(ControllerScheme::Type1)==default_football_bindings);
 assert(!scheme_bindings(ControllerScheme::Free));assert(!scheme_bindings(ControllerScheme(255)));
}
''')

 def test_type5_adapts_pes_positions_without_claiming_compound_one_two(self):
  self.run_cpp(r'''#include "controller_schemes.hpp"
#include <cassert>
using namespace iss2000;
int main(){
 auto b=scheme_bindings(ControllerScheme::Type5);assert(b&&valid_football_bindings(*b));
 const PhysicalControl expected[8]={PhysicalControl::South,PhysicalControl::West,PhysicalControl::R2,PhysicalControl::East,PhysicalControl::North,PhysicalControl::R1,PhysicalControl::L2,PhysicalControl::L1};
 for(unsigned a=0;a<8;++a)assert((*b)[a]==expected[a]);
 // L1 retains Cursor alone; Pass alone stays Pass. OneTwo has its own R1.
 assert(football_guest_pad(*b,physical_control_mask(PhysicalControl::L1),0)==0x10);
 assert(football_guest_pad(*b,physical_control_mask(PhysicalControl::South),0)==0x8000);
 assert(football_guest_pad(*b,physical_control_mask(PhysicalControl::R1),0)==1);
 assert(football_guest_pad(*b,physical_control_mask(PhysicalControl::L1)|physical_control_mask(PhysicalControl::South),0)==0x8010);
}
''')

 def test_free_swap_keeps_every_action_accessible_and_ports_independent(self):
  self.run_cpp(r'''#include "controller_schemes.hpp"
#include <array>
#include <cassert>
using namespace iss2000;
int main(){std::array<FootballBindings,4> saved{default_football_bindings,default_football_bindings,default_football_bindings,default_football_bindings};
 auto draft=saved[2];assert(assign_free(draft,FootballAction::Pass,PhysicalControl::South));
 assert(football_guest_pad(draft,1,0)==0x8000);assert(football_guest_pad(draft,4,0)==4);
 assert(valid_football_bindings(draft));for(auto& port:saved)assert(port==default_football_bindings);
 // Draft cancellation is simple discard; a confirmed change updates one port.
 saved[2]=draft;assert(saved[0]==default_football_bindings&&saved[1]==default_football_bindings&&saved[3]==default_football_bindings);
 assert(assign_free(draft,FootballAction::Pass,PhysicalControl::South));assert(draft==saved[2]);
 const auto before=draft;assert(!assign_free(draft,FootballAction::Count,PhysicalControl::North));assert(draft==before);
 assert(!assign_free(draft,FootballAction::Pass,PhysicalControl(255)));assert(draft==before);
 auto invalid=draft;invalid[0]=invalid[1];const auto bad=invalid;assert(!valid_football_bindings(invalid));assert(!assign_free(invalid,FootballAction::Pass,PhysicalControl::R2));assert(invalid==bad);
 assert(!football_guest_pad(invalid,0,0));assert(!football_guest_pad(draft,0x100,0));assert(!football_guest_pad(draft,1,3));assert(!football_guest_pad(draft,1,~0u));
 assert(physical_control_mask(PhysicalControl(255))==0);
 for(unsigned a=0;a<8;++a)for(unsigned p=0;p<8;++p){auto b=default_football_bindings;assert(assign_free(b,FootballAction(a),PhysicalControl(p)));assert(valid_football_bindings(b));assert(b[a]==PhysicalControl(p));}
}
''')

 def test_all_presets_reach_same_actions_through_original_pal_normalizer(self):
  # Wrong raw/normalized bit spaces, wrong alternate-profile order, or bypassing
  # the original conversion must fail these actual original-code comparisons.
  source=ROOT/'.local/pal-map-bound-01/functions/func_801D4880_overlay_25aaf0_801ad820.c';rom=ROOT/'.local/inputs/pal-en-de/rom.z64'
  if not source.exists()or not rom.exists():self.skipTest('Private original PAL input/translation unavailable')
  r=rom.read_bytes();import hashlib
  self.assertEqual(hashlib.sha256(r).hexdigest(),'6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf')
  profiles=[[int.from_bytes(r[0x780f0+t*12+i*2:0x780f2+t*12+i*2],'big')for i in range(6)]for t in range(3)]
  profiles='{{'+ '},{'.join(','.join(hex(x)for x in row)for row in profiles)+'}}'
  self.run_cpp(r'''#include "controller_schemes.hpp"
#include "recomp.h"
#include <cassert>
#include <cstring>
#include <vector>
extern "C" void func_801D4880_overlay_25aaf0_801ad820(uint8_t*,recomp_context*);
recomp_func_t* get_function(int32_t){assert(false);return nullptr;}
void switch_error(const char*,uint32_t,uint32_t){assert(false);}
using namespace iss2000;
int main(){std::vector<uint8_t> ram(0x800000);auto*rdram=ram.data();
 auto half=[&](uint32_t a,uint16_t v){std::memcpy(rdram+((a&0x7fffff)^2),&v,2);};
 auto read=[&](uint32_t a){uint16_t v;std::memcpy(&v,rdram+((a&0x7fffff)^2),2);return v;};
 const uint16_t profiles[3][6]=PROFILES;
 const uint16_t normalized[6]={0x8000,0x4000,2,4,8,1};
 // Semantic oracle from primary manual + exact PAL table: Dash is normalized2.
 const uint16_t want[8]={4,8,2,1,0x4000,0x8000,0x2000,0x10};
 for(unsigned i=0;i<6;++i){half(0x801d9a70+i*2,normalized[i]);}
 ram[0x13b44c^3]=14;
 for(unsigned t=0;t<5;++t)for(unsigned profile=0;profile<3;++profile)for(unsigned port=0;port<4;++port){const uint32_t base=0x80127468+port*0xa8,input=0x8013b454+port*10;
 std::memcpy(rdram+(base+0x24-0x80000000),&input,4);for(unsigned i=0;i<6;++i)half(base+0x72+i*2,profiles[profile][i]);
 auto b=*scheme_bindings(ControllerScheme(t));
 for(unsigned a=0;a<8;++a){auto raw=football_guest_pad(b,physical_control_mask(b[a]),profile);assert(raw);half(input+2,*raw);half(input+4,*raw);
 recomp_context c{};c.r4=int32_t(base);c.r29=0xffffffff800a4000ull;func_801D4880_overlay_25aaf0_801ad820(rdram,&c);
 assert(read(base+0x66)==want[a]&&read(base+0x68)==want[a]);assert(read(input+2)==*raw&&read(input+4)==*raw);}
 }
}
'''.replace('PROFILES',profiles),(source,))

 def test_type5_dash_reaches_the_genuine_original_held_dash_consumer(self):
  folder=ROOT/'.local/pal-map-bound-01/functions'
  sources=[folder/'func_801D4880_overlay_25aaf0_801ad820.c',folder/'func_801D4F88_overlay_25aaf0_801ad820.c']
  if not all(p.is_file()for p in sources):self.skipTest('Private original PAL translations required')
  self.run_cpp(r'''#include "controller_schemes.hpp"
#include "recomp.h"
#include <cassert>
#include <cstring>
#include <vector>
extern "C" void func_801D4880_overlay_25aaf0_801ad820(uint8_t*,recomp_context*);
extern "C" void func_801D4F88_overlay_25aaf0_801ad820(uint8_t*,recomp_context*);
recomp_func_t* get_function(int32_t){assert(false);return nullptr;}
void switch_error(const char*,uint32_t,uint32_t){assert(false);}
using namespace iss2000;
int main(){std::vector<uint8_t>ram(0x800000);auto*r=ram.data();
 auto sh=[&](uint32_t a,uint16_t v){std::memcpy(r+((a&0x7fffff)^2),&v,2);};
 auto sw=[&](uint32_t a,uint32_t v){std::memcpy(r+(a&0x7fffff),&v,4);};
 auto half=[&](uint32_t a){uint16_t v;std::memcpy(&v,r+((a&0x7fffff)^2),2);return v;};
 auto word=[&](uint32_t a){uint32_t v;std::memcpy(&v,r+(a&0x7fffff),4);return v;};
 const uint16_t profiles[3][6]={{1,8,4,0x8000,0x4000,2},{1,8,0x4000,0x8000,2,4},{0x8000,0x4000,2,4,8,1}};
 const uint16_t normalized[6]={0x8000,0x4000,2,4,8,1};
 const uint16_t old_dash[3]={1,1,0x8000};
 for(unsigned i=0;i<6;++i)sh(0x801D9A70+i*2,normalized[i]);
 ram[0x13B44C^3]=14;const uint32_t actor=0x80200000;sw(0x800C1A2C,actor);
 const auto type5=*scheme_bindings(ControllerScheme::Type5);
 for(unsigned profile=0;profile<3;++profile)for(unsigned port=0;port<4;++port)for(bool negative:{false,true}){
  const uint32_t object=0x80127468+port*0xA8,packet=0x8013B454+port*10;
  std::memset(r+(object&0x7fffff),0,0xA8);sw(object+0x24,packet);sw(object+0x38,actor);sw(actor+0xC4,0x100);
  for(unsigned i=0;i<6;++i)sh(object+0x72+i*2,profiles[profile][i]);
  const auto raw=negative?old_dash[profile]:*football_guest_pad(type5,physical_control_mask(PhysicalControl::R2),profile);
  for(unsigned frame=0;frame<6;++frame){sh(packet+2,frame<5?raw:0);sh(packet+4,frame==0?raw:0);
   recomp_context c{};c.r4=int32_t(object);c.r29=0xffffffff800A4000ull;func_801D4880_overlay_25aaf0_801ad820(r,&c);
   c.r4=int32_t(object);func_801D4F88_overlay_25aaf0_801ad820(r,&c);
   assert(half(object+0x84)==(!negative&&frame<5?frame+1:0));
   if(frame==4){assert(bool(word(object)&0x400)==!negative);assert(bool(word(actor+0xC4)&0x100)==negative);}
  }
 }
}
''',sources)
