#include "runtime/pal_menu_view.hpp"
// Original project work: djultra64.
#include "runtime/game_settings_menu.hpp"
#include <optional>
namespace iss2000 {
namespace {
bool valid(const GameSettingsDraft& d){
 if(unsigned(d.graphics.aspect_ratio)>unsigned(AspectRatio::Wide16x9)||
    unsigned(d.graphics.resolution)>unsigned(RenderResolution::P2160)||
    unsigned(d.graphics.refresh_rate)>unsigned(RenderRefresh::Hz120)||
    unsigned(d.graphics.filter_2d)>unsigned(Filter2D::Bilinear))return false;
 for(const auto family:d.families)if(unsigned(family)>unsigned(platform::Family::Nintendo))return false;
 return true;
}
std::optional<std::string> label(std::string_view name){
 if(name.empty())return std::nullopt;
 std::string out;
 for(char c:name){
  if(c=='+')out+="Plus";
  else if(c=='-')out+=name.size()==1?"Minus":" ";
  else if((c>='A'&&c<='Z')||(c>='a'&&c<='z')||(c>='0'&&c<='9')||c==' '||c=='.')out+=c;
  else return std::nullopt;
 }
 if(out.size()>32||out.find_first_not_of(' ')==std::string::npos)return std::nullopt;
 return out;
}
template<class T>T cycle(T current,unsigned count,int direction){return T((unsigned(current)+count+direction)%count);}

}
void GameSettingsMenu::sound(PalMenuSound value){if(sounds_.size()<32)sounds_.push_back({++sound_sequence_,value});}
std::optional<SettingsSoundEvent> GameSettingsMenu::pending_sound()const{std::lock_guard lock(mutex_);if(sounds_.empty())return {};return sounds_.front();}
void GameSettingsMenu::acknowledge_sound(uint64_t sequence){std::lock_guard lock(mutex_);if(!sounds_.empty()&&sounds_.front().sequence==sequence)sounds_.pop_front();}
bool GameSettingsMenu::open(unsigned port,const GameSettingsDraft& initial){
 std::lock_guard lock(mutex_);
 if(active_||busy_||port>=4||!valid(initial))return false;
 initial_=draft_=initial;input_port_=port;target_port_=0;selected_=0;
 page_=Page::Main;status_=Status::None;active_=true;sounds_.clear();sound(PalMenuSound::Accept);return true;
}
bool GameSettingsMenu::can_apply_shortcut()const{std::lock_guard lock(mutex_);return active_&&page_==Page::Graphics;}
void GameSettingsMenu::sync_fullscreen(bool fullscreen){
 std::lock_guard lock(mutex_);initial_.graphics.fullscreen=draft_.graphics.fullscreen=fullscreen;
 status_=Status::None;
}
bool GameSettingsMenu::active()const{std::lock_guard lock(mutex_);return active_;}
unsigned GameSettingsMenu::port()const{std::lock_guard lock(mutex_);return input_port_;}
GameSettingsDraft GameSettingsMenu::draft()const{std::lock_guard lock(mutex_);return draft_;}
void GameSettingsMenu::command(ControlsMenuCommand command,const SaveGameSettingsCallback& save,const OpenSettingsRemapCallback&){
 std::unique_lock lock(mutex_);if(!active_||busy_)return;
 const unsigned count=page_==Page::Graphics?6:page_==Page::Controllers?5:page_==Page::Port?3:4;
 auto back=[&]{
  status_=Status::None;
  switch(page_){
   case Page::Main:draft_=initial_;active_=false;break;
   case Page::Graphics:page_=Page::Main;selected_=0;break;
   case Page::Controllers:page_=Page::Main;selected_=1;break;
   case Page::Port:page_=Page::Controllers;selected_=target_port_;break;
  }
 };
 auto persist=[&](bool close){
  const auto draft=draft_;busy_=true;status_=Status::Saving;lock.unlock();bool success=false;
  try{success=save&&save(draft);}catch(...){success=false;}
  lock.lock();busy_=false;sound(success?PalMenuSound::Accept:PalMenuSound::Error);status_=success?Status::Saved:Status::SaveFailed;
  if(success){initial_=draft_;if(close)active_=false;}
 };
 if(command==ControlsMenuCommand::ApplySave){if(page_==Page::Graphics)persist(false);return;}
 if(command==ControlsMenuCommand::Cancel){sound(PalMenuSound::Back);back();return;}
 if(command==ControlsMenuCommand::Up||command==ControlsMenuCommand::Down){
  sound(PalMenuSound::Navigate);selected_=(selected_+count+(command==ControlsMenuCommand::Up?-1:1))%count;status_=Status::None;return;
 }
 const bool accept=command==ControlsMenuCommand::Accept;
 const bool next=command==ControlsMenuCommand::NextPage,previous=command==ControlsMenuCommand::PreviousPage;
 if(!accept&&!next&&!previous)return;
 const int direction=previous?-1:1;
 if(page_==Page::Graphics){
  if(selected_==5){if(accept){sound(PalMenuSound::Back);back();}return;}
  sound(PalMenuSound::Navigate);status_=Status::None;
  if(selected_==0)draft_.graphics.aspect_ratio=cycle(draft_.graphics.aspect_ratio,2,direction);
  else if(selected_==1)draft_.graphics.resolution=cycle(draft_.graphics.resolution,7,direction);
  else if(selected_==2)draft_.graphics.refresh_rate=cycle(draft_.graphics.refresh_rate,3,direction);
  else if(selected_==3)draft_.graphics.fullscreen=!draft_.graphics.fullscreen;
  else if(selected_==4)draft_.graphics.filter_2d=cycle(draft_.graphics.filter_2d,2,direction);
  return;
 }
 if(page_==Page::Port&&selected_==0){sound(PalMenuSound::Navigate);draft_.families[target_port_]=cycle(draft_.families[target_port_],4,direction);status_=Status::None;return;}
 if(page_==Page::Port&&selected_==1){sound(PalMenuSound::Navigate);draft_.vibration[target_port_]=!draft_.vibration[target_port_];status_=Status::None;return;}
 if(!accept)return;
 if(!(page_==Page::Main&&selected_==2))sound(PalMenuSound::Accept);
 if(page_==Page::Main){
  if(selected_==0){page_=Page::Graphics;selected_=0;}
  else if(selected_==1){page_=Page::Controllers;selected_=0;}
  else if(selected_==3)back();
  else {
   persist(true);
  }
 }else if(page_==Page::Controllers){
  if(selected_==4)back();else{target_port_=selected_;page_=Page::Port;selected_=0;}
 }else if(selected_==2)back();

}
std::vector<EngineTextLine> GameSettingsMenu::lines(std::string_view physical_accept,std::string_view physical_back)const{
 std::lock_guard lock(mutex_);if(!active_)return {};
 const auto accept=label(physical_accept),back=label(physical_back);if(!accept||!back)return {};
 std::string title="PC Settings";std::vector<std::string> rows;
 switch(page_){
  case Page::Main:rows={"Graphics","Controls","Save options","Cancel"};break;
  case Page::Graphics:{
   title="Graphics";
   constexpr const char* resolutions[]={"Original","720p","900p","1080p","1440p","1800p","2160p"};
   constexpr const char* rates[]={"Original","60","120"};
   rows={draft_.graphics.aspect_ratio==AspectRatio::Wide16x9?"Aspect 16 by 9":"Aspect 4 by 3",
         std::string("Resolution ")+resolutions[unsigned(draft_.graphics.resolution)],
         std::string("Framerate limit ")+rates[unsigned(draft_.graphics.refresh_rate)],draft_.graphics.fullscreen?"Screen Fullscreen":"Screen Windowed",draft_.graphics.filter_2d==Filter2D::Bilinear?"Filtering 2D Bilinear":"Filtering 2D Original","Back"};break;
  }
  case Page::Controllers:title="Controls";for(unsigned p=0;p<4;++p)rows.push_back("Player "+std::to_string(p+1));rows.push_back("Back");break;
  case Page::Port:{
   title="Player "+std::to_string(target_port_+1);
   constexpr const char* families[]={"Auto","Xbox","PlayStation","Nintendo"};
   rows={std::string("Controller type ")+families[unsigned(draft_.families[target_port_])],draft_.vibration[target_port_]?"Vibration On":"Vibration Off","Back"};break;
  }
 }
 std::vector<EngineTextLine> result{{24,20,title},{24,38,"Changes apply when saved"}};
 for(unsigned row=0;row<rows.size();++row)result.push_back({24,int16_t(60+row*(page_==Page::Graphics?18:20)),(row==selected_?"SELECT ":"       ")+rows[row]});
 const char* status=(page_==Page::Graphics||page_==Page::Port)?"Left and Right change":"";
 switch(status_){case Status::SaveFailed:status="Save failed. Try again";break;case Status::Saving:status="Saving";break;case Status::Saved:status="Options saved";break;default:break;}
 if(*status)result.push_back({24,166,status});
 result.push_back({24,188,*accept+" select"});result.push_back({24,206,*back+" back"});return result;
}
PalOptionsSkinView GameSettingsMenu::view(std::string_view accept,std::string_view back)const{
 auto result=pal_menu_view(lines(accept,back),false);
 for(auto& row:result.rows)if(row.label.starts_with("Controller type ")){row.value=row.label.substr(16);row.label="Controller type";}
 return result;
}
GameSettingsMenu& game_settings_menu(){static GameSettingsMenu menu;return menu;}
}
