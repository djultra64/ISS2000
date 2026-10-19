"""Exercise the production title wrapper against real owned PAL draw bytes.

Original project work: djultra64. CPU-only; original execution and font boundaries
are instrumented, while title planning/suppression is the actual production module.
"""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
MINIZ=ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz'
MINIZ_BUILD=ROOT/'.local/runtime-deps-build/librecomp/miniz'


@unittest.skipUnless(shutil.which('c++') and (MINIZ_BUILD/'libminiz.a').is_file(),'Compiler and pinned miniz required')
class NativeTitlePromptTests(unittest.TestCase):
    def test_production_wrapper_preserves_original_context_and_requires_font_success_before_suppression(self):
        snapshot=ROOT/'.local/title-acceptance-01/completed-title11.rdram'
        rom=ROOT/'.local/inputs/pal-en-de/rom.z64'
        if not snapshot.is_file() or not rom.is_file():self.skipTest('Private completed original PAL title draw and pinned ROM required')
        native=(ROOT/'src/runtime/native_game.cpp').read_text()
        # Execute the actual whole-frame prefix before the controller-screen gate.
        # Removing its title adaptation, or moving adaptation inside that gate,
        # must leave the real20 title calls unsuppressed and fail below.
        helper_match=re.search(r'void adapt_physical_title_model\([^}]*',native)
        self.assertIsNotNone(helper_match,'Whole-frame title adaptation is not implemented')
        def function(name):
            start=native.index('void '+name+'('); opening=native.index('{',start);depth=1;end=opening+1
            while depth:
                if native[end]=='{':depth+=1
                elif native[end]=='}':depth-=1
                end+=1
            return native[start:end]
        helper=function('adapt_physical_title_model')
        wrapper='void draw_original_controller_menu('+native.split('void draw_original_controller_menu(',1)[1].split('    auto& menu=game_controls_menu();',1)[0]+'}'
        hook=re.search(r'    if\(uint32_t\(address\)==0x80000BB8u\)return &iss2000::draw_original_controller_menu;',native).group()
        header=(ROOT/'src/platform.hpp').read_text()
        declarations='\n'.join(re.search(pattern,header).group() for pattern in (
            r'enum class Family \{[^}]+\};',r'enum class Action \{[^}]+\};',r'struct Prompt \{[^}]+\};'))
        code=r'''#include "recomp.h"
#include "runtime/prompt_title_model.hpp"
#include "runtime/menu_sprite_runtime.hpp"
#include "runtime/pal_sky_widescreen.hpp"
#include <cassert>
#include <cstring>
#include <fstream>
#include <iostream>
#include <span>
#include <string>
#include <vector>
using Bytes=std::vector<uint8_t>;
constexpr uint32_t begin=0x800e0388,end=0x800e1e10;
uint32_t word(const uint8_t*r,uint32_t p){uint32_t v;std::memcpy(&v,r+(p&0x7fffff),4);return v;}
void put(uint8_t*r,uint32_t p,uint32_t v){std::memcpy(r+(p&0x7fffff),&v,4);}
unsigned original_calls{},font_calls{};bool font_success=true,original_font=true,corrupt_after_font=false,wrong_arena=false;
extern "C" void func_80048660_resident(uint8_t*,recomp_context*){}
extern "C" void foreign_font(uint8_t*,recomp_context*){}
void original_frame(uint8_t*ram,recomp_context*ctx){
 ++original_calls;ctx->r2=0x12345678;ctx->r4=0x87654321;ctx->f8.u64=0x1000200030004000;
 put(ram,0x8009e0c8,end);if(wrong_arena)put(ram,0x800a4aa4,0x800d0320);
}
namespace iss2000 {
struct FakeRegistry {recomp_func_t* find(uint32_t a){
 if(a==0x80048660)return original_font?func_80048660_resident:foreign_font;
 return nullptr;
}} registry;
void run_original_guest(uint32_t pc,uint8_t*ram,recomp_context*ctx){assert(pc==0x80000BB8);original_frame(ram,ctx);}
namespace platform {
DECLARATIONS
Prompt prompt(int port,Action action){assert(port==0&&action==Action::Start);return {"Options","Options",Family::PlayStation};}
}
struct EngineTextLine {int16_t x{},y{};std::string text;};
bool draw_pal_engine_text(std::span<uint8_t>ram,const recomp_context&ctx,std::span<const EngineTextLine>lines,recomp_func_t*draw){
 ++font_calls;assert(original_calls==1&&draw==func_80048660_resident);
 assert(ctx.r2==0x12345678&&ctx.r4==0x87654321&&ctx.f8.u64==0x1000200030004000);
 assert(lines.size()==1&&lines[0].text=="PRESS Options"&&lines[0].x==121&&lines[0].y==164);
 // The font must see all20 owned original calls still intact. Failed preflight
 // leaves every command untouched; success appends outside the original pass.
 for(unsigned n=0;n<20;++n)assert(word(ram.data(),0x800e19b0+n*0x38)==0xde000000);
 if(!font_success)return false;
 put(ram.data(),end,0xe7000000);put(ram.data(),end+4,0);put(ram.data(),0x8009e0c8,end+8);
 if(corrupt_after_font)put(ram.data(),0x800e19b4,0);
 return true;
}
void runtime_message(const char*message){std::cerr<<message<<'\n';}
void draw_startup_loading(uint8_t*,recomp_context*){}
void draw_main_select_exit(uint8_t*,recomp_context*){} // Unrelated scene; its real CPU rendering has a separate fixture.
HELPER
WRAPPER
}
recomp_func_t* hook_lookup(uint32_t address){
HOOK
 return nullptr;
}
int main(int argc,char**argv){
 assert(argc==4);std::ifstream rom_file(argv[3],std::ios::binary);Bytes rom((std::istreambuf_iterator<char>(rom_file)),{});
 assert(iss2000::configure_menu_sprite_runtime(rom));
 std::ifstream input(argv[1],std::ios::binary);Bytes ram(0x800000);
 input.read(reinterpret_cast<char*>(ram.data()),ram.size());assert(bool(input));
 const std::string mode=argv[2];font_success=mode!="font_fail";original_font=mode!="foreign_font";
 corrupt_after_font=mode=="changed_after_font";wrong_arena=mode=="wrong_arena";
 auto hook=hook_lookup(0x80000BB8);assert(hook==iss2000::draw_original_controller_menu);
 assert(!hook_lookup(0x8002B618)&&!hook_lookup(0x80000BBC));
 put(ram.data(),0x8009e0c8,begin);const auto before=ram;
 recomp_context context{};context.r29=0x800a4000;context.f_odd=&context.f0.u32h;
 auto expected=context;expected.r2=0x12345678;expected.r4=0x87654321;expected.f8.u64=0x1000200030004000;
 hook(ram.data(),&context);
 assert(original_calls==1&&std::memcmp(&context,&expected,sizeof context)==0);
 if(mode=="foreign_font"||wrong_arena)assert(font_calls==0);else assert(font_calls==1);
 const bool suppressed=font_success&&original_font&&!wrong_arena;
 for(unsigned n=0;n<20;++n){auto p=0x800e19b0+n*0x38;
  assert(word(ram.data(),p)==(suppressed?0:0xde000000));
  if(suppressed)assert(word(ram.data(),p+4)==0);
  else assert(word(ram.data(),p+4)==word(before.data(),p+4));
 }
 if(suppressed){assert(word(ram.data(),end)==0xe7000000&&word(ram.data(),0x8009e0c8)==end+8);}
 else assert(word(ram.data(),0x8009e0c8)==end);
 // CPU/Gfx cursor changes are instrumented; every other byte outside the20
 // original DE commands and appended font command must remain original.
 for(unsigned n=0;n<ram.size();++n){bool allowed=n>=0x9e0c8&&n<0x9e0cc;
  if(wrong_arena&&n>=0xa4aa4&&n<0xa4aa8)allowed=true;
  if(suppressed){allowed|=n>=(end&0x7fffff)&&n<(end&0x7fffff)+8;
   for(unsigned j=0;j<20;++j)allowed|=n>=0xe19b0+j*0x38&&n<0xe19b8+j*0x38;}
  if(!allowed)assert(ram[n]==before[n]);
 }
}
'''.replace('DECLARATIONS',declarations).replace('HELPER',helper).replace('WRAPPER',wrapper).replace('HOOK',hook)
        with tempfile.TemporaryDirectory()as directory:
            folder=Path(directory);source=folder/'native-title.cpp';source.write_text(code);exe=folder/'native-title'
            result=subprocess.run(['c++','-std=c++20','-O1','-Wall','-Wextra','-Werror','-I'+str(ROOT/'src'),'-I'+str(ROOT/'.local/deps/N64Recomp/include'),'-I'+str(MINIZ),'-I'+str(MINIZ_BUILD),str(source),str(ROOT/'src/runtime/menu_sprite_runtime.cpp'),str(ROOT/'src/runtime/pal_radar_interpolation.cpp'),str(ROOT/'src/runtime/graphics_task_bank.cpp'),str(ROOT/'src/runtime/prompt_title_model.cpp'),str(ROOT/'src/runtime/pal_sky_widescreen.cpp'),str(ROOT/'src/runtime/rom_image.cpp'),str(MINIZ_BUILD/'libminiz.a'),'-o',str(exe)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            for mode in ('success','font_fail','foreign_font','wrong_arena'):
                result=subprocess.run([str(exe),str(snapshot),mode,str(rom)],capture_output=True,text=True)
                self.assertEqual(result.returncode,0,mode+': '+result.stderr)
            result=subprocess.run([str(exe),str(snapshot),'changed_after_font',str(rom)],capture_output=True,text=True)
            self.assertEqual(result.returncode,1,result.stderr)
            self.assertIn('changed during its native font draw',result.stderr)

if __name__=='__main__':unittest.main()
