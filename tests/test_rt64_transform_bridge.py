"""Original project work: djultra64. Pure transform policy; no game execution."""
from pathlib import Path
import shutil, subprocess, tempfile, unittest
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(shutil.which('c++'), 'C++20 compiler required')
class RT64TransformBridgeTests(unittest.TestCase):
 def test_exact_camera_addresses_model_identity_and_closed_scene_policy(self):
  source=r'''#include "runtime/rt64_transform_bridge.hpp"
#include <cassert>
using namespace iss2000;
int main(){
 TransformTracker tracker(us_transform_layout());tracker.begin_scene(0x604);auto tag=tracker.allocate(0x80148104);
 auto frame=tracker.begin_frame(0,0xAA128,0xAF228);
 assert(tracker.capture_matrix({frame,tag.record,0x80000000,0,0xAA128,0xAA128,0xAA168,0x80400000,TransformMatrixBuilder::Conditional252F8}));
 auto token=tracker.publish_task(frame,0xD2C08);auto snapshot=tracker.consume_task(token.sequence,0xD2C08);
 auto choose=[&](uint32_t address,bool projection,bool load,bool perspective=true,bool allow=true){return select_rt64_transform(snapshot.get(),allow,address,projection,load,perspective);};
 for(auto address:{0xC43A0u,0xC43E0u}){auto c=choose(address,true,true);assert(c.kind==TransformSelection::Kind::Camera&&c.id==snapshot->camera_id(0));}
 for(auto address:{0xCEC68u,0xCECA8u})assert(choose(address,true,false).id==snapshot->camera_id(0));
 for(auto address:{0xCECE8u,0xCED28u})assert(choose(address,true,false).id==snapshot->camera_id(1));
 for(auto address:{0xC43A0u,0xCEC68u,0xCECE8u}){
  assert(choose(address,true,true,false).kind==TransformSelection::Kind::Ignore);
  assert(choose(address,true,true,true,false).kind==TransformSelection::Kind::Ignore);
 }
 assert(choose(0x12340,true,true).kind==TransformSelection::Kind::Ignore);
 assert(choose(0xCEC68,true,true).kind==TransformSelection::Kind::Ignore);
 assert(choose(0xC43A0,true,false).kind==TransformSelection::Kind::Ignore);
 auto model=choose(0xAA128,false,true);assert(model.kind==TransformSelection::Kind::Model&&model.id==tag.id);
 assert(choose(0xAA128,false,false).id==tag.id);
 assert(choose(0x12340,false,true).kind==TransformSelection::Kind::Ignore);
 assert(choose(0x12340,false,false).kind==TransformSelection::Kind::Inherit);
 assert(choose(0x12340,false,false,false).kind==TransformSelection::Kind::Ignore);
 auto menu=*snapshot;menu.scene_token=0x607;
 assert(select_rt64_transform(&menu,true,0xAA128,false,true,true).kind==TransformSelection::Kind::Model);
 assert(select_rt64_transform(nullptr,true,0xAA128,false,true,true).kind==TransformSelection::Kind::Ignore);
 auto phase=*snapshot;phase.scene_token=0x12340604;
 assert(select_rt64_transform(&phase,true,0xAA128,false,true,true).id==tag.id);
}
'''
  with tempfile.TemporaryDirectory() as directory:
   folder=Path(directory);(folder/'main.cpp').write_text(source)
   result=subprocess.run(['c++','-std=c++20','-Wall','-Wextra','-Werror','-I'+str(ROOT/'src'),str(folder/'main.cpp'),str(ROOT/'src/runtime/transform_tracker.cpp'),'-o',str(folder/'test')],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
   subprocess.run([str(folder/'test')],check=True,capture_output=True)

 def test_callback_original_once_scope_restore_stack_parity_and_other_app(self):
  # Small API fixture: validates our adapter mechanics, not RT64 rendering.
  fake=r'''#pragma once
#include <array>
#include <cstdint>
#include <vector>
#define G_EX_COMPONENT_SKIP 0
#define G_EX_COMPONENT_INTERPOLATE 1
#define G_EX_COMPONENT_AUTO 2
#define G_EX_ASPECT_AUTO 0
#define G_EX_ORDER_AUTO 1
#define G_EX_EDIT_NONE 0
namespace RT64 {
struct State;struct DisplayList{uint32_t w0{},w1{};uint32_t p0(int,int)const{return w0&255;}};
using GBIFunction=void(*)(State*,DisplayList**);
enum class GBIUCode{Unknown,F3DEX2};
struct GBI{GBIUCode ucode=GBIUCode::F3DEX2;GBIFunction map[256]{};};
struct Interpreter{GBI* hleGBI{};};
struct Projection{enum class Type{Perspective,Orthographic};};
struct TransformGroup{uint32_t matrixId{};bool decompose{};uint8_t positionInterpolation{},rotationInterpolation{},scaleInterpolation{},skewInterpolation{},perspectiveInterpolation{},vertexInterpolation{},texcoordInterpolation{},tileInterpolation{},lookAtInterpolation{},ordering{},aspectMode{},editable{};};
struct RSP{
 uint32_t pushMask=1,projMask=4,loadMask=2;int modelMatrixStackSize=1;
 struct{std::array<TransformGroup,256> modelMatrixIdStack{},viewProjMatrixIdStack{};int modelMatrixIdStackSize=1,viewProjMatrixIdStackSize=1;}extended;
 bool perspective=true;int originalMatrixCalls{},originalPopCalls{};
 uint32_t fromSegmentedMasked(uint32_t address){return address&0x7FFFFF;}
 Projection::Type getCurrentProjectionType(){return perspective?Projection::Type::Perspective:Projection::Type::Orthographic;}
 void matrixId(uint32_t id,bool push,bool proj,bool decompose,uint8_t pos,uint8_t rot,uint8_t scale,uint8_t skew,uint8_t persp,uint8_t vpos,uint8_t vtc,uint8_t tile,uint8_t look,uint8_t order,uint8_t aspect,uint8_t edit,bool,bool){
 auto& size=proj?extended.viewProjMatrixIdStackSize:extended.modelMatrixIdStackSize;
 auto& stack=proj?extended.viewProjMatrixIdStack:extended.modelMatrixIdStack;
 if(push)++size;
 stack[size-1]={id,decompose,pos,rot,scale,skew,persp,vpos,vtc,tile,look,order,aspect,edit};
 }
 void popMatrixId(uint8_t count,bool){while(count--&&extended.modelMatrixIdStackSize>1)--extended.modelMatrixIdStackSize;}
};
struct State{RSP* rsp{};struct{Interpreter* interpreter{};}ext;};
}
'''
  source=r'''#include "runtime/rt64_transform_bridge.hpp"
#include "fake.hpp"
#include <cassert>
#include <stdexcept>
using namespace iss2000;using namespace RT64;
void originalMatrix(State* s,DisplayList** dl){
 ++s->rsp->originalMatrixCalls;auto params=(*dl)->p0(0,8)^s->rsp->pushMask;
 if(!(params&s->rsp->projMask)&&(params&s->rsp->pushMask)&&s->rsp->modelMatrixStackSize<32)++s->rsp->modelMatrixStackSize;
}
void originalPop(State* s,DisplayList** dl){++s->rsp->originalPopCalls;auto count=(*dl)->w1>>6;while(count--&&s->rsp->modelMatrixStackSize>1)--s->rsp->modelMatrixStackSize;}
int main(){
 TransformTracker tracker(us_transform_layout());tracker.begin_scene(0x604);auto tag=tracker.allocate(0x80148104);
 auto frame=tracker.begin_frame(0,0xAA128,0xAF228);assert(tracker.capture_matrix({frame,tag.record,0x80000000,0,0xAA128,0xAA128,0xAA168,0x80400000,TransformMatrixBuilder::Conditional252F8}));
 auto token=tracker.publish_task(frame,0xD2C08);auto snapshot=tracker.consume_task(token.sequence,0xD2C08);
 GBI gbi;gbi.map[0xDA]=originalMatrix;gbi.map[0xD8]=originalPop;
 Interpreter interpreter{&gbi};RSP rsp;State state{&rsp,{&interpreter}};
 GBI other;other.map[0xDA]=originalMatrix;other.map[0xD8]=originalPop;
 Interpreter otherInterpreter{&other};RSP otherRsp;State otherState{&otherRsp,{&otherInterpreter}};
 auto matrix=[&](uint32_t address,uint32_t params){DisplayList command{params^rsp.pushMask,address};auto* p=&command;gbi.map[0xDA](&state,&p);};
 auto pop=[&](uint32_t count){DisplayList command{0,count<<6};auto* p=&command;gbi.map[0xD8](&state,&p);};
 {
 RT64TransformBridge bridge(&state,&gbi,snapshot,true);assert(bridge.installed());
 assert(other.map[0xDA]==originalMatrix&&other.map[0xD8]==originalPop);
 RT64TransformBridge nested(&state,&gbi,snapshot,true);assert(!nested.installed());
 assert(rsp.extended.modelMatrixIdStack[0].matrixId==0);
 matrix(0xC43A0,6);assert(rsp.originalMatrixCalls==1);assert(rsp.extended.viewProjMatrixIdStack[0].matrixId==snapshot->camera_id(0));
 matrix(0xCECE8,4);assert(rsp.originalMatrixCalls==2);assert(rsp.extended.viewProjMatrixIdStack[0].matrixId==snapshot->camera_id(1));
 matrix(0xAA128,3);assert(rsp.originalMatrixCalls==3&&rsp.modelMatrixStackSize==2&&rsp.extended.modelMatrixIdStackSize==2);
 auto stats=bridge.stats();assert(stats.matrix_calls==3&&stats.camera_groups==2&&stats.model_groups==1&&stats.ignored_groups==0);
 auto group=rsp.extended.modelMatrixIdStack[1];assert(group.matrixId==tag.id&&group.decompose&&group.positionInterpolation==1&&group.perspectiveInterpolation==0);
 matrix(0x12340,1);assert(rsp.extended.modelMatrixIdStackSize==3&&rsp.extended.modelMatrixIdStack[2].matrixId==tag.id);
 matrix(0x12340,2);assert(rsp.extended.modelMatrixIdStack[2].matrixId==0);
 pop(1);assert(rsp.originalPopCalls==1&&rsp.modelMatrixStackSize==2&&rsp.extended.modelMatrixIdStackSize==2&&rsp.extended.modelMatrixIdStack[1].matrixId==tag.id);
 pop(999);assert(rsp.originalPopCalls==2&&rsp.modelMatrixStackSize==1&&rsp.extended.modelMatrixIdStackSize==1);
 rsp.perspective=false;matrix(0xAA128,2);assert(rsp.extended.modelMatrixIdStack[0].matrixId==tag.id);
 rsp.perspective=true;matrix(0xAA128,2);assert(rsp.extended.modelMatrixIdStack[0].matrixId==tag.id);
 for(int i=0;i<40;++i)matrix(0x12340,1);
 assert(rsp.modelMatrixStackSize==32&&rsp.extended.modelMatrixIdStackSize==32);
 }
 assert(gbi.map[0xDA]==originalMatrix&&gbi.map[0xD8]==originalPop);
 try{RT64TransformBridge bridge(&state,&gbi,snapshot,false);assert(bridge.installed());matrix(0xAA128,2);assert(rsp.extended.modelMatrixIdStack[rsp.extended.modelMatrixIdStackSize-1].matrixId==0);throw std::runtime_error("unwind");}catch(const std::runtime_error&){}
 assert(gbi.map[0xDA]==originalMatrix&&gbi.map[0xD8]==originalPop);
 // A verified menu cloth owns vertex interpolation without UV interpolation;
 // unrelated menu matrices, multiplies and the camera stay excluded.
 auto cloth=std::make_shared<TransformTaskSnapshot>(*snapshot);cloth->scene_token=0x607;
 cloth->model_scope=TransformModelScope{};cloth->model_scope->scene=0x607;
 cloth->model_scope->vertex_models[0]={tag.record,123,456};
 {RT64TransformBridge bridge(&state,&gbi,cloth,true);matrix(0xAA128,2);
  const auto&g=rsp.extended.modelMatrixIdStack[rsp.extended.modelMatrixIdStackSize-1];
  assert(g.matrixId==123&&g.vertexInterpolation==G_EX_COMPONENT_INTERPOLATE&&g.texcoordInterpolation==G_EX_COMPONENT_SKIP);
  matrix(0xAA128,0);assert(rsp.extended.modelMatrixIdStack[rsp.extended.modelMatrixIdStackSize-1].matrixId==0);
  matrix(0xC43A0,6);assert(rsp.extended.viewProjMatrixIdStack[0].matrixId==0);
 }
 RT64TransformBridge mismatch(&otherState,&gbi,snapshot,true);assert(!mismatch.installed());
}
'''
  with tempfile.TemporaryDirectory() as directory:
   folder=Path(directory);(folder/'fake.hpp').write_text(fake)
   for name in ['gbi/rt64_gbi.h','hle/rt64_interpreter.h','hle/rt64_rsp.h','hle/rt64_state.h']:
    target=folder/name;target.parent.mkdir(exist_ok=True);target.write_text('#include "fake.hpp"\n')
   (folder/'main.cpp').write_text(source)
   result=subprocess.run(['c++','-std=c++20','-Wall','-Wextra','-Werror','-I'+str(folder),'-I'+str(ROOT/'src'),str(folder/'main.cpp'),str(ROOT/'src/runtime/transform_tracker.cpp'),str(ROOT/'src/runtime/rt64_transform_bridge.cpp'),'-o',str(folder/'test')],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
   subprocess.run([str(folder/'test')],check=True,capture_output=True)
