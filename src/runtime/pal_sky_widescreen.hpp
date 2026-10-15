// Original project work: djultra64.
#pragma once
#include <array>
#include <cstdint>
#include <span>
namespace iss2000 {
struct PalGfxBounds {
    uint32_t begin{},end{},cursor{};
    explicit operator bool()const noexcept{return begin!=0;}
};
// Original 800006A4/80002A10: two 0x10060-byte frame records, 64 KiB Gfx
// array at +8 followed by OSTask metadata at +0x10008.
PalGfxBounds pal_gfx_bounds(std::span<const uint8_t>) noexcept;
struct PalSkyRectangle {bool visible{};std::array<uint32_t,6> words{};};
// Compress geometry by 3/4 and increase horizontal sampling by 4/3. The
// scoped RT64 STRETCH restores physical size; it does not stretch the texture.
PalSkyRectangle pal_sky_rectangle(int32_t x,int32_t y,uint32_t flags,bool high_resolution) noexcept;
bool pal_sky_preflight(std::span<const uint8_t>,bool wide) noexcept;
uint32_t append_pal_sky_rectangle(std::span<uint8_t>,uint32_t cursor,uint32_t end,
    int32_t x,int32_t y,uint32_t flags,bool high_resolution) noexcept;
// Only instantiate around the hash-pinned derivative. Invalid scopes perform
// no writes. This bound is local to the guest CPU thread, never renderer state.
class PalSkyWriteScope {
    uint32_t previous_end{};
    uint8_t* previous_ram{};
    bool active{};
public:
    PalSkyWriteScope(std::span<uint8_t>,bool wide) noexcept;
    ~PalSkyWriteScope();
    explicit operator bool()const noexcept{return active;}
    PalSkyWriteScope(const PalSkyWriteScope&)=delete;
    PalSkyWriteScope& operator=(const PalSkyWriteScope&)=delete;
};
}
extern "C" uint32_t iss2000_pal_sky_emit(uint8_t*,uint32_t,int32_t,int32_t,uint32_t,int);
extern "C" void iss2000_pal_sky_aspect(uint8_t*,int);
