"""Bounded PAL clock correction; original leaves run only on synthetic RAM."""
from pathlib import Path
import json
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
HARNESS=r'''
#include "runtime/ntsc_match_clock.hpp"
#include <array>
#include <cassert>
#include <cmath>
#include <cstring>
#include <span>
#include <string>
#include <vector>
using Bytes=std::vector<uint8_t>;
constexpr std::array<uint32_t,2> REM={0x8012DDD6,0x8012DDDA},SUB={0x8012DDD8,0x8012DDDC};
void put(Bytes& b,uint32_t a,uint16_t v){std::memcpy(b.data()+((a&0x7FFFFF)^2),&v,2);}
uint16_t get(const Bytes& b,uint32_t a){uint16_t v;std::memcpy(&v,b.data()+((a&0x7FFFFF)^2),2);return v;}
Bytes initialized(){Bytes b(0x800000,0xCD);for(int i=0;i<2;++i){put(b,REM[i],300);put(b,SUB[i],25);}return b;}
void only_subcounters_changed(const Bytes& old,const Bytes& b){for(size_t x=0;x<b.size();++x){bool allowed=false;for(auto a:SUB){auto p=(a&0x7FFFFF)^2;allowed|=x>=p&&x<p+2;}if(!allowed)assert(old[x]==b[x]);}}
int main(int argc,char** argv){assert(argc==2);std::string mode=argv[1];
 if(mode=="carry"){
  auto b=initialized();iss2000::NtscMatchClock timer;assert(timer.reset_after_init(b));
  for(int cycle=1;cycle<=24;++cycle){
   for(auto a:SUB){put(b,a,0);}auto before=timer.before_tick(b);
   for(int i=0;i<2;++i){put(b,REM[i],get(b,REM[i])-1);put(b,SUB[i],25);}auto original=b;
   assert(timer.after_tick(b,before));
   for(auto a:SUB){assert(get(b,a)==(cycle%6==5?24:25));}only_subcounters_changed(original,b);
  }
 }else if(mode=="gated"){
  auto b=initialized();iss2000::NtscMatchClock timer;assert(timer.reset_after_init(b));
  for(int cycle=1;cycle<=5;++cycle){
   put(b,SUB[0],0);put(b,SUB[1],0);auto before=timer.before_tick(b);
   put(b,REM[0],get(b,REM[0])-1);put(b,SUB[0],25);
   assert(timer.after_tick(b,before));assert(get(b,SUB[1])==0);
  }
  assert(get(b,SUB[0])==24);
  for(int cycle=1;cycle<=4;++cycle){
   auto before=timer.before_tick(b);auto paused=b;assert(timer.after_tick(b,before));assert(b==paused);
   put(b,SUB[1],0);before=timer.before_tick(b);put(b,REM[1],get(b,REM[1])-1);put(b,SUB[1],25);
   assert(timer.after_tick(b,before));assert(get(b,SUB[1])==25);
  }
  put(b,SUB[1],0);auto before=timer.before_tick(b);put(b,REM[1],get(b,REM[1])-1);put(b,SUB[1],25);
  assert(timer.after_tick(b,before));assert(get(b,SUB[1])==24);
 }else if(mode=="end_reset"){
  auto b=initialized();iss2000::NtscMatchClock timer;assert(timer.reset_after_init(b));
  put(b,REM[0],1);put(b,SUB[0],0);auto before=timer.before_tick(b);put(b,REM[0],0);auto ended=b;
  assert(timer.after_tick(b,before));assert(b==ended);
  auto stale=before;assert(!timer.after_tick(b,stale));assert(b==ended);
  b=initialized();assert(timer.reset_after_init(b));
  put(b,SUB[0],0);before=timer.before_tick(b);put(b,REM[0],299);put(b,SUB[0],25);
  assert(timer.after_tick(b,before));assert(get(b,SUB[0])==25);
 }else if(mode=="invalid"){
  iss2000::NtscMatchClock timer;Bytes small(10,0xCD);auto old=small;
  assert(!timer.reset_after_init(small));auto invalid=timer.before_tick(small);assert(!timer.after_tick(small,invalid));assert(small==old);
  auto b=initialized();put(b,SUB[1],30);old=b;assert(!timer.reset_after_init(b));assert(b==old);
  b=initialized();assert(timer.reset_after_init(b));auto before=timer.before_tick(b);put(b,SUB[1],26);old=b;
  assert(!timer.after_tick(b,before));assert(b==old);
 }else return 2;
}
'''

