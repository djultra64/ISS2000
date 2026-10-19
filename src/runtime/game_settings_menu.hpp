// Original project work: djultra64.
#pragma once
#include "runtime/game_controls_menu.hpp"
#include "runtime/graphics_settings.hpp"
#include "runtime/pal_options_skin.hpp"
#include <array>
#include <deque>
#include <optional>
#include "runtime/pal_menu_audio.hpp"
#include <functional>
#include <mutex>
#include <string_view>
namespace iss2000 {
struct GameSettingsDraft {
 GraphicsSettings graphics{};
 std::array<bool,4> vibration{true,true,true,true};
 // Automatic follows detection; Keyboard is not a valid manual override.
 std::array<platform::Family,4> families{platform::Family::Automatic,platform::Family::Automatic,platform::Family::Automatic,platform::Family::Automatic};
 bool operator==(const GameSettingsDraft&) const = default;
};
using SaveGameSettingsCallback=std::function<bool(const GameSettingsDraft&)>;
// Retained signature compatibility; GameSettingsMenu never invokes this.
using OpenSettingsRemapCallback=std::function<bool(unsigned)>;
// Graphics and per-port device preferences share one transactional draft.
// Football types and Free editing belong to the original Controller screen.
struct SettingsSoundEvent {uint64_t sequence;PalMenuSound sound;};
class GameSettingsMenu {
public:
 bool open(unsigned input_port,const GameSettingsDraft& initial);
 void command(ControlsMenuCommand command,const SaveGameSettingsCallback& save={},
              const OpenSettingsRemapCallback& remap={});
 bool active() const;
 bool can_apply_shortcut() const;
 // External session fullscreen changes update just this field in the draft and
 // Cancel baseline; other unsaved edits remain pending until explicit Save.
 void sync_fullscreen(bool fullscreen);
 std::optional<SettingsSoundEvent> pending_sound() const;
 void acknowledge_sound(uint64_t sequence);
 unsigned port() const;
 GameSettingsDraft draft() const;
 // Original-font text only. Unsupported or oversized physical labels reject the
 // complete view so a caller cannot accidentally draw misleading fallback names.
 PalOptionsSkinView view(std::string_view physical_accept,std::string_view physical_back) const;
 std::vector<EngineTextLine> lines(std::string_view physical_accept,std::string_view physical_back) const;
private:
 enum class Page { Main,Graphics,Controllers,Port };
 enum class Status { None,SaveFailed,Saving,Saved };
 mutable std::mutex mutex_;
 GameSettingsDraft initial_{},draft_{};
 Page page_=Page::Main;
 Status status_=Status::None;
 unsigned input_port_=0,target_port_=0,selected_=0;
 bool active_=false,busy_=false;
 std::deque<SettingsSoundEvent> sounds_;uint64_t sound_sequence_=0;
 void sound(PalMenuSound value);
};
GameSettingsMenu& game_settings_menu();
}
