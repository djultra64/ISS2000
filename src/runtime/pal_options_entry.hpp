// Original project work: djultra64.
#pragma once
#include <cstdint>
#include <optional>
#include <span>
namespace iss2000 {
struct PalOptionsEntry {unsigned row{};bool pc_settings{};};
struct PalOptionsLabel {int x{},y{};unsigned width{},height{};bool selected{};};
// Read-only exact PAL Options owner. Native dispatch must also compare the
// active registry pointer with the reviewed original symbol, not address alone.
std::optional<PalOptionsEntry> pal_options_entry(std::span<const uint8_t>) noexcept;
// Only the original Resolution WORD sprite, reused as PC Settings by explicit
// user request. Original bar, bullet and selection-frame objects are excluded.
std::optional<PalOptionsLabel> pal_options_pc_label(std::span<const uint8_t>,uint64_t object) noexcept;
}
