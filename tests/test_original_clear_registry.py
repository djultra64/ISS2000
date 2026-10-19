"""Original work: djultra64. CPU-only original PAL zero-fill/registry chain."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=ROOT/'.local/pal-map-bound-01/functions/func_8005CD50_resident.c'
INCLUDE=ROOT/'.local/deps/N64Recomp-runtime-lookup/include'

@unittest.skipUnless(shutil.which('cc') and shutil.which('c++') and ORIGINAL.is_file() and (INCLUDE/'recomp.h').is_file(), 'Private original PAL CPU translation and pinned compiler headers required')
class OriginalClearRegistryTests(unittest.TestCase):
    def test_real_original_clear_and_production_observer_preserve_exact_write_bounds(self):
        source=(ROOT/'src/runtime/native_game.cpp').read_text()
        match=re.search(r'void clear_original_guest_memory\(uint8_t\* ram,recomp_context\* ctx\)\{.*?\n\}',source,re.S)
        self.assertIsNotNone(match,'Production original clear observer must be present')
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);harness=folder/'main.cpp';obj=folder/'original.o';exe=folder/'check'
            harness.write_text(r'''
#include "recomp.h"
#include "runtime/section_registry.hpp"
#include "runtime/pi_transfer.hpp"
#include <cassert>
#include <cstring>
#include <vector>
extern "C" void func_8005CD50_resident(uint8_t*,recomp_context*);
namespace iss2000 {
using Function=void(*)(uint8_t*,recomp_context*);
SectionRegistry<Function> registry;
unsigned calls=0;
void runtime_message(const char*) {assert(false);}
void run_original_guest(uint32_t pc,uint8_t* ram,recomp_context* ctx){
 assert(pc==0x8005CD50);++calls;func_8005CD50_resident(ram,ctx);
}
'''+match[0]+r'''
}
void a(uint8_t*,recomp_context*){} void b(uint8_t*,recomp_context*){}
int main(){
 using namespace iss2000;
 registry.add({"original",0x1000,0x80100000,0x100,0x80,
              {{0,a,0x20,{{0x90,0xA0}}},{0x40,b,0x20}}});
 std::vector<uint8_t> ram(0x800000);
 for(unsigned alignment=0;alignment<4;++alignment){
  for(int32_t length:{-1,0,1,3,4,11,12,31,32,33}){
   registry.dma_completed(0x1000,0x80100000,0x100);
   std::fill(ram.begin()+0x100000,ram.begin()+0x100100,0xAB);
   recomp_context context{};const auto start=0x8010001Cu+alignment;
   context.r4=(uint64_t)(int64_t)(int32_t)start;context.r5=(uint64_t)(int64_t)length;
   const auto before_calls=calls;clear_original_guest_memory(ram.data(),&context);
   assert(calls==before_calls+1);
   for(unsigned n=0;n<0x100;++n){
    const bool written=length>0 && n>=start-0x80100000u && n<start-0x80100000u+unsigned(length);
    assert(ram[(0x100000u+n)^3]==(written?0:0xAB));
   }
   assert(registry.find(0x80100000)==(length>0?nullptr:a));
   assert(registry.find(0x80100040)==b);
  }
 }
 // The same actual helper clears a table byte: complete code alone no longer
 // enables the compiled switch, and restoring the exact byte enables it again.
 registry.dma_completed(0x1000,0x80100000,0x100);
 recomp_context context{};context.r4=(uint64_t)(int64_t)(int32_t)0x80100097;context.r5=1;
 clear_original_guest_memory(ram.data(),&context);
 assert(registry.find(0x80100000)==nullptr&&registry.find(0x80100040)==b);
 registry.dma_completed(0x1097,0x80100097,1);assert(registry.find(0x80100000)==a);
}
''')
            for command in [
                ['cc','-O1','-I'+str(INCLUDE),'-c',str(ORIGINAL),'-o',str(obj)],
                ['c++','-std=c++20','-O1','-I'+str(INCLUDE),'-I'+str(ROOT/'src'),str(harness),str(obj),'-o',str(exe)],
                [str(exe)],
            ]:
                result=subprocess.run(command,capture_output=True,text=True)
                self.assertEqual(result.returncode,0,result.stderr)
