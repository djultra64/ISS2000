// Original project work: djultra64.
#pragma once
#include "transform_tracker.hpp"
#include <array>
#include <optional>
#include <span>
namespace iss2000 {
struct PalMenuAvatarProof {
    TransformModelScope models;
    std::array<std::array<uint32_t,2>,38> matrices{};
};
// Exact original Training-preparation, yellow single-team and blue two-team
// Select Teams607 owners and their genuine19-node player rigs.
// Exact active Select Teams can additionally prove two original cloth roots.
// Reading this proof never changes guest state or advances its animation.
std::optional<PalMenuAvatarProof> verified_pal_menu_avatar(std::span<const uint8_t>) noexcept;
// Traverse the original task, following known lists/segments/microcode switches.
// All owned model matrices (19 or38) must identify the same bank; ambiguity rejects.
std::optional<unsigned> pal_menu_avatar_task_bank(std::span<const uint8_t>,uint64_t root,const PalMenuAvatarProof&) noexcept;
}
