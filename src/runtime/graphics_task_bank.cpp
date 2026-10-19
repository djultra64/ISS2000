// Original project work: djultra64.
#include "graphics_task_bank.hpp"
#include <array>
#include <cstring>

namespace iss2000 {
namespace {
constexpr uint32_t MemorySize=0x800000;
// Genuine all22-player r55 tasks traverse20,157..22,099 slots, including
// repeatedly called geometry lists. The old16K cap discarded their entire map.
// Bound traversal to1MiB of command traffic (one eighth of RDRAM): enough
// headroom for these measured tasks while cycles remain finite and depth-limited.
constexpr unsigned CommandLimit=131072,DepthLimit=32;
std::optional<uint32_t> physical(uint32_t address) noexcept {
    if(address<MemorySize)return address;
    if(address>=0x80000000u && address<0x80800000u)return address-0x80000000u;
    if(address>=0xA0000000u && address<0xA0800000u)return address-0xA0000000u;
    return std::nullopt;
}
// Pinned public RT64 GBI commands emitted by the verified sky/HUD/background
// scopes. They affect raster state only, never matrix/segment/list control flow.
// Sizes count complete64-bit slots, including payloads that may look like opcodes.
std::optional<unsigned> raster_extension_slots(uint32_t command,uint32_t parameter) noexcept {
    switch(command){
    case 0x64000033u:if(parameter<=2)return 1;break; // Rectangle aspect.
    case 0x64000017u:case 0x64000018u:if(!parameter)return 1;break; // Scissor push/pop.
    case 0x64000005u:if(!(parameter&0xFC000000u))return 2;break; // Extended scissor.
    case 0x64000006u:if(!(parameter&0xFF000000u))return 2;break; // Rectangle alignment.
    case 0x64000002u:if(!(parameter&0xF0000000u))return 3;break; // Texture rectangle.
    }
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
    std::vector<uint32_t> model_loads{};
    std::optional<uint32_t> wanted_list{};bool reached_list{};
    std::span<const TransformMicrocode> microcodes{};
    std::optional<unsigned> first_perspective{};
    std::optional<unsigned> run(uint64_t root,bool collect=false) {
        auto start=resolve(root);
        if(!start)return std::nullopt;
        uint32_t pc=*start;
        std::array<uint32_t,DepthLimit-1> returns{};
        unsigned depth=0;bool extended_enabled=false;uint32_t half1=0;
        for(unsigned command=0;command<CommandLimit;++command){
            if(pc%8 || pc>ram.size()-8)return std::nullopt;
            if(wanted_list && pc==*wanted_list)reached_list=true;
            const uint32_t w=word(pc),v=word(pc+4),op=w>>24;
            if(w==0xE0525464u){
                if(v!=0x10000064u)return std::nullopt;
                extended_enabled=true;
            }
            if(op==0x64){
                if(!extended_enabled)return std::nullopt;
                const auto slots=raster_extension_slots(w,v);
                if(!slots || *slots*8>ram.size()-pc || command+*slots>CommandLimit)return std::nullopt;
                command+=*slots-1;
                pc+=*slots*8;
                continue;
            }
            if(op==0xE1)half1=v;
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
                if(collect && (w!=0xDF000000u || v))return std::nullopt;
                if(!depth)return collect?first_perspective.value_or(2):std::optional<unsigned>{};
                pc=returns[--depth];
                continue;
            }else if(op==0xDA){
                if((w&0x00FFFFF8u)!=0x00380000u)return std::nullopt;
                auto matrix=resolve(v);
                if(!matrix || *matrix%8 || *matrix>ram.size()-64)return std::nullopt;
                if(collect && (w&6u)==2u)model_loads.push_back(*matrix);
                if((w&6u)==6u){
                    std::optional<unsigned> bank;
                    if(*matrix==perspective[0])bank=0;
                    if(*matrix==perspective[1])bank=1;
                    if(!collect)return bank;
                    if(bank && !first_perspective)first_perspective=bank;
                }
            }else if(op==0xDD && collect){
                auto code=physical(v),data=physical(half1);bool known_pair=false;
                for(const auto& m:microcodes)if(code&&data&&*code==m.code&&*data==m.data)known_pair=true;
                if(w!=0xDD0007FFu || !known_pair)return std::nullopt;
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
bool graphics_task_reaches_list(std::span<const uint8_t> ram,uint64_t root,uint32_t list,const TransformGuestLayout& layout){
    if(ram.size()!=MemorySize)return false;
    Probe probe{ram,layout.perspective_matrices};probe.known[0]=true;probe.microcodes=layout.microcodes;probe.wanted_list=physical(list);
    return probe.wanted_list && probe.run(root,true).has_value() && probe.reached_list;
}
std::optional<GraphicsTaskModelReferences> graphics_task_model_references(
    std::span<const uint8_t> ram,uint64_t root,const TransformGuestLayout& layout){
    if(ram.size()!=MemorySize)return std::nullopt;
    Probe probe{ram,layout.perspective_matrices};probe.known[0]=true;probe.microcodes=layout.microcodes;
    if(!probe.run(root,true))return std::nullopt;
    return GraphicsTaskModelReferences{std::move(probe.model_loads),probe.first_perspective};
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
