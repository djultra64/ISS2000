// Original project work: djultra64.
#include "menu_sprite_render.hpp"
#include "hle/rt64_workload_queue.h"
#include "hle/rt64_game_frame.h"
#include "render/rt64_buffer_uploader.h"
#include <algorithm>
#include <bit>
#include <cmath>
#include <mutex>
#include <unordered_map>
namespace iss2000 {namespace {
struct Stamp {uint64_t generation{},sequence{},epoch{};bool allow{};};
std::mutex stamp_mutex;
std::unordered_map<const RT64::Workload*,Stamp> stamps;
struct Hash {
 uint64_t value=14695981039346656037ULL;
 template<class T>void add(const T&v){auto*b=reinterpret_cast<const uint8_t*>(&v);for(size_t i=0;i<sizeof(T);++i){value^=b[i];value*=1099511628211ULL;}}
};
MenuRectFrame capture(const RT64::Workload&w,const Stamp&s){
 MenuRectFrame out{s.sequence,s.epoch,{}};
 if(w.fbPairCount>w.fbPairs.size())return out;
 for(unsigned f=0;f<w.fbPairCount;++f){const auto&fb=w.fbPairs[f];if(fb.projectionCount>fb.projections.size())return {s.sequence,s.epoch,{}};
  for(unsigned p=0;p<fb.projectionCount;++p){const auto&proj=fb.projections[p];if(proj.type!=RT64::Projection::Type::Rectangle)continue;if(proj.gameCallCount>proj.gameCalls.size())return {s.sequence,s.epoch,{}};
   for(unsigned n=0;n<proj.gameCallCount;++n){const auto&call=proj.gameCalls[n];const auto&d=call.callDesc;
    if(!d.uid||d.callIndex>=w.drawData.rdpParams.size()||d.triangleCount!=2||d.tileCount>2||size_t(d.tileIndex)+d.tileCount>w.drawData.callTiles.size()||size_t(d.tileIndex)+d.tileCount>w.drawData.rdpTiles.size())continue;
    const size_t uv= size_t(call.meshDesc.rawVertexStart)*2,uvCount=size_t(d.triangleCount)*6;
    if(uv>w.drawData.triTcFloats.size()||uvCount>w.drawData.triTcFloats.size()-uv)continue;
    Hash h;h.add(f);h.add(p);h.add(fb.colorImage.fmt);h.add(fb.colorImage.siz);h.add(fb.colorImage.width);
    h.add(d.otherMode.H);h.add(d.otherMode.L);h.add(d.colorCombiner.H);h.add(d.colorCombiner.L);
    h.add(d.rectDsdx);h.add(d.rectDtdy);h.add(d.rectLeftOrigin);h.add(d.rectRightOrigin);h.add(d.rectAspect);
    h.add(d.scissorRect.ulx);h.add(d.scissorRect.uly);h.add(d.scissorRect.lrx);h.add(d.scissorRect.lry);h.add(d.scissorLeftOrigin);h.add(d.scissorRightOrigin);h.add(d.scissorMode);
    h.add(d.textureOn);h.add(d.textureTile);h.add(d.textureLevels);h.add(d.tileCount);h.add(d.fillColor);
    // Prim/env are the only varying material fields; every other RDP parameter
    // must remain identical. Avoid C++ padding in compatibility identities.
    const auto&rp=d.rdpParams;
    for(unsigned i=0;i<2;++i){h.add(rp.primLOD[i]);h.add(rp.primDepth[i]);}
    for(unsigned i=0;i<4;++i){h.add(rp.fogColor[i]);h.add(rp.blendColor[i]);}
    for(unsigned i=0;i<3;++i){h.add(rp.keyCenter[i]);h.add(rp.keyScale[i]);}
    for(auto k:rp.convertK)h.add(k);
    bool safe=true;
    for(unsigned t=0;t<d.tileCount;++t){const auto&tile=w.drawData.callTiles[d.tileIndex+t];// Pinned fullSyncFramebufferPairTiles assigns uploadTMEM's XXH3
     // of the complete 4 KiB image (including TLUT) before rendering. Raw
     // addressing is compatible only with that nonzero immutable content key;
     // framebuffer-copy IDs are deliberately excluded. A too-small
     // copy can clear tileCopyUsed while retaining its ID and dimensions;
     // that uploadEmpty fallback is not a TMEM content identity.
     if(!tile.valid||tile.tileCopyUsed||tile.tileCopyWidth||tile.tileCopyHeight||(tile.rawTMEM&&!tile.tmemHashOrID)){safe=false;break;}
     h.add(tile.rawTMEM);
     h.add(tile.tmemHashOrID);h.add(tile.sampleWidth);h.add(tile.sampleHeight);h.add(tile.lineWidth);h.add(tile.tlut);h.add(tile.reinterpretTile);h.add(tile.reinterpretSiz);h.add(tile.reinterpretFmt);
     const auto&r=w.drawData.rdpTiles[d.tileIndex+t];h.add(r.fmt);h.add(r.siz);h.add(r.stride);h.add(r.address);h.add(r.palette);h.add(r.masks);h.add(r.maskt);h.add(r.shifts);h.add(r.shiftt);h.add(r.uls);h.add(r.ult);h.add(r.lrs);h.add(r.lrt);h.add(r.cms);h.add(r.cmt);h.add(r.nativeSampler);
    }
    for(size_t i=0;i<uvCount;++i){auto v=w.drawData.triTcFloats[uv+i];if(!std::isfinite(v)){safe=false;break;}h.add(v);}
    if(!safe)continue;
    MenuRectSample sample;sample.uid=d.uid;sample.call_index=d.callIndex;sample.compatibility=h.value;sample.rect={float(d.rect.ulx),float(d.rect.uly),float(d.rect.lrx),float(d.rect.lry)};
    for(unsigned i=0;i<4;++i){sample.prim[i]=rp.primColor[i];sample.env[i]=rp.envColor[i];if(!std::isfinite(sample.prim[i])||!std::isfinite(sample.env[i]))safe=false;}
    if(safe)out.rectangles.push_back(sample);
   }
  }
 }
 return out;
}
thread_local MenuRectRenderStats last_stats;
struct Active {MenuRectRenderStats stats;const RT64::Workload*workload{};std::unordered_map<uint32_t,MenuRectPrevious>previous;};
thread_local Active*active{};
struct Uploader {decltype(RT64::RenderWorker::device) device{};std::unique_ptr<RT64::BufferUploader>value;};
thread_local Uploader render_uploader;
}
void record_menu_workload(const RT64::Workload*w,const MenuSpriteTaskSnapshot*s,bool allow){
 if(!w)return;
 std::lock_guard lock(stamp_mutex);auto it=stamps.find(w);
 const Stamp fresh{w->submissionFrame,s?s->sequence:0,s?s->epoch:0,allow&&s&&!s->commands.empty()};
 if(it!=stamps.end()&&it->second.generation==fresh.generation){if(it->second.sequence!=fresh.sequence||it->second.epoch!=fresh.epoch||!fresh.allow)it->second.allow=false;return;}
 // RT64 has four reusable workload slots. Bound stale pointer retention when
 // a renderer is destroyed/recreated; losing a stamp safely disables a match.
 if(stamps.size()>=32)stamps.clear();
 stamps[w]=fresh;
}
struct MenuRectRenderScope::Impl {
 Active context;Active*previous{};std::vector<interop::RDPParams>params;RT64::BufferUploader*upload{};
 ~Impl(){if(upload)upload->wait();last_stats=context.stats;active=previous;}
};
MenuRectRenderScope::MenuRectRenderScope(RT64::WorkloadQueue*q,RT64::Workload*w,const RT64::GameFrame*current,const RT64::GameFrame*previous,float weight,RT64::RenderWorker*worker){
 last_stats={};
 if(!q||!w||!current||!previous||!std::isfinite(weight)||weight<0||weight>1)return;
 Stamp now,old;const RT64::Workload*prior{};
 {std::lock_guard lock(stamp_mutex);auto it=stamps.find(w);if(it==stamps.end()||!it->second.allow||it->second.generation!=w->submissionFrame)return;now=it->second;
  auto index=std::find_if(q->workloads.begin(),q->workloads.end(),[&](const auto&v){return &v==w;});if(index==q->workloads.end())return;auto i=size_t(index-q->workloads.begin());
  if(std::find(current->workloads.begin(),current->workloads.end(),i)==current->workloads.end())return;
  if(i<current->frameMap.workloads.size()){const auto&map=current->frameMap.workloads[i];if(map.mapped&&map.prevWorkloadIndex<q->workloads.size()&&std::find(previous->workloads.begin(),previous->workloads.end(),map.prevWorkloadIndex)!=previous->workloads.end())prior=&q->workloads[map.prevWorkloadIndex];}
  if(prior){auto p=stamps.find(prior);if(p!=stamps.end()&&p->second.allow&&p->second.generation==prior->submissionFrame)old=p->second;else prior=nullptr;}
 }
 impl_=std::make_unique<Impl>();impl_->previous=active;impl_->context.workload=w;active=&impl_->context;
 auto nowFrame=capture(*w,now);MenuRectFrame previousFrame;std::vector<MenuRectMatch>matches;
 if(prior){previousFrame=capture(*prior,old);matches=match_menu_rectangles(nowFrame,previousFrame,weight);}
 impl_->context.stats.rectangles=uint32_t(nowFrame.rectangles.size());impl_->context.stats.matches=uint32_t(matches.size());impl_->context.stats.fractional=weight>0&&weight<1;
 for(const auto&m:matches){impl_->context.stats.moved+=m.moved;impl_->context.stats.fades+=m.faded;}
 for(const auto&m:matches){MenuRectPrevious p;p.weight=weight;for(unsigned i=0;i<4;++i)p.rect[i]=int32_t(m.previous[i]);impl_->context.previous.emplace(m.call_index,p);}
 if(!worker||!worker->device||nowFrame.rectangles.empty())return;
 // The queued CPU data stays immutable. This private per-render copy remains
 // alive through original recordSetup / execute / GPU fence wait in the loop.
 impl_->params=w->drawData.rdpParams;
 for(const auto&m:matches)for(unsigned i=0;i<4;++i){impl_->params[m.call_index].primColor[i]=m.prim[i];impl_->params[m.call_index].envColor[i]=m.env[i];}
 if(render_uploader.device!=worker->device){render_uploader.value=std::make_unique<RT64::BufferUploader>(worker->device);render_uploader.device=worker->device;}
 impl_->upload=render_uploader.value.get();impl_->upload->submit(worker,{{impl_->params.data(),{0,impl_->params.size()},sizeof(interop::RDPParams),RenderBufferFlag::STORAGE,{},&w->drawBuffers.rdpParamsBuffer}});
}
MenuRectRenderScope::~MenuRectRenderScope()=default;
RT64::BufferUploader*MenuRectRenderScope::uploader()const{return impl_?impl_->upload:nullptr;}
MenuRectRenderStats menu_rect_render_stats(){return active?active->stats:last_stats;}
bool menu_rect_previous(const RT64::Workload*w,uint32_t index,MenuRectPrevious&out){if(!active||active->workload!=w)return false;auto it=active->previous.find(index);if(it==active->previous.end())return false;out=it->second;return true;}
}
