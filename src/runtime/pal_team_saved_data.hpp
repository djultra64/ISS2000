// Original project work: djultra64.
#pragma once
#include "recomp.h"
#include <cstdint>
#include <optional>
#include <span>
#include <string_view>
namespace iss2000 {
struct PalTeamSavedDataLabel {
    std::string_view text;
    int16_t x{},y{};
    uint16_t width{},height{};
};
// Exact original Select Teams consumers only. Edit Data, Original J1/J2 and
// foreign scenes remain untouched. Coordinates are original logical pixels.
std::optional<PalTeamSavedDataLabel> pal_team_saved_data_label(
    std::span<const uint8_t>,uint64_t sprite);
// Invoke before the original80041B50 sprite call; suppress that call only when
// true. Literal resident font2 I4 pixels are copied into this original task's
// arena and rendered by original80041B50. This uses an existing original font,
// not an imitation of the separate precomposed caption face. Original source
// sprites, scripts, atlases and caller/stack bytes remain unchanged.
// Caller must supply the exact registered original80041B50 identity.
bool draw_pal_team_saved_data(std::span<uint8_t>,const recomp_context&,
                             recomp_func_t* original_sprite);
}
