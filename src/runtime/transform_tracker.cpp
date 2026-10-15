// Original project work: djultra64.
#include "transform_tracker.hpp"
#include <array>
#include <limits>
#include <deque>
#include <thread>
#include <mutex>
#include <stdexcept>
#include <unordered_set>
namespace iss2000 {
namespace {
std::optional<uint32_t> physical(uint64_t address,uint32_t bytes,bool allow_physical){
    uint32_t lo=uint32_t(address),hi=uint32_t(address>>32);
    if(hi!=0&&!(hi==0xFFFFFFFFu&&(lo&0x80000000u)))return {};
    if((lo&0xE0000000u)==0x80000000u||(lo&0xE0000000u)==0xA0000000u)lo&=0x1FFFFFFFu;
    else if(!allow_physical||hi||lo>=0x800000u)return {};
    if(lo>0x800000u||bytes>0x800000u-lo)return {};
    return lo;
}
uint32_t record_address(uint64_t address,const TransformGuestLayout& layout){
    auto p=physical(address,0x60,false);
    if(p){
        for(const auto& pool:layout.record_pools)
            if(*p>=pool.base && (*p-pool.base)/pool.stride<pool.count &&
               (*p-pool.base)%pool.stride==0)return *p|0x80000000u;
    }
    throw std::invalid_argument("Invalid original render-record address");
}
uint64_t advance(uint64_t& value){
    if(value==std::numeric_limits<uint64_t>::max())throw std::overflow_error("Transform sequence exhausted");
    return ++value;
}
std::optional<TransformTaskFingerprint> fingerprint(const TransformTaskFingerprint& value){
    auto root=physical(value.data_ptr,8,true),code=physical(value.ucode,1,true),data=physical(value.ucode_data,1,true);
    if(!root||!code||!data||(*root&7u)||value.data_size>0x800000u-*root)return {};
    return TransformTaskFingerprint{*root,*code,*data,value.data_size};
}
bool same(const TransformTaskFingerprint& a,const TransformTaskFingerprint& b){
    return a.data_ptr==b.data_ptr&&a.data_size==b.data_size&&a.ucode==b.ucode&&a.ucode_data==b.ucode_data;
}
uint32_t task_root(uint64_t address){
    auto p=physical(address,8,true);
    if(!p||(*p&7u))throw std::invalid_argument("Invalid graphics task root");
    return *p;
}
}
std::optional<TransformTag> TransformTaskSnapshot::lookup(uint64_t address)const{
    auto p=physical(address,64,true);if(!p)return {};
    auto it=matrices_.find(*p);return it==matrices_.end()?std::optional<TransformTag>{}:it->second;
}
struct TransformTracker::State {
    struct Record {TransformTag tag;};
    struct Frame {
        uint64_t token{};uint32_t begin{},end{};
        std::unordered_map<uint32_t,TransformTag> matrices;
        std::unordered_set<uint32_t> ambiguous;
    };
    std::mutex mutex;
    const TransformGuestLayout layout;
    size_t capacity;
    uint32_t next_id=1;
    uint64_t epoch=1,scene_token{},sequence{},frame_sequence{};
    bool scene_known{},synchronized=true;
    std::optional<std::thread::id> graphics_producer;
    std::array<uint32_t,2> camera_ids{};
    struct Submission{TransformTaskFingerprint fingerprint;TransformTaskToken token;};
    std::deque<Submission> submissions;
    std::array<Frame,2> frames;
    std::unordered_map<uint32_t,uint64_t> generations;
    std::unordered_map<uint32_t,Record> records;
    std::unordered_map<uint64_t,std::shared_ptr<const TransformTaskSnapshot>> pending;
    explicit State(const TransformGuestLayout& guest_layout,size_t count):layout(guest_layout),capacity(count){camera_ids={id(),id()};}
    uint32_t id(){
        if(next_id==0xFFFFFFFFu)throw std::overflow_error("Transform ID space exhausted");
        return next_id++;
    }
    void invalidate_scene(){
        if(next_id>=0xFFFFFFFEu)throw std::overflow_error("Transform camera IDs exhausted");
        advance(epoch);camera_ids={id(),id()};
        for(auto& f:frames)f=Frame{};
    }
    std::pair<unsigned,Frame*> frame(uint64_t token){
        for(unsigned n=0;n<2;++n)if(token&&frames[n].token==token)return {n,&frames[n]};
        throw std::invalid_argument("Stale or unknown transform frame token");
    }
};
TransformTracker::TransformTracker(const TransformGuestLayout& layout,size_t count):state_(std::make_unique<State>(layout,count)){
    validate_transform_guest_layout(layout);
    if(!count||count>4096)throw std::invalid_argument("Invalid pending transform task limit");
}
TransformTracker::~TransformTracker()=default;
void TransformTracker::begin_scene(uint64_t token){
    std::lock_guard lock(state_->mutex);
    if(!state_->scene_known){state_->scene_known=true;state_->scene_token=token;return;}
    if(state_->scene_token==token)return;
    state_->invalidate_scene();state_->scene_token=token;
    // IDs are renewed lazily for surviving allocations, without confusing a
    // scene transition with a guest free/reallocation generation.
}
void TransformTracker::invalidate_scene(){
    std::lock_guard lock(state_->mutex);state_->invalidate_scene();
}
TransformTag TransformTracker::allocate(uint64_t address){
    uint32_t record=record_address(address,state_->layout);std::lock_guard lock(state_->mutex);
    auto& generation=state_->generations[record];
    if(generation==std::numeric_limits<uint64_t>::max())throw std::overflow_error("Render-record generation exhausted");
    TransformTag tag{state_->id(),record,++generation,state_->epoch};
    state_->records[record]={tag};return tag;
}
bool TransformTracker::release(uint64_t address){
    uint32_t record=record_address(address,state_->layout);std::lock_guard lock(state_->mutex);
    return state_->records.erase(record)!=0;
}
uint64_t TransformTracker::begin_frame(unsigned bank,uint64_t begin,uint64_t end){
    auto b=physical(begin,0,true),e=physical(end,0,true);
    uint32_t expected=state_->layout.arena_base+bank*state_->layout.arena_size;
    if(bank>=2||!b||!e||*b!=expected||*e!=expected+state_->layout.arena_size)
        throw std::invalid_argument("Matrix arena disagrees with original252B0 bounds");
    std::lock_guard lock(state_->mutex);auto token=advance(state_->frame_sequence);
    auto& f=state_->frames[bank];f=State::Frame{};f.token=token;f.begin=*b;f.end=*e;return token;
}
bool TransformTracker::capture_matrix(const TransformMatrixCapture& capture){
    uint32_t record;
    try{record=record_address(capture.record,state_->layout);}catch(const std::invalid_argument&){return false;}
    auto before=physical(capture.matrix_before,0,true),after=physical(capture.matrix_after,64,true);
    auto cb=physical(capture.cursor_before,0,true),ce=physical(capture.cursor_after,0,true);
    if(!before||!after||!cb||!ce||!(capture.flags&0x80000000u)||
       (capture.flags_after&0x80400000u)!=0x80400000u)return false;
    if(capture.builder==TransformMatrixBuilder::Conditional252F8){
        // flags800 diverts to25204 without allocating this record's matrix.
        if(capture.flags&0x800u)return false;
    }else if(capture.builder!=TransformMatrixBuilder::Unconditional25710)return false;
    std::lock_guard lock(state_->mutex);auto [bank,frame]=state_->frame(capture.frame);(void)bank;
    if(*after<frame->begin||*after>frame->end-64||(*after-frame->begin)%64||
       *cb!=*after||*ce<*cb+64||*ce>frame->end||(*ce-frame->begin)%64)return false;
    auto it=state_->records.find(record);if(it==state_->records.end())return false;
    auto& owner=it->second;
    if(owner.tag.scene_epoch!=state_->epoch){owner.tag.id=state_->id();owner.tag.scene_epoch=state_->epoch;}
    if(frame->ambiguous.contains(*after))return true;
    auto found=frame->matrices.find(*after);
    if(found!=frame->matrices.end()&&found->second.id!=owner.tag.id){
        frame->matrices.erase(found);frame->ambiguous.insert(*after);
    }else frame->matrices[*after]=owner.tag;
    return true;
}
TransformTaskToken TransformTracker::publish_locked(std::optional<uint64_t> frame_token,uint32_t root){
    if(state_->pending.size()>=state_->capacity)throw std::overflow_error("Pending transform task snapshots exhausted");
    auto snapshot=std::make_shared<TransformTaskSnapshot>();
    snapshot->layout=state_->layout;
    snapshot->scene_epoch=state_->epoch;snapshot->scene_token=state_->scene_token;snapshot->root=root;snapshot->bank=2;
    if(frame_token){
        auto [bank,frame]=state_->frame(*frame_token);snapshot->bank=bank;
        snapshot->matrices_=frame->matrices;snapshot->camera_ids=state_->camera_ids;
    }
    snapshot->sequence=advance(state_->sequence);
    state_->pending.emplace(snapshot->sequence,snapshot);return {snapshot->sequence,root};
}
TransformTaskToken TransformTracker::publish_task(uint64_t frame_token,uint64_t data_ptr){
    uint32_t root=task_root(data_ptr);std::lock_guard lock(state_->mutex);
    return publish_locked(frame_token,root);
}
std::optional<TransformTaskToken> TransformTracker::submit_task(uint32_t type,const TransformTaskFingerprint& submitted,std::optional<uint64_t> frame){
    if(type!=1)return {}; // Original M_GFXTASK=1; audio/other RSP work has no graphics event.
    auto normalized=fingerprint(submitted);
    if(!normalized)throw std::invalid_argument("Invalid graphics submission fingerprint");
    std::lock_guard lock(state_->mutex);if(!state_->synchronized)return {};
    const auto producer=std::this_thread::get_id();
    if(state_->graphics_producer&&*state_->graphics_producer!=producer){
        // The pinned queue uses implicit per-thread producer streams. A mutex
        // cannot impose cross-producer FIFO order on that upstream queue.
        state_->synchronized=false;state_->submissions.clear();state_->pending.clear();return {};
    }
    state_->graphics_producer=producer;
    auto token=publish_locked(frame,uint32_t(normalized->data_ptr));
    try{state_->submissions.push_back({*normalized,token});}
    catch(...){state_->pending.erase(token.sequence);throw;}
    return token;
}
std::shared_ptr<const TransformTaskSnapshot> TransformTracker::consume_submission(const TransformTaskFingerprint& submitted){
    auto normalized=fingerprint(submitted);std::lock_guard lock(state_->mutex);
    if(!state_->synchronized)return {};
    if(!normalized||state_->submissions.empty()||!same(*normalized,state_->submissions.front().fingerprint)){
        state_->synchronized=false;state_->submissions.clear();state_->pending.clear();return {};
    }
    auto token=state_->submissions.front().token;
    auto found=state_->pending.find(token.sequence);
    if(found==state_->pending.end()){
        state_->synchronized=false;state_->submissions.clear();state_->pending.clear();return {};
    }
    auto snapshot=found->second;state_->pending.erase(found);state_->submissions.pop_front();return snapshot;
}
bool TransformTracker::submissions_synchronized()const{
    std::lock_guard lock(state_->mutex);return state_->synchronized;
}
void TransformTracker::reset_submissions(){
    std::lock_guard lock(state_->mutex);state_->submissions.clear();state_->pending.clear();state_->synchronized=true;state_->graphics_producer.reset();
}
std::shared_ptr<const TransformTaskSnapshot> TransformTracker::consume_task(uint64_t sequence,uint64_t data_ptr){
    uint32_t root=task_root(data_ptr);std::lock_guard lock(state_->mutex);
    auto it=state_->pending.find(sequence);
    if(it==state_->pending.end()||it->second->root!=root)throw std::invalid_argument("Graphics task snapshot identity mismatch");
    auto snapshot=it->second;state_->pending.erase(it);return snapshot;
}
}
