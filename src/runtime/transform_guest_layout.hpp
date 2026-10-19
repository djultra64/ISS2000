// Original project work: djultra64.
#pragma once
#include <array>
#include <cstdint>
#include <optional>
#include <stdexcept>

namespace iss2000 {
// Physical RDRAM offsets, verified independently for each supported ROM revision.
// A runtime owns a const copy; selecting a ROM must select its matching layout.
struct TransformRecordPool { uint32_t base{},count{},stride{}; };
struct TransformMicrocode { uint32_t code{},data{}; };
struct ReplayContinuityLayout {
    uint32_t cursor_halfword{},phase_byte{};
    uint8_t playback_phase{};
    uint16_t capacity{};
};
struct TransformGuestLayout {
    std::array<TransformRecordPool,2> record_pools{};
    uint32_t arena_base{},arena_size{};
    uint32_t bank_selector{},arena_cursor{},arena_end{};
    std::array<uint32_t,2> scene_bytes{};
    std::array<uint32_t,2> perspective_matrices{};
    std::array<std::array<uint32_t,2>,2> view_matrices{};
    std::array<TransformMicrocode,2> microcodes{};
    uint16_t interpolation_scene_token{};
    std::array<uint32_t,4> epoch_bytes{};
    unsigned epoch_byte_count{};
    std::optional<ReplayContinuityLayout> replay_continuity{};
    // Optional port-owned double buffer; original banks remain valid in menus.
    uint32_t extended_arena_base{},extended_arena_size{};
};
// Preserved US evidence, never a fallback for an unconfigured/PAL runtime.
inline constexpr TransformGuestLayout us_transform_layout(){
    return {{{{0x148104,285,0x98},{0x152A3C,900,0x60}}},
        0xAA128,0x5100,0xA07B8,0xB4328,0xB432C,{0x13DF26,0x13DF2C},
        {0xC43A0,0xC43E0},{{{0xCEC68,0xCECA8},{0xCECE8,0xCED28}}},
        {{{0x69250,0x9C8E0},{0x6A5E0,0x9CD00}}},0x604};
}
inline void validate_transform_guest_layout(const TransformGuestLayout& layout){
    const auto bounded=[](uint64_t offset,uint64_t bytes,unsigned alignment){
        return offset%alignment==0 && offset<0x800000 && bytes<=0x800000-offset;
    };
    for(const auto& p:layout.record_pools)
        if(!p.count || p.stride<0x60 || p.stride%4 ||
           !bounded(p.base,uint64_t(p.count-1)*p.stride+0x60,4))
            throw std::invalid_argument("Invalid transform record-pool layout");
    if(layout.arena_size<64 || layout.arena_size%64 ||
       !bounded(layout.arena_base,uint64_t(layout.arena_size)*2,8))
        throw std::invalid_argument("Invalid transform arena layout");
    if(layout.extended_arena_base || layout.extended_arena_size){
        if(layout.extended_arena_size<64 || layout.extended_arena_size%64 ||
           !bounded(layout.extended_arena_base,uint64_t(layout.extended_arena_size)*2,8) ||
           (layout.extended_arena_base<layout.arena_base+2*layout.arena_size &&
            layout.arena_base<layout.extended_arena_base+2*layout.extended_arena_size))
            throw std::invalid_argument("Invalid extended transform arena layout");
    }
    for(auto offset:{layout.bank_selector,layout.arena_cursor,layout.arena_end})
        if(!bounded(offset,4,4))throw std::invalid_argument("Invalid transform globals layout");
    for(auto offset:layout.scene_bytes)
        if(!bounded(offset,1,1))throw std::invalid_argument("Invalid transform scene layout");
    for(auto offset:layout.perspective_matrices)
        if(!bounded(offset,64,8))throw std::invalid_argument("Invalid transform perspective layout");
    if(layout.perspective_matrices[0]==layout.perspective_matrices[1])
        throw std::invalid_argument("Ambiguous transform perspective layout");
    for(const auto& camera:layout.view_matrices)
        for(auto offset:camera)
            if(!bounded(offset,64,8))throw std::invalid_argument("Invalid transform camera layout");
    if(layout.epoch_byte_count>layout.epoch_bytes.size())
        throw std::invalid_argument("Too many transform epoch bytes");
    for(unsigned n=0;n<layout.epoch_byte_count;++n)
        if(!bounded(layout.epoch_bytes[n],1,1))throw std::invalid_argument("Invalid transform epoch byte");
    if(layout.replay_continuity){
        const auto& replay=*layout.replay_continuity;
        if(replay.capacity<2 || !bounded(replay.cursor_halfword,2,2) || !bounded(replay.phase_byte,1,1))
            throw std::invalid_argument("Invalid transform replay continuity layout");
    }
    for(const auto& code:layout.microcodes)
        if(!bounded(code.code,1,1)||!bounded(code.data,1,1))
            throw std::invalid_argument("Invalid transform microcode layout");
}
}
