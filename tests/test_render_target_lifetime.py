"""Original project work: djultra64. Deterministic present/cleanup lifetime regression, CPU only."""
from pathlib import Path
import importlib.util,resource,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
CODE=r'''#include "runtime/render_target_lifetime.hpp"
#include <atomic>
#include <array>
#include <chrono>
#include <condition_variable>
#include <cstdio>
#include <future>
#include <memory>
#include <mutex>
#include <optional>
#include <thread>
using namespace std::chrono_literals;
struct Target{std::atomic<bool>&destroyed;~Target(){destroyed=true;}};
struct Counters{unsigned presented=0,available=0,count=0;bool skipped=false;};
struct Shared{std::mutex interpolatedMutex;std::array<Counters,2> interpolatedFrames;std::mutex configurationMutex;bool fbConfigChanged=true,swapChainSizeChanged=false;std::unique_ptr<Target> target;};
struct Ext{Shared*sharedResources;};
std::atomic<bool> destroyed=false,attempted=false;
std::promise<void> pinnedSignal,extraSignal,cleanupSignal,releaseFenceSignal;
auto extra=extraSignal.get_future().share();auto fence=releaseFenceSignal.get_future().share();
void present(Ext ext){
 PRESENT_PIN
 const auto*target=ext.sharedResources->target.get();pinnedSignal.set_value();
 extra.wait(); // Producer must remain free to publish the remaining frame.
 fence.wait(); // Actual GPU completion governs the end of the presentation pin.
 if(destroyed||target!=ext.sharedResources->target.get()){fprintf(stderr,"TARGET DESTROYED BEFORE PRESENT FENCE\n");std::abort();}
}
void cleanup(Ext ext){
 CLEANUP_PROLOG
 CLEANUP_RETIRE
 ext.sharedResources->target.reset();cleanupSignal.set_value();
}
void ordinary(Ext ext){
 CLEANUP_PROLOG
 if(ext.sharedResources->fbConfigChanged||ext.sharedResources->swapChainSizeChanged)std::abort();
}
int main(){Shared shared;shared.target=std::make_unique<Target>(destroyed);Ext ext{&shared};auto pinned=pinnedSignal.get_future(),cleaned=cleanupSignal.get_future();
 std::thread p(present,ext);if(pinned.wait_for(1s)!=std::future_status::ready)std::abort();
 // This is the SAME workload producer: publish all remaining frame outcomes
 // before entering the next workload's destructive configuration boundary.
 std::thread producer([&]{extraSignal.set_value();attempted=true;cleanup(ext);});
 while(!attempted)std::this_thread::yield();
 if(cleaned.wait_for(30ms)==std::future_status::ready){fprintf(stderr,"TARGET DESTROYED BEFORE PRESENT FENCE\n");std::abort();}
 // Inspector/config reentry remains possible while cleanup waits for the pin.
 // A producer holding configurationMutex here would invert the lock order.
 {std::lock_guard lock(shared.configurationMutex);if(destroyed)std::abort();}
 releaseFenceSignal.set_value();p.join();if(cleaned.wait_for(1s)!=std::future_status::ready)std::abort();producer.join();if(!destroyed)std::abort();
 // Unrelated owners do not block each other; an ordinary non-destructive
 // configuration update must not acquire an exclusive lifetime scope.
 Shared next;next.target=std::make_unique<Target>(destroyed);next.interpolatedFrames[0]={0,2,3,false};next.interpolatedFrames[1]={4,2,3,false};
 {Ext ext{&next};
 CLEANUP_PROLOG
 CLEANUP_RETIRE
 next.target.reset();
 for(const auto&c:next.interpolatedFrames)if(c.presented!=0||c.available!=0||c.count!=1||c.skipped)std::abort();
 }
 {iss2000::RenderTargetPresentationScope pendingPin(&next);for(const auto&c:next.interpolatedFrames)if(c.count!=1||c.available||next.target)std::abort();}
 int other;{iss2000::RenderTargetPresentationScope pin(&shared);iss2000::RenderTargetCleanupScope independent(&other);shared.fbConfigChanged=false;auto normal=std::async(std::launch::async,ordinary,ext);if(normal.wait_for(1s)!=std::future_status::ready)std::abort();normal.get();}
 return 0;
}
'''
def module(name):
 path=ROOT/'tools'/f'{name}.py';spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
class RenderTargetLifetimeTests(unittest.TestCase):
 def test_actual_derivative_scopes_preserve_interpolated_targets_until_present_fence(self):
  self.assertTrue((ROOT/'src/runtime/render_target_lifetime.cpp').is_file(),'Missing lifetime pin for the real Pre-season dangling RenderTarget')
  workload=module('prepare_rt64_menu_interpolation');present=module('prepare_rt64_present_lifetime')
  self.assertTrue(hasattr(workload,'CLEANUP_RETIRE'),'Missing coherent retirement of both interpolated counter generations')
  with tempfile.TemporaryDirectory()as d:
   p=Path(d)
   for enabled in[False,True]:
    code=CODE.replace('PRESENT_PIN',present.PRESENT_PIN if enabled else '').replace('CLEANUP_PROLOG',workload.CLEANUP_PROLOG if enabled else 'std::unique_lock configurationLock(ext.sharedResources->configurationMutex);').replace('CLEANUP_RETIRE',workload.CLEANUP_RETIRE if enabled else '')
    (p/'test.cpp').write_text(code);exe=p/('guarded'if enabled else'old')
    built=subprocess.run(['c++','-std=c++20','-O1','-pthread','-I'+str(ROOT/'src'),str(p/'test.cpp'),str(ROOT/'src/runtime/render_target_lifetime.cpp'),'-o',str(exe)],capture_output=True,text=True);self.assertEqual(built.returncode,0,built.stderr)
    run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=5,preexec_fn=lambda:resource.setrlimit(resource.RLIMIT_CORE,(0,0)))
    if enabled:self.assertEqual(run.returncode,0,run.stderr)
    else:self.assertNotEqual(run.returncode,0);self.assertIn('TARGET DESTROYED BEFORE PRESENT FENCE',run.stderr)
if __name__=='__main__':unittest.main()
