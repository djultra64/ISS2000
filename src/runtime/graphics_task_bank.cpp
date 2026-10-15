// Original project work: djultra64.
#include "graphics_task_bank.hpp"
#include <array>
#include <cstring>

namespace iss2000 {
namespace {
constexpr uint32_t MemorySize=0x800000;
constexpr unsigned CommandLimit=16384,DepthLimit=32;
std::optional<uint32_t> physical(uint32_t address) noexcept {
    if(address<MemorySize)return address;
    if(address>=0x80000000u && address<0x80800000u)return address-0x80000000u;
    if(address>=0xA0000000u && address<0xA0800000u)return address-0xA0000000u;
    return std::nullopt;
}
struct Probe {
    std::span<const uint8_t> ram;
    std::span<const uint32_t,2> perspective;
    std::array<uint32_t,16> segments{};
    std::array<bool,16> known{};
    std::optional<uint32_t> resolve(uint64_t address) const noexcept {
        const uint32_t low=uint32_t(address),high=uint32_t(address>>32);
        if(high && (high!=0xFFFFFFFFu || !(low&0x80000000u)))return std::nullopt;
        if(low>=0x80000000u)return physical(low);
        if(low>=0x10000000u)return std::nullopt;
        const unsigned segment=low>>24;
        if(!known[segment])return std::nullopt;
        const uint64_t result=uint64_t(segments[segment])+(low&0xFFFFFFu);
        if(result>=ram.size())return std::nullopt;
        return uint32_t(result);
    }
    uint32_t word(uint32_t offset) const noexcept {
        uint32_t value;
        std::memcpy(&value,ram.data()+offset,sizeof(value));
        return value;
    }
    std::optional<unsigned> run(uint64_t root) noexcept {
        auto start=resolve(root);
        if(!start)return std::nullopt;
        uint32_t pc=*start;
        std::array<uint32_t,DepthLimit-1> returns{};
        unsigned depth=0;
        for(unsigned command=0;command<CommandLimit;++command){
            if(pc%8 || pc>ram.size()-8)return std::nullopt;
            const uint32_t w=word(pc),v=word(pc+4),op=w>>24;
            if(op==0xDB && ((w>>16)&0xFF)==6){
                const uint32_t offset=w&0xFFFFu;
                if(offset%4 || offset/4>=segments.size())return std::nullopt;
                auto base=physical(v);
                if(!base)return std::nullopt;
                segments[offset/4]=*base;known[offset/4]=true;
            }else if(op==0xDE){
                if(w!=0xDE000000u && w!=0xDE010000u)return std::nullopt;
                auto target=resolve(v);
                if(!target)return std::nullopt;
                if(w==0xDE000000u){
                    if(depth>=returns.size())return std::nullopt;
                    returns[depth++]=pc+8;
                }
                pc=*target;
                continue;
            }else if(op==0xDF){
                if(!depth)return std::nullopt;
                pc=returns[--depth];
                continue;
            }else if(op==0xDA){
                if((w&0x00FFFFF8u)!=0x00380000u)return std::nullopt;
                auto matrix=resolve(v);
                if(!matrix || *matrix%8 || *matrix>ram.size()-64)return std::nullopt;
                if((w&6u)==6u){
                    if(*matrix==perspective[0])return 0;
                    if(*matrix==perspective[1])return 1;
                    return std::nullopt;
                }
            }else if(op==0x03 || op==0x04 || op==0xDD){
                // Vertex-dependent branches and a new microcode require more
                // execution context than this deliberately narrow probe owns.
                return std::nullopt;
            }else if(!(op==0x00 || op==0x01 || op==0x02 ||
                       (op>=0x05 && op<=0x08) || (op>=0xD7 && op<=0xDC) || op>=0xE0)){
                return std::nullopt;
            }
            pc+=8;
        }
        return std::nullopt;
    }
};
}
std::optional<unsigned> graphics_task_bank(std::span<const uint8_t> ram,uint64_t root,
                                         std::span<const uint32_t,2> perspective) noexcept {
    if(ram.size()!=MemorySize)return std::nullopt;
    Probe probe{ram,perspective};probe.known[0]=true;
    return probe.run(root);
}
std::optional<unsigned> graphics_task_bank(std::span<const uint8_t> ram,uint64_t root,
                                         std::span<const uint32_t,2> perspective,
                                         std::span<const uint32_t,16> initial) noexcept {
    if(ram.size()!=MemorySize)return std::nullopt;
    Probe probe{ram,perspective};
    for(unsigned i=0;i<initial.size();++i){
        auto base=physical(initial[i]);
        if(!base)return std::nullopt;
        probe.segments[i]=*base;probe.known[i]=true;
    }
    return probe.run(root);
}
}
