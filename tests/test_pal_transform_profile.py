"""The verified PAL layout must reset on PAL controls, not similarly named RAM."""
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
class PalTransformProfileTests(unittest.TestCase):
    def test_pal_task_camera_pause_and_replay_continuity(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);s=p/'profile.cpp'
            s.write_text(r'''#include "runtime/pal_game_layout.hpp"
#include "runtime/transform_runtime.hpp"
#include <vector>
#include <cstring>
#include <cassert>
using namespace iss2000;
void word(std::vector<uint8_t>& b,uint32_t p,uint32_t v){std::memcpy(b.data()+p,&v,4);}
void half(std::vector<uint8_t>& b,uint32_t p,uint16_t v){std::memcpy(b.data()+(p^2),&v,2);}
int main(){
 auto l=verified_pal_transform_layout();validate_transform_guest_layout(l);
 assert(l.record_pools[0].base==0x145624 && l.record_pools[1].base==0x14FF5C);
 assert(l.epoch_bytes[0]==0x13B452 && l.scene_bytes[0]==0x13B446 && l.scene_bytes[1]==0x13B44C);
 TransformRuntime rt(l);std::vector<uint8_t>b(0x800000);
 word(b,0x9DED0,0);word(b,0xB1A48,0x800A7848);word(b,0xB1A4C,0x800AC948);
 b[0x13B446^3]=6;b[0x13B44C^3]=4;
 word(b,0x1000,0xDA380007);word(b,0x1004,0x800C1AC0);word(b,0x1008,0xDF000000);
 TransformTaskFingerprint fp{0x80001000,0x80069AD0,0x80099EF0,16};
 auto frame=[&]{rt.observe_frame(b);rt.submit_metadata(b,1,fp);return rt.consume_metadata(fp);};
 auto first=frame();assert(first&&first->camera_id(0));
 b[0xB452^3]=1;auto unrelated=frame();assert(unrelated->camera_id(0)==first->camera_id(0));
 b[0x13B452^3]=1;auto paused=frame();assert(paused->camera_id(0)!=first->camera_id(0));
 b[0x12DE27^3]=3;half(b,0x12DDF0,10);auto replay=frame();
 half(b,0x12DDF0,11);auto forward=frame();assert(forward->camera_id(0)==replay->camera_id(0));
 half(b,0x12DDF0,10);auto reverse=frame();assert(reverse->camera_id(0)!=replay->camera_id(0));
 rt.invalidate_scene();auto reset=frame();assert(reset->camera_id(0)!=reverse->camera_id(0));
 assert(first->scene_token==0x604 && first->camera_id(0)==unrelated->camera_id(0));
}
''')
            exe=p/'profile'
            args=['c++','-std=c++20','-O2','-pthread','-I',str(ROOT/'src'),str(s),*[str(ROOT/'src/runtime'/name) for name in ['transform_tracker.cpp','transform_runtime.cpp','graphics_task_bank.cpp','pal_menu_avatar.cpp']],'-o',str(exe)]
            build=subprocess.run(args,capture_output=True,text=True);self.assertEqual(build.returncode,0,build.stderr)
            result=subprocess.run([str(exe)],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
