// Original project work: djultra64.
#include "pal_shadow_vertices.hpp"
#include "pal_projected_shadow.hpp"
#include "pal_game_layout.hpp"
#include "graphics_task_bank.hpp"
#include <array>
#include <atomic>
#include <deque>
#include <cstring>
#include <limits>
#include <mutex>
#include <thread>
#include <unordered_map>
namespace iss2000 {
namespace {
uint32_t word(std::span<const uint8_t> r,uint32_t a){uint32_t v;std::memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
uint8_t byte(std::span<const uint8_t> r,uint32_t a){return r[(a&0x7fffff)^3];}
std::optional<uint32_t> node(uint64_t a){auto lo=uint32_t(a);if(a!=lo&&a!=uint64_t(int64_t(int32_t(lo))))return {};
 if(lo<0x80145624 || lo>=0x80145624+285*0x98 || (lo-0x80145624)%0x98)return {};
 return lo;}
bool span(uint32_t a,uint32_t n){return !(a&7) && a>=0x801B0000 && a<=0x80700000-n;}
uint16_t replay_cursor(std::span<const uint8_t> r){uint16_t v;std::memcpy(&v,r.data()+(0x12ddf0^2),2);return v;}
bool scene(std::span<const uint8_t> r){return r.size()==0x800000&&word(r,0x8009E02C)==0x8013B418&&
 byte(r,0x8013B446)==6&&byte(r,0x8013B44C)==4&&byte(r,0x8013B452)==0&&(byte(r,0x8012DE27)<=1||(byte(r,0x8012DE27)==3&&replay_cursor(r)<68));}
bool fingerprint(const TransformTaskFingerprint&a,const TransformTaskFingerprint&b){return a.data_ptr==b.data_ptr&&a.ucode==b.ucode&&a.ucode_data==b.ucode_data&&a.data_size==b.data_size;}
bool known_code(const TransformTaskFingerprint&t){
 const auto canonical=[](uint64_t a){return a<0x800000 || (a>=0x80000000&&a<0x80800000) || (a>=0xA0000000&&a<0xA0800000);};
 if(!canonical(t.ucode)||!canonical(t.ucode_data)||!canonical(t.data_ptr)||!t.data_size||t.data_size%8||t.data_size>0x10000)return false;
 const auto l=verified_pal_transform_layout();for(auto c:l.microcodes)if((t.ucode&0x1fffffff)==c.code&&(t.ucode_data&0x1fffffff)==c.data)return true;return false;}
std::atomic<uint32_t> next_shadow_id{PalShadowIdFirst};
std::mutex configured_mutex;std::shared_ptr<PalShadowVertices> configured;
std::shared_ptr<PalShadowVertices> current(){std::lock_guard lock(configured_mutex);return configured;}
}
bool verified_pal_near_shadow_list(std::span<const uint8_t> r)noexcept {
 if(r.size()!=0x800000)return false;
 constexpr std::array<uint32_t,48> commands={0xE200001Cu,0x005049F8u,0xD7000000u,0xFFFFFFFFu,0xE2001D00u,0x00000004u,0xEE000000u,0x7FFF7FFFu,0xDA380003u,0x801A3F00u,0xD9FFFBFFu,0x00000000u,0x0101C038u,0x05000000u,0x06000204u,0x00040602u,0x06080A0Cu,0x000C0E0Au,0x06101214u,0x00141612u,0x06181A1Cu,0x001C1E1Au,0x06202224u,0x00242622u,0x06282A2Cu,0x002C2E2Au,0x06303234u,0x00343632u,0x06040608u,0x00080A06u,0x06141618u,0x00181A16u,0x062C2E30u,0x0030322Eu,0x0100C018u,0x050001C0u,0x06000204u,0x00040602u,0x06080A0Cu,0x000C0E0Au,0x06101214u,0x00141612u,0x06040608u,0x00080A06u,0xE2001D00u,0x00000000u,0xDF000000u,0x00000000u};
 for(unsigned i=0;i<commands.size();++i)if(word(r,0x80083AD0+i*4)!=commands[i])return false;
 return true;
}
std::optional<uint32_t> PalShadowTaskSnapshot::lookup(uint32_t p,unsigned count,unsigned destination)const noexcept {
 if(destination)return {};
 p&=0x1fffffff;
 for(const auto&t:tags){if(t.epoch!=epoch)continue;
  if(t.ball){if(p==(t.vertices&0x1fffffff)&&count==16)return t.first_id;continue;}
  if(t.projected){for(unsigned n=0;n<4;++n)if(p==(t.vertices&0x1fffffff)+n*24*16&&count==(n<3?24u:8u))return t.first_id+n;continue;}
  if(p==(t.vertices&0x1fffffff)&&count==28)return t.first_id;
  if(p==(t.vertices&0x1fffffff)+28*16&&count==12)return t.second_id;}
 return {};
}
struct PalShadowVertices::State {
 struct Owner {uint64_t generation{},epoch{};uint32_t first{},second{},parent{};};
 struct Frame {uint64_t token{};std::vector<PalShadowVertexTag> tags;};
 struct Pending {TransformTaskFingerprint task;std::shared_ptr<const PalShadowTaskSnapshot> snapshot;};
 std::mutex mutex;std::unordered_map<uint32_t,Owner> owners;std::unordered_map<uint32_t,uint64_t> generations;
 std::array<Frame,2> frames;std::deque<Pending> queue;
 uint64_t epoch=1,frame_sequence{},submission_sequence{};
 std::optional<uint16_t> cursor;
 std::optional<std::array<uint8_t,5>> signature;std::optional<std::thread::id> producer;bool synchronized=true;
 bool ids(Owner&o){auto next=next_shadow_id.load();
  do{if(next>PalShadowIdLast-3)return false;}while(!next_shadow_id.compare_exchange_weak(next,next+4));
  o.first=next;o.second=next+1;o.epoch=epoch;return true;}
 void invalidate(){if(epoch==std::numeric_limits<uint64_t>::max()){synchronized=false;queue.clear();return;}++epoch;frames={};}
};
PalShadowVertices::PalShadowVertices():state(std::make_unique<State>()){}
PalShadowVertices::~PalShadowVertices()=default;
void PalShadowVertices::allocation(uint64_t a){const auto n=node(a);if(!n)return;std::lock_guard lock(state->mutex);
 state->owners.erase(*n);for(auto&f:state->frames)std::erase_if(f.tags,[&](const auto&t){return t.object==*n;});
 auto&g=state->generations[*n];if(g==std::numeric_limits<uint64_t>::max())return;
 State::Owner owner{.generation=++g};if(!state->ids(owner))return;state->owners[*n]=owner;
 for(auto&f:state->frames)std::erase_if(f.tags,[&](const auto&t){return t.object==*n;});
}
void PalShadowVertices::release(uint64_t a){const auto n=node(a);if(!n)return;std::lock_guard lock(state->mutex);state->owners.erase(*n);
 for(auto&f:state->frames)std::erase_if(f.tags,[&](const auto&t){return t.object==*n;});}
void PalShadowVertices::invalidate(){std::lock_guard lock(state->mutex);state->invalidate();}
void PalShadowVertices::begin_frame(std::span<const uint8_t> r){std::lock_guard lock(state->mutex);
 if(!scene(r)){if(state->signature)state->invalidate();state->signature.reset();state->cursor.reset();state->frames={};return;}
 const std::array<uint8_t,5> sig={byte(r,0x8013B446),byte(r,0x8013B44C),byte(r,0x8013B452),byte(r,0x8012DE27),byte(r,0x800C81A4)};
 if(state->signature&&*state->signature!=sig)state->invalidate();
 // The original replay uses68 ring entries; only the same/next cursor is
 // continuous. A seek receives fresh interpolation identities.
 if(byte(r,0x8012DE27)==3){
  const auto cursor=replay_cursor(r);
  if(state->cursor&&cursor!=*state->cursor&&cursor!=(*state->cursor+1)%68)state->invalidate();
  state->cursor=cursor;
 }else state->cursor.reset();
 state->signature=sig;
 const auto bank=word(r,0x8009DED0);if(bank>1){state->frames={};return;}
 const auto first=0x800A7848u+bank*0x5100;
 const auto extended=0x80000000u+PalFieldMatrixBase+bank*PalFieldMatrixBankSize;
 if((word(r,0x800B1A48)!=first || word(r,0x800B1A4C)!=first+0x5100) &&
    (word(r,0x800B1A48)!=extended || word(r,0x800B1A4C)!=extended+PalFieldMatrixBankSize)){state->frames[bank]={};return;}
 if(state->frame_sequence==std::numeric_limits<uint64_t>::max()){state->frames={};return;}
 state->frames[bank]={.token=++state->frame_sequence,.tags={}};
}
bool PalShadowVertices::capture(std::span<const uint8_t> r,uint64_t a){const auto n=node(a);if(!n||!scene(r))return false;
 const auto bank=word(r,0x8009DED0);if(bank>1)return false;
 const auto object=*n;const auto projected=pal_projected_shadow(r,object,bank);
 const bool ball=projected&&projected->ball;
 const auto parent=ball?std::optional<uint32_t>{object}:node(word(r,object+0x50));
 uint32_t vertices=projected?projected->vertices:word(r,object+0x5c);
 if(!ball){
  const auto flags=word(r,object+0x28),metadata=word(r,object+0x80);
  if((flags&0x80004000u)!=0x80004000u || word(r,object+0x7C)!=0x80037498 ||
     !parent || word(r,*parent+0x4C)!=object || metadata<0x800A5250 || metadata>=0x800A5250+140*0x40 || (metadata-0x800A5250)%0x40 ||
     (!projected&&word(r,object+0x24)!=0x80083B90 && word(r,object+0x24)!=0x80083BC8))return false;
  const auto base=word(r,metadata);
  if(!span(base,1280)||vertices!=(projected?projected->vertices:base+bank*640))return false;
 }
 if(!verified_pal_near_shadow_list(r))return false;
 std::lock_guard lock(state->mutex);auto&frame=state->frames[bank];if(!frame.token)return false;
 auto owner=state->owners.find(object);if(owner==state->owners.end())return false;
 if((owner->second.epoch!=state->epoch || (owner->second.parent && owner->second.parent!=*parent))&&!state->ids(owner->second))return false;
 owner->second.parent=*parent;
 auto&tag=owner->second;
 for(const auto&t:frame.tags)if(t.object!=object&&vertices<t.vertices+(t.projected?1280u:640u)&&t.vertices<vertices+(projected?1280u:640u)){frame.token=0;frame.tags.clear();return false;}
 std::erase_if(frame.tags,[&](const auto&t){return t.object==object;});
 if(frame.tags.size()>=PalProjectedShadowCount){frame.token=0;frame.tags.clear();return false;}
 frame.tags.push_back({object,vertices,tag.first,tag.second,tag.generation,state->epoch,bool(projected),ball});return true;
}
void PalShadowVertices::submit(std::span<const uint8_t> r,uint32_t type,const TransformTaskFingerprint&t){
 if(type!=1)return;
 std::lock_guard lock(state->mutex);if(!state->synchronized)return;
 auto thread=std::this_thread::get_id();if(state->producer&&*state->producer!=thread){state->synchronized=false;state->queue.clear();return;}state->producer=thread;
 if(state->queue.size()>=64||state->submission_sequence==std::numeric_limits<uint64_t>::max()){state->synchronized=false;state->queue.clear();return;}
 std::shared_ptr<PalShadowTaskSnapshot> snapshot;
 if(scene(r)&&known_code(t))if(auto bank=graphics_task_bank(r,t.data_ptr,verified_pal_transform_layout().perspective_matrices)){
  const auto&frame=state->frames[*bank];if(frame.token){snapshot=std::make_shared<PalShadowTaskSnapshot>();
   snapshot->sequence=++state->submission_sequence;snapshot->epoch=state->epoch;snapshot->root=uint32_t(t.data_ptr)&0x1fffffff;snapshot->bank=*bank;snapshot->scene=0x604;snapshot->tags=frame.tags;}}
 state->queue.push_back({t,std::move(snapshot)});
}
std::shared_ptr<const PalShadowTaskSnapshot> PalShadowVertices::consume(const TransformTaskFingerprint&t){std::lock_guard lock(state->mutex);
 if(!state->synchronized||state->queue.empty())return {};
 auto p=std::move(state->queue.front());state->queue.pop_front();
 if(!fingerprint(p.task,t)){state->synchronized=false;state->queue.clear();return {};}return std::move(p.snapshot);}
void configure_pal_shadow_vertices(bool enabled){std::lock_guard lock(configured_mutex);configured=enabled?std::make_shared<PalShadowVertices>():nullptr;}
void observe_pal_shadow_allocation(uint64_t r){if(auto c=current())c->allocation(r);}
void observe_pal_shadow_release(uint64_t r){if(auto c=current())c->release(r);}
void observe_pal_shadow_frame(std::span<const uint8_t> r){if(auto c=current())c->begin_frame(r);}
void invalidate_pal_shadow_vertices(){if(auto c=current())c->invalidate();}
void observe_pal_shadow_vertices(std::span<const uint8_t> r,uint64_t object){if(auto c=current())c->capture(r,object);}
void submit_pal_shadow_metadata(std::span<const uint8_t>r,uint32_t type,const TransformTaskFingerprint&t){if(auto c=current())c->submit(r,type,t);}
std::shared_ptr<const PalShadowTaskSnapshot> consume_pal_shadow_metadata(const TransformTaskFingerprint&t){if(auto c=current())return c->consume(t);return {};}
}
