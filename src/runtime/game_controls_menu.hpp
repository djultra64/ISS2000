// Original project work: djultra64.
#pragma once
#include "platform.hpp"
#include <cstdint>
#include <functional>
#include <mutex>
#include <atomic>
#include <vector>
#include <span>
#include "recomp.h"
namespace iss2000 {
enum class ControlsMenuCommand { None, Up, Down, PreviousPage, NextPage, Accept, Cancel, RestoreDefault };
struct EngineTextLine { int16_t x=24,y=24;std::string text; };
using SavePortCallback=std::function<bool(unsigned,const platform::PortPreferences&)>;
// Input snapshots come from the host input thread. Drawing uses the original game font.
// The callback must persist and then apply the selected port; it runs without this mutex.
class GameControlsMenu {
public:
 bool open(unsigned port,const platform::PortPreferences& initial);
 void update(ControlsMenuCommand command,uint32_t physical_held,platform::Family active_family,const SavePortCallback& save);
 bool active()const;
 bool capturing()const;
 unsigned port()const;
 std::vector<EngineTextLine> lines(platform::Family active_family)const;
private:
 mutable std::mutex mutex_;
 std::atomic<bool> visible_{false};
 bool keyboard_navigation_=false;
 platform::Family last_gamepad_family_=platform::Family::Xbox;
 platform::PortPreferences draft_{},navigation_{};
 unsigned port_=0,selected_=0;
 bool active_=false,capture_=false,released_=false,saving_=false,error_=false,conflict_=false;
};
GameControlsMenu& game_controls_menu();
// Call only under the verified PAL original-menu owner guard, on the original main
// guest thread, after complete frame 80000BB8. original_draw is original80048660.
// Optional original_clear is original019FC and composes an opaque engine screen.
// Rejects the entire request before mutation if text, stack or Gfx bounds are invalid.
bool draw_pal_engine_text(std::span<uint8_t> ram,const recomp_context& caller,
                          std::span<const EngineTextLine> lines,recomp_func_t* original_draw,
                          recomp_func_t* original_clear=nullptr);
}
