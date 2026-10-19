// Original project work: djultra64.
#pragma once
#include "menu_sprite_runtime.hpp"
#include <array>
#include <memory>
#include <vector>
namespace RT64 {struct Workload;struct WorkloadQueue;struct GameFrame;struct RenderWorker;struct BufferUploader;}
namespace iss2000 {
struct MenuRectSample {
 uint32_t uid{},call_index{};uint64_t compatibility{};
 std::array<float,4> rect{},prim{},env{};
};
struct MenuRectFrame {uint64_t sequence{},epoch{};std::vector<MenuRectSample>rectangles;};
struct MenuRectMatch {uint32_t call_index{};std::array<float,4>previous{},prim{},env{};bool moved{},faded{};};
std::vector<MenuRectMatch> match_menu_rectangles(const MenuRectFrame&,const MenuRectFrame&,float weight);
struct MenuRectRenderStats {uint32_t rectangles{},matches{},moved{},fades{};bool fractional{};};
// Private existing render-evidence log only; no HUD or presentation claim.
MenuRectRenderStats menu_rect_render_stats();
struct MenuRectPrevious {std::array<int32_t,4>rect{};float weight=1;};
void record_menu_workload(const RT64::Workload*,const MenuSpriteTaskSnapshot*,bool allow);
// One scope per queued workload and actual fractional render, inside RT64's
// existing workload mutex and before its original recordSetup/execute/wait.
class MenuRectRenderScope {
 struct Impl;std::unique_ptr<Impl>impl_;
public:
 MenuRectRenderScope(RT64::WorkloadQueue*,RT64::Workload*,const RT64::GameFrame*,const RT64::GameFrame*,float weight,RT64::RenderWorker*);
 ~MenuRectRenderScope();
 RT64::BufferUploader* uploader()const;
};
bool menu_rect_previous(const RT64::Workload*,uint32_t call_index,MenuRectPrevious&);
}
