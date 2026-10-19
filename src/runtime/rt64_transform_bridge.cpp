// Original project work: djultra64.
#include "rt64_transform_bridge.hpp"
#include "gbi/rt64_gbi.h"
#include "hle/rt64_interpreter.h"
#include "hle/rt64_rsp.h"
#include "hle/rt64_state.h"
#include <algorithm>
#include <mutex>
#include <unordered_map>
namespace iss2000 {
namespace {
struct Binding {
    RT64::State* state{};
    RT64::GBI* gbi{};
    RT64::GBIFunction matrix{},pop{};
    std::shared_ptr<const TransformTaskSnapshot> snapshot;
    bool allow{};
    TransformBridgeStats stats{};
};
std::mutex bindings_mutex;
std::unordered_map<RT64::GBI*,std::shared_ptr<Binding>> bindings;
std::shared_ptr<Binding> binding_for(RT64::State* state){
    if(!state || !state->ext.interpreter)return {};
    std::lock_guard lock(bindings_mutex);
    const auto found=bindings.find(state->ext.interpreter->hleGBI);
    return found==bindings.end()?nullptr:found->second;
}
void group(RT64::RSP& rsp,const RT64::TransformGroup& g,bool push,bool projection){
    rsp.matrixId(g.matrixId,push,projection,g.decompose,g.positionInterpolation,
        g.rotationInterpolation,g.scaleInterpolation,g.skewInterpolation,g.perspectiveInterpolation,
        g.vertexInterpolation,g.texcoordInterpolation,g.tileInterpolation,g.lookAtInterpolation,
        g.ordering,g.aspectMode,g.editable,false,false);
}
RT64::TransformGroup selection_group(TransformSelection choice){
    RT64::TransformGroup result;
    result.matrixId=choice.id;
    result.aspectMode=G_EX_ASPECT_AUTO;
    result.ordering=G_EX_ORDER_AUTO;
    result.editable=G_EX_EDIT_NONE;
    result.vertexInterpolation=choice.vertices?G_EX_COMPONENT_INTERPOLATE:G_EX_COMPONENT_SKIP;
    result.texcoordInterpolation=G_EX_COMPONENT_SKIP;
    result.skewInterpolation=G_EX_COMPONENT_SKIP;
    result.tileInterpolation=G_EX_COMPONENT_AUTO;
    result.lookAtInterpolation=G_EX_COMPONENT_AUTO;
    if(choice.kind==TransformSelection::Kind::Ignore){
        result.decompose=false;
        result.positionInterpolation=result.rotationInterpolation=result.scaleInterpolation=
            result.perspectiveInterpolation=G_EX_COMPONENT_SKIP;
    }else{
        result.decompose=choice.kind==TransformSelection::Kind::Model;
        result.positionInterpolation=result.rotationInterpolation=G_EX_COMPONENT_INTERPOLATE;
        result.scaleInterpolation=G_EX_COMPONENT_AUTO;
        result.perspectiveInterpolation=choice.kind==TransformSelection::Kind::Camera?G_EX_COMPONENT_AUTO:G_EX_COMPONENT_SKIP;
    }
    return result;
}
void matrix_callback(RT64::State* state,RT64::DisplayList** dl){
    const auto binding=binding_for(state);
    // These callbacks are installed/restored as one synchronous scope, so every
    // reachable callback has its saved original. Never invent a replacement.
    if(!binding)std::terminate();
    auto& rsp=*state->rsp;
    const auto params=(*dl)->p0(0,8)^rsp.pushMask;
    const bool projection=(params&rsp.projMask)!=0,load=(params&rsp.loadMask)!=0;
    const uint32_t physical=rsp.fromSegmentedMasked((*dl)->w1);
    const int before=rsp.modelMatrixStackSize;
    binding->matrix(state,dl);
    if(state!=binding->state)return;
    const bool push=!projection && rsp.modelMatrixStackSize>before;
    const auto choice=select_rt64_transform(binding->snapshot.get(),binding->allow,physical,
        projection,load,rsp.getCurrentProjectionType()==RT64::Projection::Type::Perspective);
    ++binding->stats.matrix_calls;
    switch(choice.kind){
    case TransformSelection::Kind::Model:++binding->stats.model_groups;break;
    case TransformSelection::Kind::Camera:++binding->stats.camera_groups;break;
    case TransformSelection::Kind::Inherit:++binding->stats.inherited_groups;break;
    case TransformSelection::Kind::Ignore:++binding->stats.ignored_groups;break;
    }
    if(choice.kind==TransformSelection::Kind::Inherit){
        const auto inherited=rsp.extended.modelMatrixIdStack[rsp.extended.modelMatrixIdStackSize-1];
        if(push)group(rsp,inherited,true,false);
    }else group(rsp,selection_group(choice),push,projection);
}
void pop_callback(RT64::State* state,RT64::DisplayList** dl){
    const auto binding=binding_for(state);
    if(!binding)std::terminate();
    auto& rsp=*state->rsp;
    const int before=rsp.modelMatrixStackSize;
    binding->pop(state,dl);
    if(state!=binding->state)return;
    const auto count=std::min(before-rsp.modelMatrixStackSize,rsp.extended.modelMatrixIdStackSize-1);
    if(count>0)rsp.popMatrixId(static_cast<uint8_t>(count),false);
}
}
struct RT64TransformBridge::Impl {std::shared_ptr<Binding> binding;};
RT64TransformBridge::RT64TransformBridge(RT64::State* state,RT64::GBI* gbi,
    std::shared_ptr<const TransformTaskSnapshot> snapshot,bool allow){
    if(!state || !state->rsp || !state->ext.interpreter || !gbi ||
       state->ext.interpreter->hleGBI!=gbi || gbi->ucode!=RT64::GBIUCode::F3DEX2 ||
       !gbi->map[0xDA] || !gbi->map[0xD8])return;
    std::lock_guard lock(bindings_mutex);
    if(bindings.contains(gbi) || gbi->map[0xDA]==matrix_callback || gbi->map[0xD8]==pop_callback)return;
    auto binding=std::make_shared<Binding>(Binding{state,gbi,gbi->map[0xDA],gbi->map[0xD8],std::move(snapshot),allow});
    impl_=std::make_unique<Impl>();impl_->binding=binding;
    bindings.emplace(gbi,binding);
    gbi->map[0xDA]=matrix_callback;gbi->map[0xD8]=pop_callback;
    // Unknown draws must not retain RT64 AUTO IDs from a previous task.
    group(*state->rsp,selection_group({}),false,true);
    group(*state->rsp,selection_group({}),false,false);
}
RT64TransformBridge::~RT64TransformBridge(){
    if(!impl_)return;
    std::lock_guard lock(bindings_mutex);
    const auto& b=*impl_->binding;
    if(b.gbi->map[0xDA]==matrix_callback)b.gbi->map[0xDA]=b.matrix;
    if(b.gbi->map[0xD8]==pop_callback)b.gbi->map[0xD8]=b.pop;
    bindings.erase(b.gbi);
}
bool RT64TransformBridge::installed()const noexcept{return bool(impl_);}
TransformBridgeStats RT64TransformBridge::stats()const noexcept{return impl_?impl_->binding->stats:TransformBridgeStats{};}
}
