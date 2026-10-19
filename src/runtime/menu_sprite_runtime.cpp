// Original project work: djultra64.
#include "menu_sprite_runtime.hpp"
#include "rom_image.hpp"
#include <array>
#include <deque>
#include <cstring>
#include <vector>
#include <map>
#include <mutex>
#include <optional>
#include <set>
#include <tuple>
#include <thread>
namespace iss2000 {namespace {
thread_local uint64_t semantic_owner{};thread_local unsigned semantic_ordinal{};
std::mutex mutex;
uint32_t word(std::span<const uint8_t>r,uint32_t a){uint32_t v;std::memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
uint8_t byte(std::span<const uint8_t>r,uint32_t a){return r[(a&0x7fffff)^3];}
std::optional<uint32_t> physical(uint64_t a){auto lo=uint32_t(a),hi=uint32_t(a>>32);if(hi&&!(hi==0xffffffffu&&(lo&0x80000000)))return {};if(lo<0x800000)return lo;if((lo>=0x80000000&&lo<0x80800000)||(lo>=0xa0000000&&lo<0xa0800000))return lo&0x7fffff;return {};}
using Fingerprint=std::tuple<uint32_t,uint32_t,uint32_t,uint32_t>;
std::optional<Fingerprint> fingerprint(const TransformTaskFingerprint&t){auto root=physical(t.data_ptr),code=physical(t.ucode),data=physical(t.ucode_data);if(!root||!code||!data)return {};return Fingerprint{*root,*code,*data,t.data_size};}
using Key=std::tuple<uint64_t,unsigned,uint32_t,uint32_t,unsigned,unsigned>;
std::optional<unsigned>text_index(uint32_t p){if(p<0x1650dc||(p-0x1650dc)%0x28||(p-0x1650dc)/0x28>=80)return {};return (p-0x1650dc)/0x28;}
struct PendingObservation {uint64_t owner;unsigned ordinal;uint32_t descriptor,segments;};
struct Runtime {
 bool configured{},active{},synchronized=true;std::optional<std::thread::id>producer;uint64_t frame{},epoch=1,serial{},observation{};uint32_t last_scene=~0u,base{},next_id=1;
 std::array<uint64_t,273>lifetimes{};std::map<uint64_t,unsigned>draws;
 std::map<uint64_t,PendingObservation>observations;std::map<Key,uint32_t>ids;
 std::unordered_map<uint32_t,uint32_t>commands;std::set<uint32_t>used;
 std::vector<MenuRadarOwnership>radar;std::array<uint64_t,2>radar_generations{};
 using RadarKey=std::tuple<uint32_t,uint64_t,uint64_t,uint32_t,uint64_t,uint32_t>;
 std::map<RadarKey,uint32_t>radar_ids;
 std::deque<std::pair<Fingerprint,std::shared_ptr<const MenuSpriteTaskSnapshot>>>queue;
 // BB8 may draw the next arena before the scheduler submits the previous
 // one. Ownership belongs to the observed task arena, not the latest frame.
 std::array<std::shared_ptr<const MenuSpriteTaskSnapshot>,2>retained;
 bool published{};
 std::array<uint64_t,80>text_lifetimes{};
 static std::optional<unsigned>arena(uint32_t b){if(b==0x800d0320)return 0;if(b==0x800e0380)return 1;return {};}
 void seal(){
  auto i=arena(base);
  if(i&&active&&!published&&!commands.empty()&&observations.empty())
   retained[*i]=std::make_shared<MenuSpriteTaskSnapshot>(MenuSpriteTaskSnapshot{frame,epoch,commands,radar});
 }
 void retire(uint32_t b){if(auto i=arena(b))retained[*i].reset();}
 bool acquire(uint32_t current){if(!commands.empty()&&base!=current){reject();return false;}base=current;retire(current);return true;}
 void cut(){++epoch;ids.clear();radar_ids.clear();active=false;commands.clear();observations.clear();used.clear();radar.clear();retained={};published=false;}
 void quarantine(){synchronized=false;queue.clear();cut();}
 void reject(){active=false;commands.clear();observations.clear();used.clear();radar.clear();}
 bool live_task(std::span<const uint8_t>r){
  const auto current=word(r,0x800a4aa4),head=word(r,0x8009e0c8);
  if((current!=0x800d0320&&current!=0x800e0380)||(head&7)||head<current+8||head>current+0x10008)return false;
  return acquire(current);
 }
 void capture(std::span<const uint8_t>r,uint32_t begin,uint32_t end,const PendingObservation&o){
  const auto current=word(r,0x800a4aa4);if(!arena(current)||!acquire(current))return reject();
  if(begin&7||end&7||begin<base+8||end<begin||end>base+0x10008)return reject();
  std::vector<uint32_t>pcs;
  for(auto p=begin;p<end;p+=8){auto a=word(r,p);if(a>>24==0xe4){if(p+24>end||word(r,p+8)!=0xe1000000||word(r,p+16)!=0xf1000000)return reject();pcs.push_back(p&0x7fffff);p+=16;}
   else if(a==0x64000002){if(p+24>end)return reject();pcs.push_back(p&0x7fffff);p+=16;}
   else if(a==0x64000005||a==0x64000006){if(p+16>end)return reject();p+=8;}
  }
  for(unsigned i=0;i<pcs.size();++i){Key key{o.owner,o.ordinal,o.descriptor,o.segments,i,unsigned(pcs.size())};auto [it,inserted]=ids.try_emplace(key,0);if(inserted){if(next_id==0)return reject();it->second=next_id++;}
   if(!used.insert(it->second).second||commands.contains(pcs[i]))return reject();
   commands.emplace(pcs[i],it->second);
  }
 }
}state;
}
MenuSpriteSemanticScope::MenuSpriteSemanticScope(uint64_t value):previous_(semantic_owner),previous_ordinal_(semantic_ordinal){semantic_owner=value;semantic_ordinal=0;}
MenuSpriteSemanticScope::~MenuSpriteSemanticScope(){semantic_owner=previous_;semantic_ordinal=previous_ordinal_;}
bool configure_menu_sprite_runtime(std::span<const uint8_t>rom){std::lock_guard lock(mutex);if(rom.size()!=0x1000000||rom_detail::sha256_hex(rom)!="6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf")return false;state.configured=true;return true;}
void begin_menu_sprite_frame(std::span<const uint8_t>r){std::lock_guard lock(mutex);state.seal();++state.frame;state.reject();state.published=false;state.draws.clear();
 for(auto&owner:state.retained)if(owner&&(owner->epoch!=state.epoch||owner->sequence+1!=state.frame))owner.reset();
 if(!state.configured||!state.synchronized||r.size()!=0x800000)return;
 auto scene=uint32_t(byte(r,0x8013b446))<<24|uint32_t(byte(r,0x8013b44c))<<16|uint32_t(byte(r,0x8013b42a))<<8|byte(r,0x8013b452);if(scene!=state.last_scene){state.cut();state.last_scene=scene;}
 const auto high=byte(r,0x8013b42a);if(word(r,0x8009e02c)!=0x8013b418||high>1||word(r,0x8013b42c)!=(high?0x02800220u:0x014000f0u))return;
 state.base=word(r,0x800a4aa4);if(state.base!=0&&state.base!=0x800d0320&&state.base!=0x800e0380)return;state.retire(state.base);state.active=true;
}
void observe_menu_sprite_initialization(uint64_t object){std::lock_guard lock(mutex);auto p=physical(object);if(!p||*p<0x13c47c||(*p-0x13c47c)%0x3c||(*p-0x13c47c)/0x3c>=273)return;state.lifetimes[(*p-0x13c47c)/0x3c]=++state.serial;}
void observe_menu_text_initialization(uint64_t object){std::lock_guard lock(mutex);auto p=physical(object);if(!p)return;if(auto i=text_index(*p))state.text_lifetimes[*i]=++state.serial;}
MenuSpriteObservation observe_menu_sprite_before(std::span<const uint8_t>r,uint64_t object){std::lock_guard lock(mutex);MenuSpriteObservation result;if(!state.active||r.size()!=0x800000||!state.live_task(r))return result;auto p=physical(object);if(!p||*p>0x800000-0x3c)return result;
 uint64_t owner;unsigned ordinal;bool pool=*p>=0x13c47c&&(*p-0x13c47c)%0x3c==0&&(*p-0x13c47c)/0x3c<273;
 if(pool){auto&life=state.lifetimes[(*p-0x13c47c)/0x3c];if(!life)life=++state.serial;
  owner=life;ordinal=state.draws[owner]++;}
 else{if(!semantic_owner)return result;owner=semantic_owner|0x8000000000000000ULL;ordinal=semantic_ordinal++;}
 auto descriptor=physical(word(r,*p+0x14)),segments=physical(word(r,*p+0x30));if(!descriptor||!segments||*descriptor>0x800000-12||*segments>0x800000-12)return result;
 const uint32_t d=pool?*descriptor:word(r,*descriptor)^word(r,*descriptor+4),s=pool?*segments:0;auto token=++state.observation;state.observations.emplace(token,PendingObservation{owner,ordinal,d,s});
 return {state.frame,token,word(r,0x8009e0c8),uint32_t(object),true};
}
MenuSpriteObservation observe_menu_text_before(std::span<const uint8_t>r,uint64_t object){
 std::lock_guard lock(mutex);if(!state.active||r.size()!=0x800000||!state.live_task(r))return {};auto p=physical(object);if(!p||*p>0x800000-0x24||(*p&3))return {};
 const bool sprite_pool=*p>=0x13c47c&&(*p-0x13c47c)%0x3c==0&&(*p-0x13c47c)/0x3c<273;
 const auto text_slot=text_index(*p);const bool pool=sprite_pool||text_slot.has_value();
 uint64_t owner;unsigned ordinal;
 if(pool){
  if(text_slot&&byte(r,*p+4)!=2)return {};
  auto&life=text_slot?state.text_lifetimes[*text_slot]:state.lifetimes[(*p-0x13c47c)/0x3c];
  if(!life)life=++state.serial;
  owner=life;ordinal=state.draws[owner]++;
 }else{if(!semantic_owner)return {};owner=semantic_owner|0x8000000000000000ULL;ordinal=semantic_ordinal++;}
 const auto mode=byte(r,*p+5),font=byte(r,*p+4);auto source=word(r,*p+0x14);
 // Mode0 is the original encoded-string pointer. Numeric modes use the same
 // original field as a scalar, not a pointer. Its value can cut that text run.
 if(mode==0&&!physical(source))return {};
 const uint32_t style=0xF04E0000u|uint32_t(font)<<8|mode;
 const auto token=++state.observation;state.observations.emplace(token,PendingObservation{owner,ordinal,style,pool?source:0});
 return {state.frame,token,word(r,0x8009e0c8),uint32_t(object),true};
}
void observe_menu_sprite_after(std::span<const uint8_t>r,MenuSpriteObservation o){std::lock_guard lock(mutex);if(!state.active||r.size()!=0x800000||!o.valid||o.frame!=state.frame)return;auto it=state.observations.find(o.identity);if(it==state.observations.end())return;auto data=it->second;state.observations.erase(it);state.capture(r,o.begin,word(r,0x8009e0c8),data);}
void observe_menu_canvas(std::span<const uint8_t>r,uint64_t owner,uint32_t begin,uint32_t end){std::lock_guard lock(mutex);if(!state.active||r.size()!=0x800000||!owner)return;const auto key=owner|0x8000000000000000ULL;state.capture(r,begin,end,{key,state.draws[key]++,0,0});}
void notify_menu_sprite_discontinuity(){std::lock_guard lock(mutex);state.cut();}
void retire_menu_radar_bank(uint32_t begin){std::lock_guard lock(mutex);if(begin==0x802b4408||begin==0x802b4d68)++state.radar_generations[(begin-0x802b4408)/0x960];}
void observe_menu_radar(std::span<const uint8_t> r,const PalRadarCapture& capture){
 std::lock_guard lock(mutex);if(!state.active||!capture.unchanged(r)||!state.live_task(r))return;
 auto bank=(capture.begin_address()-0x802b4408)/0x960;if(bank>1)return;
 for(const auto& c:capture.commands()){
  const auto&o=capture.owner();Runtime::RadarKey key{o.record,o.generation,o.scene_epoch,c.actor.record,c.actor.generation,c.role};
  auto[it,inserted]=state.radar_ids.try_emplace(key,0);if(inserted){if(!state.next_id)return state.reject();it->second=state.next_id++;}
  if(!state.used.insert(it->second).second||state.commands.contains(c.pc&0x7fffff))return state.reject();
  state.commands.emplace(c.pc&0x7fffff,it->second);
 }
 state.radar.push_back({capture,state.radar_generations[bank]});
}
namespace {
std::shared_ptr<const MenuSpriteTaskSnapshot> validate_radar(std::shared_ptr<const MenuSpriteTaskSnapshot> original,std::span<const uint8_t> ram,uint64_t root,bool submission){
 if(!original||original->radar.empty())return original;
 auto filtered=std::make_shared<MenuSpriteTaskSnapshot>(*original);
 for(const auto& item:original->radar){auto bank=(item.capture.begin_address()-0x802b4408)/0x960;
  if(bank>1||item.generation!=state.radar_generations[bank]||!item.capture.unchanged(ram)||(submission&&!item.capture.reachable(ram,root)))
   for(const auto& c:item.capture.commands())filtered->commands.erase(c.pc&0x7fffff);
 }
 return filtered;
}
}
void submit_menu_sprite_metadata(uint32_t type,const TransformTaskFingerprint&t,std::span<const uint8_t> ram){std::lock_guard lock(mutex);if(!state.configured||!state.synchronized||type!=1)return;const auto producer=std::this_thread::get_id();if(state.producer&&*state.producer!=producer){state.quarantine();return;}state.producer=producer;auto fp=fingerprint(t);if(!fp){state.quarantine();return;}const auto [root,code,data,size]=*fp;
 const bool microcode=(code==0x69ad0&&data==0x99ef0)||(code==0x6ae60&&data==0x9a310);
 std::shared_ptr<const MenuSpriteTaskSnapshot>snapshot;
 // A submission consumes that arena's ownership once, including unsupported
 // microcode. Exact FIFO fingerprints still bind the immutable queued copy.
 for(unsigned i=0;i<state.retained.size();++i){const auto b=i?0xe0380u:0xd0320u;if(root<b+8||root>=b+0x10008)continue;
  if(state.active&&!state.published&&state.base==(b|0x80000000u)){
   state.published=true;state.retained[i].reset();
   if(microcode&&state.observations.empty())snapshot=std::make_shared<MenuSpriteTaskSnapshot>(MenuSpriteTaskSnapshot{state.frame,state.epoch,state.commands,state.radar});
  }else if(auto owner=std::move(state.retained[i]);owner&&microcode&&owner->epoch==state.epoch&&owner->sequence+1==state.frame)snapshot=std::move(owner);
  break;
 }
 if(!snapshot)snapshot=std::make_shared<MenuSpriteTaskSnapshot>(MenuSpriteTaskSnapshot{state.frame,state.epoch,{},{}});
 snapshot=validate_radar(std::move(snapshot),ram,t.data_ptr,true);
 if(state.queue.size()>=64){state.quarantine();return;}state.queue.emplace_back(*fp,std::move(snapshot));
}
std::shared_ptr<const MenuSpriteTaskSnapshot> consume_menu_sprite_metadata(const TransformTaskFingerprint&t,std::span<const uint8_t> ram){std::lock_guard lock(mutex);auto fp=fingerprint(t);if(!state.configured||!state.synchronized)return {};if(!fp||state.queue.empty()||state.queue.front().first!=*fp){state.quarantine();return {};}auto result=state.queue.front().second;state.queue.pop_front();return validate_radar(std::move(result),ram,t.data_ptr,false);}
}
