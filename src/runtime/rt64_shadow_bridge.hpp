// Original project work: djultra64.
#pragma once
#include "pal_shadow_vertices.hpp"
namespace RT64 {struct State;struct GBI;}
namespace iss2000 {
struct PalShadowBridgeStats {uint64_t vertex_calls{},shadow_chunks{};};
// Construct after RT64TransformBridge and destroy before it. Only exact F3DEX2
// VTX chunks from the current immutable near-shadow snapshot interpolate.
class RT64ShadowBridge {
    struct Impl;std::unique_ptr<Impl> impl;
public:
    RT64ShadowBridge(RT64::State*,RT64::GBI*,std::shared_ptr<const PalShadowTaskSnapshot>,bool allow);
    ~RT64ShadowBridge();
    RT64ShadowBridge(const RT64ShadowBridge&)=delete;
    RT64ShadowBridge& operator=(const RT64ShadowBridge&)=delete;
    bool installed()const noexcept;
    PalShadowBridgeStats stats()const noexcept;
};
}
