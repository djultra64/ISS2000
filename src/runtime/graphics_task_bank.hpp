// Original project work: djultra64.
#pragma once
#include <cstdint>
#include <optional>
#include <span>
#include <vector>
#include "transform_guest_layout.hpp"

namespace iss2000 {
// Read-only probe for tasks already identified as the verified F3DEX2 family.
// Returns the first original perspective LOAD's bank, never a mutable global.
// Unknown/conditional control flow, microcode changes, unsupported projections,
// invalid addresses, depth overflow or command-budget exhaustion return nullopt.
// Exact RT64 enable magic permits only the current non-control raster extensions;
// their bounded payload slots are skipped, never decoded as matrix commands.
// With no initial context only segment0 is known; DB06 establishes other bases.
std::optional<unsigned> graphics_task_bank(std::span<const uint8_t> native_rdram,
                                         uint64_t root,
                                         std::span<const uint32_t,2> perspective_matrices) noexcept;
// Prove a bounded nested list is actually traversed by this task.
bool graphics_task_reaches_list(std::span<const uint8_t>,uint64_t root,uint32_t list,const TransformGuestLayout&);
struct GraphicsTaskModelReferences {
    std::vector<uint32_t> loads;
    std::optional<unsigned> perspective_bank;
};
// Full bounded task traversal. Unknown/static projections do not imply model
// ownership. Only exact known microcode switches retain the common F3DEX2 ABI.
std::optional<GraphicsTaskModelReferences> graphics_task_model_references(
    std::span<const uint8_t>,uint64_t root,const TransformGuestLayout&);
// A segmented root with a nonzero segment requires explicit initial context.
std::optional<unsigned> graphics_task_bank(std::span<const uint8_t> native_rdram,
                                         uint64_t root,
                                         std::span<const uint32_t,2> perspective_matrices,
                                         std::span<const uint32_t,16> initial_segments) noexcept;
}
