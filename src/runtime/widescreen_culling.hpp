// Original project work: djultra64.
#pragma once
#include <array>
#include <cstdint>
#include <span>

namespace iss2000 {
// Original guest addresses, selected only after the exact ROM revision is known.
// Factories are backed by original instruction/body evidence in pal-code-map.md.
struct WidescreenGuestLayout {
    uint32_t aspect, horizontal, vertical, far_horizontal, far_vertical;
    std::array<uint32_t,3> corner_axes;
};
constexpr WidescreenGuestLayout verified_us_widescreen_layout() noexcept {
    return {0x800A07E8,0x800A0984,0x800A08D0,0x800AA104,0x800AA108,
            {0x800C5D3C,0x80177ED0,0x801A2FF0}};
}
constexpr WidescreenGuestLayout verified_pal_widescreen_layout() noexcept {
    return {0x8009DF00,0x8009E09C,0x8009DFE8,0x800A7824,0x800A7828,
            {0x800C345C,0x801755F0,0x801A0760}};
}
// Native RDRAM contains host-order words, as used by the generated CPU code.
// Call immediately after the corresponding original camera builder. False means
// unsupported/invalid state; no byte is changed on failure. Original mode is a
// byte-exact no-op. These helpers neither alter projection nor select settings.
// Runtime callers pass their selected layout explicitly; the US default preserves
// existing US diagnostic/test callers. Invalid or overlapping layout fields fail
// before any memory access or mutation.
bool apply_widescreen_culling(std::span<uint8_t> rdram, bool wide,
    const WidescreenGuestLayout& layout=verified_us_widescreen_layout()) noexcept;
// Original800228D0 rewrites the far pair without refreshing angular bounds.
bool apply_widescreen_far_extents(std::span<uint8_t> rdram, bool wide,
    const WidescreenGuestLayout& layout=verified_us_widescreen_layout()) noexcept;
// Original80022760 consumes the far pair during each corner test. Ensure at
// entry before original execution; an already-wide pair is a successful no-op.
bool ensure_widescreen_far_extents(std::span<uint8_t> rdram, bool wide,
    const WidescreenGuestLayout& layout=verified_us_widescreen_layout()) noexcept;
// Original800243E0 rebuilds all four rotated rays before each application.
// The caller must not apply this repeatedly to already widened rays.
bool apply_widescreen_world_corners(std::span<uint8_t> rdram, bool wide,
    const WidescreenGuestLayout& layout=verified_us_widescreen_layout()) noexcept;
}
