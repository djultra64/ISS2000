// Original project work: djultra64.
#pragma once
#include <cstdint>
#include <optional>
#include <span>

namespace iss2000 {
// Read-only probe for tasks already identified as the verified F3DEX2 family.
// Returns the first original perspective LOAD's bank, never a mutable global.
// Unknown/conditional control flow, microcode changes, unsupported projections,
// invalid addresses, depth overflow or command-budget exhaustion return nullopt.
// With no initial context only segment0 is known; DB06 establishes other bases.
std::optional<unsigned> graphics_task_bank(std::span<const uint8_t> native_rdram,
                                         uint64_t root,
                                         std::span<const uint32_t,2> perspective_matrices) noexcept;
// A segmented root with a nonzero segment requires explicit initial context.
std::optional<unsigned> graphics_task_bank(std::span<const uint8_t> native_rdram,
                                         uint64_t root,
                                         std::span<const uint32_t,2> perspective_matrices,
                                         std::span<const uint32_t,16> initial_segments) noexcept;
}
