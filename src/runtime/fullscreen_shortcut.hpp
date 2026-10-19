// Original project work: djultra64.
#pragma once
#include <SDL.h>
#include <array>
namespace iss2000 {
// Consume each Alt+Enter chord through Enter release, including repeats after
// Alt is released. Filter a local keyboard snapshot, never SDL's own state.
class FullscreenShortcut {
 std::array<bool,2> consumed_{};
 static constexpr std::array<SDL_Scancode,2> enter_{SDL_SCANCODE_RETURN,SDL_SCANCODE_KP_ENTER};
public:
 struct Result {bool consumed=false,toggle=false;};
 Result handle(const SDL_Event& event){
  if(event.type!=SDL_KEYDOWN&&event.type!=SDL_KEYUP)return {};
  for(unsigned i=0;i<enter_.size();++i){
   if(event.key.keysym.scancode!=enter_[i])continue;
   const bool alt=(event.key.keysym.mod&KMOD_ALT)!=0;
   if(!alt&&!consumed_[i])return {};
   const bool toggle=event.type==SDL_KEYDOWN&&!event.key.repeat&&!consumed_[i];
   consumed_[i]=event.type==SDL_KEYDOWN;
   return {true,toggle};
  }
  return {};
 }
 void filter(Uint8* keyboard,int count){
  for(unsigned i=0;i<enter_.size();++i){
   const auto key=enter_[i];if(int(key)>=count)continue;
   if(!keyboard[key])consumed_[i]=false;
   if(consumed_[i])keyboard[key]=0;
  }
 }
};
}
