// Original project work: djultra64.
#pragma once
#include <cstdint>
namespace iss2000 {
// Cycle bits are already extracted from OtherMode: 0/1 are one/two-cycle;
// copy and fill must retain their original sampling. Never alter 3D materials,
// framebuffer copies, guest OtherMode, guest texture coordinates or sprite geometry.
constexpr bool filter_2d_call(bool enabled,bool rectangle,uint32_t cycle,
                             uint32_t tiles,bool framebuffer_copy){
 return enabled&&rectangle&&cycle<0x200000&&tiles&&!framebuffer_copy;
}
}
extern "C" bool iss2000_filter_2d_enabled();
