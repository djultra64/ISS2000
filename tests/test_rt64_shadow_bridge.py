"""Original project work: djultra64. Scoped VTX adapter mechanics, no GPU claims."""
from pathlib import Path
import re,shutil,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class ShadowBridgeTests(unittest.TestCase):
 def test_exact_vtx_chunks_original_once_group_restore_foreign_and_lifetimes(self):
  if not shutil.which('c++'):self.skipTest('C++ compiler required')
  previous=(ROOT/'tests/test_rt64_transform_bridge.py').read_text();fake=re.search("fake=r'''(.*?)'''",previous,re.S).group(1)
  fake=fake.replace('int modelMatrixStackSize=1;','int modelMatrixStackSize=1;bool modelViewProjChanged=false;std::array<uint32_t,32>modelMatrixPhysicalAddressStack{};')
  fake=fake.replace('struct State{RSP* rsp{};',"enum class DrawAttribute{PrimDepth};struct RDP{struct Float2{float x{},y{};};struct Float4{float x{},y{},z{},w{};};std::array<Float2,16>primDepthStack{};int primDepthStackSize=1;struct{uint32_t L{},H{};}otherMode;std::array<Float4,16>primColorStack{};int primColorStackSize=1;struct Combiner{uint32_t L{},H{};};std::array<Combiner,16>colorCombinerStack{};int colorCombinerStackSize=1;};struct State{RSP* rsp{};")
  fake=fake.replace(';}ext;};',';}ext;RDP*rdp{};uint8_t*RDRAM{};void updateDrawStatusAttribute(DrawAttribute){}uint8_t*fromRDRAM(uint32_t p){return RDRAM+(p&0x7fffff);}};')
  code=r'''#include "fake.hpp"
#include "runtime/rt64_shadow_bridge.hpp"
#include <cassert>
#include <cstring>
#include <stdexcept>
using namespace iss2000;using namespace RT64;
static unsigned calls,interpolated;static bool fail;static uint32_t observed;
void original(State*s,DisplayList**){++calls;auto&r=*s->rsp;const auto g=r.extended.modelMatrixIdStack[r.extended.modelMatrixIdStackSize-1];observed=g.matrixId;
 if(g.vertexInterpolation==G_EX_COMPONENT_INTERPOLATE){++interpolated;assert(r.modelViewProjChanged);assert(!g.decompose&&g.positionInterpolation==G_EX_COMPONENT_SKIP&&g.rotationInterpolation==G_EX_COMPONENT_SKIP&&g.scaleInterpolation==G_EX_COMPONENT_SKIP&&g.perspectiveInterpolation==G_EX_COMPONENT_SKIP&&g.skewInterpolation==G_EX_COMPONENT_SKIP&&g.texcoordInterpolation==G_EX_COMPONENT_SKIP&&g.tileInterpolation==G_EX_COMPONENT_SKIP&&g.lookAtInterpolation==G_EX_COMPONENT_SKIP);}
 r.modelViewProjChanged=false;if(fail)throw std::runtime_error("originalunwind");}
int main(){GBI gbi;gbi.map[1]=original;Interpreter interpreter{&gbi};RSP rsp;State state{&rsp,{&interpreter}};rsp.modelMatrixPhysicalAddressStack[0]=0x1a3f00;
 auto snapshot=std::make_shared<PalShadowTaskSnapshot>();snapshot->scene=0x604;snapshot->epoch=2;snapshot->bank=0;
 snapshot->tags.push_back({0x8014E964,0x803A9398,PalShadowIdFirst,PalShadowIdFirst+1,1,2});
 rsp.extended.modelMatrixIdStack[0].matrixId=71;const auto pristine=rsp.extended.modelMatrixIdStack[0];
 auto vertex=[&](uint32_t address,uint32_t cmd=0x0101C038){DisplayList command{cmd,address};auto*p=&command;gbi.map[1](&state,&p);};
 vertex(0x3A9398);assert(calls==1&&interpolated==0); // Existingmatrix-onlypath cannot interpolate shadow vertices.
 {RT64ShadowBridge bridge(&state,&gbi,snapshot,true);assert(bridge.installed());RT64ShadowBridge nested(&state,&gbi,snapshot,true);assert(!nested.installed());
  vertex(0x3A9398);assert(calls==2&&interpolated==1&&observed==PalShadowIdFirst);
  assert(!memcmp(&pristine,&rsp.extended.modelMatrixIdStack[0],sizeof pristine)&&rsp.modelViewProjChanged);
  vertex(0x3A9558,0x0100C018);assert(calls==3&&interpolated==2&&observed==PalShadowIdFirst+1);
  for(int bad=0;bad<7;++bad){auto before=interpolated;if(bad==1)rsp.perspective=false;if(bad==2)rsp.modelMatrixPhysicalAddressStack[0]=0x12340;
   if(bad==3)snapshot->scene=0x607;if(bad==4)snapshot->tags[0].epoch=3;if(bad==5)snapshot->tags[0].first_id=12;
   vertex(bad==0?0x3A9398+16:0x3A9398,bad==6?0x0101C03A:0x0101C038);assert(interpolated==before&&observed==71);
   rsp.perspective=true;rsp.modelMatrixPhysicalAddressStack[0]=0x1a3f00;snapshot->scene=0x604;snapshot->tags[0].epoch=2;snapshot->tags[0].first_id=PalShadowIdFirst;}
  fail=true;try{vertex(0x3A9398);assert(false);}catch(const std::runtime_error&){}fail=false;
  assert(!memcmp(&pristine,&rsp.extended.modelMatrixIdStack[0],sizeof pristine)&&rsp.modelViewProjChanged);
  auto stats=bridge.stats();assert(stats.vertex_calls==10&&stats.shadow_chunks==3);
 }
 assert(gbi.map[1]==original);
 {RT64ShadowBridge off(&state,&gbi,snapshot,false);vertex(0x3A9398);assert(observed==71);}
 {RT64ShadowBridge missing(&state,&gbi,{},true);vertex(0x3A9398);assert(observed==71);}
 // New geometry is admitted only by the exact captured address/count pairs.
 // Merely being a24/8 vertex load or using identity is never sufficient.
 snapshot->tags.push_back({0x8014e9fc,0x807e0040,PalShadowIdFirst+8,PalShadowIdFirst+9,1,2,true});
 {RT64ShadowBridge projected(&state,&gbi,snapshot,true);
  for(unsigned chunk=0;chunk<4;++chunk){const auto before=interpolated;const auto count=chunk<3?24u:8u;const auto command=0x01000000|(count<<12)|(count<<1);vertex(0x7e0040+chunk*384,command);assert(interpolated==before+1&&observed==PalShadowIdFirst+8+chunk);
   vertex(0x7e0040+chunk*384+16,command);assert(interpolated==before+1&&observed==71);
   vertex(0x3a9398,command);assert(interpolated==before+1&&observed==71);
   vertex(0x7e0040+chunk*384,command+2);assert(interpolated==before+1&&observed==71);
  }
  vertex(0x7e0040,0x0101c038);assert(observed==71); // Old count cannot alias new geometry.
 }
 // Ball's sixteen vertices receive their own lifetime, never a human chunk.
 snapshot->tags.push_back({0x8014d23c,0x807ec840,PalShadowIdFirst+16,PalShadowIdFirst+17,1,2,true,true});
 {RT64ShadowBridge ball(&state,&gbi,snapshot,true);const auto before=interpolated;
  vertex(0x7ec840,0x01010020);assert(interpolated==before+1&&observed==PalShadowIdFirst+16);
  vertex(0x7ec840+16,0x01010020);assert(interpolated==before+1&&observed==71);
  vertex(0x7ec840,0x01018030);assert(interpolated==before+1&&observed==71);
  vertex(0x7e0040,0x01010020);assert(interpolated==before+1&&observed==71);
 }
 GBI other;other.map[1]=original;Interpreter otherInterpreter{&other};RSP otherRsp;State otherState{&otherRsp,{&otherInterpreter}};
 RT64ShadowBridge mismatch(&otherState,&gbi,snapshot,true);assert(!mismatch.installed());assert(other.map[1]==original);
 std::weak_ptr<const PalShadowTaskSnapshot> weak=snapshot;{RT64ShadowBridge lifetime(&state,&gbi,snapshot,true);snapshot.reset();assert(!weak.expired());}assert(weak.expired());
}
'''
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);(p/'fake.hpp').write_text(fake)
   for name in ['gbi/rt64_gbi.h','hle/rt64_interpreter.h','hle/rt64_rsp.h','hle/rt64_state.h','hle/rt64_rdp.h']:
    target=p/name;target.parent.mkdir(exist_ok=True);target.write_text('#include "fake.hpp"\n')
   (p/'test.cpp').write_text(code)
   q=subprocess.run(['c++','-std=c++20','-O2','-I'+str(p),'-I'+str(ROOT/'src'),str(p/'test.cpp'),str(ROOT/'src/runtime/rt64_shadow_bridge.cpp'),str(ROOT/'src/runtime/pal_shadow_vertices.cpp'),str(ROOT/'src/runtime/graphics_task_bank.cpp'),'-pthread','-o',str(p/'test')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
   q=subprocess.run([str(p/'test')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
