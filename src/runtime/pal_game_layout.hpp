// Original project work: djultra64.
#pragma once
#include "transform_guest_layout.hpp"
namespace iss2000 {
// Original PAL instruction, scene-dispatch and replay evidence is recorded in
// pal-runtime.md and pal-scene-epochs.md. All fields below are physical offsets.
inline TransformGuestLayout verified_pal_transform_layout(){
    TransformGuestLayout l;
    l.record_pools={{{0x145624,285,0x98},{0x14FF5C,900,0x60}}};
    l.arena_base=0xA7848;l.arena_size=0x5100;
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
