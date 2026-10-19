// Original project work: djultra64.
#pragma once
#include "runtime/controller_schemes.hpp"
#include <array>
#include <mutex>
namespace iss2000 {
struct FootballPortConfig {
 ControllerScheme scheme=ControllerScheme::Type1;
 FootballBindings free_bindings=default_football_bindings;
 bool operator==(const FootballPortConfig&)const=default;
};
enum class FootballEditorStatus { None,ReleaseControls,InvalidInput };
struct FootballEditorInput {
 uint16_t held=0;
 bool start=false,cancel=false,up=false,down=false;
};
struct FootballEditorSnapshot {
 bool active=false,editing_free=false,armed=false;
 unsigned selected_port=0,selected_action=0;
 std::array<FootballPortConfig,4> draft{};
 FootballEditorStatus status=FootballEditorStatus::None;
 bool operator==(const FootballEditorSnapshot&)const=default;
};
// Pure four-port draft state. The original controller screen owns rendering and
// actual persistence. Input fields are held states; neutral gates prevent an
// opening/held control from editing or confirming a new draft.
class FootballControllerEditor {
public:
 bool begin(const std::array<FootballPortConfig,4>& initial,unsigned selected_port=0);
 void end();
 bool select_port(unsigned port);
 bool cycle_scheme(int direction);
 bool open_free();
 bool input(const FootballEditorInput& input);
 FootballEditorSnapshot snapshot()const;
private:
 mutable std::mutex mutex_;
 FootballEditorSnapshot state_{};
 std::array<FootballPortConfig,4> initial_{};
 FootballBindings free_entry_=default_football_bindings;
};
FootballControllerEditor& football_controller_editor();
}
