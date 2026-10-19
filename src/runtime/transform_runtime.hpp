// Original project work: djultra64.
#pragma once
#include "transform_tracker.hpp"
#include <mutex>
#include <span>
namespace iss2000 {
struct MatrixBuildObservation {
    TransformMatrixCapture capture;
    unsigned bank{};
    bool valid{};
    const void* owner{};
};
struct TransformPositionObservation {
    uint32_t pointer_field{},record{};
    std::array<uint32_t,3> position{};
    std::array<uint64_t,2> frames{};
    const void* owner{};
    bool valid{};
};
// Host-only observer. Caller synchronizes access to the guest memory itself.
// Metadata/frame publication is serialized internally; snapshots own their data.
class TransformRuntime {
    struct State;
    std::unique_ptr<State> state_;
public:
    explicit TransformRuntime(const TransformGuestLayout&);
    ~TransformRuntime();
    TransformRuntime(const TransformRuntime&)=delete;
    TransformRuntime& operator=(const TransformRuntime&)=delete;
    void observe_allocation(uint64_t record);
    void observe_release(uint64_t record);
    std::optional<TransformTag> lookup_record(uint64_t record)const;
    void observe_frame(std::span<const uint8_t> ram);
    void invalidate_scene();
    // Use only around a verified original correction routine. Its ordinary
    // calls leave this record's position unchanged; no distance heuristic.
    TransformPositionObservation observe_position_before(std::span<const uint8_t> ram,uint32_t pointer_field);
    void observe_position_after(std::span<const uint8_t> ram,TransformPositionObservation);
    MatrixBuildObservation observe_matrix_before(std::span<const uint8_t> ram,uint64_t record,TransformMatrixBuilder builder);
    void observe_matrix_after(std::span<const uint8_t> ram,MatrixBuildObservation observation);
    void submit_metadata(std::span<const uint8_t> ram,uint32_t type,const TransformTaskFingerprint& task);
    std::shared_ptr<const TransformTaskSnapshot> consume_metadata(const TransformTaskFingerprint& task);
};
// Select once, before guest/render threads start, using the verified ROM profile.
// Global hooks are disabled until configured; no regional-address fallback.
void configure_transform_runtime(const TransformGuestLayout&);
void observe_transform_allocation(uint64_t record);
void observe_transform_release(uint64_t record);
std::optional<TransformTag> lookup_transform_record(uint64_t record);
void observe_transform_frame(std::span<const uint8_t> ram);
// Call after an independently verified original scene/cut/stage setter.
void notify_transform_discontinuity();
TransformPositionObservation observe_transform_position_before(std::span<const uint8_t> ram,uint32_t pointer_field);
void observe_transform_position_after(std::span<const uint8_t> ram,TransformPositionObservation);
MatrixBuildObservation observe_transform_matrix_before(std::span<const uint8_t> ram,uint64_t record,TransformMatrixBuilder builder);
void observe_transform_matrix_after(std::span<const uint8_t> ram,MatrixBuildObservation observation);
// Must enclose metadata publication AND the original graphics submission.
std::mutex& transform_submission_mutex();
void submit_transform_metadata(std::span<const uint8_t> ram,uint32_t type,const TransformTaskFingerprint& task);
std::shared_ptr<const TransformTaskSnapshot> consume_transform_metadata(const TransformTaskFingerprint& task);
}
