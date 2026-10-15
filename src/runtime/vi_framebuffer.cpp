// Original project work: djultra64.
#include "vi_framebuffer.hpp"
namespace iss2000 {
void ViFramebufferRegistry::record(uint32_t origin,uint32_t width,uint32_t status,uint32_t base){
    const auto size=uint8_t(status&3u);
    if(size<2 || !width || width>0xFFF || origin>=0x800000 || base>=0x800000 ||
       (base&7) || base>origin || uint64_t(base)+uint64_t(width)*(size==2?2:4)>0x800000)return;
    std::lock_guard lock(mutex_);
    for(auto& e:entries_)if(e.used && e.origin==origin && e.width==width && e.size==size){
        if(e.base!=base)e.conflict=true;
        return;
    }
    entries_[next_]={origin,width,base,size,true,false};next_=(next_+1)%entries_.size();
}
std::optional<uint32_t> ViFramebufferRegistry::resolve(uint32_t origin,uint32_t width,uint8_t size)const{
    std::lock_guard lock(mutex_);
    for(const auto& e:entries_)if(e.used && e.origin==origin && e.width==width && e.size==size)
        return e.conflict?std::optional<uint32_t>{}:e.base;
    return {};
}
}
namespace {iss2000::ViFramebufferRegistry registry;}
extern "C" void iss2000_record_vi_framebuffer(uint32_t origin,uint32_t width,uint32_t status,uint32_t framebuffer){
    registry.record(origin,width,status,framebuffer);
}
extern "C" uint32_t iss2000_resolve_vi_framebuffer(uint32_t origin,uint32_t width,uint8_t size){
    return registry.resolve(origin,width,size).value_or(UINT32_MAX);
}
extern "C" uint32_t iss2000_vi_original_rate(uint32_t vertical_sync){return vertical_sync>600?50:60;}
