"""Execute the real AI progress adapter against device pulls and the PAL producer.
Original project work: djultra64. Synthetic PCM timing only; no game or audio device.
"""
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
def function(source,marker):
 start=source.index(marker);opening=source.index('{',start);depth=1;end=opening+1
 while depth:
  depth+=(source[end]=='{')-(source[end]=='}');end+=1
 return source[start:end]
class AudioDmaClockTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory(prefix='iss2000-ai-clock-');cls.addClassCleanup(cls.temp.cleanup)
  p=Path(cls.temp.name);source=(ROOT/'src/platform.cpp').read_text()
  clock=re.search(r'Audio\w+Clock audio_clock;',source).group()
  code=r'''
#include "runtime/audio_fifo.hpp"
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <mutex>
#include <stdexcept>
#include <string>
using namespace iss2000;
AudioFifo audio_fifo;
CLOCK
uint32_t source_frequency=44099;
uint64_t output_frames_emitted{},output_frames_consumed{};
uint64_t now_ns{},device_frames{},device_pulls{},conversion_remainder{};
unsigned audio_device=1;
void* audio_stream{};
std::mutex audio_mutex;
constexpr int AUDIO_S16SYS=0;
uint64_t audio_now_ns(){return now_ns;}
uint32_t SDL_GetQueuedAudioSize(unsigned){
 // Actual1024-frame SDL device pulls at48000Hz, independently of the50Hz VI.
 uint64_t pulls=(now_ns/1000000000*48000+now_ns%1000000000*48000/1000000000)/1024;
 device_frames-=std::min(device_frames,(pulls-device_pulls)*1024);device_pulls=pulls;
 return uint32_t(device_frames*4);
}
void SDL_FreeAudioStream(void*){}
void* SDL_NewAudioStream(int,int,uint32_t,int,int,int){return reinterpret_cast<void*>(1);}
[[noreturn]] void fail(const char*){throw std::runtime_error("converter failure");}
SYNC
FREQUENCY
bool submit(unsigned frames){
 sync_audio_locked();if(!audio_fifo.submit(frames*4))return false;
 uint64_t out=uint64_t(frames)*48000+conversion_remainder;
 conversion_remainder=out%source_frequency;out/=source_frequency;
 output_frames_emitted+=out;device_frames+=out;return true;
}
void require(bool condition,const char* message){if(!condition)throw std::runtime_error(message);}
int main(int,char** argv){try{
 std::string name=argv[1];
 if(name=="progress"){
  require(submit(1072),"initial descriptor");now_ns=20000000;sync_audio_locked();
  require(audio_fifo.length()==190*4,"AI progress must advance before the next1024-frame host pull");
 }else if(name=="producer"){
  unsigned pending=0,rejected=0;
  // Original PAL4BB20/4BB30..70: previous PCM submitted, then target-current+176,
  // aligned16 and clamped to target-16.44099Hz*0.02 rounds up to896frames.
  for(unsigned tick=0;tick<3000;++tick){
   now_ns=uint64_t(tick)*20000000;sync_audio_locked();
   if(pending&&!submit(pending))++rejected;
   sync_audio_locked();unsigned current=audio_fifo.length()/4;
   pending=std::max(880,int(896-current+176)&~15);
  }
  std::cout<<"rejected="<<rejected<<'\n';
  require(rejected==0,"original50Hz PAL producer lost a DMA at a host callback boundary");
 }else if(name=="two_slots"){
  require(submit(32)&&submit(32),"two real descriptors");
  require(!submit(32)&&audio_fifo.status()==0xC0000000u,"third DMA must still fail when genuinely full");
  now_ns=1000000;sync_audio_locked();
  require(audio_fifo.length()==20*4&&audio_fifo.status()==0x40000000u,"continuous clock must cross exactly one descriptor");
  require(submit(32),"completed descriptor must be available");
 }else if(name=="idle"){
  sync_audio_locked();now_ns=uint64_t(90)*86400*1000000000;sync_audio_locked();
  require(submit(64)&&audio_fifo.length()==64*4,"idle time cannot consume a future DMA");
  now_ns+=2000000;sync_audio_locked();require(audio_fifo.status()==0,"DMA completes");
  now_ns+=uint64_t(90)*86400*1000000000;sync_audio_locked();
  require(submit(64)&&audio_fifo.length()==64*4,"drained time cannot be banked as future credit");
 }else if(name=="fractional"){
  require(submit(65536),"large DMA");
  for(unsigned i=1;i<=100000;++i){now_ns=uint64_t(i)*10000;sync_audio_locked();}
  require(audio_fifo.length()==21436*4,"fractional source frames drifted across repeated observations");
 }else if(name=="frequency"){
  frequency(44099);require(submit(64)&&submit(64),"active descriptors");bool threw=false;
  try{frequency(32000);}catch(const std::runtime_error&){threw=true;}
  require(threw&&source_frequency==44099&&audio_fifo.status()==0xC0000000u,"active transition must not discard DMA or converter");
  now_ns=100000000;sync_audio_locked();frequency(32000);
  require(source_frequency==32000&&submit(64),"idle frequency transition");
  now_ns+=1000000;sync_audio_locked();require(audio_fifo.length()==32*4,"new frequency or clock reset is wrong");
 }else if(name=="zero"){
  require(submit(64),"initial DMA");now_ns=1000000;sync_audio_locked();auto before=audio_fifo.length();
  require(submit(0)&&audio_fifo.length()==before,"zero DMA must not reset active progress");
  bool threw=false;try{frequency(0);}catch(const std::runtime_error&){threw=true;}
  require(threw&&source_frequency==44099&&audio_fifo.length()==before,"zero frequency must reject without discarding DMA");
  now_ns+=100000;sync_audio_locked();require(audio_fifo.length()==16*4,"zero submission lost fractional clock progress");
 }else if(name=="monotonic"){
  require(submit(1072),"initial DMA");now_ns=10000000;sync_audio_locked();auto before=audio_fifo.length();
  sync_audio_locked();require(audio_fifo.length()==before,"same instant consumed audio twice");
 }else return 2;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
'''.replace('CLOCK',clock).replace('SYNC',function(source,'void sync_audio_locked(')).replace('FREQUENCY',function(source,'void frequency('))
  path=p/'clock.cpp';path.write_text(code);cls.exe=p/'clock'
  result=subprocess.run(['c++','-std=c++20','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I',str(ROOT/'src'),str(path),'-o',str(cls.exe)],capture_output=True,text=True)
  if result.returncode:raise RuntimeError(result.stderr)
 def run_case(self,name):
  result=subprocess.run([str(self.exe),name],capture_output=True,text=True)
  self.assertEqual(result.returncode,0,result.stdout+result.stderr)
 def test_continuous_ai_progress_between_sdl_pulls(self):self.run_case('progress')
 def test_original_pal_producer_never_rejects_at_host_quantum(self):self.run_case('producer')
 def test_real_two_slot_full_and_completion_semantics(self):self.run_case('two_slots')
 def test_long_idle_and_drained_time_is_not_future_dma_credit(self):self.run_case('idle')
 def test_fractional_frames_have_no_query_rate_drift(self):self.run_case('fractional')
 def test_frequency_transition_requires_idle_and_resets_clock(self):self.run_case('frequency')
 def test_zero_submission_and_invalid_frequency_preserve_active_progress(self):self.run_case('zero')
 def test_repeated_monotonic_observation_does_not_double_consume(self):self.run_case('monotonic')
if __name__=='__main__':unittest.main()
