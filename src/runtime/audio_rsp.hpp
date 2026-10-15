// Original project work: djultra64.
#pragma once
#include "game_revision.hpp"
#include <cstdint>
#include <cstring>
#include <span>
namespace iss2000 {
// Both original programs are instruction-identical; each revision loads its own
// verified address. Exact ROM identity pins the remaining code and data bytes.
inline bool matches_audio_rsp(std::span<const uint8_t> ram,uint32_t type,uint32_t address){
    const auto code=address&0x1FFFFFFFu;
    if(type!=2 || code!=active_revision().audio_ucode || code>ram.size() || ram.size()-code<8)return false;
    uint32_t first,second;
    std::memcpy(&first,ram.data()+code,4);std::memcpy(&second,ram.data()+code+4,4);
    return first==0x20180360u && second==0x20170F90u;
}
}
