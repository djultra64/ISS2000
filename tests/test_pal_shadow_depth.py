"""Original project work: djultra64. Original PAL primitive Z and pinned RT64 path."""
from pathlib import Path
import re,shutil,struct,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class PalShadowDepthTests(unittest.TestCase):
 def test_genuine_shadow_primitive_preserves_clear_blocker_and_overlap_distinction(self):
  snapshot=ROOT/'.local/training-timing-01/free-training-high43-completed.rdram'
  dep=ROOT/'.local/deps/rt64/src'
  if not shutil.which('c++') or not snapshot.is_file():self.skipTest('Private original PAL frame and compiler required')
  # Walk the genuine completed task through its real nested lists/segments.
  # Both original microcodes use this F3DEX2 command layout. Reject unknown
  # control opcodes rather than treating a payload as a later shadow command.
  ram=snapshot.read_bytes();word=lambda a:struct.unpack_from('<I',ram,a&0x7fffff)[0]
  pc=0xd0328;returns=[];segments=[0]*16;low=high=half=0;combine=(0,0);color=0;observed=[]
  for commands in range(16384):
   a,b=word(pc),word(pc+4);op=a>>24
   self.assertIn(op,{0xdb,0xde,0xe7,0xdc,0xed,0xd9,0xdf,0xff,0xfe,0xe3,0xf7,0xf6,0xf9,0xfc,0xe2,0xe0,0x64,0xfd,0xe8,0xf5,0xe6,0xf0,0xf3,0xf2,0xe4,0xe1,0xf1,0xda,0xfb,0xf8,0xd7,1,6,0xfa,5,0xdd,0xee,0xe9})
   if op==0xdb and a>>16&255==6:segments[(a&65535)//4]=b&0x7fffff
   if op==0xde:
    self.assertIn(a,{0xde000000,0xde010000})
    if not a&0x10000:returns.append(pc+8)
    self.assertLess(len(returns),32);pc=(segments[b>>24&15]+(b&0xffffff))&0x7ffff8;continue
   if op==0xdf:
    if not returns:break
    pc=returns.pop();continue
   if op==0xe1:half=b
   if op==0xdd:self.assertIn((b&0x7fffff,half&0x7fffff),{(0x69ad0,0x99ef0),(0x6ae60,0x9a310)})
   if op in (0xe2,0xe3):
    size=(a&255)+1;off=max(0,32-(a>>8&255)-size);mask=((1<<size)-1)<<off
    if op==0xe2:low=(low&~mask)|b
    else:high=(high&~mask)|b
   if op==0xfc:combine=(a&0xffffff,b)
   if op==0xfa:color=b
   if pc==0x83ae8:observed.append((low,high,combine,color,b))
   pc+=8*({2:3,5:2,6:2}.get(a&255,1)if op==0x64 else 1)
  else:self.fail('Original task walk exceeded bounded command count')
  self.assertEqual(len(observed),3)
  self.assertTrue(all(x==(0x5049fc,0x98ace0,(0xffffff,0xfffdf6fb),0xaa,0x7fff7fff)for x in observed))
  previous=(ROOT/'tests/test_rt64_transform_bridge.py').read_text();fake=re.search("fake=r'''(.*?)'''",previous,re.S).group(1)
  fake=fake.replace('int modelMatrixStackSize=1;','int modelMatrixStackSize=1;bool modelViewProjChanged=false;std::array<uint32_t,32>modelMatrixPhysicalAddressStack{};')
  fake=fake.replace('uint32_t p0(int,int)const{return w0&255;}','uint32_t p0(int o,int n)const{return (w0>>o)&((uint64_t(1)<<n)-1);}uint32_t p1(int o,int n)const{return (w1>>o)&((uint64_t(1)<<n)-1);}')
  fake=fake.replace('struct State{RSP* rsp{};',r'''enum class DrawAttribute{PrimDepth};
struct Float2{float x{},y{};};struct Float4{float x{},y{},z{},w{};};
struct RDP{std::array<Float2,16>primDepthStack{};int primDepthStackSize=1;struct{uint32_t L=0x5049fc,H=0x98ace0;}otherMode;
 std::array<Float4,16>primColorStack{};int primColorStackSize=1;struct Combiner{uint32_t L=0xfffdf6fb,H=0xffffff;};std::array<Combiner,16>colorCombinerStack{};int colorCombinerStackSize=1;
 State*state{};void setPrimDepth(uint16_t z,uint16_t dz);};
struct State{RSP* rsp{};''')
  state_source=(dep/'hle/rt64_state.cpp').read_text()
  depth_load=re.search(r'        if \(drawStatus.isChanged\(DrawAttribute::PrimDepth\)\) \{.*?\n        \}',state_source,re.S).group()
  check_draw=re.search(r'    bool State::checkDrawState\(\).*?\n    \}',state_source,re.S).group().replace('State::','')
  fake=fake.replace(';}ext;};',';}ext;RDP*rdp{};uint8_t*RDRAM{};unsigned depthChanges{};struct Status{bool changed{};bool isChanged(DrawAttribute)const{return changed;}bool isChanged()const{return changed;}void clearChanges(){changed=false;}}drawStatus;struct Call{struct{Float2 primDepth;}rdpParams;unsigned triangleCount{};}drawCall;std::vector<Call>calls;void updateDrawStatusAttribute(DrawAttribute){++depthChanges;drawStatus.changed=true;}void flush(){if(!drawCall.triangleCount)return;calls.push_back(drawCall);drawCall.triangleCount=0;}CHECK_DRAW void loadDrawState(){DEPTH_LOAD drawStatus.clearChanges();}void tri(){if(checkDrawState())loadDrawState();drawCall.triangleCount+=2;}uint8_t*fromRDRAM(uint32_t p){return RDRAM+(p&0x7fffff);}};')
  fake=fake.replace('CHECK_DRAW',check_draw).replace('DEPTH_LOAD',depth_load)
  # Execute the pinned real RDP conversion and GBI decoder, not replacement math.
  rdp=(dep/'hle/rt64_rdp.cpp').read_text();method=re.search(r'    void RDP::setPrimDepth\(.*?\n    \}',rdp,re.S).group().replace('hlslpp::float2','Float2')
  decoder=re.search(r'        void setPrimDepth\(State.*?\n        \}',(dep/'gbi/rt64_gbi_rdp.cpp').read_text(),re.S).group()
  depth_decode=re.search(r'    float ColorConverter::D16::toF\(.*?\n    \}',(dep/'hle/rt64_color_converter.cpp').read_text(),re.S).group().replace('ColorConverter::D16::toF','decode_depth')
  code=r'''#include "fake.hpp"
#include "runtime/rt64_shadow_bridge.hpp"
#include <cassert>
#include <algorithm>
#include <cmath>
#define DEPTH_EXPONENT_MASK 0xE000
#define DEPTH_MANTISSA_MASK 0x1FFC
#define DEPTH_EXPONENT_SHIFT 13
#define DEPTH_MANTISSA_SHIFT 2
#include <cstdio>
#include <cstring>
#include <stdexcept>
DEPTH_DECODE
namespace RT64{METHOD
DECODER
}
using namespace RT64;using namespace iss2000;
static unsigned eeCalls,e2Calls;static bool failReset;
void vertex(State*,DisplayList**){}
void ee(State*s,DisplayList**p){++eeCalls;setPrimDepth(s,p);}
void e2(State*s,DisplayList**p){++e2Calls;s->rdp->otherMode.L=(s->rdp->otherMode.L&~4u)|((*p)->w1&4u);if(failReset)throw std::runtime_error("original reset");}
int main(int argc,char**argv){assert(argc==2);std::vector<uint8_t>r(0x800000);auto*f=fopen(argv[1],"rb");assert(f&&fread(r.data(),1,r.size(),f)==r.size());fclose(f);const auto untouched=r;
 GBI gbi;gbi.map[1]=vertex;gbi.map[0xee]=ee;gbi.map[0xe2]=e2;Interpreter interpreter{&gbi};RSP rsp;RDP rdp;State state{&rsp,{&interpreter},&rdp,r.data()};rdp.state=&state;rdp.primColorStack[0]={0,0,0,170/255.f};
 auto snap=std::make_shared<PalShadowTaskSnapshot>();snap->scene=0x604;snap->epoch=2;snap->tags.push_back({0x8014e964,0x803a9398,PalShadowIdFirst,PalShadowIdFirst+1,1,2});
 auto call=[&](uint32_t a){auto*p=reinterpret_cast<DisplayList*>(state.fromRDRAM(a));gbi.map[p->w0>>24](&state,&p);};
 // Authentic primitive7FFF is 15.3 fixed point3FFF8, not maximum18-bit3FFFF.
 // RT64's own depth-image decoder represents that exact nonmax code identically.
 const float exact=262136.f/262143.f;assert(exact<1&&std::lround(exact*262143.f)==0x3fff8&&decode_depth(0xffe0)==exact&&decode_depth(0xfffc)==1.f);
 for(bool interpolate:{false,true}){
  rdp.otherMode.L=0x5049fc;rdp.primDepthStack[0]={.2f,.3f};
  {RT64ShadowBridge bridge(&state,&gbi,snap,interpolate);assert(bridge.installed());call(0x83ae8);
   assert(rdp.primDepthStack[0].x==exact); // RED: pinned /32767 maps it to1 and rejects clear.
   assert(rdp.primDepthStack[0].y==32767*(1.f/65535.f));
   assert(rdp.primDepthStack[0].x<1.f); // Original clear/max depth accepts first shadow.
   assert(!(rdp.primDepthStack[0].x<exact)); // Equal shadow overlap rejects; LEQUAL would double blend.
   assert(!(rdp.primDepthStack[0].x<.9f)); // A player/closer depth still occludes the shadow.
   assert(rdp.otherMode.L==0x5049fc&&r==untouched);
   state.calls.clear();state.drawCall.triangleCount=0;state.tri();state.tri();assert(state.drawCall.triangleCount==4&&state.calls.empty()&&state.drawCall.rdpParams.primDepth.x==exact);
   unsigned changes=state.depthChanges;call(0x83b80);assert(state.depthChanges>changes&&state.drawStatus.changed);state.tri();assert(state.calls.size()==1&&state.calls[0].triangleCount==4&&state.calls[0].rdpParams.primDepth.x==exact&&state.drawCall.rdpParams.primDepth.x==1);state.flush();assert(state.calls.size()==2&&state.calls[1].rdpParams.primDepth.x==1);assert(rdp.primDepthStack[0].x==1&&rdp.otherMode.L==0x5049f8);
  }
  assert(gbi.map[0xee]==ee&&gbi.map[0xe2]==e2);
 }
 // All unknown states call original once and retain the original conversion.
 for(int bad=0;bad<11;++bad){r=untouched;state.RDRAM=r.data();rdp.otherMode.L=0x5049fc;rdp.primColorStack[0]={0,0,0,170/255.f};rdp.colorCombinerStack[0]={};snap->scene=0x604;snap->tags[0].epoch=2;
  if(bad==0)snap->scene=0x607;if(bad==1)snap->tags[0].epoch=3;if(bad==2)rdp.primColorStack[0].w=.5f;if(bad==3)rdp.colorCombinerStack[0].L^=1;if(bad==4)rdp.otherMode.L^=0x20;if(bad==5)rsp.perspective=false;
  if(bad==6)r[0x83b88]^=1;if(bad==7){uint32_t v=0x7ffe7fff;memcpy(r.data()+0x83aec,&v,4);}if(bad==8)rdp.primColorStack[0].x=.1f;if(bad==9)rdp.otherMode.H=2u<<20;
  auto* foreign=reinterpret_cast<DisplayList*>(r.data()+0x1000);*foreign={0xee000000,0x7fff7fff};unsigned before=eeCalls;
  {RT64ShadowBridge bridge(&state,&gbi,snap,true);call(bad==10?0x1000:0x83ae8);assert(rdp.primDepthStack[0].x==(bad==7?32766*(1.f/32767.f):1.f));}
  assert(eeCalls==before+1);rsp.perspective=true;rdp.otherMode.H=0x98ace0;
 }
 r=untouched;state.RDRAM=r.data();rdp.otherMode.L=0x5049fc;rdp.primColorStack[0]={0,0,0,100/255.f};snap->scene=0x604;snap->tags[0].epoch=2;
 // Alternate authentic weather alpha and nested callback-map ownership.
 {RT64ShadowBridge bridge(&state,&gbi,snap,false);RT64ShadowBridge nested(&state,&gbi,snap,true);assert(!nested.installed());call(0x83ae8);assert(rdp.primDepthStack[0].x==exact);}
 assert(rdp.primDepthStack[0].x==1&&r==untouched);
 // Exception through original reset restores at outer bridge destruction.
 try{RT64ShadowBridge bridge(&state,&gbi,snap,true);call(0x83ae8);assert(rdp.primDepthStack[0].x==exact);failReset=true;call(0x83b80);assert(false);}catch(const std::runtime_error&){}failReset=false;
 assert(rdp.primDepthStack[0].x==1&&gbi.map[0xee]==ee&&gbi.map[0xe2]==e2);
 // Only the owned stack slot restores even if a caller clones/pushes RDP state.
 rdp.otherMode.L=0x5049fc;rdp.primDepthStackSize=1;rdp.primDepthStack[1]={.7f,.8f};{RT64ShadowBridge bridge(&state,&gbi,snap,true);call(0x83ae8);rdp.primDepthStackSize=2;call(0x83b80);assert(rdp.primDepthStack[0].x==1&&rdp.primDepthStack[1].x==.7f&&rdp.primDepthStack[1].y==.8f);}rdp.primDepthStackSize=1;
 // A foreign EE supersedes pending state; bridge teardown must not undo it.
 rdp.otherMode.L=0x5049fc;{RT64ShadowBridge bridge(&state,&gbi,snap,true);call(0x83ae8);auto*q=reinterpret_cast<DisplayList*>(r.data()+0x1000);*q={0xee000000,0x12345678};call(0x1000);assert(rdp.primDepthStack[0].x==0x1234*(1.f/32767.f));}assert(rdp.primDepthStack[0].x==0x1234*(1.f/32767.f));
 printf("Original PAL primitive18-bit3FFF8: clear accepts, blocker/equal overlap reject; Original/60/120 interpolation-independent.\n");
}
'''.replace('METHOD',method).replace('DECODER',decoder).replace('DEPTH_DECODE',depth_decode)
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);(p/'fake.hpp').write_text(fake)
   for name in ['gbi/rt64_gbi.h','hle/rt64_interpreter.h','hle/rt64_rsp.h','hle/rt64_state.h','hle/rt64_rdp.h']:
    target=p/name;target.parent.mkdir(exist_ok=True);target.write_text('#include "fake.hpp"\n')
   (p/'test.cpp').write_text(code)
   q=subprocess.run(['c++','-std=c++20','-O2','-I'+str(p),'-I'+str(ROOT/'src'),str(p/'test.cpp'),str(ROOT/'src/runtime/rt64_shadow_bridge.cpp'),str(ROOT/'src/runtime/pal_shadow_vertices.cpp'),str(ROOT/'src/runtime/graphics_task_bank.cpp'),'-pthread','-o',str(p/'test')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
   q=subprocess.run([str(p/'test'),str(snapshot)],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr);print(q.stdout.strip())
