"""Original project work: djultra64. Real host observers over synthetic RDRAM."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = r'''
#include "runtime/transform_runtime.hpp"
#include "runtime/rt64_transform_bridge.hpp"
#include <atomic>
#include <cassert>
#include <cstring>
#include <string>
#include <thread>
#include <vector>
using namespace iss2000;
using Bytes=std::vector<uint8_t>;
void word(Bytes& ram, size_t offset, uint32_t value) {std::memcpy(ram.data()+offset,&value,4);}
void half(Bytes& ram,size_t offset,uint16_t value){std::memcpy(ram.data()+(offset^2),&value,2);}
TransformGuestLayout shifted_layout(){
    auto layout=us_transform_layout();
    for(auto& p:layout.record_pools)p.base+=0x10000;
    layout.arena_base+=0x10000;
    layout.bank_selector+=0x10000;layout.arena_cursor+=0x10000;layout.arena_end+=0x10000;
    for(auto& a:layout.scene_bytes)a+=0x10000;
    for(auto& a:layout.perspective_matrices)a+=0x10000;
    for(auto& camera:layout.view_matrices)for(auto& a:camera)a+=0x10000;
    for(auto& m:layout.microcodes){m.code+=0x10000;m.data+=0x10000;}
    layout.interpolation_scene_token=0x704;
    return layout;
}
Bytes frame_ram(const TransformGuestLayout& l,unsigned bank=0){
    Bytes ram(0x800000);
    word(ram,l.bank_selector,bank);
    word(ram,l.arena_cursor,0x80000000+l.arena_base+bank*l.arena_size);
    word(ram,l.arena_end,0x80000000+l.arena_base+(bank+1)*l.arena_size);
    ram[l.scene_bytes[0]^3]=l.interpolation_scene_token>>8;
    ram[l.scene_bytes[1]^3]=l.interpolation_scene_token&255;
    word(ram,0x1000,0xDA380007);word(ram,0x1004,0x80000000+l.perspective_matrices[bank]);
    return ram;
}
TransformTaskFingerprint task(const TransformGuestLayout& l){return {0x80001000,0x80000000+l.microcodes[0].code,0x80000000+l.microcodes[0].data,8};}
std::shared_ptr<const TransformTaskSnapshot> submit(TransformRuntime& rt,const Bytes& ram,const TransformTaskFingerprint& fp){
    rt.submit_metadata(ram,1,fp);return rt.consume_metadata(fp);
}
int main(int argc,char** argv){
    assert(argc==2);const std::string mode=argv[1];
    if(mode=="disabled"){
        auto l=us_transform_layout();auto ram=frame_ram(l);auto fp=task(l);
        observe_transform_allocation(0x80148104);observe_transform_frame(ram);
        assert(!observe_transform_matrix_before(ram,0x80148104,TransformMatrixBuilder::Conditional252F8).valid);
        submit_transform_metadata(ram,1,fp);assert(!consume_transform_metadata(fp));
        configure_transform_runtime(l);observe_transform_frame(ram);submit_transform_metadata(ram,1,fp);
        assert(consume_transform_metadata(fp));
        bool rejected=false;try{configure_transform_runtime(l);}catch(const std::logic_error&){rejected=true;}assert(rejected);
        return 0;
    }
    if(mode=="invalid"){
        for(int field=0;field<9;++field){
            auto l=us_transform_layout();
            if(field==0)l.record_pools[0].stride=0;
            if(field==1)l.arena_base=0x7FFFF8;
            if(field==2)l.scene_bytes[0]=0x800000;
            if(field==3)l.arena_cursor=0x7FFFFE;
            if(field==4)l.perspective_matrices[1]=l.perspective_matrices[0];
            if(field==5)l.epoch_byte_count=5;
            if(field==6){l.epoch_bytes[0]=0x800000;l.epoch_byte_count=1;}
            if(field==7)l.replay_continuity=ReplayContinuityLayout{0x6001,0x6006,3,68};
            if(field==8)l.replay_continuity=ReplayContinuityLayout{0x6004,0x6006,3,1};
            bool rejected=false;try{TransformRuntime rt(l);}catch(const std::invalid_argument&){rejected=true;}assert(rejected);
        }
        return 0;
    }
    auto layout=mode=="relocated"?shifted_layout():us_transform_layout();
    if(mode.starts_with("epoch")){layout.epoch_bytes={0x6000,0x6001,0x6002,0};layout.epoch_byte_count=3;}
    if(mode=="replay")layout.replay_continuity=ReplayContinuityLayout{0x6004,0x6006,3,68};
    TransformRuntime rt(layout);auto ram=frame_ram(layout);auto fp=task(layout);
    if(mode=="replay"){ram[0x6006^3]=3;half(ram,0x6004,10);}
    const uint32_t record=layout.record_pools[0].base, matrix=layout.arena_base;
    rt.observe_allocation(0x80000000+record);rt.observe_frame(ram);
    if(mode=="concurrent"){
        const auto stable=ram;std::atomic<bool> start=false;
        std::thread resetter([&]{while(!start.load()){}for(int i=0;i<100000;++i)rt.observe_frame(stable);});
        start=true;
        for(int i=0;i<100000;++i){auto snapshot=submit(rt,stable,fp);assert(snapshot&&snapshot->bank==0);}
        resetter.join();assert(ram==stable);return 0;
    }
    if(mode=="producer"){
        auto first=submit(rt,ram,fp);assert(first);
        std::thread second([&]{rt.submit_metadata(ram,1,fp);});second.join();
        assert(!rt.consume_metadata(fp));rt.invalidate_scene();rt.submit_metadata(ram,1,fp);assert(!rt.consume_metadata(fp));return 0;
    }
    const auto builder=mode=="unconditional"?TransformMatrixBuilder::Unconditional25710:TransformMatrixBuilder::Conditional252F8;
    word(ram,record+0x28,(mode=="unconditional"||mode=="conditional_skip")?0x80000800:0x80000000);
    auto before=rt.observe_matrix_before(ram,0x80000000+record,builder);
    assert(before.valid&&before.capture.builder==builder);
    word(ram,record+0x18,0x80000000+matrix);word(ram,record+0x28,mode=="flags_reject"?0x80000000:0x80400000);
    word(ram,layout.arena_cursor,0x80000000+matrix+64);
    if(mode=="stale"){
        auto newFrame=frame_ram(layout);rt.observe_frame(newFrame);
    }
    const auto unchanged=ram;rt.observe_matrix_after(ram,before);assert(ram==unchanged);
    auto snapshot=submit(rt,ram,fp);assert(snapshot);
    if(mode=="conditional_skip"||mode=="flags_reject"||mode=="stale"){
        assert(!snapshot->lookup(matrix));return 0;
    }
    assert(snapshot->lookup(matrix)&&"observer must record post-call flags");
    if(mode=="relocated"){
        assert(snapshot->lookup(0x80000000+matrix)->record==0x80000000+record);
        assert(!snapshot->lookup(0xAA128));
        auto choose=[&](uint32_t a,bool load){return select_rt64_transform(snapshot.get(),true,a,true,load,true);};
        assert(choose(0xD43A0,true).kind==TransformSelection::Kind::Camera);
        assert(choose(0xDEC68,false).id==snapshot->camera_id(0));
        assert(choose(0xDECE8,false).id==snapshot->camera_id(1));
        assert(choose(0xC43A0,true).kind==TransformSelection::Kind::Ignore);
        layout.record_pools={}; // construction and task snapshots own their layout
        assert(snapshot->layout.record_pools[0].base==0x158104);
        auto us=task(us_transform_layout());assert(submit(rt,ram,us)->bank==2);
    }
    if(mode=="position"){
        constexpr uint32_t field=0x6500;
        word(ram,field,0x80000000+record);
        auto idle=rt.observe_position_before(ram,field);assert(idle.valid);
        rt.observe_position_after(ram,idle);assert(submit(rt,ram,fp)->lookup(matrix)->id==snapshot->lookup(matrix)->id);
        // Arbitrary guest pointers, partial records and short memory fail closed.
        for(uint32_t bad:{0u,0x80800000u,0x80000000+record+4}){
            word(ram,field,bad);assert(!rt.observe_position_before(ram,field).valid);
        }
        assert(!rt.observe_position_before(ram,0x7FFFFE).valid);
        assert(!rt.observe_position_before(std::span<const uint8_t>(ram.data(),16),field).valid);
        word(ram,field,0x80000000+record);
        TransformRuntime other(layout);auto foreign=other.observe_position_before(ram,field);
        word(ram,record,1);rt.observe_position_after(ram,foreign);assert(submit(rt,ram,fp)->lookup(matrix));
        word(ram,record,0);
    }
    if(mode=="discontinuity"||mode=="position"||mode.starts_with("epoch")){
        const auto oldId=snapshot->lookup(matrix)->id;
        const auto oldCamera=snapshot->camera_id(0);
        rt.submit_metadata(ram,1,fp); // queued immutable snapshot must survive reset
        auto staleObservation=rt.observe_matrix_before(ram,0x80000000+record,builder);
        if(mode=="discontinuity")rt.invalidate_scene();
        else if(mode=="position"){
            auto position=rt.observe_position_before(ram,0x6500);assert(position.valid);
            word(ram,record+8,0x3F800000); // bit-exact correction, no invented distance cutoff
            const auto original=ram;rt.observe_position_after(ram,position);assert(ram==original);
        }
        else{auto changed=frame_ram(layout);changed[(0x6000+unsigned(mode.back()-'0'))^3]=1;rt.observe_frame(changed);}
        auto queued=rt.consume_metadata(fp);
        assert(queued&&queued->lookup(matrix)->id==oldId&&queued->camera_id(0)==oldCamera);
        rt.observe_matrix_after(ram,staleObservation);
        auto empty=submit(rt,ram,fp);
        assert(empty&&!empty->lookup(matrix));
        if(mode=="discontinuity"||mode=="position")assert(empty->bank==2&&!empty->camera_id(0));
        else assert(empty->camera_id(0)!=oldCamera);
        // Original phase bytes are unchanged. The next frame renews IDs for the
        // SAME existing allocation, without an invented guest free/allocate.
        auto next=frame_ram(layout);
        if(mode.starts_with("epoch"))next[(0x6000+unsigned(mode.back()-'0'))^3]=1;
        rt.observe_frame(next);
        word(next,record+0x28,0x80000000);
        auto capture=rt.observe_matrix_before(next,0x80000000+record,builder);
        word(next,record+0x18,0x80000000+matrix);word(next,record+0x28,0x80400000);
        word(next,layout.arena_cursor,0x80000000+matrix+64);rt.observe_matrix_after(next,capture);
        auto newer=submit(rt,next,fp);assert(newer&&newer->lookup(matrix));
        assert(newer->scene_token==snapshot->scene_token&&newer->scene_epoch>snapshot->scene_epoch);
        assert(newer->lookup(matrix)->id!=oldId&&newer->camera_id(0)!=oldCamera);
        assert(newer->lookup(matrix)->generation==snapshot->lookup(matrix)->generation);
        assert(snapshot->lookup(matrix)->id==oldId&&queued->lookup(matrix)->id==oldId);
    }
    if(mode=="replay"){
        auto id=snapshot->lookup(matrix)->id;
        auto frameAt=[&](uint16_t cursor){
            auto next=frame_ram(layout);next[0x6006^3]=3;half(next,0x6004,cursor);rt.observe_frame(next);
            word(next,record+0x28,0x80000000);auto capture=rt.observe_matrix_before(next,0x80000000+record,builder);
            word(next,record+0x18,0x80000000+matrix);word(next,record+0x28,0x80400000);
            word(next,layout.arena_cursor,0x80000000+matrix+64);rt.observe_matrix_after(next,capture);
            return submit(rt,next,fp);
        };
        assert(frameAt(10)->lookup(matrix)->id==id); // held replay frame
        assert(frameAt(11)->lookup(matrix)->id==id);
        assert(frameAt(12)->lookup(matrix)->id==id);
        rt.submit_metadata(ram,1,fp);auto reverse=frameAt(11);
        // frameAt consumes the queued old snapshot first; then drain its own.
        assert(reverse->lookup(matrix)->id==id);reverse=rt.consume_metadata(fp);
        assert(reverse&&reverse->lookup(matrix)->id!=id);id=reverse->lookup(matrix)->id;
        assert(frameAt(12)->lookup(matrix)->id==id);
        auto jump=frameAt(67);assert(jump->lookup(matrix)->id!=id);id=jump->lookup(matrix)->id;
        assert(frameAt(0)->lookup(matrix)->id==id); // forward ring wrap
        assert(frameAt(0)->lookup(matrix)->id==id); // still held
        auto scrub=frameAt(20);assert(scrub->lookup(matrix)->id!=id);
        auto invalid=frameAt(68);assert(invalid&&!invalid->lookup(matrix)&&!invalid->camera_id(0));
        assert(snapshot->lookup(matrix)->id!=scrub->lookup(matrix)->id);
    }
    if(mode=="ownership"){
        auto id=snapshot->lookup(matrix)->id;
        rt.observe_release(0x80000000+record);rt.observe_allocation(0x80000000+record);
        auto next=frame_ram(layout);rt.observe_frame(next);
        word(next,record+0x28,0x80000000);
        auto capture=rt.observe_matrix_before(next,0x80000000+record,builder);
        word(next,record+0x18,0x80000000+matrix);word(next,record+0x28,0x80400000);
        word(next,layout.arena_cursor,0x80000000+matrix+64);rt.observe_matrix_after(next,capture);
        auto newer=submit(rt,next,fp);assert(newer->lookup(matrix)->id!=id);
        std::thread reader([&]{for(int i=0;i<10000;++i)assert(snapshot->lookup(matrix)->id==id);});
        rt.observe_release(0x80000000+record);reader.join();
    }
}
'''

class TransformRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        directory = Path(cls.temp.name)
        source = directory/'runtime.cpp'
        source.write_text(SOURCE)
        cls.binary = directory/'runtime'
        result = subprocess.run(['c++','-std=c++20','-pthread','-O2','-Wall','-Wextra','-Werror',
            '-I'+str(ROOT/'src'),str(source),str(ROOT/'src/runtime/transform_runtime.cpp'),
            str(ROOT/'src/runtime/transform_tracker.cpp'),str(ROOT/'src/runtime/graphics_task_bank.cpp'),
            '-o',str(cls.binary)],text=True,capture_output=True)
        if result.returncode:
            raise RuntimeError(result.stderr)
    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()
    def run_case(self, name):
        result = subprocess.run([str(self.binary),name],text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
    def test_post_call_flags_and_builder_identity_make_capture_eligible(self):self.run_case('post_flags')
    def test_conditional_builder_skip_never_tags_record(self):self.run_case('conditional_skip')
    def test_unconditional_builder_allows_conditional_skip_flag(self):self.run_case('unconditional')
    def test_missing_post_call_built_flag_rejects_stale_pointer(self):self.run_case('flags_reject')
    def test_observation_from_previous_frame_is_ignored(self):self.run_case('stale')
    def test_explicit_relocated_layout_drives_records_arenas_microcode_and_camera_policy(self):self.run_case('relocated')
    def test_unconfigured_global_hooks_are_disabled(self):self.run_case('disabled')
    def test_invalid_layouts_are_rejected_before_guest_reads(self):self.run_case('invalid')
    def test_frame_resets_cannot_invalidate_submission_snapshot(self):self.run_case('concurrent')
    def test_second_graphics_producer_quarantines_runtime(self):self.run_case('producer')
    def test_same_byte_scene_discontinuity_renews_ids_without_discarding_queued_tasks(self):self.run_case('discontinuity')
    def test_each_watched_epoch_byte_retires_ids_and_preserves_queued_snapshots(self):
        for field in range(3):self.run_case('epoch'+str(field))
    def test_replay_forward_and_hold_preserve_ids_but_reverse_and_scrub_retire_them(self):self.run_case('replay')
    def test_position_correction_observer_resets_only_for_valid_changed_records(self):self.run_case('position')
    def test_snapshots_survive_record_reallocation_and_worker_reads(self):self.run_case('ownership')
