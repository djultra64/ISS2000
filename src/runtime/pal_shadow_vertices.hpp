// Original project work: djultra64.
#pragma once
#include "transform_tracker.hpp"
#include <memory>
#include <optional>
#include <span>
#include <vector>
namespace iss2000 {
inline constexpr uint32_t PalShadowIdFirst=0x60000000u,PalShadowIdLast=0x6FFFFFFFu;
static_assert(TransformModelIdLimit<=PalShadowIdFirst);
struct PalShadowVertexTag {
    uint32_t object{},vertices{},first_id{},second_id{};
    uint64_t generation{},epoch{};
    bool projected=false;
    bool ball=false;
};
struct PalShadowTaskSnapshot {
    uint64_t sequence{},epoch{};
    uint32_t root{},scene{};
    unsigned bank{};
    std::vector<PalShadowVertexTag> tags;
    std::optional<uint32_t> lookup(uint32_t physical,unsigned count,unsigned destination)const noexcept;
};
// Complete original192-byte common near list, including its terminator.
bool verified_pal_near_shadow_list(std::span<const uint8_t>) noexcept;
// Read-only original near-shadow recognition plus independent immutable FIFO.
// Allocate/release observations must accompany the original285-node pool calls.
class PalShadowVertices {
    struct State;std::unique_ptr<State> state;
public:
    PalShadowVertices();~PalShadowVertices();
    void allocation(uint64_t);
    void release(uint64_t);
    void begin_frame(std::span<const uint8_t>);
    void invalidate();
    bool capture(std::span<const uint8_t>,uint64_t object);
    void submit(std::span<const uint8_t>,uint32_t type,const TransformTaskFingerprint&);
    std::shared_ptr<const PalShadowTaskSnapshot> consume(const TransformTaskFingerprint&);
};
// Configure before starting guest/render threads; false disables all hooks.
void configure_pal_shadow_vertices(bool enabled);
void observe_pal_shadow_allocation(uint64_t);
void observe_pal_shadow_release(uint64_t);
void observe_pal_shadow_frame(std::span<const uint8_t>);
void invalidate_pal_shadow_vertices();
void observe_pal_shadow_vertices(std::span<const uint8_t>,uint64_t object);
// Co-publish/consume with the transform FIFO under its existing submission lock.
void submit_pal_shadow_metadata(std::span<const uint8_t>,uint32_t type,const TransformTaskFingerprint&);
std::shared_ptr<const PalShadowTaskSnapshot> consume_pal_shadow_metadata(const TransformTaskFingerprint&);
}
