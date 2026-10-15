// Original project work: djultra64.
#include "transform_runtime.hpp"
#include "graphics_task_bank.hpp"
#include <array>
#include <cstring>
namespace iss2000 {
namespace {
std::mutex submission_mutex,configuration_mutex;
std::shared_ptr<TransformRuntime> configured_runtime;
std::shared_ptr<TransformRuntime> runtime(){
    std::lock_guard lock(configuration_mutex);return configured_runtime;
}
std::optional<uint32_t> address(uint64_t value,size_t bytes){
    uint32_t low=uint32_t(value);
    if(value!=low && value!=(uint64_t(int64_t(int32_t(low)))))return {};
    uint32_t offset;
    if(low<0x800000)offset=low;
    else if(low>=0x80000000 && low<0x80800000)offset=low-0x80000000;
    else if(low>=0xA0000000 && low<0xA0800000)offset=low-0xA0000000;
    else return {};
    if(offset%4 || bytes>0x800000-offset)return {};
    return offset;
}
uint32_t word(std::span<const uint8_t> ram,size_t offset){uint32_t result;std::memcpy(&result,ram.data()+offset,4);return result;}
uint16_t halfword(std::span<const uint8_t> ram,size_t offset){uint16_t result;std::memcpy(&result,ram.data()+(offset^2),2);return result;}
}
struct TransformRuntime::State {
    const TransformGuestLayout layout;
    TransformTracker tracker;
    std::mutex frame_mutex;
    std::array<uint64_t,2> frames{};
    std::optional<uint64_t> scene;
    std::optional<std::array<uint8_t,4>> epoch_values;
    std::optional<uint8_t> replay_phase;
    std::optional<uint16_t> replay_cursor;
    explicit State(const TransformGuestLayout& guest_layout):layout(guest_layout),tracker(layout){}
    bool known_record(uint64_t value)const{
        const auto offset=address(value,0x60);if(!offset)return false;
        for(const auto& pool:layout.record_pools)
            if(*offset>=pool.base && (*offset-pool.base)/pool.stride<pool.count &&
               (*offset-pool.base)%pool.stride==0)return true;
        return false;
    }
};
TransformRuntime::TransformRuntime(const TransformGuestLayout& layout):state_(std::make_unique<State>(layout)){}
TransformRuntime::~TransformRuntime()=default;
void TransformRuntime::observe_allocation(uint64_t record){
    if(state_->known_record(record))state_->tracker.allocate(0x80000000ull+*address(record,0x60));
}
void TransformRuntime::observe_release(uint64_t record){
    if(state_->known_record(record))state_->tracker.release(0x80000000ull+*address(record,0x60));
}
void TransformRuntime::observe_frame(std::span<const uint8_t> ram){
    if(ram.size()!=0x800000)return;
    std::lock_guard lock(state_->frame_mutex);
    const auto& layout=state_->layout;
    const unsigned bank=word(ram,layout.bank_selector);if(bank>1){state_->frames={};return;}
    const uint64_t token=(uint64_t(ram[layout.scene_bytes[0]^3])<<8)|ram[layout.scene_bytes[1]^3];
    bool discontinuity=false,invalid_replay=false;
    std::array<uint8_t,4> epoch_values{};
    for(unsigned n=0;n<layout.epoch_byte_count;++n){
        epoch_values[n]=ram[layout.epoch_bytes[n]^3];
        if(state_->epoch_values && (*state_->epoch_values)[n]!=epoch_values[n])discontinuity=true;
    }
    state_->epoch_values=epoch_values;
    if(layout.replay_continuity){
        const auto& replay=*layout.replay_continuity;
        const uint8_t phase=ram[replay.phase_byte^3];
        const uint16_t cursor=halfword(ram,replay.cursor_halfword);
        if(phase==replay.playback_phase){
            invalid_replay=cursor>=replay.capacity;
            if(invalid_replay)discontinuity=true;
            else if(state_->replay_phase==phase && state_->replay_cursor &&
                    cursor!=*state_->replay_cursor && cursor!=(*state_->replay_cursor+1)%replay.capacity)
                discontinuity=true;
        }
        state_->replay_phase=phase;
        state_->replay_cursor=invalid_replay?std::optional<uint16_t>{}:cursor;
    }
    const bool scene_changed=state_->scene && *state_->scene!=token;
    if(!state_->scene || scene_changed){state_->tracker.begin_scene(token);state_->scene=token;state_->frames={};}
    if(discontinuity && !scene_changed){state_->tracker.invalidate_scene();state_->frames={};}
    if(invalid_replay)return; // Never publish a model/camera map for an invalid cursor.
    state_->frames[bank]=state_->tracker.begin_frame(bank,word(ram,layout.arena_cursor),word(ram,layout.arena_end));
}
void TransformRuntime::invalidate_scene(){
    std::lock_guard lock(state_->frame_mutex);
    state_->tracker.invalidate_scene();state_->frames={};
}
TransformPositionObservation TransformRuntime::observe_position_before(std::span<const uint8_t> ram,uint32_t pointer_field){
    TransformPositionObservation result;
    if(ram.size()!=0x800000 || pointer_field%4 || pointer_field>ram.size()-4)return result;
    std::lock_guard lock(state_->frame_mutex);
    const uint32_t pointer=word(ram,pointer_field);
    if(!state_->known_record(pointer))return result;
    result.pointer_field=pointer_field;result.record=*address(pointer,0x60);
    for(unsigned n=0;n<3;++n)result.position[n]=word(ram,result.record+n*4);
    result.frames=state_->frames;result.owner=this;result.valid=true;
    return result;
}
void TransformRuntime::observe_position_after(std::span<const uint8_t> ram,TransformPositionObservation before){
    if(!before.valid || before.owner!=this || ram.size()!=0x800000 ||
       before.pointer_field%4 || before.pointer_field>ram.size()-4)return;
    std::lock_guard lock(state_->frame_mutex);
    if(before.frames!=state_->frames)return;
    const uint32_t pointer=word(ram,before.pointer_field);
    if(!state_->known_record(pointer) || address(pointer,0x60)!=before.record)return;
    for(unsigned n=0;n<3;++n)if(word(ram,before.record+n*4)!=before.position[n]){
        state_->tracker.invalidate_scene();state_->frames={};return;
    }
}
MatrixBuildObservation TransformRuntime::observe_matrix_before(std::span<const uint8_t> ram,uint64_t record,TransformMatrixBuilder builder){
    MatrixBuildObservation result;
    if(ram.size()!=0x800000 || !state_->known_record(record) ||
       (builder!=TransformMatrixBuilder::Conditional252F8 && builder!=TransformMatrixBuilder::Unconditional25710))return result;
    std::lock_guard lock(state_->frame_mutex);
    const auto& layout=state_->layout;
    const unsigned bank=word(ram,layout.bank_selector);if(bank>1)return result;
    const auto offset=*address(record,0x60);
    result.bank=bank;result.owner=this;
    result.capture={.frame=state_->frames[bank],.record=0x80000000ull+offset,.flags=word(ram,offset+0x28),
        .matrix_before=word(ram,offset+0x18+bank*4),.matrix_after=0,
        .cursor_before=word(ram,layout.arena_cursor),.cursor_after=0,
        .flags_after=0,.builder=builder};
    result.valid=result.capture.frame!=0;return result;
}
void TransformRuntime::observe_matrix_after(std::span<const uint8_t> ram,MatrixBuildObservation observation){
    if(!observation.valid || observation.owner!=this || ram.size()!=0x800000)return;
    std::lock_guard lock(state_->frame_mutex);
    const auto& layout=state_->layout;
    const unsigned bank=word(ram,layout.bank_selector);
    if(bank>1 || bank!=observation.bank || state_->frames[bank]!=observation.capture.frame)return;
    const auto offset=address(observation.capture.record,0x60);if(!offset)return;
    // Recursive children can advance the cursor beyond this record's matrix.
    observation.capture.matrix_after=word(ram,*offset+0x18+bank*4);
    observation.capture.cursor_after=word(ram,layout.arena_cursor);
    observation.capture.flags_after=word(ram,*offset+0x28);
    state_->tracker.capture_matrix(observation.capture);
}
void TransformRuntime::submit_metadata(std::span<const uint8_t> ram,uint32_t type,const TransformTaskFingerprint& task){
    // Hold the lock until the tracker has copied the frame. A scene/bank reset
    // between selecting its token and submit_task would invalidate that token.
    std::lock_guard lock(state_->frame_mutex);
    std::optional<uint64_t> frame;
    const auto code=address(task.ucode,1),data=address(task.ucode_data,1);
    bool known_microcode=false;
    for(const auto& candidate:state_->layout.microcodes)
        if(code && data && *code==candidate.code && *data==candidate.data)known_microcode=true;
    if(type==1 && known_microcode && ram.size()==0x800000){
        if(auto bank=graphics_task_bank(ram,task.data_ptr,state_->layout.perspective_matrices))
            if(state_->frames[*bank])frame=state_->frames[*bank];
    }
    state_->tracker.submit_task(type,task,frame);
}
std::shared_ptr<const TransformTaskSnapshot> TransformRuntime::consume_metadata(const TransformTaskFingerprint& task){return state_->tracker.consume_submission(task);}
void configure_transform_runtime(const TransformGuestLayout& layout){
    auto candidate=std::make_shared<TransformRuntime>(layout);
    std::lock_guard lock(configuration_mutex);
    if(configured_runtime)throw std::logic_error("Transform runtime is already configured");
    configured_runtime=std::move(candidate);
}
void observe_transform_allocation(uint64_t record){if(auto r=runtime())r->observe_allocation(record);}
void observe_transform_release(uint64_t record){if(auto r=runtime())r->observe_release(record);}
void observe_transform_frame(std::span<const uint8_t> ram){if(auto r=runtime())r->observe_frame(ram);}
void notify_transform_discontinuity(){if(auto r=runtime())r->invalidate_scene();}
TransformPositionObservation observe_transform_position_before(std::span<const uint8_t> ram,uint32_t pointer_field){
    if(auto r=runtime())return r->observe_position_before(ram,pointer_field);
    return {};
}
void observe_transform_position_after(std::span<const uint8_t> ram,TransformPositionObservation before){
    if(auto r=runtime())r->observe_position_after(ram,before);
}
MatrixBuildObservation observe_transform_matrix_before(std::span<const uint8_t> ram,uint64_t record,TransformMatrixBuilder builder){
    if(auto r=runtime())return r->observe_matrix_before(ram,record,builder);
    return {};
}
void observe_transform_matrix_after(std::span<const uint8_t> ram,MatrixBuildObservation observation){if(auto r=runtime())r->observe_matrix_after(ram,observation);}
std::mutex& transform_submission_mutex(){return submission_mutex;}
void submit_transform_metadata(std::span<const uint8_t> ram,uint32_t type,const TransformTaskFingerprint& task){if(auto r=runtime())r->submit_metadata(ram,type,task);}
std::shared_ptr<const TransformTaskSnapshot> consume_transform_metadata(const TransformTaskFingerprint& task){if(auto r=runtime())return r->consume_metadata(task);return {};}
}
