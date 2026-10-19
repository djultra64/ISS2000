"""Original work: djultra64. Execute emitted queued-image fallback without a GPU."""
from pathlib import Path
import importlib.util
import subprocess
import os
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
HARNESS=r'''
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <vector>
#include <mutex>
struct Size{uint32_t x=2,y=2;};
struct VI{bool shown=true;uint32_t size=2;Size dimensions;bool visible()const{return shown;}Size fbSize()const{return dimensions;}uint32_t fbSiz()const{return size;}uint32_t fbAddress()const{return 0x1000;}bool operator!=(const VI&)const{return false;}};
struct Present{VI screenVI;std::vector<uint8_t> storage;bool paused=false;};
struct Change{};using FramebufferChange=Change;
struct Worker{};
struct RenderWorkerExecution{explicit RenderWorkerExecution(Worker*){}};
struct Target{std::vector<uint8_t> pixels;bool resized=false;struct Scale{float x,y;}resolutionScale;int downsampleMultiplier=0;void resize(Worker*,unsigned,unsigned){resized=true;}void clearColorTarget(Worker*){pixels.clear();}void copyFromChanges(Worker*,Change&,unsigned,unsigned,int,void*){pixels=queued; }static inline std::vector<uint8_t> queued;};
struct RenderTargetKey{template<class T>RenderTargetKey(uint32_t,uint32_t,uint32_t,T){}};
struct Framebuffer{enum class Type{Color};uint32_t addressStart=0,width=0,height=0,siz=0;struct Native{void resetBufferHistory(){}}nativeTarget;template<class Pool>Change* readChangeFromBytes(Worker*,Pool&,Type,int,const uint8_t* bytes,int,unsigned h,void*){Target::queued.assign(bytes,bytes+width*h*(siz==2?2:4));static Change c;return &c;}};
struct Pool{void reset(){}};
struct Manager{Target target;Target&get(RenderTargetKey,bool){return target;}};
struct Lock{unsigned acquisitions=0;void lock(){assert(acquisitions==0);++acquisitions;}};
struct Shared{Lock workloadMutex;};
struct Ext{Shared*sharedResources;Worker*presentGraphicsWorker=nullptr;void*shaderLibrary=nullptr;};
struct History{struct Entry{VI vi;}entry;Entry&top(){return entry;}void pushVI(VI,unsigned){}};
constexpr int G_IM_FMT_RGBA=0,G_IM_SIZ_16b=2,G_IM_SIZ_32b=3;
int main(){
 for(bool visible:{true,false})for(bool descriptor:{true,false})for(bool existing:{false,true})for(bool alreadyLocked:{false,true})for(unsigned size:{2u,3u,1u})for(int bytes:{8,16,7,0})for(uint32_t width:{2u,0xffffffffu}){
  Present present;present.screenVI.shown=visible;present.screenVI.size=size;present.screenVI.dimensions.x=width;present.storage.assign(bytes,0x5a);
  Shared shared;if(alreadyLocked)shared.workloadMutex.lock();Ext ext{&shared};Manager targetManager;Framebuffer scratchFb;Pool scratchFbChangePool;History viHistory;
  bool lockedWorkloadMutex=alreadyLocked;int framesToPresent=3;Target original;original.pixels={0x11};Target*colorTarget=nullptr;
  void* presentFb=descriptor?&original:nullptr;void*viFb=presentFb;
  const bool viVisible=present.screenVI.visible();auto fbSize=present.screenVI.fbSize();
  if(viVisible&&fbSize.x>0&&fbSize.y>0){
   if(presentFb&&viFb){if(existing)colorTarget=&original;}
   EMITTED_FALLBACK
  }
  const bool usable=width==2&&((size==2&&bytes>=8)||(size==3&&bytes>=16));
  const bool fallback=visible&&!(descriptor&&existing)&&usable;
  if(visible&&descriptor&&existing){assert(colorTarget==&original&&original.pixels==std::vector<uint8_t>{0x11});assert(!targetManager.target.resized);}
  else if(fallback){assert(colorTarget==&targetManager.target&&colorTarget->resized);assert(framesToPresent==1);assert(colorTarget->pixels==std::vector<uint8_t>((size==2?8:16),0x5a));assert(shared.workloadMutex.acquisitions==1);}
  else {assert(colorTarget==nullptr);assert(!targetManager.target.resized);}
 }
}
'''

class PresentOriginalFallbackTests(unittest.TestCase):
 def test_emitted_fallback_uses_valid_original_bytes_without_blanking_or_double_lock(self):
  spec=importlib.util.spec_from_file_location('present_fallback_generator',ROOT/'tools/prepare_rt64_present_lifetime.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  path=ROOT/'.local/deps/rt64/src/hle/rt64_present_queue.cpp'
  if not path.is_file():self.skipTest('Pinned upstream source unavailable')
  for evidence in (False,True):
   emitted=m.derive(path.read_bytes(),evidence).decode()
   # Execute the exact emitted fallback after the descriptor-selection branch.
   anchor='viHistory.pushVI(present.screenVI, viFb->width);'
   start=emitted.index(anchor)+len(anchor)
   start=emitted.index('\n            }\n',start)+len('\n            }')
   end=emitted.index('        // Create the framebuffers if necessary.',start)
   block=emitted[start:end].rstrip()
   assert block.endswith('}')
   block=block[:-1] # enclosing visible-VI block is supplied by the harness
   with tempfile.TemporaryDirectory()as d:
    p=Path(d);(p/'test.cpp').write_text(HARNESS.replace('EMITTED_FALLBACK',block))
    q=subprocess.run(['c++','-std=c++20','-O1',str(p/'test.cpp'),'-o',str(p/'test')],capture_output=True,text=True)
    self.assertEqual(q.returncode,0,q.stderr)
    env=os.environ.copy();env.pop('ISS2000_RENDER_EVIDENCE',None)
    q=subprocess.run([str(p/'test')],env=env,capture_output=True,text=True,timeout=5)
    self.assertEqual(q.returncode,0,q.stderr);self.assertEqual(q.stderr,'')
    env['ISS2000_RENDER_EVIDENCE']='unused-evidence-path'
    q=subprocess.run([str(p/'test')],env=env,capture_output=True,text=True,timeout=5)
    self.assertEqual(q.returncode,0,q.stderr)
    self.assertIn('reason=empty_target',q.stderr);self.assertIn('reason=missing_framebuffer',q.stderr)
