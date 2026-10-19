// Original project work: djultra64.
#include "controller_schemes.hpp"
#include <utility>

namespace iss2000 {
namespace {
using P = PhysicalControl;
constexpr std::array<FootballBindings, 5> presets{{
    default_football_bindings,
    {P::South, P::West, P::East, P::North, P::R2, P::L2, P::L1, P::R1},
    {P::South, P::North, P::West, P::East, P::R2, P::L2, P::L1, P::R1},
    {P::South, P::West, P::R1, P::East, P::North, P::R2, P::L2, P::L1},
    // Adapted eFootball positions; ISS OneTwo remains a single R1 action.
    {P::South, P::West, P::R2, P::East, P::North, P::R1, P::L2, P::L1},
}};
// Original PAL table 800774F0 (ROM 780F0), reordered from its six slots
// into FootballAction order. Primary manual20/21 identifies the ROM slots as
// OneTwo, Through, Dash, Pass, Shoot, Lob. Standard C-down/left/right raw
// masks are4/2/1. Z and R are preserved by original801D4880.
constexpr uint16_t guest_actions[3][8]{
    {0x8000, 0x4000, 0x0004, 0x0002, 0x0008, 0x0001, 0x2000, 0x0010},
    {0x8000, 0x0002, 0x4000, 0x0004, 0x0008, 0x0001, 0x2000, 0x0010},
    {0x0004, 0x0008, 0x0002, 0x0001, 0x4000, 0x8000, 0x2000, 0x0010},
};
}

std::optional<FootballBindings> scheme_bindings(ControllerScheme scheme) noexcept {
    const auto index = unsigned(scheme);
    if (index >= presets.size()) return std::nullopt;
    return presets[index];
}

bool valid_football_bindings(const FootballBindings& bindings) noexcept {
    uint16_t seen = 0;
    for (const auto control : bindings) {
        const auto mask = physical_control_mask(control);
        if (!mask || (seen & mask)) return false;
        seen |= mask;
    }
    return seen == 0xff;
}

bool assign_free(FootballBindings& bindings, FootballAction action, PhysicalControl control) noexcept {
    const auto index = unsigned(action);
    if (index >= bindings.size() || !physical_control_mask(control) ||
        !valid_football_bindings(bindings)) return false;
    for (auto& occupied : bindings) {
        if (occupied == control) {
            std::swap(bindings[index], occupied);
            return true;
        }
    }
    return false;
}

std::optional<uint16_t> football_guest_pad(const FootballBindings& bindings,
    uint16_t held_physical_mask, unsigned original_n64_profile) noexcept {
    if (original_n64_profile >= 3 || (held_physical_mask & 0xff00) ||
        !valid_football_bindings(bindings)) return std::nullopt;
    uint16_t pad = 0;
    for (unsigned action = 0; action < bindings.size(); ++action) {
        if (held_physical_mask & physical_control_mask(bindings[action]))
            pad |= guest_actions[original_n64_profile][action];
    }
    return pad;
}
}
