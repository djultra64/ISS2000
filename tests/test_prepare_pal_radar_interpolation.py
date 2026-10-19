"""Pinned producer preparation checks. Original project work: djultra64."""
from pathlib import Path
import importlib.util,unittest,subprocess,tempfile,json,re
ROOT=Path(__file__).resolve().parents[1]
class RadarPreparationTests(unittest.TestCase):
 def test_pinned_sources_and_explicit_emission_roles(self):
  tool=ROOT/'tools/prepare_pal_radar_interpolation.py'
  self.assertTrue(tool.is_file(),'Missing bounded radar preparation')
  spec=importlib.util.spec_from_file_location('radar_prepare',tool);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  source=(ROOT/'.local/pal-map-bound-01/functions/func_802A5290_overlay_376010_802a4380.c').read_bytes()
  result=m.derive(source).decode()
  self.assertEqual(result.count('radar_call(rdram, ctx,'),7)
  self.assertIn('0x100u + uint32_t(ctx->r16)',result)
  self.assertIn('0x200u + uint32_t(ctx->r16)',result)
  self.assertIn('iss2000_pal_radar_callback',result)
  with self.assertRaises(ValueError):m.derive(source+b'\n')

 def test_original_callback_has_exact_ram_and_register_parity(self):
  spec=importlib.util.spec_from_file_location('radar_prepare',ROOT/'tools/prepare_pal_radar_interpolation.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  folder=ROOT/'.local/pal-map-bound-01/functions';names=['802A5290','802A5230','802A5180','802A4DC0','802A4F78']
  fixture=ROOT/'.local/corrections-r55/baseline/field-b.rdram'
  if not fixture.is_file():self.skipTest('Private live PAL field snapshot required')
  code=r"""
#include "recomp.h"
#include "runtime/pal_radar_interpolation.hpp"
#include "runtime/menu_sprite_runtime.hpp"
#include "runtime/transform_runtime.hpp"
#include "runtime/pal_game_layout.hpp"
#include "runtime/pal_hud_widescreen.hpp"
#include "runtime/graphics_settings.hpp"
#include <set>
#include <vector>
#include <cassert>
#include <cstring>
#include <fstream>
#include <cstdlib>
DECLS
using namespace iss2000;
namespace iss2000::platform { GraphicsSettings render_settings(){return GraphicsSettings{};} }
WRAPPERS
static bool compose_wrappers=false;
extern "C" void iss2000_pal_radar_callback(uint8_t*,recomp_context*);
extern "C" recomp_func_t*get_function(int32_t a){if(compose_wrappers){if(uint32_t(a)==0x802a4dc0)return &align_training_radar_marker;if(uint32_t(a)==0x802a4f78)return &align_projected_radar_marker;}switch(uint32_t(a)){LOOKUP default:abort();}}
extern "C" void do_break(uint32_t){abort();}extern "C" void switch_error(const char*,uint32_t,uint32_t){abort();}
static unsigned observed=0;static std::vector<iss2000::PalRadarCommand> captured;
namespace iss2000 {
// Runtime boundary delegates to the real tracker, including releases/reallocation.
static TransformTracker allocations(verified_pal_transform_layout());
std::optional<TransformTag> lookup_transform_record(uint64_t a){return allocations.lookup_record(a);}
void retire_menu_radar_bank(uint32_t){}
void observe_menu_radar(std::span<const uint8_t> r,const PalRadarCapture& c){assert(c.unchanged(r));++observed;captured=c.commands();}
}
uint32_t word(const std::vector<uint8_t>&r,uint32_t a){uint32_t v;memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
int main(int argc,char**argv){std::vector<uint8_t> base(0x800000);std::ifstream f(argv[1],std::ios::binary);f.read((char*)base.data(),base.size());assert(f.gcount()==base.size());
 allocations.begin_scene(0x604);
 for(unsigned n=0;n<285;++n){const uint32_t p=0x80145624+n*0x98;if(word(base,p+0x28)&0x80000000u)allocations.allocate(p);}
 const std::set<uint32_t> ordinary={0x8014ec5c,0x8014eb2c,0x8014e9fc,0x8014e79c,0x8014e66c,0x8014e53c,0x8014e40c,0x8014e2dc,0x8014e1ac,0x8014e07c,0x8014df4c,0x8014de1c,0x8014dcec,0x8014dbbc,0x8014da8c,0x8014d95c,0x8014d82c,0x8014d6fc,0x8014d5cc,0x8014d49c};
 auto field_roots=ordinary;field_roots.insert(0x8014e8cc);field_roots.insert(0x8014d36c);assert(field_roots.size()==22);
 for(auto root:field_roots)assert(allocations.lookup_record(root));

 for(unsigned composed=0;composed<2;++composed)for(unsigned bank=0;bank<2;++bank)for(unsigned high=0;high<2;++high)for(unsigned projected=0;projected<2;++projected){
  compose_wrappers=composed;
  auto original=base;original[0x13b418^3]=0;original[0x13b419^3]=bank;original[0x13b42a^3]=high;original[0x12e6a3^3]=projected;auto instrumented=original;
  recomp_context a{},b{};a.r29=b.r29=int32_t(0x800a4000);a.r4=b.r4=int32_t(word(base,0x802b2950));a.f_odd=&a.f0.u32h;b.f_odd=&b.f0.u32h;
  func_802A5290_overlay_376010_802a4380(original.data(),&a);observed=0;iss2000_pal_radar_callback(instrumented.data(),&b);
  assert(original==instrumented);a.f_odd=nullptr;b.f_odd=nullptr;assert(memcmp(&a,&b,sizeof(a))==0);assert(observed==1);
  std::set<std::pair<uint32_t,uint32_t>> expected,actual;
  for(auto root:ordinary){expected.emplace(root,1);expected.emplace(root,2);}
  expected.emplace(0x8014e8cc,0x100);expected.emplace(0x8014d36c,0x104);
  expected.emplace(0x8014e8cc,0x200);expected.emplace(0x8014d36c,0x204);
  expected.emplace(0x8014e66c,0x300);expected.emplace(0x8014ceac,0x400);
  unsigned inset=0;
  for(const auto& c:captured){assert(c.role>>16==projected);actual.emplace(c.actor.record,c.role&0xffff);auto tag=allocations.lookup_record(c.actor.record);assert(tag&&tag->generation==c.actor.generation&&tag->id==c.actor.id);if(word(instrumented,c.pc+20)==(high?0x01f001f0u:0x03e003e0u))++inset;}
  assert(captured.size()==46);assert(actual==expected);
  if(composed)assert(inset>0);else assert(inset==0);
 }
 // A real release must suppress metadata; reallocation renews every role of that actor.
 const uint32_t target=0x8014e66c;const auto previous=*allocations.lookup_record(target);
 assert(allocations.release(target));assert(!allocations.lookup_record(target));
 for(unsigned renewed=0;renewed<2;++renewed){
  if(renewed){auto fresh=allocations.allocate(target);assert(fresh.generation==previous.generation+1&&fresh.id!=previous.id);}
  auto original=base,instrumented=base;recomp_context a{},b{};a.r29=b.r29=int32_t(0x800a4000);a.r4=b.r4=int32_t(word(base,0x802b2950));a.f_odd=&a.f0.u32h;b.f_odd=&b.f0.u32h;
  func_802A5290_overlay_376010_802a4380(original.data(),&a);observed=0;iss2000_pal_radar_callback(instrumented.data(),&b);
  assert(original==instrumented);a.f_odd=nullptr;b.f_odd=nullptr;assert(memcmp(&a,&b,sizeof(a))==0);assert(observed==renewed);
  if(renewed){unsigned roles=0;for(const auto&c:captured)if(c.actor.record==target){assert(c.actor.generation==previous.generation+1&&c.actor.id!=previous.id);++roles;}assert(roles==3);}
 }
}
"""
  native=(ROOT/'src/runtime/native_game.cpp').read_text()
  wrappers='\n'.join(re.search(r'void '+name+r'\(uint8_t\* rdram,recomp_context\* ctx\)\{.*?\n\}',native,re.S).group(0) for name in ['align_training_radar_marker','align_projected_radar_marker'])
  decls='\n'.join('extern "C" void func_'+n+'_overlay_376010_802a4380(uint8_t*,recomp_context*);' for n in names)
  lookup=''.join('case 0x'+n+':return func_'+n+'_overlay_376010_802a4380;' for n in names)
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);(p/'test.cpp').write_text(code.replace('DECLS',decls).replace('LOOKUP',lookup).replace('WRAPPERS',wrappers));(p/'radar.cpp').write_bytes(m.derive((folder/'func_802A5290_overlay_376010_802a4380.c').read_bytes()))
   (p/'original.c').write_text('\n'.join('#include '+json.dumps(str(folder/('func_'+n+'_overlay_376010_802a4380.c'))) for n in names))
   inc=str(ROOT/'.local/deps/N64Recomp/include')
   commands=[['cc','-O1','-fno-strict-aliasing','-I'+inc,'-c',str(p/'original.c'),'-o',str(p/'original.o')],['c++','-std=c++20','-O1','-fno-strict-aliasing','-I'+inc,'-I'+str(ROOT/'src'),str(p/'test.cpp'),str(p/'radar.cpp'),str(p/'original.o'),str(ROOT/'src/runtime/pal_radar_interpolation.cpp'),str(ROOT/'src/runtime/graphics_task_bank.cpp'),str(ROOT/'src/runtime/transform_tracker.cpp'),str(ROOT/'src/runtime/pal_hud_widescreen.cpp'),str(ROOT/'src/runtime/pal_sky_widescreen.cpp'),str(ROOT/'src/runtime/rom_image.cpp'),'-I'+str(ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz'),'-I'+str(ROOT/'.local/runtime-deps-build/librecomp/miniz'),'-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-o',str(p/'test')],[str(p/'test'),str(fixture)]]
   for cmd in commands:
    q=subprocess.run(cmd,capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
