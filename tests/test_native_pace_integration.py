"""Production PAL pace lookup rejects stale same-address function identities.

Original project work: djultra64. CPU-only lookup boundary; no game execution.
"""
from pathlib import Path
import re,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class NativePaceIntegrationTests(unittest.TestCase):
 def test_exact_production_lookup_requires_active_original_identity(self):
  source=(ROOT/'src/runtime/native_game.cpp').read_text()
  # Extract the whole production decision, including its identity condition.
  match=re.search(r'    if\([^\n]*0x80000C30u[^\n]*\)\n        return &iss2000_pal_native_frame_pace;',source)
  self.assertIsNotNone(match,'Exact PAL original frame lookup branch is missing')
  hook=match.group()
  code=r'''#include "recomp.h"
#include <cassert>
#include <cstdint>
static unsigned originals{},derived{},foreigns{},queries{};
extern "C" void func_80000C30_resident(uint8_t*,recomp_context* c){++originals;c->r2=0x11;}
extern "C" void iss2000_pal_native_frame_pace(uint8_t*,recomp_context* c){++derived;c->r2=0x22;}
extern "C" void foreign_original(uint8_t*,recomp_context* c){++foreigns;c->r2=0x33;}
namespace iss2000 {
struct Registry {
 recomp_func_t* active=nullptr;
 recomp_func_t* find(uint32_t address){++queries;assert(address==0x80000C30u);return active;}
} registry;
}
recomp_func_t* extracted_lookup(int32_t address){
HOOK
 return nullptr;
}
int main(){
 recomp_context context{};
 for(auto* active:{&func_80000C30_resident,&foreign_original,static_cast<recomp_func_t*>(nullptr)}){
  iss2000::registry.active=active;queries=0;
  auto* hook=extracted_lookup(int32_t(0x80000C30u));assert(queries==1);
  if(active==&func_80000C30_resident){assert(hook==&iss2000_pal_native_frame_pace);hook(nullptr,&context);assert(derived==1&&context.r2==0x22);}
  else assert(!hook);
  for(uint32_t address:{0x80000C2Cu,0x80000C34u,0xA0000C30u,0x00000C30u}){
   queries=0;assert(!extracted_lookup(int32_t(address)));assert(!queries);
  }
 }
 assert(derived==1&&originals==0&&foreigns==0);
}
'''.replace('HOOK',hook)
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'check.cpp').write_text(code)
   result=subprocess.run(['c++','-std=c++20','-Wall','-Wextra','-Werror','-I'+str(ROOT/'.local/deps/N64Recomp/include'),'-include','initializer_list',str(p/'check.cpp'),'-o',str(p/'check')],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
   result=subprocess.run([str(p/'check')],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
