// Original project work: djultra64.
#include "runtime/football_controller_editor.hpp"
#include <bit>
namespace iss2000 {
bool FootballControllerEditor::begin(const std::array<FootballPortConfig,4>& initial,unsigned selected_port){
 std::lock_guard lock(mutex_);
 if(state_.active||selected_port>=initial.size())return false;
 for(const auto& port:initial)
  if(unsigned(port.scheme)>unsigned(ControllerScheme::Free)||!valid_football_bindings(port.free_bindings))return false;
 initial_=initial;state_={};state_.active=true;state_.selected_port=selected_port;state_.draft=initial;return true;
}
void FootballControllerEditor::end(){
 std::lock_guard lock(mutex_);state_={};state_.draft=initial_;
}
bool FootballControllerEditor::select_port(unsigned port){
 std::lock_guard lock(mutex_);
 if(!state_.active||state_.editing_free||port>=state_.draft.size())return false;
 state_.selected_port=port;state_.selected_action=0;state_.status=FootballEditorStatus::None;return true;
}
bool FootballControllerEditor::cycle_scheme(int direction){
 std::lock_guard lock(mutex_);
 if(!state_.active||state_.editing_free||(direction!=-1&&direction!=1))return false;
 auto& scheme=state_.draft[state_.selected_port].scheme;
 constexpr int count=int(ControllerScheme::Free)+1;
 scheme=ControllerScheme((int(scheme)+count+direction)%count);state_.status=FootballEditorStatus::None;return true;
}
bool FootballControllerEditor::open_free(){
 std::lock_guard lock(mutex_);
 if(!state_.active||state_.editing_free||state_.draft[state_.selected_port].scheme!=ControllerScheme::Free)return false;
 free_entry_=state_.draft[state_.selected_port].free_bindings;
 state_.editing_free=true;state_.selected_action=0;state_.armed=false;state_.status=FootballEditorStatus::ReleaseControls;return true;
}
bool FootballControllerEditor::input(const FootballEditorInput& input){
 std::lock_guard lock(mutex_);
 if(!state_.active||!state_.editing_free)return false;
 if(input.held&0xff00){state_.status=FootballEditorStatus::InvalidInput;return false;}
 if(!state_.armed){
  if(input.held||input.start||input.cancel||input.up||input.down)return false;
  state_.armed=true;state_.status=FootballEditorStatus::None;return true;
 }
 if(input.cancel||input.start){
  if(input.cancel)state_.draft[state_.selected_port].free_bindings=free_entry_;
  state_.editing_free=false;state_.armed=false;state_.status=FootballEditorStatus::None;return true;
 }
 if(input.up||input.down){
  if(input.up&&input.down){state_.status=FootballEditorStatus::InvalidInput;return false;}
  constexpr unsigned count=unsigned(FootballAction::Count);
  state_.selected_action=(state_.selected_action+count+(input.up?-1:1))%count;
  state_.armed=false;state_.status=FootballEditorStatus::ReleaseControls;return true;
 }
 if(!input.held)return true;
 if(!std::has_single_bit(input.held)){
  state_.armed=false;state_.status=FootballEditorStatus::InvalidInput;return false;
 }
 auto next=state_.draft[state_.selected_port].free_bindings;
 if(!assign_free(next,FootballAction(state_.selected_action),PhysicalControl(std::countr_zero(input.held))))return false;
 state_.draft[state_.selected_port].free_bindings=next;
 state_.armed=false;state_.status=FootballEditorStatus::ReleaseControls;return true;
}
FootballEditorSnapshot FootballControllerEditor::snapshot()const{std::lock_guard lock(mutex_);return state_;}
FootballControllerEditor& football_controller_editor(){static FootballControllerEditor editor;return editor;}

}
