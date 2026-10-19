// Original project work: djultra64.
#pragma once
#include "transform_guest_layout.hpp"
#include <span>
#include <cstring>
namespace iss2000 {
// PAL High loader owns807AA000..807B4A60; framebuffer/depth end at807AA000.
// The port reserves the disjoint807C0000..807E0000 for two1024-matrix banks.
// This prevents original324-entry exhaustion with all22 highest-detail rigs.
inline constexpr uint32_t PalFieldMatrixBase=0x7C0000,PalFieldMatrixBankSize=0x10000;
inline bool extend_pal_field_matrix_arena(std::span<uint8_t> ram) noexcept {
    if(ram.size()!=0x800000)return false;
    auto w=[&](uint32_t a){uint32_t v;std::memcpy(&v,ram.data()+(a&0x7fffff),4);return v;};
    auto b=[&](uint32_t a){return ram[(a&0x7fffff)^3];};
    const unsigned bank=w(0x8009DED0),mode=b(0x8013B42A);
    if(w(0x8009E02C)!=0x8013B418 || b(0x8013B429)!=1 ||
       b(0x8013B446)!=6 || b(0x8013B44C)!=4 || bank>1 || mode>1 ||
       w(0x8013B42C)!=(mode?0x02800220u:0x014000F0u) ||
       w(0x800B1A48)!=0x800A7848+bank*0x5100 ||
       w(0x800B1A4C)!=0x800AC948+bank*0x5100)return false;
    const uint32_t begin=0x80000000+PalFieldMatrixBase+bank*PalFieldMatrixBankSize,end=begin+PalFieldMatrixBankSize;
    std::memcpy(ram.data()+0xB1A48,&begin,4);std::memcpy(ram.data()+0xB1A4C,&end,4);return true;
}

// Original PAL instruction, scene-dispatch and replay evidence is recorded in
// pal-runtime.md and pal-scene-epochs.md. All fields below are physical offsets.
inline TransformGuestLayout verified_pal_transform_layout(){
    TransformGuestLayout l;
    l.record_pools={{{0x145624,285,0x98},{0x14FF5C,900,0x60}}};
    l.arena_base=0xA7848;l.arena_size=0x5100;
    l.extended_arena_base=PalFieldMatrixBase;l.extended_arena_size=PalFieldMatrixBankSize;
    l.bank_selector=0x9DED0;l.arena_cursor=0xB1A48;l.arena_end=0xB1A4C;
    l.scene_bytes={0x13B446,0x13B44C};
    l.perspective_matrices={0xC1AC0,0xC1B00};
    l.view_matrices={{{0xCC388,0xCC3C8},{0xCC408,0xCC448}}};
    l.microcodes={{{0x69AD0,0x99EF0},{0x6AE60,0x9A310}}};
    l.interpolation_scene_token=0x604;
    l.epoch_bytes={0x13B452,0x12DE27,0xC81A4,0};l.epoch_byte_count=3;
    l.replay_continuity=ReplayContinuityLayout{0x12DDF0,0x12DE27,3,68};
    return l;
}
}
