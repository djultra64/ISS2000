"""Synthetic AI DMA contracts; no ROM or game execution.
Original project work: djultra64.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
class AudioFifoTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory(prefix='iss2000-ai-')
  cls.addClassCleanup(cls.temp.cleanup)
  folder=Path(cls.temp.name)
  source=folder/'audio.cpp'
  source.write_text(r'''
#include "runtime/audio_fifo.hpp"
#include <stdexcept>
#include <string>
using namespace iss2000;
void require(bool ok){if(!ok)throw std::runtime_error("AI DMA contract failed");}
int main(int,char** argv){try{
 AudioFifo fifo;std::string test=argv[1];
 if(test=="current"){
  require(fifo.submit(3200));require(fifo.submit(2880));
  require(fifo.length()==3200);fifo.consume(100);require(fifo.length()==2800);
 }else if(test=="full"){
  require(fifo.status()==0);require(fifo.submit(32));require(fifo.status()==0x40000000u);
  require(fifo.submit(64));require(fifo.status()==0xC0000000u);
  require(!fifo.submit(128));require(fifo.length()==32);
  fifo.consume(8);require(fifo.length()==64);require(fifo.status()==0x40000000u);
  require(fifo.submit(128));
 }else if(test=="crossing"){
  require(fifo.submit(32));require(fifo.submit(64));fifo.consume(12);
  require(fifo.length()==48);fifo.consume(1000000);require(fifo.status()==0);require(fifo.length()==0);
  require(fifo.submit(80));require(fifo.length()==80);
 }else if(test=="range"){
  require(valid_audio_buffer(0x80000400,8));require(valid_audio_buffer(0xA07FFFF8,8));
  require(valid_audio_buffer(0x400,8));require(valid_audio_buffer(0x807C0000,262144));
  require(!valid_audio_buffer(0x80000400,0xFFFFFF80));require(!valid_audio_buffer(0x807FFFF8,16));
  require(!valid_audio_buffer(0x80000404,8));require(!valid_audio_buffer(0x80000400,12));
  require(!valid_audio_buffer(0xC0000400,8));require(!valid_audio_buffer(0x1FFFFFF8,16));
 }else if(test=="invalid"){
  require(!fifo.submit(12));require(!fifo.submit(0xFFFFFF80u));require(fifo.status()==0);
 }else if(test=="zero"){
  require(fifo.submit(0));require(fifo.status()==0);require(valid_audio_buffer(0x80800000,0));
  require(fifo.submit(8));require(fifo.submit(8));require(fifo.submit(0));require(fifo.status()==0xC0000000u);
 }else if(test=="conversion"){
  AudioFrameClock clock;
  require(clock.consume(1,32000)==0);require(clock.consume(1,32000)==1);
  require(clock.consume(48000,32000)==32000);require(clock.consume(1,32000)==1);
  require(clock.consume(0,32000)==0);
 }else if(test=="regression"){
  require(fifo.submit(736*4));require(fifo.submit(720*4));
  // Guest target-current+176 stays non-negative when current DMA is reported.
  require(736-int(fifo.length()/4)+176>=0);
  fifo.consume(730);require(fifo.length()==24);fifo.consume(6);require(fifo.length()==720*4);
 }else return 2;
}catch(const std::exception&){return 1;}
}
''')
  cls.exe=folder/'audio'
  subprocess.run(['c++','-std=c++20','-Wall','-Wextra','-Werror','-I',str(ROOT/'src'),str(source),'-o',str(cls.exe)],check=True,capture_output=True,text=True)
 def run_case(self,name):subprocess.run([str(self.exe),name],check=True,capture_output=True,text=True)
 def test_current_dma_not_total_backlog(self):self.run_case('current')
 def test_two_slots_and_busy_third(self):self.run_case('full')
 def test_consumption_crosses_descriptor_and_underrun(self):self.run_case('crossing')
 def test_guest_audio_bounds_before_pcm_read(self):self.run_case('range')
 def test_invalid_dma_cannot_enter_fifo(self):self.run_case('invalid')
 def test_zero_does_not_occupy_dma_slot(self):self.run_case('zero')
 def test_fractional_output_frame_conversion_has_no_drift(self):self.run_case('conversion')
 def test_original_negative_size_regression(self):self.run_case('regression')
if __name__=='__main__':unittest.main()
