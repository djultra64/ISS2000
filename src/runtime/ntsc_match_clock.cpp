// Original project work: djultra64.
#include "ntsc_match_clock.hpp"
#include <cstring>

namespace iss2000 {
namespace {
constexpr size_t MemorySize=0x800000;
constexpr std::array<uint32_t,2> Remaining={0x8012DDD6,0x8012DDDA};
constexpr std::array<uint32_t,2> Subcounter={0x8012DDD8,0x8012DDDC};
uint16_t read(std::span<const uint8_t> ram,uint32_t guest) noexcept {
    uint16_t value;
    std::memcpy(&value,ram.data()+((guest&0x7FFFFF)^2),sizeof(value));
    return value;
}
void write(std::span<uint8_t> ram,uint32_t guest,uint16_t value) noexcept {
    std::memcpy(ram.data()+((guest&0x7FFFFF)^2),&value,sizeof(value));
}
}
bool NtscMatchClock::reset_after_init(std::span<const uint8_t> ram) noexcept {
    ready_=false;
    ++sequence_;
    if(ram.size()!=MemorySize)return false;
    const auto remaining=read(ram,Remaining[0]);
    if(!remaining || read(ram,Remaining[1])!=remaining ||
       read(ram,Subcounter[0])!=25 || read(ram,Subcounter[1])!=25)return false;
    phase_={1,1};
    ready_=true;
    return true;
}
NtscMatchClock::Snapshot NtscMatchClock::before_tick(std::span<const uint8_t> ram) const noexcept {
    Snapshot result;
    if(!ready_ || ram.size()!=MemorySize)return result;
    result.sequence=sequence_;
    for(size_t i=0;i<2;++i){
        result.remaining[i]=read(ram,Remaining[i]);
        result.subcounter[i]=read(ram,Subcounter[i]);
        if(result.subcounter[i]>25)return result;
    }
    result.valid=true;
    return result;
}
bool NtscMatchClock::after_tick(std::span<uint8_t> ram,const Snapshot& before) noexcept {
    if(!ready_ || !before.valid || before.sequence!=sequence_ || ram.size()!=MemorySize)return false;
    std::array<bool,2> reload{};
    for(size_t i=0;i<2;++i){
        const auto remaining=read(ram,Remaining[i]),counter=read(ram,Subcounter[i]);
        if(before.subcounter[i]>25 || counter>25)return false;
        reload[i]=before.subcounter[i]==0 && before.remaining[i]>1 &&
            remaining==before.remaining[i]-1 && counter==25;
    }
    for(size_t i=0;i<2;++i)if(reload[i]){
        phase_[i]=uint8_t((phase_[i]+1)%6);
        if(phase_[i]==0)write(ram,Subcounter[i],24);
    }
    ++sequence_;
    return true;
}
}
