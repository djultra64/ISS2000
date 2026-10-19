// Original project work: djultra64.
#include "menu_sprite_bridge.hpp"
#include "menu_sprite_render.hpp"
#include "gbi/rt64_gbi.h"
#include "hle/rt64_interpreter.h"
#include "hle/rt64_workload_queue.h"
#include <mutex>
#include <unordered_map>
namespace iss2000 {namespace {
struct Binding {RT64::State*state{};RT64::GBI*gbi{};RT64::GBIFunction rectangle{},flip{},fill{},extended{};std::shared_ptr<const MenuSpriteTaskSnapshot>snapshot;bool allow{};};
std::mutex mutex;std::unordered_map<RT64::State*,std::shared_ptr<Binding>>bindings;
std::shared_ptr<Binding>binding(RT64::State*s){std::lock_guard lock(mutex);auto it=bindings.find(s);if(it==bindings.end())std::terminate();return it->second;}
uint32_t identity(const Binding&b,const RT64::DisplayList*dl){if(!b.allow||!b.snapshot)return 0;auto p=reinterpret_cast<uintptr_t>(dl),base=reinterpret_cast<uintptr_t>(b.state->RDRAM);if(p<base||p-base>=0x800000||(p-base)&7)return 0;auto it=b.snapshot->commands.find(uint32_t(p-base));return it==b.snapshot->commands.end()?0:it->second;}
// Empty original rectangles return before State::flush. Preserve the identity
// of the pending previous call in that case; never retag it with an empty draw.
void draw(RT64::State*s,RT64::DisplayList**dl,RT64::GBIFunction original,uint32_t id){auto*q=s->ext.workloadQueue;auto&w=q->workloads[q->writeCursor];const auto count=w.gameCallCount,triangles=s->drawCall.triangleCount;original(s,dl);if(s->drawCall.triangleCount&&(!triangles||w.gameCallCount!=count))s->drawCall.uid=id;}
void rectangle(RT64::State*s,RT64::DisplayList**dl){auto b=binding(s);draw(s,dl,b->rectangle,identity(*b,*dl));}
void flip(RT64::State*s,RT64::DisplayList**dl){auto b=binding(s);draw(s,dl,b->flip,0);}
void fill(RT64::State*s,RT64::DisplayList**dl){auto b=binding(s);draw(s,dl,b->fill,0);}
void extended(RT64::State*s,RT64::DisplayList**dl){auto b=binding(s);auto op=(*dl)->w0;auto id=op==0x64000002?identity(*b,*dl):0;if(op==0x64000002||op==0x64000003)draw(s,dl,b->extended,id);else b->extended(s,dl);}
}
struct MenuSpriteBridge::Impl {std::shared_ptr<Binding>binding;};
MenuSpriteBridge::MenuSpriteBridge(RT64::State*s,RT64::GBI*gbi,std::shared_ptr<const MenuSpriteTaskSnapshot>snapshot,bool allow){
 if(!s||!gbi||!s->ext.interpreter||s->ext.interpreter->hleGBI!=gbi||gbi->ucode!=RT64::GBIUCode::F3DEX2||!gbi->map[0xe4]||!gbi->map[0xe5]||!gbi->map[0xf6]||!s->ext.interpreter->extendedFunction||!s->ext.workloadQueue)return;
 std::lock_guard lock(mutex);if(bindings.contains(s)||gbi->map[0xe4]==rectangle||s->ext.interpreter->extendedFunction==extended)return;
 auto b=std::make_shared<Binding>(Binding{s,gbi,gbi->map[0xe4],gbi->map[0xe5],gbi->map[0xf6],s->ext.interpreter->extendedFunction,std::move(snapshot),allow});impl_=std::make_unique<Impl>();impl_->binding=b;bindings.emplace(s,b);gbi->map[0xe4]=rectangle;gbi->map[0xe5]=flip;gbi->map[0xf6]=fill;s->ext.interpreter->extendedFunction=extended;s->drawCall.uid=0;
 auto*q=s->ext.workloadQueue;record_menu_workload(&q->workloads[q->writeCursor],b->snapshot.get(),allow);
}
MenuSpriteBridge::~MenuSpriteBridge(){if(!impl_)return;std::lock_guard lock(mutex);auto&b=*impl_->binding;if(b.gbi->map[0xe4]==rectangle)b.gbi->map[0xe4]=b.rectangle;if(b.gbi->map[0xe5]==flip)b.gbi->map[0xe5]=b.flip;if(b.gbi->map[0xf6]==fill)b.gbi->map[0xf6]=b.fill;if(b.state->ext.interpreter->extendedFunction==extended)b.state->ext.interpreter->extendedFunction=b.extended;bindings.erase(b.state);}
}
