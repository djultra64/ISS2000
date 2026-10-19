// Original project work: djultra64.
#pragma once
#include <memory>
#include <mutex>
#include <shared_mutex>
namespace iss2000 {
struct RenderTargetLifetimeState;
// Pins all targets owned by one RT64 SharedQueueResources instance during the
// complete presentation. The scope starts only inside threadPresent, after
// waitForWorkloadId; it does not stop the workload's extra-frame producer.
class RenderTargetPresentationScope {
    std::shared_ptr<RenderTargetLifetimeState> state;
    std::shared_lock<std::shared_mutex> lock;
public:
    explicit RenderTargetPresentationScope(const void* owner);
    ~RenderTargetPresentationScope();
    RenderTargetPresentationScope(const RenderTargetPresentationScope&)=delete;
    RenderTargetPresentationScope& operator=(const RenderTargetPresentationScope&)=delete;
};
// Only destructive configuration changes take the exclusive scope. Acquire it
// with configurationMutex released, then reacquire configurationMutex. This
// preserves the common lifetime -> configuration lock order, including inspector
// reentry, and prevents clearing interpolated targets before the last GPU fence.
class RenderTargetCleanupScope {
    std::shared_ptr<RenderTargetLifetimeState> state;
    std::unique_lock<std::shared_mutex> lock;
public:
    explicit RenderTargetCleanupScope(const void* owner);
    ~RenderTargetCleanupScope();
    RenderTargetCleanupScope(const RenderTargetCleanupScope&)=delete;
    RenderTargetCleanupScope& operator=(const RenderTargetCleanupScope&)=delete;
};
}
