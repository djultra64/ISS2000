// Original project work: djultra64.
#include "runtime/game_controls_menu.hpp"
#include <bit>
#include <cstring>
#include <array>
namespace iss2000 {
namespace {
constexpr unsigned action_count=unsigned(platform::Action::Count),item_count=action_count+4,page_rows=6;
constexpr const char* actions[]={"N64 A","N64 B","Start","Z","L","R","C up","C down","C left","C right","D up","D down","D left","D right"};
std::string family_name(platform::Family family){switch(family){case platform::Family::Automatic:return "Auto";case platform::Family::Nintendo:return "Nintendo";case platform::Family::PlayStation:return "PlayStation";case platform::Family::Keyboard:return "Keyboard";default:return "Xbox";}}
std::string binding_name(const platform::PortPreferences& p,unsigned action,platform::Family family){
 auto binding=p.bindings[action];std::string result(platform::button_label(family,binding));
 if(platform::axis_fallback(platform::Action(action),binding)){
  if(action==unsigned(platform::Action::Z))return "Left trigger";
  if(binding==SDL_CONTROLLER_BUTTON_INVALID)return "Right stick";
  result+=" or stick";
 }
 // Only characters independently verified in the original font are passed to the adapter.
 if(result=="+")result="Plus";else if(result=="-")result="Minus";
 for(auto& c:result)if(c=='-')c=' ';
 return result;
}
}
bool GameControlsMenu::open(unsigned port,const platform::PortPreferences& initial){
 std::lock_guard lock(mutex_);if(active_||port>=4||unsigned(initial.manual_family)>unsigned(platform::Family::Nintendo))return false;
 for(auto button:initial.bindings)if(button<SDL_CONTROLLER_BUTTON_INVALID||button>=SDL_CONTROLLER_BUTTON_MAX)return false;
 draft_=initial;navigation_=initial;port_=port;selected_=0;active_=true;visible_.store(true,std::memory_order_release);keyboard_navigation_=false;capture_=released_=saving_=error_=conflict_=false;return true;
}
bool GameControlsMenu::active()const{return visible_.load(std::memory_order_acquire);}
bool GameControlsMenu::capturing()const{std::lock_guard lock(mutex_);return active_&&capture_;}
unsigned GameControlsMenu::port()const{std::lock_guard lock(mutex_);return port_;}
void GameControlsMenu::update(ControlsMenuCommand command,uint32_t held,platform::Family active_family,const SavePortCallback& save){
 std::unique_lock lock(mutex_);if(!active_||saving_)return;
 keyboard_navigation_=active_family==platform::Family::Keyboard;
 if(active_family!=platform::Family::Keyboard&&active_family!=platform::Family::Automatic)last_gamepad_family_=active_family;
 if(capture_){
  if(command==ControlsMenuCommand::Cancel){capture_=false;return;}
  if(held==0){released_=true;return;}
  constexpr uint32_t valid=(uint32_t(1)<<SDL_CONTROLLER_BUTTON_MAX)-1;
  if(released_&&(held&~valid)==0&&std::has_single_bit(held)){
   draft_.bindings[selected_]=SDL_GameControllerButton(std::countr_zero(held));capture_=false;error_=conflict_=false;
  }else released_=false;
  return;
 }
 switch(command){
 case ControlsMenuCommand::Up:selected_=(selected_+item_count-1)%item_count;break;
 case ControlsMenuCommand::Down:selected_=(selected_+1)%item_count;break;
 case ControlsMenuCommand::PreviousPage:selected_=(selected_+item_count-page_rows)%item_count;break;
 case ControlsMenuCommand::NextPage:selected_=(selected_+page_rows)%item_count;break;
 case ControlsMenuCommand::Cancel:active_=false;visible_.store(false,std::memory_order_release);break;
 case ControlsMenuCommand::RestoreDefault:if(selected_<action_count)draft_.bindings[selected_]=platform::default_binding(platform::Action(selected_));else draft_=platform::PortPreferences{};error_=conflict_=false;break;
 case ControlsMenuCommand::Accept:
  if(selected_<action_count){capture_=true;released_=false;}
  else if(selected_==action_count){draft_.manual_family=platform::Family((unsigned(draft_.manual_family)+1)%4);}
  else if(selected_==action_count+1){draft_=platform::PortPreferences{};error_=conflict_=false;}
  else if(selected_==action_count+3){active_=false;visible_.store(false,std::memory_order_release);}
  else {
   // Draft duplicates are useful while swapping two bindings. Never publish
   // them: mapped Accept/Cancel or navigation could become the same press.
   uint32_t assigned=0;conflict_=false;
   for(const auto button:draft_.bindings){
    if(button==SDL_CONTROLLER_BUTTON_INVALID)continue;
    const auto bit=uint32_t(1)<<unsigned(button);
    if(assigned&bit){conflict_=true;break;}
    assigned|=bit;
   }
   if(conflict_){error_=false;break;}
   const auto draft=draft_;const auto port=port_;saving_=true;lock.unlock();bool success=false;
   try{success=save&&save(port,draft);}catch(...){success=false;}
   lock.lock();saving_=false;error_=!success;if(success){active_=false;visible_.store(false,std::memory_order_release);}
  }
  break;
 default:break;
 }
}
std::vector<EngineTextLine> GameControlsMenu::lines(platform::Family active_family)const{
 std::lock_guard lock(mutex_);if(!active_)return {};
 const auto gamepad_family=active_family==platform::Family::Keyboard||active_family==platform::Family::Automatic?last_gamepad_family_:active_family;
 const auto family=draft_.manual_family==platform::Family::Automatic?gamepad_family:draft_.manual_family;
 std::vector<EngineTextLine> lines{{24,20,"Remap Gamepad P"+std::to_string(port_+1)},{24,36,"Family "+family_name(draft_.manual_family)+(draft_.manual_family==platform::Family::Automatic?" "+family_name(family):"")}};
 const auto first=(selected_/page_rows)*page_rows;
 for(unsigned row=first;row<first+page_rows&&row<item_count;++row){
  std::string text=row==selected_?"SELECT ":"       ";
  if(row<action_count)text+=std::string(actions[row])+"   "+binding_name(draft_,row,family);
  else text+=row==action_count?"Change family":row==action_count+1?"Restore defaults":row==action_count+2?"Save":"Cancel";
  lines.push_back({24,int16_t(58+(row-first)*18),text});
 }
 lines.push_back({24,178,capture_?(released_?"Press one physical button":"Release all buttons"):saving_?"Saving":conflict_?"Resolve duplicate bindings":error_?"Save failed. Try again":keyboard_navigation_||active_family==platform::Family::Keyboard?"Z edit. X cancel":binding_name(navigation_,0,family)+" edit. "+binding_name(navigation_,1,family)+" cancel"});
 lines.push_back({24,196,capture_?"Escape cancels capture":"Page "+std::to_string(first/page_rows+1)+" of 3"});
 return lines;
}
GameControlsMenu& game_controls_menu(){static GameControlsMenu menu;return menu;}

namespace {
uint16_t read_half(std::span<uint8_t> ram,uint32_t a){uint16_t value;std::memcpy(&value,ram.data()+((a&0x7fffff)^2),2);return value;}
uint32_t read_word(std::span<uint8_t> ram,uint32_t a){uint32_t value;std::memcpy(&value,ram.data()+(a&0x7fffff),4);return value;}
void write_word(std::span<uint8_t> ram,uint32_t a,uint32_t value){std::memcpy(ram.data()+(a&0x7fffff),&value,4);}
void write_byte(std::span<uint8_t> ram,uint32_t a,uint8_t value){ram[(a&0x7fffff)^3]=value;}
void write_half(std::span<uint8_t> ram,uint32_t a,uint16_t value){std::memcpy(ram.data()+((a&0x7fffff)^2),&value,2);}
int encode_font(char c){
 if(c==' ')return 0;
 if(c>='0'&&c<='9')return c-'0'+1;
 if(c>='A'&&c<='Z')return c-'A'+0x0b;
 if(c>='a'&&c<='z')return c-'a'+0x25;
 return c=='.'?0x3f:-1;
}
}
bool draw_pal_engine_text(std::span<uint8_t> ram,const recomp_context& caller,std::span<const EngineTextLine> lines,recomp_func_t* draw,recomp_func_t* clear){
 if(ram.size()!=0x800000||!draw||lines.empty()||lines.size()>10)return false;
 // recomp_context contains an internal FPU alias. A shallow copy must not
 // retain an alias into the live guest context (FR0 and FR1 use different words).
 const auto fp= reinterpret_cast<uintptr_t>(caller.f_odd);
 const auto fp_begin=reinterpret_cast<uintptr_t>(&caller.f0);
 const auto fp_end=reinterpret_cast<uintptr_t>(&caller.f31)+sizeof(fpr);
 if(fp&&(fp<fp_begin||fp>fp_end-sizeof(uint32_t)||(fp-fp_begin)%alignof(uint32_t)))return false;
 const uint32_t sp=uint32_t(caller.r29);
 // Original main stack is 800A02D8..800A42D8. Preserve 0x400 bytes below
 // the live caller SP; our object/source frame is 0x100, original closure <0x100.
 if(sp<0x800A06D8||sp>0x800A42D8||(sp&7))return false;
 const auto base=read_word(ram,0x800A4AA4),head=read_word(ram,0x8009E0C8);
 if(base!=0x800D0320&&base!=0x800E0380)return false;
 const auto end=base+0x10008;
 if((head&7)||head<base+8||head>end)return false;
 // Only ordinary font-2 glyphs, constant palette 0, no encoded control tokens.
 // Original 49490 emits <=56 palette bytes once +56 texture bytes per glyph;
 // 49158 emits 24 rect bytes; setup <=32. Rounded bound includes full setup.
 size_t required=clear?256:0;
 for(const auto& line:lines){
  if(line.text.empty()||line.text.size()>40||line.x<0||line.y<0||line.x+line.text.size()*6>320||line.y+12>240)return false;
  for(char c:line.text)if(encode_font(c)<0)return false;
  required+=128*line.text.size()+256;
 }
 if(required>end-head)return false;
 const auto frame=read_word(ram,0x8009E02C);
 if(frame<0x80000000||frame>0x807FFFEC)return false;
 if(clear){
  // Original 019FC/01B2C clear is the proven 320x240 controller-screen path.
  // Its color-image command needs one original task framebuffer fixup slot.
  const auto fixup=read_word(ram,base+0x1005c);
  if((frame&3)||frame>0x807fffe8||ram[((frame+0x12)&0x7fffff)^3]||read_half(ram,frame+0x14)!=320||read_half(ram,frame+0x16)!=240||
     (fixup&3)||fixup<base+0x1000c||fixup>=base+0x1005c)return false;
 }
 std::array<uint8_t,0x400> saved{};const uint32_t low=sp-0x400;
 std::memcpy(saved.data(),ram.data()+(low&0x7fffff),saved.size());
 const uint32_t local=sp-0x100,object=local+0x20,source=local+0x60;
 if(clear){
  const std::array<uint32_t,3> colors{read_word(ram,frame+4),read_word(ram,frame+8),read_word(ram,frame+12)};
  write_half(ram,frame+6,0);write_half(ram,frame+8,0);write_half(ram,frame+10,0);write_half(ram,frame+12,1);
  auto context=caller;
  if(fp)context.f_odd=reinterpret_cast<uint32_t*>(reinterpret_cast<uint8_t*>(&context.f0)+(fp-fp_begin));
  context.r29=S32(local);clear(ram.data(),&context);
  write_word(ram,frame+4,colors[0]);write_word(ram,frame+8,colors[1]);write_word(ram,frame+12,colors[2]);
  // The fill changed cycle mode without consulting sprite material caches.
  // Force original 423FC to emit its complete font material on the next draw.
  write_half(ram,0x800BDB26,0xffff);
 }
 for(const auto& line:lines){
  for(unsigned i=0;i<0x24;++i)write_byte(ram,object+i,0);
  write_byte(ram,object+4,2);write_half(ram,object+0xe,uint16_t(line.x));write_half(ram,object+0x10,uint16_t(line.y));
  write_word(ram,object+0x14,source);write_half(ram,object+0x22,0xffff);
  for(unsigned i=0;i<line.text.size();++i)write_byte(ram,source+i,uint8_t(encode_font(line.text[i])));
  write_byte(ram,source+uint32_t(line.text.size()),0xff);write_byte(ram,source+uint32_t(line.text.size())+1,0x11);
  auto context=caller;
  if(fp)context.f_odd=reinterpret_cast<uint32_t*>(reinterpret_cast<uint8_t*>(&context.f0)+(fp-fp_begin));
  context.r29=S32(local);context.r4=S32(object);draw(ram.data(),&context);
 }
 // Match original dispatcher 80041AE4..80041B08 after a font object. Font caches
 // retain the emitted state; restoring old caches would desynchronize the RDP.
 write_word(ram,0x800BDB20,0x80041980);write_half(ram,0x800BDB24,0xffff);write_half(ram,0x800BDB26,0xffff);
 write_half(ram,0x800BDB28,0xffff);write_half(ram,0x800BDB2A,0);
 std::memcpy(ram.data()+(low&0x7fffff),saved.data(),saved.size());
 return true;
}
}
