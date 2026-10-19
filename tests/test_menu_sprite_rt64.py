"""Original project work: djultra64. Adapter ownership/API mechanics; not GPU rendering proof."""
from pathlib import Path
import json,shlex,shutil,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
FAKE=r'''#pragma once
#include <array>
#include <vector>
#include <cstdint>
#include <utility>
#include <cassert>
struct RenderDevice{};enum class RenderBufferFlag{STORAGE};
namespace interop {
struct Vec{float v[4]{};float&operator[](unsigned i){return v[i];}const float&operator[](unsigned i)const{return v[i];}};
struct RDPParams{Vec primColor,envColor,primLOD,primDepth,fogColor,blendColor,keyCenter,keyScale;int convertK[6]{};};
struct RDPTile {int fmt{},siz{},stride{},address{},palette{},masks{},maskt{},cms{},cmt{};float shifts{},shiftt{},uls{},ult{},lrs{},lrt{};unsigned nativeSampler{};};
}
namespace RT64 {
struct State;struct DisplayList{uint32_t w0{},w1{};};using GBIFunction=void(*)(State*,DisplayList**);
enum class GBIUCode{Unknown,F3DEX2};struct GBI{GBIUCode ucode=GBIUCode::F3DEX2;GBIFunction map[256]{};};struct Interpreter{GBI*hleGBI{};GBIFunction extendedFunction{};};
struct FixedRect{int ulx{},uly{},lrx{},lry{};};struct Words{unsigned H{},L{};};
struct DrawCall{uint32_t uid{},callIndex{},triangleCount{2};FixedRect rect,scissorRect;Words otherMode,colorCombiner;int16_t rectDsdx{1024},rectDtdy{1024};uint16_t rectLeftOrigin{0x800},rectRightOrigin{0x800},scissorLeftOrigin{0x800},scissorRightOrigin{0x800};uint8_t rectAspect{},scissorMode{},textureOn{1},textureTile{},textureLevels{};uint32_t tileIndex{},tileCount{1},fillColor{};interop::RDPParams rdpParams;};
struct GameCall{DrawCall callDesc;struct{unsigned rawVertexStart{};}meshDesc;};
struct Projection{enum class Type{None,Perspective,Rectangle};Type type=Type::Rectangle;unsigned gameCallCount{};std::vector<GameCall>gameCalls;};
struct FramebufferPair{struct{uint8_t fmt{},siz{2};uint16_t width{320};uint32_t address{};}colorImage;unsigned projectionCount{};std::vector<Projection>projections;};
struct DrawCallTile{uint64_t tmemHashOrID{99};uint16_t sampleWidth{16},sampleHeight{16},lineWidth{16};unsigned tlut{};uint16_t tileCopyWidth{},tileCopyHeight{};bool reinterpretTile{},tileCopyUsed{},rawTMEM{true},valid{true};uint8_t reinterpretSiz{},reinterpretFmt{};};
struct BufferPair{};struct Workload{uint64_t submissionFrame{};struct{std::vector<interop::RDPParams>rdpParams;std::vector<DrawCallTile>callTiles;std::vector<interop::RDPTile>rdpTiles;std::vector<float>triTcFloats;}drawData;struct{BufferPair rdpParamsBuffer;}drawBuffers;unsigned fbPairCount{},gameCallCount{};std::vector<FramebufferPair>fbPairs;};
struct WorkloadQueue{std::array<Workload,4>workloads;unsigned writeCursor{};};
struct GameFrame{struct{struct Map{unsigned prevWorkloadIndex{};bool mapped{};};std::vector<Map>workloads;}frameMap;std::vector<unsigned>workloads;};
struct RenderWorker{RenderDevice*device{};};
struct BufferUploader{struct Upload{const void*srcData;std::pair<size_t,size_t>srcDataIndexRange;size_t srcDataStride;RenderBufferFlag bufferFlags;std::vector<unsigned>formatViews;BufferPair*dstPair;};inline static unsigned waits{},submissions{};std::vector<Upload>pending;BufferUploader(RenderDevice*){};void submit(RenderWorker*,const std::vector<Upload>&v){pending=v;++submissions;}void wait(){++waits;}};
struct State{uint8_t*RDRAM{};DrawCall drawCall;struct{Interpreter*interpreter{};WorkloadQueue*workloadQueue{};}ext;};
}
'''
CODE=r'''#include "fake.hpp"
#include "runtime/menu_sprite_render.hpp"
#include "runtime/menu_sprite_bridge.hpp"
#include <cassert>
#include <cstring>
using namespace iss2000;using namespace RT64;
unsigned calls{};void original(State*s,DisplayList**dl){++calls;if((*dl)->w1!=0xdead){auto&w=s->ext.workloadQueue->workloads[s->ext.workloadQueue->writeCursor];if(s->drawCall.triangleCount)++w.gameCallCount;s->drawCall.triangleCount=2;}(*dl)+=2;assert(s->drawCall.uid!=999);}
void extendedOriginal(State*s,DisplayList**dl){++calls;if(s->drawCall.triangleCount)++s->ext.workloadQueue->workloads[s->ext.workloadQueue->writeCursor].gameCallCount;s->drawCall.triangleCount=2;(*dl)+=2;}
void sample(Workload&w,unsigned uid){w.fbPairCount=1;w.fbPairs.resize(1);auto&f=w.fbPairs[0];f.projectionCount=1;f.projections.resize(1);auto&p=f.projections[0];p.gameCallCount=1;p.gameCalls.resize(1);auto&d=p.gameCalls[0].callDesc;d.uid=uid;d.rect={100,200,300,400};d.rdpParams.primColor[3]=.2f;w.drawData.rdpParams={d.rdpParams};w.drawData.callTiles.resize(1);w.drawData.rdpTiles.resize(1);w.drawData.triTcFloats={0,0,16,0,0,16,16,16,16,0,0,16};}
int main(){
 WorkloadQueue queue;queue.workloads[0].submissionFrame=8;queue.workloads[1].submissionFrame=9;
 std::vector<uint64_t>ram(0x800000/8);auto*dl=reinterpret_cast<DisplayList*>(ram.data());
 GBI gbi;gbi.map[0xe4]=original;gbi.map[0xe5]=original;gbi.map[0xf6]=original;Interpreter interpreter{&gbi,extendedOriginal};State state{reinterpret_cast<uint8_t*>(ram.data()),{}, {&interpreter,&queue}};
 auto snapshot=std::make_shared<MenuSpriteTaskSnapshot>();snapshot->sequence=80;snapshot->epoch=3;snapshot->commands={{0,7},{16,8}};
 {MenuSpriteBridge b(&state,&gbi,snapshot,true);assert(b.installed());MenuSpriteBridge nested(&state,&gbi,snapshot,true);assert(!nested.installed());auto*p=dl;gbi.map[0xe4](&state,&p);assert(p==dl+2&&calls==1&&state.drawCall.uid==7);p=dl+2;dl[2].w0=0x64000002;interpreter.extendedFunction(&state,&p);assert(state.drawCall.uid==8&&calls==2);p=dl+4;gbi.map[0xe4](&state,&p);assert(state.drawCall.uid==0&&calls==3);p=dl;gbi.map[0xe4](&state,&p);assert(state.drawCall.uid==7);dl[2].w1=0xdead;p=dl+2;gbi.map[0xe4](&state,&p);assert(state.drawCall.uid==7);dl[2].w1=0;p=dl+4;gbi.map[0xf6](&state,&p);assert(state.drawCall.uid==0);p=dl;gbi.map[0xe4](&state,&p);assert(state.drawCall.uid==7);p=dl+4;gbi.map[0xe5](&state,&p);assert(state.drawCall.uid==0);p=dl;interpreter.extendedFunction(&state,&p);assert(state.drawCall.uid==0);}
 assert(gbi.map[0xe4]==original&&interpreter.extendedFunction==extendedOriginal);
 {MenuSpriteBridge b(&state,&gbi,snapshot,false);auto*p=dl;gbi.map[0xe4](&state,&p);assert(state.drawCall.uid==0);}
 // New slot generation; exactly adjacent queue frames and matching materials.
 auto&old=queue.workloads[0];auto&now=queue.workloads[1];++old.submissionFrame;++now.submissionFrame;sample(old,7);sample(now,7);now.fbPairs[0].colorImage.address=0x307800;old.fbPairs[0].colorImage.address=0x32d000;
 auto&d=now.fbPairs[0].projections[0].gameCalls[0].callDesc;d.rect.ulx+=32;d.rect.lrx+=32;d.rdpParams.primColor[3]=.8f;now.drawData.rdpParams[0]=d.rdpParams;
 snapshot->sequence=100;record_menu_workload(&old,snapshot.get(),true);snapshot->sequence=101;record_menu_workload(&now,snapshot.get(),true);
 GameFrame previous,current;previous.workloads={0};current.workloads={1};current.frameMap.workloads.resize(4);current.frameMap.workloads[1]={0,true};RenderDevice device;RenderWorker worker{&device};
 MenuRectPrevious bounds;assert(!menu_rect_previous(&now,0,bounds));
 {MenuRectRenderScope scope(&queue,&now,&current,&previous,.25f,&worker);assert(menu_rect_previous(&now,0,bounds)&&bounds.rect[0]==100&&bounds.weight==.25f);assert(!menu_rect_previous(&old,0,bounds));auto stats=menu_rect_render_stats();assert(stats.rectangles==1&&stats.matches==1&&stats.moved==1&&stats.fades==1&&stats.fractional);auto*u=scope.uploader();assert(u&&u->pending.size()==1);auto*p=static_cast<const interop::RDPParams*>(u->pending[0].srcData);assert(p!=now.drawData.rdpParams.data());assert(p[0].primColor[3]>.349f&&p[0].primColor[3]<.351f);assert(now.drawData.rdpParams[0].primColor[3]==.8f); // owned through simulated fence/read
  {MenuRectRenderScope nested(&queue,&now,&current,&previous,1,nullptr);assert(menu_rect_previous(&now,0,bounds)&&bounds.weight==1);}assert(menu_rect_previous(&now,0,bounds)&&bounds.weight==.25f);
 }
 assert(!menu_rect_previous(&now,0,bounds)&&BufferUploader::waits>0);
 // All actual material/UV/topology/cut/generation differences reject matching.
 for(unsigned test=0;test<14;++test){auto saved=now.drawData;auto desc=d;auto oldStamp=*snapshot;auto generation=now.submissionFrame;
  if(test==0)now.drawData.callTiles[0].tmemHashOrID++;if(test==1)now.drawData.triTcFloats[0]++;if(test==2)d.scissorRect.lrx++;if(test==3)d.rectRightOrigin++;if(test==4)now.drawData.callTiles[0].tileCopyUsed=true;if(test==5)now.drawData.callTiles[0].valid=false;if(test==6){snapshot->epoch++;++now.submissionFrame;record_menu_workload(&now,snapshot.get(),true);}if(test==7)++now.submissionFrame;if(test==8){current.frameMap.workloads[1].mapped=false;}if(test==9){++d.colorCombiner.H;}if(test==10)now.drawData.callTiles[0].rawTMEM=false;if(test==11)now.drawData.callTiles[0].tmemHashOrID=0;if(test==12)now.drawData.callTiles[0].tileCopyWidth=8;if(test==13)now.drawData.callTiles[0].tileCopyHeight=8;
  {MenuRectRenderScope scope(&queue,&now,&current,&previous,.5f,&worker);assert(!menu_rect_previous(&now,0,bounds));if(auto*u=scope.uploader()){auto*p=static_cast<const interop::RDPParams*>(u->pending[0].srcData);assert(p[0].primColor[3]==.8f);}}
  now.drawData=saved;d=desc;*snapshot=oldStamp;now.submissionFrame=generation+100+test;record_menu_workload(&now,snapshot.get(),true);current.frameMap.workloads[1].mapped=true;
 }
}
'''
class MenuRT64AdapterTests(unittest.TestCase):
 def test_original_callbacks_queued_ownership_real_material_cuts_and_upload_lifetime(self):
  if not shutil.which('c++'):self.skipTest('C++ compiler required')
  with tempfile.TemporaryDirectory()as directory:
   p=Path(directory);(p/'fake.hpp').write_bytes(FAKE.encode());(p/'test.cpp').write_bytes(CODE.encode())
   for name in ['gbi/rt64_gbi.h','hle/rt64_interpreter.h','hle/rt64_workload_queue.h','hle/rt64_game_frame.h','render/rt64_buffer_uploader.h']:
    f=p/name;f.parent.mkdir(exist_ok=True);f.write_bytes(b'#include "fake.hpp"\n')
   q=subprocess.run(['c++','-std=c++20','-O1','-pthread','-I'+str(p),'-I'+str(ROOT/'src'),str(p/'test.cpp'),*[str(ROOT/'src/runtime'/x)for x in ['menu_sprite_bridge.cpp','menu_sprite_render.cpp','menu_sprite_match.cpp']],'-o',str(p/'test')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr);q=subprocess.run([str(p/'test')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
 def test_production_adapters_compile_against_real_pinned_rt64_headers(self):
  database=ROOT/'.local/pal-direct-build/compile_commands.json'
  if not database.is_file():self.skipTest('Private production compile flags required')
  x=next(x for x in json.loads(database.read_text())if x['file'].endswith('/src/renderer.cpp'));a=shlex.split(x['command']);i=a.index('-o');del a[i:i+2];i=a.index('-c');del a[i:];a+=['-w','-fsyntax-only',str(ROOT/'src/runtime/menu_sprite_render.cpp'),str(ROOT/'src/runtime/menu_sprite_bridge.cpp')];q=subprocess.run(a,capture_output=True,text=True,cwd=ROOT);self.assertEqual(q.returncode,0,q.stderr)
