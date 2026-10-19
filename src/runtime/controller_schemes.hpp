// Original project work: djultra64.
#pragma once
#include <array>
#include <cstdint>
#include <optional>
namespace iss2000 {
enum class FootballAction : uint8_t { Pass, Shoot, Dash, Lob, Through, OneTwo, Curve, Cursor, Count };
enum class PhysicalControl : uint8_t { South, East, West, North, L1, R1, L2, R2, Count };
enum class ControllerScheme : uint8_t { Type1, Type2, Type3, Type4, Type5, Free };
using FootballBindings = std::array<PhysicalControl, 8>;
inline constexpr FootballBindings default_football_bindings{
    PhysicalControl::West, PhysicalControl::North, PhysicalControl::South, PhysicalControl::East,
    PhysicalControl::R1, PhysicalControl::L1, PhysicalControl::L2, PhysicalControl::R2};
constexpr uint16_t physical_control_mask(PhysicalControl control) noexcept {
    return unsigned(control) < unsigned(PhysicalControl::Count) ? uint16_t(1u << unsigned(control)) : 0;
}
std::optional<FootballBindings> scheme_bindings(ControllerScheme scheme) noexcept;
bool valid_football_bindings(const FootballBindings& bindings) noexcept;
// Move the action to the requested physical control, exchanging the occupied
// action with its previous control. Invalid input leaves the complete map intact.
bool assign_free(FootballBindings& bindings, FootballAction action, PhysicalControl control) noexcept;
// Output is an original guest pad packet, before the game's own normalizer.
// This does not include direction, Start, or generic menu-navigation input.
std::optional<uint16_t> football_guest_pad(const FootballBindings& bindings,
    uint16_t held_physical_mask, unsigned original_n64_profile) noexcept;
}
