// Original project work: djultra64.
#pragma once
#include "menu_sprite_runtime.hpp"
namespace RT64{struct State;struct GBI;}
namespace iss2000 {
class MenuSpriteBridge {
 struct Impl;std::unique_ptr<Impl>impl_;
public:
 MenuSpriteBridge(RT64::State*,RT64::GBI*,std::shared_ptr<const MenuSpriteTaskSnapshot>,bool allow);
 ~MenuSpriteBridge();
 MenuSpriteBridge(const MenuSpriteBridge&)=delete;
 MenuSpriteBridge&operator=(const MenuSpriteBridge&)=delete;
 bool installed()const{return bool(impl_);}
};
}
