"""Genuine original PAL menu sound queue, no playback/window/game. Work by djultra64."""
from pathlib import Path
import hashlib,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
CODE=r'''#include "pal_menu_audio.hpp"
#include "runtime/game_settings_menu.hpp"
#include <cassert>
#include <cstring>
#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>
using namespace iss2000;
extern "C"void func_8004C59C_resident(uint8_t*,recomp_context*);
extern "C"void func_8004C608_resident(uint8_t*,recomp_context*);
extern "C"void func_801B7D90_overlay_2dee70_801ad820(uint8_t*,recomp_context*);
extern "C"void func_801B7E00_overlay_2dee70_801ad820(uint8_t*,recomp_context*);
extern "C"void func_801B7DC8_overlay_2dee70_801ad820(uint8_t*,recomp_context*);
extern "C"void func_8029F33C_overlay_3b47e0_8029eea0(uint8_t*,recomp_context*);
extern "C"void func_802A6234_overlay_3b47e0_8029eea0(uint8_t*,recomp_context*);
unsigned starts=0,leaves=0;bool throwing=false;
void leaf(uint8_t*r,recomp_context*c){++leaves;func_8004C608_resident(r,c);}
void original(uint8_t*r,recomp_context*c){++starts;assert(c->f_odd==&c->f0.u32h);func_8004C59C_resident(r,c);if(throwing){*c->f_odd=0x12345678;throw std::runtime_error("injectedoriginalthrow");}}
extern "C"recomp_func_t*get_function(int32_t a){switch(uint32_t(a)){case 0x8004c608:return leaf;case 0x8004c59c:return func_8004C59C_resident;case 0x801b7e00:return func_801B7E00_overlay_2dee70_801ad820;case 0x801b7dc8:return func_801B7DC8_overlay_2dee70_801ad820;default:assert(false);return nullptr;}}
extern "C"void do_break(uint32_t){assert(false);}extern "C"void switch_error(const char*,uint32_t,uint32_t){assert(false);}
void put(std::vector<uint8_t>&r,uint32_t p,uint32_t v){memcpy(r.data()+(p&0x7fffff),&v,4);}uint32_t word(std::vector<uint8_t>&r,uint32_t p){uint32_t v;memcpy(&v,r.data()+(p&0x7fffff),4);return v;}
struct TestRegistry {recomp_func_t* active=&func_8004C59C_resident;recomp_func_t* find(uint32_t pc){assert(pc==0x8004C59C);return active;}}registry;
void drain(uint8_t*ram,recomp_context*ctx,bool original_options){auto&settings=game_settings_menu();
DRAIN
}
int main(int,char**argv){std::ifstream file(argv[1],std::ios::binary);std::vector<uint8_t>rom((std::istreambuf_iterator<char>(file)),{});assert(rom.size()==0x1000000);std::vector<uint8_t>base(0x800000,0);
 for(unsigned i=0;i<0x24;++i)base[(0x4c59c+i)^3]=rom[0x4d19c+i];for(unsigned i=0;i<0x120;++i)base[(0x4c608+i)^3]=rom[0x4d208+i];
 recomp_context caller{};caller.r29=uint64_t(int64_t(int32_t(0x800a4000)));caller.r4=0x12345678;caller.r31=0xffffffff80123450ull;caller.f_odd=&caller.f0.u32h;caller.f0.u32h=0x11223344;const auto saved=caller;
 for(unsigned i=0;i<64;++i)base[0xa3fc0+i]=uint8_t(i*7);const auto stack=std::vector<uint8_t>(base.begin()+0xa3fc0,base.begin()+0xa4000);
 const std::string mode=argv[2];
 if(mode=="drain"){
  auto r=base;auto&settings=game_settings_menu();using C=ControlsMenuCommand;
  assert(settings.open(0,{}));settings.command(C::Down);settings.command(C::Up);settings.command(C::Accept);settings.command(C::NextPage);
  auto e=settings.pending_sound();assert(e);const auto first=e->sequence;const auto before=r;
  drain(r.data(),&caller,false);assert(r==before&&settings.pending_sound()->sequence==first&&leaves==0);
  registry.active=nullptr;drain(r.data(),&caller,true);assert(r==before&&settings.pending_sound()->sequence==first&&leaves==0);registry.active=&func_8004C59C_resident;
  drain(r.data(),&caller,true);assert(leaves==4&&settings.pending_sound()&&settings.pending_sound()->sequence==first+4);
  assert(r[0x9dea4^3]==2&&word(r,0x80166198)==0x100&&word(r,0x8016619c)==0x101);
  drain(r.data(),&caller,true);assert(!settings.pending_sound()&&leaves==5);
  settings.command(C::ApplySave,[](const auto&){return false;});e=settings.pending_sound();assert(e&&e->sound==PalMenuSound::Error);
  r[0x9dea4^3]=8;const auto full=r;drain(r.data(),&caller,true);assert(r==full&&settings.pending_sound()->sequence==e->sequence&&leaves==6);
  r[0x9dea4^3]=0;drain(r.data(),&caller,true);assert(!settings.pending_sound()&&word(r,0x80166198)==0x152&&leaves==7);
  settings.command(C::Down);settings.command(C::Down);e=settings.pending_sound();assert(e);r[0x4c59c]^=1;const auto foreign=r;
  drain(r.data(),&caller,true);assert(r==foreign&&leaves==7&&settings.pending_sound()->sequence==e->sequence+1);
  assert(memcmp(&caller,&saved,sizeof caller)==0&&memcmp(r.data()+0xa3fc0,stack.data(),64)==0);
 }else if(mode=="provenance"){
  auto r=base;auto c=caller;c.f_odd=&c.f0.u32h;func_801B7D90_overlay_2dee70_801ad820(r.data(),&c);assert(word(r,0x80166198)==0x100);
  r=base;c=caller;c.f_odd=&c.f0.u32h;func_8029F33C_overlay_3b47e0_8029eea0(r.data(),&c);assert(word(r,0x80166198)==0x101);
  r=base;r[0x2b10f0^3]=1;c=caller;c.f_odd=&c.f0.u32h;func_802A6234_overlay_3b47e0_8029eea0(r.data(),&c);assert(word(r,0x80166198)==0x152);
 }else if(mode=="sounds"){
  const PalMenuSound events[]{PalMenuSound::Navigate,PalMenuSound::Accept,PalMenuSound::Back,PalMenuSound::Error};const uint32_t ids[]{0x101,0x100,0x100,0x152};
  for(unsigned i=0;i<4;++i){auto r=base;assert(play_pal_menu_sound(r,caller,events[i],original)==PalMenuAudioResult::Queued);assert(r[0x9dea4^3]==1&&word(r,0x80166198)==ids[i]&&r[0x9e07c^3]==0);assert(memcmp(&caller,&saved,sizeof caller)==0);assert(memcmp(r.data()+0xa3fc0,stack.data(),64)==0);}
  assert(starts==4&&leaves==4);
 }else if(mode=="queue"){
  auto r=base;assert(play_pal_menu_sound(r,caller,PalMenuSound::Accept,original)==PalMenuAudioResult::Queued);const auto first=r;assert(play_pal_menu_sound(r,caller,PalMenuSound::Back,original)==PalMenuAudioResult::AlreadyPending);assert(r==first&&starts==2&&leaves==2);
  r=base;r[0x9dea4^3]=8;for(unsigned i=0;i<8;++i)put(r,0x80166198+i*4,0x200+i);const auto before=r;assert(play_pal_menu_sound(r,caller,PalMenuSound::Navigate,original)==PalMenuAudioResult::Full);assert(r==before&&starts==3&&leaves==3);
 }else if(mode=="guards"){
  for(unsigned bad=0;bad<12;++bad){auto r=base;auto c=caller;c.f_odd=&c.f0.u32h;auto sound=PalMenuSound::Accept;auto fn=original;std::span<uint8_t>ram=r;
   switch(bad){case 0:r[0x4c59c]^=1;break;case 1:r[0x4c608]^=1;break;case 2:c.r29=0xffffffff800a02e0ull;break;case 3:c.r29=0x12345678800a4000ull;break;case 4:c.r29|=1;break;case 5:c.f_odd=reinterpret_cast<uint32_t*>(r.data());break;case 6:sound=PalMenuSound(99);break;case 7:fn=nullptr;break;case 8:r[0x9dea4^3]=9;break;case 9:r[0x9e07c^3]=0xff;break;case 10:ram=ram.first(0x7fffff);break;case 11:c.r29=0xffffffff800a42e0ull;break;}
   const auto before=r;const auto context=c;assert(play_pal_menu_sound(ram,c,sound,fn)==PalMenuAudioResult::Rejected);assert(r==before&&memcmp(&c,&context,sizeof c)==0&&starts==0&&leaves==0);
  }
 }else if(mode=="throw"){
  auto r=base;throwing=true;bool threw=false;try{play_pal_menu_sound(r,caller,PalMenuSound::Error,original);}catch(const std::runtime_error&){threw=true;}assert(threw&&starts==1&&leaves==1);assert(memcmp(&caller,&saved,sizeof caller)==0&&memcmp(r.data()+0xa3fc0,stack.data(),64)==0);assert(r[0x9dea4^3]==1&&word(r,0x80166198)==0x152);
 }else return 2;
}
'''
class PalMenuAudioTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  rom=ROOT/'.local/inputs/pal-en-de/rom.z64';g=ROOT/'.local/pal-map-bound-01/functions';h=ROOT/'.local/deps/N64Recomp/include';mb=ROOT/'.local/runtime-deps-build/librecomp/miniz'
  if not rom.exists()or not(mb/'libminiz.a').exists():raise unittest.SkipTest('Private PAL CPU fixtures required')
  assert hashlib.sha256(rom.read_bytes()).hexdigest()=='6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf';cls.rom=rom;cls.temp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.temp.cleanup);p=Path(cls.temp.name);native=(ROOT/'src/runtime/native_game.cpp').read_text();drain=native.split('    if(original_options&&registry.find(0x8004C59C)',1)[1].split('    if(!controller&&!original_options)',1)[0];drain='    if(original_options&&registry.find(0x8004C59C)'+drain
  (p/'test.cpp').write_text(CODE.replace('DRAIN',drain).replace('extern "C"void','extern "C" void').replace('extern "C"recomp','extern "C" recomp'))
  (p/'original.c').write_text('\n'.join('#include "'+str(g/f'func_{n}_resident.c')+'"'for n in ['8004C59C','8004C608']))
  with (p/'original.c').open('a')as out:
   for name,suffix in [('801B7D90','overlay_2dee70_801ad820'),('801B7E00','overlay_2dee70_801ad820'),('801B7DC8','overlay_2dee70_801ad820'),('8029F33C','overlay_3b47e0_8029eea0'),('802A6234','overlay_3b47e0_8029eea0')]:out.write('\n#include "'+str(g/f'func_{name}_{suffix}.c')+'"')
  q=subprocess.run(['cc','-O1','-I'+str(h),'-c',str(p/'original.c'),'-o',str(p/'original.o')],capture_output=True,text=True)
  if q.returncode:raise RuntimeError(q.stderr)
  cls.binary=p/'test';q=subprocess.run(['c++','-std=c++20','-O1','-pthread','-I'+str(ROOT/'src'),'-I'+str(ROOT/'src/runtime'),'-I/home/linuxbrew/.linuxbrew/include/SDL2','-I'+str(ROOT/'.local/deps/N64ModernRuntime/librecomp/include'),'-I'+str(ROOT/'.local/deps/N64ModernRuntime/ultramodern/include'),'-I'+str(ROOT/'.local/deps/N64ModernRuntime/thirdparty'),'-I'+str(ROOT/'.local/deps/N64ModernRuntime/thirdparty/concurrentqueue'),'-I'+str(h),'-I'+str(ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz'),'-I'+str(mb),str(p/'test.cpp'),str(ROOT/'src/runtime/game_settings_menu.cpp'),str(ROOT/'src/runtime/pal_menu_audio.cpp'),str(ROOT/'src/runtime/rom_image.cpp'),str(p/'original.o'),str(mb/'libminiz.a'),'-o',str(cls.binary)],capture_output=True,text=True)
  if q.returncode:raise RuntimeError(q.stderr)
 def case(self,name):
  q=subprocess.run([str(self.binary),str(self.rom),name],capture_output=True,text=True,timeout=8);self.assertEqual(q.returncode,0,q.stderr)
 def test_actual_native_drain_uses_owner_identity_limits_defers_full_and_acks_one_rejection(self):self.case('drain')
 def test_semantic_ids_match_actual_Options_navigation_accept_and_invalid_Password_routes(self):self.case('provenance')
 def test_authentic_sound_ids_reach_genuine_queue_with_caller_and_stack_preserved(self):self.case('sounds')
 def test_original_dedup_and_eight_slot_full_behavior_are_preserved(self):self.case('queue')
 def test_foreign_code_context_queue_and_sound_reject_without_mutation(self):self.case('guards')
 def test_throw_preserves_caller_and_stack_without_undoing_original_queue(self):self.case('throw')
if __name__=='__main__':unittest.main()