ORIGINAL_HARNESS=r'''
#include "runtime/ntsc_match_clock.hpp"
#include "recomp.h"
#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstring>
#include <iostream>
#include <vector>
ORIGINAL_INCLUDES
using Bytes=std::vector<uint8_t>;
void put(Bytes& b,uint32_t a,uint16_t v){std::memcpy(b.data()+((a&0x7FFFFF)^2),&v,2);}
uint16_t get(const Bytes& b,uint32_t a){uint16_t v;std::memcpy(&v,b.data()+((a&0x7FFFFF)^2),2);return v;}
std::vector<int> run(bool pal,bool corrected){
 Bytes b(0x800000,0);recomp_context ctx{};
 const uint32_t table=pal?0x80097F1C:0x8009A90C,option=pal?0x8012E696:0x80131076;
 const uint32_t remaining=pal?0x8012DDD6:0x801307B6,elapsed=pal?0x8012DDDE:0x801307BE;
 const uint16_t options[]={180,300,420,2700,60,180,180,900};for(int i=0;i<8;++i)put(b,table+i*2,options[i]);
 b[(option&0x7FFFFF)^3]=3;
 if(pal)func_801DB94C_overlay_287ab0_801db100(b.data(),&ctx);else func_801DD9EC_overlay_289ba0_801dd1a0(b.data(),&ctx);
 assert(get(b,remaining)==2700);iss2000::NtscMatchClock timer;if(corrected)assert(timer.reset_after_init(b));
 std::vector<int> result;uint16_t old=get(b,remaining);
 for(int tick=1;get(b,remaining);++tick){
  auto before=timer.before_tick(b);
  if(pal)func_801DC14C_overlay_287ab0_801db100(b.data(),&ctx);else func_801DE1EC_overlay_289ba0_801dd1a0(b.data(),&ctx);
  if(corrected)assert(timer.after_tick(b,before));
  const auto now=get(b,remaining);assert(get(b,pal?0x8012DDDA:0x801307BA)==now);if(now!=old){assert(now+1==old);result.push_back(tick);old=now;}
  assert(tick<100000);
 }
 assert(get(b,elapsed)==2700&&result.size()==2700);return result;
}
int main(){
 auto us=run(false,false),pal=run(true,false),corrected=run(true,true);
 for(const auto rates:std::array<std::array<int,2>,2>{{{30,25},{60,50}}}){
 const double us_rate=rates[0],pal_rate=rates[1];
 double uncorrected_drift=0,corrected_error=0;
 for(size_t i=0;i<us.size();++i){
  uncorrected_drift=std::max(uncorrected_drift,std::abs(double(pal[i])/pal_rate-double(us[i])/us_rate));
  corrected_error=std::max(corrected_error,std::abs(double(corrected[i])/pal_rate-double(us[i])/us_rate));
  assert(std::abs(double(corrected[i])/pal_rate-double(us[i])/us_rate)<1./pal_rate);
  if((i+1)%6==0)assert(std::abs(double(corrected[i])/pal_rate-double(us[i])/us_rate)<1.e-9);
 }
 assert(uncorrected_drift>8.9&&corrected_error<1./pal_rate);
 assert(us.back()==83700&&pal.back()==70200&&corrected.back()==69750);
 std::cout<<"original PAL drift "<<uncorrected_drift<<"s; corrected max error "<<corrected_error<<"s at "<<pal_rate<<"/"<<us_rate<<" updates/s\n";
 }
}
'''

@unittest.skipUnless(shutil.which('c++'),'Native C++ compiler required')
class NtscMatchClockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.root=Path(cls.temp.name)
        (cls.root/'test.cpp').write_text(HARNESS);cls.binary=cls.root/'test'
        command=['c++','-std=c++20','-O2','-Wall','-Wextra','-Werror','-I'+str(ROOT/'src'),str(cls.root/'test.cpp'),str(ROOT/'src/runtime/ntsc_match_clock.cpp'),'-o',str(cls.binary)]
        built=subprocess.run(command,text=True,capture_output=True)
        if built.returncode:raise RuntimeError(built.stderr)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def run_case(self,case):subprocess.run([str(self.binary),case],check=True,capture_output=True)
    def test_six_clock_intervals_total_155_updates_with_only_subcounter_writes(self):self.run_case('carry')
    def test_independent_gated_counter_and_pauses_preserve_carry(self):self.run_case('gated')
    def test_zero_end_stale_snapshot_and_new_match_reset(self):self.run_case('end_reset')
    def test_invalid_memory_or_uninitialized_clock_has_no_writes(self):self.run_case('invalid')
    def test_original_clock_leaves_match_ntsc_pace_without_accumulating_drift(self):
        us=ROOT/'.local/runtime-map-04/functions';pal=ROOT/'.local/pal-map-bound-01/functions';header=ROOT/'.local/deps/N64Recomp/include'
        paths=[us/'func_801DD9EC_overlay_289ba0_801dd1a0.c',us/'func_801DE1EC_overlay_289ba0_801dd1a0.c',pal/'func_801DB94C_overlay_287ab0_801db100.c',pal/'func_801DC14C_overlay_287ab0_801db100.c']
        if not all(p.is_file() for p in [*paths,header/'recomp.h']):self.skipTest('Private pinned original clock translations required')
        for path in paths:self.assertNotIn('LOOKUP_FUNC',path.read_text(),'clock fixture must stay a leaf with no host or gameplay calls')
        source=self.root/'original.cpp';source.write_text(ORIGINAL_HARNESS.replace('ORIGINAL_INCLUDES','\n'.join('#include '+json.dumps(str(p)) for p in paths)))
        binary=self.root/'original';built=subprocess.run(['c++','-std=c++20','-O2','-I'+str(ROOT/'src'),'-I'+str(header),str(source),str(ROOT/'src/runtime/ntsc_match_clock.cpp'),'-o',str(binary)],text=True,capture_output=True)
        self.assertEqual(built.returncode,0,built.stderr)
        result=subprocess.run([str(binary)],text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
