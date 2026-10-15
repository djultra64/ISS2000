// Original project work: djultra64.
#pragma once
#include "runtime/game_controls_menu.hpp"
#include <array>
namespace iss2000 {
struct ControlsMenuControllerSample {
 uint32_t held=0;
 float x=0,y=0;
 platform::PortPreferences preferences{};
};
struct ControlsMenuInputFrame {
 bool active=false,capturing=false,focused=true,any_input=false,escape=false,keyboard_active=false;
 unsigned port=0;
 ControlsMenuCommand keyboard_command=ControlsMenuCommand::None;
 std::array<ControlsMenuControllerSample,4> controllers{};
};
struct ControlsMenuInputResult {
 ControlsMenuCommand command=ControlsMenuCommand::None;
 uint32_t held=0;
 bool suppress=false,keyboard_navigation=false,deliver=false;
};
// SDL sampling and preference persistence remain in platform.cpp. This bounded
// state machine owns the same opening, rising-edge and closing-release rules.
class ControlsMenuInputRouter {
 bool was_active_=false,armed_=false,await_release_=false,keyboard_=false,was_capturing_=false;
 uint32_t previous_navigation_=0;
public:
 ControlsMenuInputResult route(const ControlsMenuInputFrame& frame){
  ControlsMenuInputResult result;
  if(!frame.active){
   if(was_active_)await_release_=true;
   was_active_=armed_=was_capturing_=false;previous_navigation_=0;
   if(frame.focused&&!frame.any_input)await_release_=false;
   result.suppress=await_release_;return result;
  }
  result.suppress=true;
  if(!was_active_){was_active_=true;armed_=false;await_release_=true;previous_navigation_=0;keyboard_=frame.keyboard_active;}
  if(was_capturing_&&!frame.capturing){armed_=false;previous_navigation_=0;}
  was_capturing_=frame.capturing;
  result.keyboard_navigation=keyboard_;
  if(frame.port>=4)return result;
  if(!frame.focused){armed_=false;previous_navigation_=0;return result;}
  const auto& sample=frame.controllers[frame.port];result.held=sample.held;
  if(frame.escape){result.deliver=true;result.command=ControlsMenuCommand::Cancel;keyboard_=result.keyboard_navigation=true;return result;}
  if(!armed_){if(!frame.any_input)armed_=true;return result;}
  result.deliver=true;
  if(frame.capturing){if(sample.held)keyboard_=result.keyboard_navigation=false;return result;}
  auto pressed=[&](platform::Action action){auto b=sample.preferences.bindings[size_t(action)];return b>=0&&b<SDL_CONTROLLER_BUTTON_MAX&&(sample.held&(uint32_t(1)<<unsigned(b)));};
  uint32_t navigation=0;
  if(pressed(platform::Action::A))navigation|=1;
  if(pressed(platform::Action::B))navigation|=2;
  if(pressed(platform::Action::DUp)||sample.y>.5f)navigation|=4;
  if(pressed(platform::Action::DDown)||sample.y<-.5f)navigation|=8;
  if(pressed(platform::Action::L)||pressed(platform::Action::DLeft)||sample.x<-.5f)navigation|=16;
  if(pressed(platform::Action::R)||pressed(platform::Action::DRight)||sample.x>.5f)navigation|=32;
  const auto rising=navigation&~previous_navigation_;previous_navigation_=navigation;
  if(frame.keyboard_command!=ControlsMenuCommand::None){result.command=frame.keyboard_command;keyboard_=result.keyboard_navigation=true;}
  else if(rising){
   result.command=(rising&2)?ControlsMenuCommand::Cancel:(rising&1)?ControlsMenuCommand::Accept:(rising&4)?ControlsMenuCommand::Up:(rising&8)?ControlsMenuCommand::Down:(rising&16)?ControlsMenuCommand::PreviousPage:ControlsMenuCommand::NextPage;
   keyboard_=result.keyboard_navigation=false;
  }
  return result;
 }
};
}
