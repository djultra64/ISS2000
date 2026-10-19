// Original project work: djultra64.
#pragma once
#include "transform_tracker.hpp"
#include "pal_radar_interpolation.hpp"
#include <memory>
#include <span>
#include <unordered_map>
namespace iss2000 {
struct MenuSpriteObservation {uint64_t frame{},identity{};uint32_t begin{},object{};bool valid{};};
struct MenuRadarOwnership {PalRadarCapture capture;uint64_t generation{};};
struct MenuSpriteTaskSnapshot {
 uint64_t sequence{},epoch{};
 std::unordered_map<uint32_t,uint32_t> commands; // physical original E4 address -> nonzero stable ID
 std::vector<MenuRadarOwnership> radar;
};
// Original PAL English profile only, selected before guest threads start.
bool configure_menu_sprite_runtime(std::span<const uint8_t> canonical_rom);
// At entry to the existing original80000BB8 wrapper, before original once.
void begin_menu_sprite_frame(std::span<const uint8_t> ram);
// After exact original80008A54 returns; preserves queued snapshot ownership.
void observe_menu_sprite_initialization(uint64_t object);
// After exact original80048528 returns: the separate80-record text pool at
// 801650DC, stride28. Ordinary setters do not renew this allocation lifetime.
void observe_menu_text_initialization(uint64_t object);
// Enclose the complete existing41B50 wrapper, including its post-adapters and
// scoped background/HUD destructors. They may move/append original commands.
MenuSpriteObservation observe_menu_sprite_before(std::span<const uint8_t>,uint64_t object);
// Exact original48660 emits font rectangles directly. Same original pool
// lifetimes, including the original80-record text pool. Nonpool temporary
// text requires an explicit semantic page scope.
MenuSpriteObservation observe_menu_text_before(std::span<const uint8_t>,uint64_t text_object);
void observe_menu_sprite_after(std::span<const uint8_t>,MenuSpriteObservation);
// Exact original CI8 intro producer has no pool object. Its already-validated
// descriptor is an explicit semantic owner; call after all original adapters.
void observe_menu_canvas(std::span<const uint8_t>,uint64_t semantic_owner,uint32_t begin,uint32_t end);
// Host-owned temporary original-engine sprite objects: scope one complete
// named page/widget with a stable semantic ID; draw ordinals stay within it.
class MenuSpriteSemanticScope {
 uint64_t previous_{};unsigned previous_ordinal_{};
public:
 explicit MenuSpriteSemanticScope(uint64_t semantic_owner);
 ~MenuSpriteSemanticScope();
};
void notify_menu_sprite_discontinuity();
// Retire before original callback writes its private bank; then register only a sealed capture.
void retire_menu_radar_bank(uint32_t begin);
void observe_menu_radar(std::span<const uint8_t>,const PalRadarCapture&);
// Publish alongside transform metadata while the producer holds
// transform_submission_mutex; consume in the existing renderer FIFO stream.
// A scheduler-delayed task retains its own arena's complete prior-frame copy,
// source sequence and epoch. Arena reuse/cuts retire unsubmitted ownership.
void submit_menu_sprite_metadata(uint32_t task_type,const TransformTaskFingerprint&,std::span<const uint8_t> ram={});
std::shared_ptr<const MenuSpriteTaskSnapshot> consume_menu_sprite_metadata(const TransformTaskFingerprint&,std::span<const uint8_t> ram={});
}
