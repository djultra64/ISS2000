"""Original PAL VI/audio cadence stays independent of presentation rate."""
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
class VideoTimingTests(unittest.TestCase):
    def test_original_cadence_and_audio_quantization(self):
        with tempfile.TemporaryDirectory(prefix='iss2000-timing-') as tmp:
            p=Path(tmp); source=p/'timing.cpp'
            source.write_text(r'''#include "runtime/video_timing.hpp"
#include <chrono>
#include <stdexcept>
using namespace std::chrono_literals;
void require(bool x){if(!x)throw std::runtime_error("PAL timing mismatch");}
int main(){
    const iss2000::VideoTiming pal{50,49656530};
    const iss2000::VideoTiming ntsc{60,48681812};
    require(pal.deadline(50,1)==1s);
    require(pal.deadline(3500,1)==70s);
    require(pal.deadline(50,2)==500ms);
    require(pal.elapsed_vis(70s,1)==3501);
    require(ntsc.elapsed_vis(70s,1)==4201);
    require(pal.elapsed_vis(19999us,1)==1);
    require(pal.elapsed_vis(20ms,1)==2);
    require(pal.elapsed_vis(10ms,2)==2);
    auto f=iss2000::audio_frequency(32000,pal.audio_clock);
    require(f && f->divider==1552 && f->actual_hz==31995 && f->bitrate==16);
    auto g=iss2000::audio_frequency(44100,pal.audio_clock);
    require(g && g->divider==1126 && g->actual_hz==44099);
    require(!iss2000::audio_frequency(0,pal.audio_clock));
    require(!iss2000::audio_frequency(500000,pal.audio_clock));
    try{pal.deadline(50,0);return 2;}catch(const std::invalid_argument&){}
}
''')
            exe=p/'timing'
            build=subprocess.run(['c++','-std=c++20','-Wall','-Wextra','-Werror','-I',str(ROOT/'src'),str(source),'-o',str(exe)],capture_output=True,text=True)
            self.assertEqual(build.returncode,0,build.stderr)
            result=subprocess.run([str(exe)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
