// Original project work: djultra64.
#pragma once
#include <cstdint>
#include <span>
namespace iss2000 {
enum class PalHudDraw { Sprite, Text, ScoreFlags };
enum class PalHudGroup { None, Score, Clock, LeftPlayer, RightPlayer, Radar };
struct PalHudPlacement {
    PalHudGroup group{};
    uint16_t origin{};
    int16_t x_offset{},y_offset{}; // Original RDP quarter-pixel units.
    explicit operator bool() const noexcept { return group!=PalHudGroup::None; }
};
PalHudPlacement pal_hud_placement(std::span<const uint8_t>,bool wide,
    PalHudDraw,uint64_t object=0) noexcept;
// Remove only the verified High radar's redundant overlapping edge repairs.
// Its14 main pieces already form a complete non-overlapping canvas.
bool repair_pal_radar_background(std::span<uint8_t>,bool wide,uint32_t begin,uint32_t end) noexcept;
// Called after exact original flat802A4DC0 or projected802A4F78, once.
// Validate its complete owned24-byte output before translating the rectangle.
// World projection and simulation survive; each8x8 source cell receives a
// bounded inset to prevent POINT quantization from reading its atlas neighbor.
bool align_pal_radar_marker(std::span<uint8_t>,bool wide,uint32_t begin) noexcept;
// Compatibility for the earlier Training-only integration.
bool align_pal_training_radar_marker(std::span<uint8_t>,bool wide,uint32_t begin) noexcept;
// Scope only the reviewed original sprite/text draw or score-flag compositor.
// No guest objects, texture coordinates, assets or simulation fields are edited.
class PalHudScope {
    std::span<uint8_t> ram;
    uint32_t end{},begin{};
    bool active{},radar{};
public:
    PalHudScope(std::span<uint8_t>,bool wide,PalHudDraw,uint64_t object=0) noexcept;
    ~PalHudScope();
    explicit operator bool() const noexcept { return active; }
    PalHudScope(const PalHudScope&)=delete;
    PalHudScope& operator=(const PalHudScope&)=delete;
};
}
