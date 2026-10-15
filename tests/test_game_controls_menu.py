"""Original-engine remapping: draft isolation, capture edges and save lock ordering.
Original project work: djultra64.
"""
from pathlib import Path
import subprocess,tempfile,unittest,json,struct,hashlib
ROOT=Path(__file__).resolve().parents[1]
HARNESS=r'''
#include "runtime/game_controls_input.hpp"
#include <cassert>
#include <future>
#include <stdexcept>
using namespace iss2000;
using namespace iss2000::platform;
int main(int,char** argv){GameControlsMenu menu;PortPreferences initial;
 auto tick=[&](ControlsMenuCommand c,uint32_t held=0){menu.update(c,held,Family::Nintendo,{});};
 assert(!menu.open(4,initial));assert(menu.open(2,initial));assert(!menu.open(1,initial));
 assert(menu.active()&&menu.port()==2);auto lines=menu.lines(Family::Nintendo);assert(lines[0].text=="Remap Gamepad P3");
 assert(lines[2].text.find("N64 A   B")!=std::string::npos);
 menu.update(ControlsMenuCommand::None,0,Family::Keyboard,{});bool keyboard_help=false;
 for(auto l:menu.lines(Family::PlayStation)){keyboard_help|=l.text=="Z edit. X cancel";}assert(keyboard_help);
 assert(menu.lines(Family::PlayStation)[2].text.find("Cross")!=std::string::npos);
 tick(ControlsMenuCommand::Accept,1u<<SDL_CONTROLLER_BUTTON_A);assert(menu.capturing());
 tick(ControlsMenuCommand::None,1u<<SDL_CONTROLLER_BUTTON_A);assert(menu.capturing());
 tick(ControlsMenuCommand::None);tick(ControlsMenuCommand::None,(1u<<SDL_CONTROLLER_BUTTON_B)|(1u<<SDL_CONTROLLER_BUTTON_X));assert(menu.capturing());
 tick(ControlsMenuCommand::None,1u<<SDL_CONTROLLER_BUTTON_B);assert(menu.capturing());
 tick(ControlsMenuCommand::None);tick(ControlsMenuCommand::None,1u<<SDL_CONTROLLER_BUTTON_B);assert(!menu.capturing());
 assert(menu.lines(Family::Nintendo)[2].text.find("N64 A   A")!=std::string::npos);
 if(std::string(argv[1])=="cancel"){tick(ControlsMenuCommand::Cancel);assert(!menu.active());assert(initial.bindings[0]==SDL_CONTROLLER_BUTTON_A);return 0;}
 if(std::string(argv[1])=="conflict"||std::string(argv[1])=="conflict_restore"){
  for(int i=0;i<16;++i)tick(ControlsMenuCommand::Down);
  bool called=false;menu.update(ControlsMenuCommand::Accept,0,Family::Xbox,[&](unsigned,const PortPreferences&){called=true;return true;});
  assert(!called&&menu.active());bool conflict=false;for(auto l:menu.lines(Family::Xbox))conflict|=l.text=="Resolve duplicate bindings";assert(conflict);
  if(std::string(argv[1])=="conflict_restore"){
   tick(ControlsMenuCommand::RestoreDefault);
   for(auto l:menu.lines(Family::Xbox))assert(l.text!="Resolve duplicate bindings");
   menu.update(ControlsMenuCommand::Accept,0,Family::Xbox,[&](unsigned port,const PortPreferences& draft){called=true;assert(port==2&&draft==initial);return true;});
   assert(called&&!menu.active());return 0;
  }
  // Keep both draft edits possible: complete the A/B swap before saving.
  for(int i=0;i<15;++i){tick(ControlsMenuCommand::Up);}tick(ControlsMenuCommand::Accept);
  tick(ControlsMenuCommand::None);tick(ControlsMenuCommand::None,1u<<SDL_CONTROLLER_BUTTON_A);
  for(int i=0;i<15;++i){tick(ControlsMenuCommand::Down);}PortPreferences saved;
  menu.update(ControlsMenuCommand::Accept,0,Family::Xbox,[&](unsigned port,const PortPreferences& draft){called=true;assert(port==2);saved=draft;return true;});
  assert(called&&!menu.active()&&saved.bindings[0]==SDL_CONTROLLER_BUTTON_B&&saved.bindings[1]==SDL_CONTROLLER_BUTTON_A);
  assert(menu.open(2,saved));ControlsMenuInputRouter router;ControlsMenuInputFrame frame;frame.active=true;frame.port=2;frame.controllers[2].preferences=saved;
  router.route(frame);frame.any_input=true;frame.controllers[2].held=1u<<SDL_CONTROLLER_BUTTON_B;
  auto routed=router.route(frame);assert(routed.command==ControlsMenuCommand::Accept);
  menu.update(routed.command,routed.held,Family::Xbox,{});assert(menu.active()&&menu.capturing());return 0;
 }
 // The ordinary save-failure path starts with a valid completed swap.
 tick(ControlsMenuCommand::Down);tick(ControlsMenuCommand::Accept);tick(ControlsMenuCommand::None);
 tick(ControlsMenuCommand::None,1u<<SDL_CONTROLLER_BUTTON_A);tick(ControlsMenuCommand::Up);
 for(int i=0;i<16;++i)tick(ControlsMenuCommand::Down); // Save row:14 actions,family,defaults,save,cancel.
 bool called=false;menu.update(ControlsMenuCommand::Accept,0,Family::Xbox,[&](unsigned port,const PortPreferences& draft){called=true;assert(port==2&&draft.bindings[0]==SDL_CONTROLLER_BUTTON_B);assert(menu.active());auto view=std::async(std::launch::async,[&]{return menu.lines(Family::Xbox);});assert(view.wait_for(std::chrono::seconds(1))==std::future_status::ready);return false;});
 assert(called&&menu.active());bool error=false;for(auto l:menu.lines(Family::Xbox))error|=l.text.find("Save failed")!=std::string::npos;assert(error);
 menu.update(ControlsMenuCommand::Accept,0,Family::Xbox,[&](unsigned p,const PortPreferences& draft){assert(p==2&&draft.bindings[0]==SDL_CONTROLLER_BUTTON_B);return true;});assert(!menu.active());
 assert(menu.open(0,initial));tick(ControlsMenuCommand::PreviousPage);assert(menu.lines(Family::Xbox)[2].text.find("D left")!=std::string::npos);
 tick(ControlsMenuCommand::NextPage);assert(menu.lines(Family::Xbox)[2].text.find("N64 A")!=std::string::npos);
 tick(ControlsMenuCommand::Accept);tick(ControlsMenuCommand::Cancel);assert(!menu.capturing()&&menu.active());
 for(int i=0;i<14;++i){tick(ControlsMenuCommand::Down);}tick(ControlsMenuCommand::Accept);assert(menu.lines(Family::Nintendo)[1].text.find("Xbox")!=std::string::npos);
 tick(ControlsMenuCommand::RestoreDefault);assert(menu.lines(Family::Nintendo)[1].text.find("Auto Nintendo")!=std::string::npos);
 tick(ControlsMenuCommand::Cancel);return 0;}
'''
@unittest.skipUnless((ROOT/'.local/deps/N64Recomp/include/recomp.h').exists(),'Pinned native headers required')
class GameControlsMenuTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();d=Path(cls.tmp.name);(d/'test.cpp').write_text(HARNESS);cls.binary=d/'test'
  includes=['src','.local/deps/N64Recomp/include','.local/deps/N64ModernRuntime/librecomp/include','.local/deps/N64ModernRuntime/ultramodern/include','.local/deps/N64ModernRuntime/thirdparty','.local/deps/N64ModernRuntime/thirdparty/concurrentqueue']
  result=subprocess.run(['c++','-std=c++20','-Wall','-Wextra','-Werror','-pthread',*['-I'+str(ROOT/i) for i in includes],'-I/home/linuxbrew/.linuxbrew/include/SDL2',str(d/'test.cpp'),str(ROOT/'src/runtime/game_controls_menu.cpp'),'-o',str(cls.binary)],capture_output=True,text=True)
  if result.returncode:raise RuntimeError(result.stderr)
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def test_conflicting_draft_is_rejected_until_swap_is_completed(self):subprocess.run([str(self.binary),'conflict'],check=True,timeout=10)
 def test_restore_defaults_clears_conflict_and_preserves_axis_fallbacks(self):subprocess.run([str(self.binary),'conflict_restore'],check=True,timeout=10)
 def test_cancel_does_not_apply_draft(self):subprocess.run([str(self.binary),'cancel'],check=True,timeout=10)
 def test_capture_pagination_family_and_save_outside_mutex(self):subprocess.run([str(self.binary),'save'],check=True,timeout=10)

 def test_actual_original_font_emits_gfx_preserving_context_stack_and_bounds(self):
  rom=ROOT/'.local/inputs/pal-en-de/rom.z64';folder=ROOT/'.local/pal-map-bound-01/functions';analysis=ROOT/'.local/pal-map-bound-01/section-analysis.json'
  if not all(p.is_file() for p in [rom,analysis]):self.skipTest('Private PAL input and original translations required')
  image=rom.read_bytes();self.assertEqual(hashlib.sha256(image).hexdigest(),'6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf')
  functions={f['vram']:f for f in json.loads(analysis.read_text())[0]['functions']};pending=[0x80048660,0x800019FC];seen=set()
  while pending:
   pc=pending.pop()
   if pc in seen:continue
   seen.add(pc);f=functions[pc]
   for word in struct.unpack_from('>'+str(f['size']//4)+'I',image,pc-0x80000400+0x1000):
    if word>>26==3:pending.append(0x80000000|((word&0x3ffffff)<<2))
  self.assertEqual(len(seen),31)
  with tempfile.TemporaryDirectory() as temp:
   d=Path(temp);closure=d/'original.c';closure.write_text('\n'.join('#include '+json.dumps(str(folder/f'func_{pc:08X}_resident.c')) for pc in sorted(seen)))
   header=ROOT/'.local/deps/N64Recomp/include'
   built=subprocess.run(['cc','-O1','-fno-strict-aliasing','-fexceptions','-I'+str(header),'-c',str(closure),'-o',str(d/'original.o')],capture_output=True,text=True);self.assertEqual(built.returncode,0,built.stderr)
   source=d/'font.cpp';source.write_text(FONT_HARNESS.replace('ORIGINAL_HEADER','#include '+json.dumps(str(folder/'funcs.h'))).replace('ORIGINAL_LOOKUP','\n'.join(f'case 0x{pc:08X}u:return &func_{pc:08X}_resident;' for pc in sorted(seen))))
   includes=['src','.local/deps/N64Recomp/include','.local/deps/N64ModernRuntime/librecomp/include','.local/deps/N64ModernRuntime/ultramodern/include','.local/deps/N64ModernRuntime/thirdparty','.local/deps/N64ModernRuntime/thirdparty/concurrentqueue']
   built=subprocess.run(['c++','-std=c++20','-O1','-pthread',*['-I'+str(ROOT/i) for i in includes],'-I/home/linuxbrew/.linuxbrew/include/SDL2',str(source),str(d/'original.o'),str(ROOT/'src/runtime/game_controls_menu.cpp'),'-o',str(d/'font')],capture_output=True,text=True);self.assertEqual(built.returncode,0,built.stderr)
   ran=subprocess.run([str(d/'font'),str(rom)],capture_output=True,text=True);self.assertEqual(ran.returncode,0,ran.stderr)

FONT_HARNESS=r'''
#include "runtime/game_controls_menu.hpp"
#include "recomp.h"
#include <cassert>
#include <cstring>
#include <cstdlib>
#include <fstream>
#include <iterator>
ORIGINAL_HEADER
extern "C" recomp_func_t* get_function(int32_t a){switch(uint32_t(a)){ORIGINAL_LOOKUP
default:std::abort();}}
extern "C" void switch_error(const char*,uint32_t,uint32_t){std::abort();}
extern "C" void do_break(uint32_t){std::abort();}
void font_and_odd_register(uint8_t* ram,recomp_context* context){func_80048660_resident(ram,context);assert(context->f_odd);*context->f_odd=0xDEADBEEF;}
int main(int,char** argv){std::ifstream file(argv[1],std::ios::binary);std::vector<uint8_t> rom((std::istreambuf_iterator<char>(file)),{}),ram(0x800000);
 for(uint32_t i=0x1000;i<0xae920;++i)ram[(i-0x1000+0x400)^3]=rom[i];
 auto word=[&](uint32_t a,uint32_t v){std::memcpy(ram.data()+(a&0x7fffff),&v,4);};
 auto get=[&](uint32_t a){uint32_t v;std::memcpy(&v,ram.data()+(a&0x7fffff),4);return v;};
 auto half=[&](uint32_t a,uint16_t v){std::memcpy(ram.data()+((a&0x7fffff)^2),&v,2);};
 half(0x80100014,320);half(0x80100016,240);half(0x80100006,123);half(0x80100008,45);half(0x8010000A,67);half(0x8010000C,1);
 word(0x800E037C,0x800E032C);word(0x8009E02C,0x80100000);word(0x800A4AA4,0x800D0320);word(0x8009E0C8,0x800D0328);word(0x80165D64,0xffffffff);
 for(auto a:{0x80165D5D,0x80165D5F,0x80165D61,0x80165D63})ram[(a&0x7fffff)^3]=255;
 recomp_context ctx{};ctx.r29=S32(0x800A4000);ctx.r4=0x12345678;ctx.f_odd=&ctx.f0.u32h;auto original=ctx;auto before=ram;
 std::array<iss2000::EngineTextLine,2> lines{{{24,32,"Remap"},{24,48,"N64 A   Cross"}}};
 assert(iss2000::draw_pal_engine_text(ram,ctx,lines,&font_and_odd_register));
 assert(std::memcmp(&original,&ctx,sizeof(ctx))==0);assert(std::memcmp(ram.data()+0xA3C00,before.data()+0xA3C00,0x400)==0);
 auto original_frame=std::array<uint32_t,3>{get(0x80100004),get(0x80100008),get(0x8010000C)};
 auto clear_start=get(0x8009E0C8),fixup=get(0x800E037C);
 assert(iss2000::draw_pal_engine_text(ram,ctx,lines,&func_80048660_resident,&func_800019FC_resident));
 assert(get(0x800E037C)==fixup+4);assert(get(fixup)>=clear_start&&get(fixup)<get(0x8009E0C8));
 assert(get(0x80100004)==original_frame[0]&&get(0x80100008)==original_frame[1]&&get(0x8010000C)==original_frame[2]);
 bool black=false,fullrect=false;
 for(auto a=clear_start;a<clear_start+80;a+=8){if(get(a)==0xF7000000)black=get(a+4)==0x00010001;if(get(a)==0xF64FC3BC)fullrect=true;}assert(black&&fullrect);
 word(0x800E037C,0);before=ram;assert(!iss2000::draw_pal_engine_text(ram,ctx,lines,&func_80048660_resident,&func_800019FC_resident));assert(ram==before);
 for(auto invalid:{0x800E037Cu,0x800E032Eu,0x800E0328u}){word(0x800E037C,invalid);before=ram;assert(!iss2000::draw_pal_engine_text(ram,ctx,lines,&func_80048660_resident,&func_800019FC_resident));assert(ram==before);}
 word(0x800E037C,fixup+4);word(0x8009E02C,0x807FFFEC);before=ram;assert(!iss2000::draw_pal_engine_text(ram,ctx,lines,&func_80048660_resident,&func_800019FC_resident));assert(ram==before);word(0x8009E02C,0x80100000);
 ctx.f_odd=&ctx.f1.u32l;ctx.mips3_float_mode=1;original=ctx;
 assert(iss2000::draw_pal_engine_text(ram,ctx,lines,&font_and_odd_register));assert(std::memcmp(&original,&ctx,sizeof(ctx))==0);
 uint32_t external_odd=123;ctx.f_odd=&external_odd;before=ram;assert(!iss2000::draw_pal_engine_text(ram,ctx,lines,&font_and_odd_register));assert(ram==before&&external_odd==123);
 ctx.f_odd=&ctx.f0.u32h;ctx.mips3_float_mode=0;
 assert(get(0x8009E0C8)>0x800D0328&&get(0x8009E0C8)<0x800E0328);assert(get(0x800BDB20)==0x80041980);
 assert(get(0x800BDB24)==0xffffffff&&get(0x800BDB28)==0xffff0000);
 iss2000::GameControlsMenu menu;assert(menu.open(3,{}));
 for(auto family:{iss2000::platform::Family::Xbox,iss2000::platform::Family::Nintendo,iss2000::platform::Family::PlayStation}){
  for(int row=0;row<18;++row){word(0x8009E0C8,0x800D0328);assert(iss2000::draw_pal_engine_text(ram,ctx,menu.lines(family),&func_80048660_resident));menu.update(iss2000::ControlsMenuCommand::Down,0,family,{});}
 }
 word(0x800A4AA4,0x800E0380);word(0x8009E0C8,0x800E0388);assert(iss2000::draw_pal_engine_text(ram,ctx,lines,&func_80048660_resident));
 word(0x800A4AA4,0x800D0320);word(0x8009E0C8,0x800E0320);before=ram;assert(!iss2000::draw_pal_engine_text(ram,ctx,lines,&func_80048660_resident));assert(ram==before);
 word(0x8009E0C8,0x800D0328);lines[0].text="Unsupported!";before=ram;assert(!iss2000::draw_pal_engine_text(ram,ctx,lines,&func_80048660_resident));assert(ram==before);
 lines[0].text="Remap";ctx.r29=S32(0x800A0300);before=ram;assert(!iss2000::draw_pal_engine_text(ram,ctx,lines,&func_80048660_resident));assert(ram==before);
 return 0;}

'''
