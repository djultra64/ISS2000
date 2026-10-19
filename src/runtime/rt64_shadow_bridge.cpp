// Original project work: djultra64.
#include "rt64_shadow_bridge.hpp"
#include "gbi/rt64_gbi.h"
#include "hle/rt64_interpreter.h"
#include "hle/rt64_rsp.h"
#include "hle/rt64_rdp.h"
#include "hle/rt64_state.h"
#include <mutex>
#include <iterator>
#include <unordered_map>
namespace iss2000 {
namespace {
struct Binding {RT64::State* state{};RT64::GBI* gbi{};RT64::GBIFunction vertex{},primitive_depth{},other_mode{};
 RT64::RDP* depth_rdp{};int depth_stack{};float original_depth{};bool depth_pending{};
 std::shared_ptr<const PalShadowTaskSnapshot> snapshot;bool allow{};PalShadowBridgeStats stats{};};
std::mutex mutex;std::unordered_map<RT64::GBI*,std::shared_ptr<Binding>> bindings;
std::shared_ptr<Binding> find(RT64::State*s){if(!s||!s->ext.interpreter)return {};std::lock_guard lock(mutex);
 auto i=bindings.find(s->ext.interpreter->hleGBI);return i==bindings.end()?nullptr:i->second;}
void group(RT64::RSP&r,const RT64::TransformGroup&g){r.matrixId(g.matrixId,false,false,g.decompose,
 g.positionInterpolation,g.rotationInterpolation,g.scaleInterpolation,g.skewInterpolation,g.perspectiveInterpolation,
 g.vertexInterpolation,g.texcoordInterpolation,g.tileInterpolation,g.lookAtInterpolation,g.ordering,g.aspectMode,g.editable,false,false);}
RT64::TransformGroup shadow(uint32_t id){RT64::TransformGroup g;
 g.matrixId=id;g.decompose=false;g.positionInterpolation=g.rotationInterpolation=g.scaleInterpolation=
 g.skewInterpolation=g.perspectiveInterpolation=G_EX_COMPONENT_SKIP;
 g.vertexInterpolation=G_EX_COMPONENT_INTERPOLATE;g.texcoordInterpolation=G_EX_COMPONENT_SKIP;
 g.tileInterpolation=g.lookAtInterpolation=G_EX_COMPONENT_SKIP;
 g.ordering=G_EX_ORDER_AUTO;g.aspectMode=G_EX_ASPECT_AUTO;g.editable=G_EX_EDIT_NONE;return g;}
// RDP PRIM Z is15.3 fixed point.7FFF is3FFF8 in18-bit depth,
// seven units below the cleared maximum3FFFF. RT64's generic15-bit
// normalization maps it to1 and loses that distinction. Keep strict LESS,
// Zupdate and the original dz/material; adapt only this exact owned draw.
void restore_depth(Binding&b){if(!b.depth_pending)return;
 if(b.state->rdp && &*b.state->rdp==b.depth_rdp && b.depth_stack>0 && size_t(b.depth_stack)<=std::size(b.depth_rdp->primDepthStack)){
  b.depth_rdp->primDepthStack[b.depth_stack-1].x=b.original_depth;
  b.state->updateDrawStatusAttribute(RT64::DrawAttribute::PrimDepth);
 }
 b.depth_pending=false;
}
bool known_depth_source(const Binding&b,RT64::State*s,RT64::DisplayList*dl){
 if(s!=b.state||!s->rdp||!s->RDRAM||!b.snapshot||b.snapshot->scene!=0x604||
    s->rsp->getCurrentProjectionType()!=RT64::Projection::Type::Perspective||
    dl!=reinterpret_cast<RT64::DisplayList*>(s->fromRDRAM(0x83AE8))||
    dl->w0!=0xEE000000||dl->w1!=0x7FFF7FFF||
    !verified_pal_near_shadow_list({s->RDRAM,0x800000}))return false;
 bool owner=false;for(const auto&t:b.snapshot->tags)if(t.epoch==b.snapshot->epoch&&
    t.first_id>=PalShadowIdFirst&&t.second_id<=PalShadowIdLast&&t.first_id<t.second_id){owner=true;break;}
 if(!owner)return false;
 const auto&r=*s->rdp;
 if(r.primDepthStackSize<=0||size_t(r.primDepthStackSize)>std::size(r.primDepthStack)||
    r.primColorStackSize<=0||size_t(r.primColorStackSize)>std::size(r.primColorStack)||
    r.colorCombinerStackSize<=0||size_t(r.colorCombinerStackSize)>std::size(r.colorCombinerStack)||
    r.otherMode.L!=0x005049FC||(r.otherMode.H&(3u<<20))!=(1u<<20))return false;
 const auto&c=r.colorCombinerStack[r.colorCombinerStackSize-1];
 const auto&p=r.primColorStack[r.primColorStackSize-1];
 return c.H==0xFFFFFF&&c.L==0xFFFDF6FB&&float(p.x)==0&&float(p.y)==0&&float(p.z)==0&&
    (float(p.w)==170/255.f||float(p.w)==100/255.f);
}
void primitive_depth_callback(RT64::State*s,RT64::DisplayList**dl){auto b=find(s);if(!b)std::terminate();
 if(s!=b->state){b->primitive_depth(s,dl);return;}
 restore_depth(*b); // A later foreign EE owns its own result, including after exceptions.
 const bool known=known_depth_source(*b,s,*dl);
 b->primitive_depth(s,dl); // Preserve original decoder and original dirty-state semantics once.
 if(!known||s->rdp->primDepthStackSize<=0)return;
 auto&r=*s->rdp;auto&depth=r.primDepthStack[r.primDepthStackSize-1];
 if(float(depth.x)!=1.f||float(depth.y)!=32767*(1.f/65535.f))return;
 b->depth_rdp=&r;b->depth_stack=r.primDepthStackSize;b->original_depth=float(depth.x);b->depth_pending=true;
 depth.x=(32767u<<3)/262143.f;s->updateDrawStatusAttribute(RT64::DrawAttribute::PrimDepth);
}
void other_mode_callback(RT64::State*s,RT64::DisplayList**dl){auto b=find(s);if(!b)std::terminate();
 if(s!=b->state){b->other_mode(s,dl);return;}
 const bool pixel_source=((*dl)->w0==0xE2001D00&&(*dl)->w1==0);
 b->other_mode(s,dl);
 if(pixel_source)restore_depth(*b);
}
void vertex_callback(RT64::State*s,RT64::DisplayList**dl){auto b=find(s);if(!b)std::terminate();++b->stats.vertex_calls;
 auto&r=*s->rsp;const auto command=(*dl)->w0;
 const unsigned count=(command>>12)&255,destination=((command>>1)&127)-count;
 const auto physical=r.fromSegmentedMasked((*dl)->w1);
 std::optional<uint32_t> id;
 if(s==b->state&&b->allow&&b->snapshot&&b->snapshot->scene==0x604&&r.modelMatrixStackSize>0&&
    r.extended.modelMatrixIdStackSize>0&&r.getCurrentProjectionType()==RT64::Projection::Type::Perspective&&
    (r.modelMatrixPhysicalAddressStack[r.modelMatrixStackSize-1]&0x1fffffff)==0x1A3F00&&
    (command==0x0101C038u||command==0x0100C018u||
     command==0x01018030u||command==0x01008010u||command==0x01010020u))id=b->snapshot->lookup(physical,count,destination);
 if(!id||*id<PalShadowIdFirst||*id>PalShadowIdLast){b->vertex(s,dl);return;}
 const auto previous=r.extended.modelMatrixIdStack[r.extended.modelMatrixIdStackSize-1];
 // A fresh group also needs a fresh world transform: RT64 otherwise keeps
 // assigning vertices to the previous transform's group index.
 struct Restore {RT64::RSP&r;RT64::TransformGroup old;~Restore(){group(r,old);r.modelViewProjChanged=true;}}restore{r,previous};
 group(r,shadow(*id));r.modelViewProjChanged=true;++b->stats.shadow_chunks;b->vertex(s,dl);
}
}
struct RT64ShadowBridge::Impl {std::shared_ptr<Binding> binding;};
RT64ShadowBridge::RT64ShadowBridge(RT64::State*s,RT64::GBI*g,std::shared_ptr<const PalShadowTaskSnapshot>snapshot,bool allow){
 if(!s||!s->rsp||!s->ext.interpreter||!g||s->ext.interpreter->hleGBI!=g||g->ucode!=RT64::GBIUCode::F3DEX2||!g->map[1])return;
 std::lock_guard lock(mutex);if(bindings.contains(g)||g->map[1]==vertex_callback)return;
 auto b=std::make_shared<Binding>();b->state=s;b->gbi=g;b->vertex=g->map[1];b->snapshot=std::move(snapshot);b->allow=allow;
 impl=std::make_unique<Impl>();impl->binding=b;bindings.emplace(g,b);g->map[1]=vertex_callback;
 if(s->rdp&&s->RDRAM&&g->map[0xEE]&&g->map[0xE2]){b->primitive_depth=g->map[0xEE];b->other_mode=g->map[0xE2];
  g->map[0xEE]=primitive_depth_callback;g->map[0xE2]=other_mode_callback;}
}
RT64ShadowBridge::~RT64ShadowBridge(){if(!impl)return;std::lock_guard lock(mutex);auto&b=*impl->binding;
 restore_depth(b);
 if(b.gbi->map[1]==vertex_callback)b.gbi->map[1]=b.vertex;
 if(b.primitive_depth&&b.gbi->map[0xEE]==primitive_depth_callback)b.gbi->map[0xEE]=b.primitive_depth;
 if(b.other_mode&&b.gbi->map[0xE2]==other_mode_callback)b.gbi->map[0xE2]=b.other_mode;
 bindings.erase(b.gbi);}
bool RT64ShadowBridge::installed()const noexcept{return bool(impl);}
PalShadowBridgeStats RT64ShadowBridge::stats()const noexcept{return impl?impl->binding->stats:PalShadowBridgeStats{};}
}
