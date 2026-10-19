// Original project work: djultra64.
#pragma once
#include "transform_guest_layout.hpp"
#include <array>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <optional>
#include <span>
#include <unordered_map>
namespace iss2000 {
// Shadow vertex chunks own 0x60000000..0x6FFFFFFF; rigid/camera IDs remain below.
inline constexpr uint32_t TransformModelIdLimit=0x60000000u;
struct TransformTag {
    uint32_t id{},record{};
    uint64_t generation{},scene_epoch{};
};
struct TransformTaskFingerprint {
    uint64_t data_ptr{},ucode{},ucode_data{};
    uint32_t data_size{};
};
struct TransformTaskToken { uint64_t sequence{};uint32_t root{}; };
// Optional, verified model-only scope. Publication requires every record's current frame tag.
struct TransformVertexModel {uint32_t record{},id{};uint64_t compatibility{};};
struct TransformModelScope {
    uint16_t scene{};
    // One original19-node rig, or the two complete Select Teams rigs.
    uint8_t record_count{19};
    std::array<uint32_t,38> records{};
    // Optional original Select Teams cloth roots; copied only with live tags.
    std::array<TransformVertexModel,2> vertex_models{};
};
class TransformTaskSnapshot {
    friend class TransformTracker;
    std::unordered_map<uint32_t,TransformTag> matrices_;
public:
    uint64_t sequence{},scene_epoch{},scene_token{};
    TransformGuestLayout layout{};
    std::array<uint32_t,2> camera_ids{};
    uint32_t root{};
    unsigned bank{};
    std::optional<TransformModelScope> model_scope;
    uint32_t camera_id(unsigned slot)const{return slot<camera_ids.size()?camera_ids[slot]:0;}
    std::optional<TransformTag> lookup(uint64_t physical_or_kseg_matrix) const;
};
enum class TransformMatrixBuilder { Unknown,Conditional252F8,Unconditional25710 };
struct TransformMatrixCapture {
    uint64_t frame{},record{};
    uint32_t flags{};
    uint64_t matrix_before{},matrix_after{},cursor_before{},cursor_after{};
    uint32_t flags_after{};
    TransformMatrixBuilder builder=TransformMatrixBuilder::Unknown;
};
// Host metadata only. Hooks supply immutable before/after observations; this
// class neither reads guest memory nor changes simulation/render instructions.
class TransformTracker {
    struct State;
    std::unique_ptr<State> state_;
    TransformTaskToken publish_locked(std::optional<uint64_t> frame,uint32_t root,std::optional<TransformModelScope> scope={});
public:
    explicit TransformTracker(const TransformGuestLayout&,size_t max_pending_tasks=64);
    ~TransformTracker();
    TransformTracker(const TransformTracker&)=delete;
    TransformTracker& operator=(const TransformTracker&)=delete;
    void begin_scene(uint64_t scene_token);
    // A verified cut/replay/stage boundary may reuse the same scene bytes.
    // Keep allocations and queued snapshots; retire only current-frame IDs.
    void invalidate_scene();
    TransformTag allocate(uint64_t record);
    bool release(uint64_t record);
    // Allocation generation with current scene epoch; never invents an allocation.
    std::optional<TransformTag> lookup_record(uint64_t record) const;
    // Original252B0: bank0 [800AA128,800AF228),bank1 [800AF228,800B4328).
    uint64_t begin_frame(unsigned bank,uint64_t arena_begin,uint64_t arena_end);
    bool capture_matrix(const TransformMatrixCapture&);
    // Integration must retain the exact sequence token alongside the submitted
    // OSTask. A reused data_ptr alone cannot identify a particular submission.
    // Must surround submit_task + upstream service enqueue with one project
    // submission mutex shared by ALL graphics producers. Non-GFX types return
    // nullopt and do not enter this queue. Missing frame means an empty snapshot.
    // A second graphics producer thread quarantines tracking: upstream implicit
    // producer streams do not guarantee a single global FIFO despite a mutex.
    // References choose one captured bank under the publication lock; conflicting
    // banks reject and never fall back to the perspective/frame hint.
    std::optional<TransformTaskToken> submit_task(uint32_t type,const TransformTaskFingerprint&,std::optional<uint64_t> frame={},std::optional<TransformModelScope> scope={},std::optional<std::span<const uint32_t>> model_loads={});
    std::shared_ptr<const TransformTaskSnapshot> consume_submission(const TransformTaskFingerprint&);
    bool submissions_synchronized()const;
    // Call only while upstream graphics submissions/queue are stopped and drained.
    void reset_submissions();
    TransformTaskToken publish_task(uint64_t frame,uint64_t data_ptr);
    std::shared_ptr<const TransformTaskSnapshot> consume_task(uint64_t sequence,uint64_t data_ptr);
};
}
