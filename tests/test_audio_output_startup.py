"""Execute production output lifecycle against a deterministic SDL boundary.
Original project work: djultra64. No game, sound device, or wall-clock sleeps.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest
from test_audio_dma_clock import function
ROOT=Path(__file__).resolve().parents[1]
class AudioOutputStartupTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory(prefix="iss2000-output-");cls.addClassCleanup(cls.temp.cleanup)
  p=Path(cls.temp.name);s=(ROOT/'src/platform.cpp').read_text()
  globals_=s[s.index('SDL_AudioDeviceID audio_device'):s.index('std::mutex input_mutex')]
  init=s[s.index('    SDL_AudioSpec desired{};'):s.index('    for(auto& port:ports)')]
  shutdown=s[s.index('    {std::lock_guard lock(audio_mutex);if(audio_stream)'):s.index('    test_controller::shutdown();')]
  code=r'''#include "runtime/audio_fifo.hpp"
#include <vector>
#include <cstdint>
#include <cstring>
#include <mutex>
#include <stdexcept>
#include <iostream>
#include <string>
#include <algorithm>
using namespace iss2000;
using SDL_AudioDeviceID=unsigned;
struct SDL_AudioStream{std::vector<uint8_t> bytes;};
struct SDL_AudioSpec{int freq,format,channels,samples;};
constexpr int AUDIO_S16SYS=0;
bool paused=true;unsigned starts=0;std::vector<uint8_t> queue,submitted,expected;
uint64_t audio_now_ns(){return 0;}
[[noreturn]]void fail(const char* s){throw std::runtime_error(s);}
void check(bool x,const char* s){if(!x)fail(s);}
unsigned SDL_OpenAudioDevice(const char*,int,SDL_AudioSpec*,void*,int){paused=true;queue.clear();return 1;}
void SDL_CloseAudioDevice(unsigned){queue.clear();}
void SDL_PauseAudioDevice(unsigned,int value){paused=value;if(!value)++starts;}
SDL_AudioStream* SDL_NewAudioStream(int,int,unsigned,int,int,int){return new SDL_AudioStream;}
void SDL_FreeAudioStream(SDL_AudioStream* s){delete s;}
int SDL_AudioStreamPut(SDL_AudioStream* s,const void* d,int n){auto b=(const uint8_t*)d;s->bytes.insert(s->bytes.end(),b,b+n);return 0;}
int SDL_AudioStreamAvailable(SDL_AudioStream* s){return s->bytes.size();}
int SDL_AudioStreamGet(SDL_AudioStream* s,void* d,int n){n=std::min(n,int(s->bytes.size()));memcpy(d,s->bytes.data(),n);s->bytes.erase(s->bytes.begin(),s->bytes.begin()+n);return n;}
int SDL_QueueAudio(unsigned,const void* d,unsigned n){auto b=(const uint8_t*)d;queue.insert(queue.end(),b,b+n);submitted.insert(submitted.end(),b,b+n);return 0;}
unsigned SDL_GetQueuedAudioSize(unsigned){return queue.size();}
GLOBALS
SYNC
FREQUENCY
QUEUE
void initialize_audio(){INIT}
void shutdown_audio(){SHUTDOWN}
void send(unsigned frames){std::vector<int16_t> data(frames*2);for(unsigned i=0;i<frames;++i){data[2*i]=int16_t(i+23);data[2*i+1]=int16_t(i+7);int16_t restored[]={data[2*i+1],data[2*i]};auto b=(uint8_t*)restored;expected.insert(expected.end(),b,b+4);}queue_samples_locked(data.data(),data.size());}
int main(int,char** argv){try{
 std::string name=argv[1];initialize_audio();
 if(name=="threshold"){
  check(paused&&starts==0,"empty device started before PCM reserve");send(4095);check(paused,"started below4096frames");send(1);check(!paused&&starts==1,"must start exactly at4096realframes");send(960);check(starts==1,"must start only once");
 }else if(name=="lifecycle"){
  send(4096);check(!paused&&starts==1,"initial prime");auto saved=queue;frequency(32000);check(queue==saved&&!paused&&starts==1,"frequency transition discarded output or re-primed");send(960);shutdown_audio();initialize_audio();check(paused,"reinitialize started empty");send(4095);check(paused,"reinitialize lost priming threshold");send(1);check(!paused&&starts==2,"reinitialize did not restart once");
 }else if(name=="jitter"){
  //50Hz producer,1024-frame device pulls, one48ms producer stall.
  //Sweep callback phase; delayed packets catch up without rate correction.
  for(unsigned phase=0;phase<1024;phase+=32){
   shutdown_audio();initialize_audio();unsigned underflow=0;unsigned next_packet=0;
   for(unsigned t=0;t<48000*2;t++){
    unsigned due=next_packet*960;if(next_packet>=50&&next_packet<=51)due=49*960+2304;
    while(next_packet<100&&t>=due){send(960);++next_packet;due=next_packet*960;if(next_packet>=50&&next_packet<=51)due=49*960+2304;}
    if(t>=phase&&(t-phase)%1024==0&&!paused){unsigned n=std::min(size_t(4096),queue.size());underflow+=4096-n;queue.erase(queue.begin(),queue.begin()+n);}
   }
   check(underflow==0,"1024-frame callback starved during bounded producer jitter");
  }
 }
 check(submitted==expected,"PCM dropped, duplicated, reordered or modified");shutdown_audio();return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}}
'''
  for token,value in {'GLOBALS':globals_,'SYNC':function(s,'void sync_audio_locked()'),'FREQUENCY':function(s,'void frequency(uint32_t hz)'),'QUEUE':function(s,'void queue_samples_locked('),'INIT':init,'SHUTDOWN':shutdown}.items():code=code.replace(token,value)
  (p/'test.cpp').write_text(code);cls.exe=p/'test'
  subprocess.run(['c++','-std=c++20','-O2','-pthread','-I',str(ROOT/'src'),str(p/'test.cpp'),'-o',str(cls.exe)],check=True,capture_output=True,text=True)
 def run_case(self,name):
  r=subprocess.run([str(self.exe),name],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
 def test_real_pcm_threshold(self):self.run_case('threshold')
 def test_frequency_and_device_lifecycle(self):self.run_case('lifecycle')
 def test_callback_phase_and_producer_jitter(self):self.run_case('jitter')
if __name__=='__main__':unittest.main()
