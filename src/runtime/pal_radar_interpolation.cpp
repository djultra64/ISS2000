// Original project work: djultra64.
#include "pal_radar_interpolation.hpp"
#include "graphics_task_bank.hpp"
#include "pal_game_layout.hpp"
#include <cstring>
#include <algorithm>
namespace iss2000 {namespace {
uint32_t word(std::span<const uint8_t> r,uint32_t p){uint32_t v;std::memcpy(&v,r.data()+(p&0x7fffff),4);return v;}
bool live(TransformTag t){return (t.record<0x800000||(t.record>=0x80000000&&t.record<0x80800000))&&t.id&&t.generation&&t.scene_epoch&&(t.record&0x7fffff)>=0x145624&&((t.record&0x7fffff)-0x145624)%0x98==0&&((t.record&0x7fffff)-0x145624)/0x98<285;}
}
bool PalRadarCapture::begin(std::span<const uint8_t> r,TransformTag owner,unsigned bank,uint32_t begin){
 active_=sealed_=false;commands_.clear();bytes_.clear();
 if(r.size()!=0x800000||!live(owner)||bank>1||begin!=0x802b4408+bank*0x960)return false;
 owner_=owner;begin_=begin;active_=true;return true;
}
bool PalRadarCapture::emit(std::span<const uint8_t> r,uint32_t begin,uint32_t end,TransformTag actor,uint32_t role){
 if(!active_||sealed_)return false;
 auto reject=[&]{active_=false;commands_.clear();return false;};
 if(r.size()!=0x800000||!live(actor)||actor.scene_epoch!=owner_.scene_epoch||!role||begin%8||begin<begin_||begin>begin_+0x960-24||end!=begin+24||word(r,begin)>>24!=0xe4||word(r,begin+8)!=0xe1000000||word(r,begin+16)!=0xf1000000)return reject();
 for(const auto& c:commands_)if(c.pc==begin||(c.actor.record==actor.record&&c.actor.generation==actor.generation&&c.role==role))return reject();
 commands_.push_back({begin,actor,role});return true;
}
bool PalRadarCapture::finish(std::span<const uint8_t> r,uint32_t end){
 if(!active_||sealed_)return false;
 active_=false;
 if(r.size()!=0x800000||end%8||end<begin_+8||end>begin_+0x960||word(r,end-8)!=0xdf000000||word(r,end-4))return false;
 for(const auto& c:commands_)if(c.pc+24>end-8)return false;
 // Require every actual rectangle to have an explicit actor/role observation.
 unsigned count=0;
 for(uint32_t p=begin_;p<end-8;p+=8){auto op=word(r,p)>>24;
  if(op==0xe4){if(p+24>end-8||word(r,p+8)!=0xe1000000||word(r,p+16)!=0xf1000000)return false;
   if(std::none_of(commands_.begin(),commands_.end(),[&](const auto&c){return c.pc==p;}))return false;
   ++count;p+=16;
  }else if(op==0xde){if(p!=begin_||word(r,p)!=0xde000000||word(r,p+4)!=0x802b2890)return false;
  }else if(op==0xdf||op==0xdd||op==0x03||op==0x04)return false;
 }
 if(count!=commands_.size())return false;
 bytes_.assign(r.begin()+(begin_&0x7fffff),r.begin()+(end&0x7fffff));sealed_=true;return true;
}
bool PalRadarCapture::unchanged(std::span<const uint8_t> r)const{
 return sealed_&&r.size()==0x800000&&std::equal(bytes_.begin(),bytes_.end(),r.begin()+(begin_&0x7fffff));
}
bool PalRadarCapture::reachable(std::span<const uint8_t> r,uint64_t root)const{
 return unchanged(r)&&graphics_task_reaches_list(r,root,begin_,verified_pal_transform_layout());
}
}
