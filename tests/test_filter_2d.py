"""2D-only filtering ownership, upstream sampler and immutable derivative checks."""
from pathlib import Path
import subprocess,tempfile,unittest
from tools.prepare_rt64_filter_2d import derive,prepare,FILTER
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'.local/deps/rt64/src/hle/rt64_state.cpp'
class Filter2DTests(unittest.TestCase):
 def test_policy_preserves_3d_copies_fill_and_disabled_draws(self):
  code=r'''#include "runtime/filter_2d.hpp"
#include "shared/rt64_other_mode.h"
#include "shared/rt64_render_flags.h"
#include <cassert>
#include <vector>
int main(){
 using iss2000::filter_2d_call;
 static_assert(G_CYC_1CYCLE==0&&G_CYC_2CYCLE==0x100000&&G_CYC_COPY==0x200000&&G_CYC_FILL==0x300000);
 for(bool enabled:{false,true})for(bool rect:{false,true})for(bool copy:{false,true})for(unsigned tiles:{0u,1u,2u,8u})for(unsigned cycle:{G_CYC_1CYCLE,G_CYC_2CYCLE,G_CYC_COPY,G_CYC_FILL}){
  auto result=filter_2d_call(enabled,rect,cycle,tiles,copy);
  if(!enabled||!rect||copy||!tiles||cycle==G_CYC_COPY||cycle==G_CYC_FILL)assert(!result);
  else assert(result);
 }
 // Simulate the exact injected shader boundary with genuine OtherMode values.
 struct{unsigned tileIndex=0,tileCount=1,triangleCount=2;interop::OtherMode otherMode{0x00504341,0x000030};}callDesc;
 struct Pair{float x=0,y=0;};
 struct{bool tileCopyUsed=false;Pair minTexcoord{},maxTexcoord{8,16};} tile;
 struct Rdp{float shifts=1,shiftt=1,uls=0,ult=0,lrs=28,lrt=60;unsigned cms=G_TX_WRAP,cmt=G_TX_WRAP;}rdp;
 struct{struct{decltype(tile)*callTiles;std::vector<float>triTcFloats;Rdp*rdpTiles;}drawData;}workload{{&tile,std::vector<float>(12,10.f),&rdp}};
 struct{unsigned rawVertexStart=0;}meshDesc;
 struct{bool rect=true,linearFiltering=false,dynamicTiles=false;unsigned cms0=0,cmt0=0,cms1=0,cmt1=0,nativeSampler0=1,nativeSampler1=1;}flags;
 bool filter2D=true;
 INJECTION
 assert(flags.linearFiltering&&callDesc.otherMode.L==0x00504341&&callDesc.otherMode.H==0x000030);
 for(float uv:workload.drawData.triTcFloats)assert(uv==9.5f);
 assert(flags.cms0==G_TX_CLAMP&&flags.cmt0==G_TX_CLAMP&&flags.nativeSampler0==NATIVE_SAMPLER_NONE);
}
'''.replace('INJECTION',FILTER)
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);(p/'test.cpp').write_text('#include <initializer_list>\n'+code)
   result=subprocess.run(['c++','-std=c++20','-DHLSL_CPU','-msse4.1','-I'+str(ROOT/'.local/deps/rt64/src/contrib/hlslpp/include'),'-I'+str(ROOT/'src'),'-I'+str(ROOT/'.local/deps/rt64/src'),str(p/'test.cpp'),'-o',str(p/'test')],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
   result=subprocess.run([str(p/'test')],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
 def test_exact_pinned_shader_boundary_and_output_guards(self):
  if not SOURCE.is_file():self.skipTest('Pinned RT64 source required')
  source=SOURCE.read_bytes();generated=derive(source)
  self.assertIn(b'flags.linearFiltering = true;',generated)
  self.assertIn(b'renderParams.flags = shaderDesc.flags;',generated)
  sampler=(ROOT/'.local/deps/rt64/src/shaders/TextureSampler.hlsli').read_text()
  self.assertIn('bool filtering = or(filterBilerp, linearFiltering);',sampler)
  self.assertIn('if (linearFiltering)',sampler)
  with tempfile.TemporaryDirectory()as d:
   out=Path(d)/'out';receipt=prepare(SOURCE,out);self.assertEqual(prepare(SOURCE,out),receipt)
   (out/'rt64_state.cpp').write_bytes(generated+b'\n')
   with self.assertRaises(ValueError):prepare(SOURCE,out)
  with self.assertRaises(ValueError):derive(source+b'\n')
