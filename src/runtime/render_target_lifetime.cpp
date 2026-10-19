// Original project work: djultra64.
#include "render_target_lifetime.hpp"
#include <stdexcept>
#include <unordered_map>
namespace iss2000 {
struct RenderTargetLifetimeState {std::shared_mutex mutex;};
namespace {
std::mutex registry_mutex;
std::unordered_map<const void*,std::weak_ptr<RenderTargetLifetimeState>> owners;
std::shared_ptr<RenderTargetLifetimeState> lifetime(const void* owner){
    if(!owner)throw std::invalid_argument("Missing RT64 render-target lifetime owner");
    std::lock_guard registry_lock(registry_mutex);
    auto& entry=owners[owner];
    auto state=entry.lock();
    if(!state){state=std::make_shared<RenderTargetLifetimeState>();entry=state;}
    return state;
}
}
RenderTargetPresentationScope::RenderTargetPresentationScope(const void* owner)
    :state(lifetime(owner)),lock(state->mutex){}
RenderTargetPresentationScope::~RenderTargetPresentationScope()=default;
RenderTargetCleanupScope::RenderTargetCleanupScope(const void* owner)
    :state(lifetime(owner)),lock(state->mutex){}
RenderTargetCleanupScope::~RenderTargetCleanupScope()=default;
}
