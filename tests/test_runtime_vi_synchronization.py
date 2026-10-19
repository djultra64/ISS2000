"""Force a real VI update/swap interleaving. Original work: djultra64."""
from pathlib import Path
import subprocess,tempfile,unittest
from tools import prepare_runtime_timing
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'.local/deps/N64ModernRuntime/ultramodern/src/events.cpp'
INCLUDE=ROOT/'.local/deps/N64ModernRuntime/ultramodern/include'

def section(text,start,end):
    return text[text.index(start):text.index(end,text.index(start))]

def run_case(text):
    state=section(text,'struct ViState {','#define VI_STATE_BLACK')
    vi=section(text,'    struct {\n        std::thread thread;','    } vi;')+'    } vi;\n'
    # A barrier only in the extracted fixture forces the narrow preemption window.
    vi=vi.replace('cur_state ^= 1;','cur_state ^= 1; test_after_flip();')
    regs=section((INCLUDE/'ultramodern/renderer_context.hpp').read_text(),'        struct ViRegs {','        ViRegs* get_vi_regs();')
    swap=section(text,'extern "C" void osViSwapBuffer(','extern "C" void osViSetMode(')
    update=section(text,'        // Update VI registers and swap VI modes.','        // If the game has started, handle sending VI and AI events.')
    getters=section(text,'extern "C" PTR(void) osViGetNextFramebuffer()','void ultramodern::submit_rsp_task(')
    code='''#include <thread>
#include <mutex>
#include <condition_variable>
#include <cstdio>
#include "ultramodern/ultra64.h"
#include "runtime/vi_scale.hpp"
namespace ultramodern::renderer {\n'''+regs+'''}
extern "C" u32 osVirtualToPhysical(PTR(void) a){return a&0x1fffffff;}
void iss2000_record_vi_framebuffer(uint32_t,uint32_t,uint32_t,uint32_t){}
std::mutex gate;std::condition_variable cv;bool flipped=false,attempted=false;
void test_after_flip(){std::unique_lock lock(gate);flipped=true;cv.notify_all();cv.wait(lock,[]{return attempted;});}
'''+state+'''#define VI_STATE_BLACK 0x20
#define VI_STATE_REPEATLINE 0x40
struct {\n'''+vi+'''std::mutex message_mutex;} events_context;
'''+swap+getters+'''void update(){\n'''+update+'''}
int main(){
 OSViMode mode{};mode.comRegs.width=640;mode.comRegs.xScale=1024;
 mode.fldRegs[0].yScale=mode.fldRegs[1].yScale=1024;
 for(auto& s:events_context.vi.states){s.mode=&mode;s.framebuffer=0x80500000;}
 std::thread writer([]{
  {std::unique_lock lock(gate);cv.wait(lock,[]{return flipped;});}
  bool available=events_context.message_mutex.try_lock();
  if(available){events_context.message_mutex.unlock();osViSwapBuffer(nullptr,0x805aa000);}
  {std::lock_guard lock(gate);attempted=true;cv.notify_all();}
  if(!available)osViSwapBuffer(nullptr,0x805aa000);
 });
 update();writer.join();
 auto current=osViGetCurrentFramebuffer(),next=osViGetNextFramebuffer();
 std::printf("current=%08x next=%08x requested=805aa000\\n",current,next);
 return current==0x80500000&&next==0x805aa000?0:20;
}
'''
    with tempfile.TemporaryDirectory()as tmp:
        p=Path(tmp);(p/'case.cpp').write_text(code)
        build=subprocess.run(['c++','-std=c++20','-O1','-pthread','-I'+str(INCLUDE),'-I'+str(ROOT/'src'),str(p/'case.cpp'),'-o',str(p/'case')],text=True,capture_output=True)
        if build.returncode:raise AssertionError(build.stdout+build.stderr)
        return subprocess.run([str(p/'case')],text=True,capture_output=True,timeout=10)

@unittest.skipUnless(SOURCE.exists(),'requires pinned local runtime source')
class RuntimeViSynchronizationTests(unittest.TestCase):
    def test_update_and_swap_do_not_lose_pending_framebuffer(self):
        original=SOURCE.read_text()
        baseline=run_case(original)
        self.assertEqual(baseline.returncode,20,baseline.stdout+baseline.stderr)
        self.assertIn('next=80500000',baseline.stdout)
        with tempfile.TemporaryDirectory()as tmp:
            prepare_runtime_timing.prepare(SOURCE,Path(tmp)/'out')
            corrected=run_case((Path(tmp)/'out/events.cpp').read_text())
        self.assertEqual(corrected.returncode,0,corrected.stdout+corrected.stderr)
        self.assertIn('next=805aa000',corrected.stdout)
