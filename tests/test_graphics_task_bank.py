"""Bounded F3DEX2 bank metadata parsing; no original code/game execution."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
SOURCE=r'''
#include "runtime/graphics_task_bank.hpp"
#include "runtime/transform_guest_layout.hpp"
#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <string>
#include <vector>
using Bytes=std::vector<uint8_t>;
template<class... Args> auto bank(const Bytes& b,uint64_t root,Args&&... args){return iss2000::graphics_task_bank(b,root,iss2000::us_transform_layout().perspective_matrices,args...);}
void word(Bytes& b,size_t p,uint32_t w){std::memcpy(b.data()+p,&w,4);}
void cmd(Bytes& b,size_t p,uint32_t w,uint32_t v=0){word(b,p,w);word(b,p+4,v);}
void projection(Bytes& b,size_t p,uint32_t a){cmd(b,p,0xDA380007,a);}
int main(int argc,char** argv){assert(argc==2);std::string mode=argv[1];Bytes b(0x800000);
 if(mode=="direct"){
  projection(b,0x1000,0x800C43A0);auto old=b;
  assert(bank(b,0x80001000)==0);
  assert(bank(b,0xFFFFFFFF80001000ull)==0);
  assert(bank(b,0xA0001000)==0);
  assert(b==old);
 }else if(mode=="nested"){
  cmd(b,0x1000,0xDE000000,0x2000);projection(b,0x1008,0xC43A0);
  cmd(b,0x2000,0xD9000000);cmd(b,0x2008,0xDF000000);
  assert(bank(b,0x1000)==0);
  projection(b,0x2008,0xC43E0);assert(bank(b,0x1000)==1);
 }else if(mode=="tail"){
  cmd(b,0x1000,0xDE010000,0x3000);projection(b,0x1008,0xC43A0);
  projection(b,0x3000,0xC43E0);assert(bank(b,0x1000)==1);
  cmd(b,0x3000,0xDF000000);assert(!bank(b,0x1000));
 }else if(mode=="segments"){
  cmd(b,0x1000,0xDB060004,0x80003000);cmd(b,0x1008,0xDB060008,0xC0000);
  cmd(b,0x1010,0xDE000000,0x01000040);projection(b,0x3040,0x020043E0);
  assert(bank(b,0x1000)==1);
  std::array<uint32_t,16> bases{};bases[3]=0x80001000;
  assert(bank(b,0x03000000,bases)==1);
  assert(!bank(b,0x03000000));
  cmd(b,0x1000,0xDB060002,0x3000);assert(!bank(b,0x1000));
 }else if(mode=="segment_zero"){
  cmd(b,0x1000,0xDB060000,0x3000);cmd(b,0x1008,0xDE010000,0x00000040);
  projection(b,0x3040,0x800C43E0);
  assert(bank(b,0x80001000)==1);
 }else if(mode=="bounds"){
  assert(!bank(b,0x100000000ull));
  assert(!bank(b,0x90001000));
  assert(!bank(b,0x1003));
  assert(!bank(b,0x800000));
  assert(!bank(b,0x7FFFFC));
  cmd(b,0x1000,0xDE000000,0xA0800000);assert(!bank(b,0x1000));
  Bytes tiny(4);assert(!bank(tiny,0));
 }else if(mode=="unsafe_context"){
  for(uint32_t op:{0x03000000u,0x04000000u,0xDD000000u,0xAA000000u,0xD6000000u}){
   cmd(b,0x1000,op);projection(b,0x1008,0xC43A0);assert(!bank(b,0x1000));
  }
  projection(b,0x1000,0x12340);projection(b,0x1008,0xC43A0);assert(!bank(b,0x1000));
  cmd(b,0x1000,0xDA380003,0x12340);projection(b,0x1008,0xC43A0);assert(bank(b,0x1000)==0);
 }else if(mode=="budget"){
  cmd(b,0x1000,0xDE010000,0x1000);assert(!bank(b,0x1000));
  for(int i=0;i<16384;++i)cmd(b,0x1000+i*8,0xE7000000);
  projection(b,0x1000+16384*8,0xC43A0);assert(!bank(b,0x1000));
  projection(b,0x1000+16383*8,0xC43E0);assert(bank(b,0x1000)==1);
 }else if(mode=="depth"){
  for(int i=0;i<33;++i)cmd(b,0x1000+i*16,0xDE000000,0x1010+i*16);
  projection(b,0x1000+33*16,0xC43A0);assert(!bank(b,0x1000));
  projection(b,0x1000+31*16,0xC43E0);assert(bank(b,0x1000)==1);
 }else return 2;
}
'''
@unittest.skipUnless(shutil.which('c++'),'Native C++ compiler required')
class GraphicsTaskBankTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.directory=Path(cls.temp.name)
        source=cls.directory/'probe.cpp';source.write_text(SOURCE);cls.binary=cls.directory/'probe'
        result=subprocess.run(['c++','-std=c++20','-O2','-Wall','-Wextra','-Werror','-I'+str(ROOT/'src'),str(source),str(ROOT/'src/runtime/graphics_task_bank.cpp'),'-o',str(cls.binary)],text=True,capture_output=True)
        if result.returncode:raise RuntimeError(result.stderr)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def run_case(self,name):subprocess.run([str(self.binary),name],check=True,capture_output=True)
    def test_first_projection_uses_canonical_physical_or_kseg_alias(self):self.run_case('direct')
    def test_nested_lists_return_and_first_projection_wins(self):self.run_case('nested')
    def test_tail_branch_does_not_return_to_parent(self):self.run_case('tail')
    def test_segment_updates_and_explicit_initial_segmented_root(self):self.run_case('segments')
    def test_segment_zero_update_affects_unaliased_list_addresses(self):self.run_case('segment_zero')
    def test_invalid_addresses_and_short_buffers_fail_closed(self):self.run_case('bounds')
    def test_unknown_projection_branch_or_ucode_context_fails_closed(self):self.run_case('unsafe_context')
    def test_cycles_and_exact_command_budget_are_bounded(self):self.run_case('budget')
    def test_nested_list_depth_is_bounded(self):self.run_case('depth')
