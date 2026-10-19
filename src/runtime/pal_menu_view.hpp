// Original project work: djultra64.
#pragma once
#include "runtime/game_controls_menu.hpp"
#include <array>
namespace iss2000 {
// Adapt the existing menu's immutable text snapshot to native row/value art.
// Navigation remains in the existing state machines; SELECT is never rendered.
inline PalOptionsSkinView pal_menu_view(std::span<const EngineTextLine> lines,bool controls){
 PalOptionsSkinView view;
 if(lines.empty())return view;
 view.title=controls?"Button mapping":lines.front().text;
 if(controls&&lines.size()>1)view.help.push_back(lines[1].text);
 for(const auto& line:lines){
  if(line.y>=58&&line.y<=150){
   std::string text=line.text;
   const bool selected=text.starts_with("SELECT ");
   if(!selected&&!text.starts_with("       "))return {};
   text.erase(0,7);PalOptionsSkinRow row{text,{}};
   if(controls){
    const auto separator=text.find("   ");
    if(separator!=std::string::npos){row.label=text.substr(0,separator);row.value=text.substr(separator+3);}
    if(row.label=="N64 A")row.label="Button A";
    if(row.label=="N64 B")row.label="Button B";
    if(row.label=="Change family"){row.label="Controller type";if(lines.size()>1)row.value=lines[1].text.substr(7);}
   }else{
    constexpr std::array<std::string_view,7> prefixes{"Aspect ","Resolution ","Framerate limit ","Screen ","Player ","Vibration ","Filtering "};
    for(auto prefix:prefixes)if(text.starts_with(prefix)){row.label=std::string(prefix.substr(0,prefix.size()-1));row.value=text.substr(prefix.size());break;}
   }
   if(selected)view.selected=unsigned(view.rows.size());
   view.rows.push_back(std::move(row));
  }else if(line.y>=166)view.help.push_back(line.text);
 }
 return view;
}
}
