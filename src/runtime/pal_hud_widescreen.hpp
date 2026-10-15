// Original project work: djultra64.
#pragma once
#include <cstdint>
#include <span>
namespace iss2000 {
enum class PalHudDraw { Sprite, Text, ScoreFlags };
enum class PalHudGroup { None, Score, Clock, LeftPlayer, RightPlayer };
struct PalHudPlacement {
    PalHudGroup group{};
    uint16_t origin{};
    int16_t x_offset{},y_offset{}; // Original RDP quarter-pixel units.
    explicit operator bool() const noexcept { return group!=PalHudGroup::None; }
};
PalHudPlacement pal_hud_placement(std::span<const uint8_t>,bool wide,
    PalHudDraw,uint64_t object=0) noexcept;
// Scope only the reviewed original sprite/text draw or score-flag compositor.
// No guest objects, texture coordinates, assets or simulation fields are edited.
class PalHudScope {
    std::span<uint8_t> ram;
    uint32_t end{},begin{};
    bool active{};
public:
    PalHudScope(std::span<uint8_t>,bool wide,PalHudDraw,uint64_t object=0) noexcept;
    ~PalHudScope();
    explicit operator bool() const noexcept { return active; }
    PalHudScope(const PalHudScope&)=delete;
    PalHudScope& operator=(const PalHudScope&)=delete;
};
}
