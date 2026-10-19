// Original project work: djultra64.
#include "menu_sprite_render.hpp"
#include <cmath>
#include <map>
namespace iss2000 {
std::vector<MenuRectMatch> match_menu_rectangles(const MenuRectFrame&current,const MenuRectFrame&previous,float weight){
 std::vector<MenuRectMatch>out;if(!std::isfinite(weight)||weight<0||weight>1||current.epoch!=previous.epoch||current.sequence!=previous.sequence+1)return out;
 std::map<uint32_t,const MenuRectSample*>old,now;
 for(const auto&r:previous.rectangles){auto [it,ok]=old.emplace(r.uid,&r);if(!ok)it->second=nullptr;}
 for(const auto&r:current.rectangles){auto [it,ok]=now.emplace(r.uid,&r);if(!ok)it->second=nullptr;}
 for(const auto&[id,c]:now){auto it=old.find(id);if(!id||!c||it==old.end()||!it->second||c->compatibility!=it->second->compatibility)continue;const auto&p=*it->second;
  MenuRectMatch m;m.call_index=c->call_index;m.previous=p.rect;m.moved=c->rect!=p.rect;m.faded=c->prim!=p.prim||c->env!=p.env;for(unsigned n=0;n<4;++n){m.prim[n]=weight==1?c->prim[n]:weight==0?p.prim[n]:p.prim[n]+(c->prim[n]-p.prim[n])*weight;m.env[n]=weight==1?c->env[n]:weight==0?p.env[n]:p.env[n]+(c->env[n]-p.env[n])*weight;}out.push_back(m);
 }return out;
}
}
