"""Synthetic PI boundary contracts; no ROM or game execution.

Original project work: djultra64.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


class PiTransferTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='iss2000-pi-boundaries-')
        cls.addClassCleanup(cls.temp.cleanup)
        root=Path(cls.temp.name)
        source=root/'pi.cpp'
        source.write_text(r'''
#include "runtime/pi_transfer.hpp"
#include <iostream>
#include <stdexcept>
#include <string>
using namespace iss2000;
void require(bool condition){if(!condition)throw std::runtime_error("PI contract failed");}
template<class Fn> void rejects(Fn fn){bool failed=false;try{fn();}catch(const std::invalid_argument&){failed=true;}require(failed);}
int main(int argc,char** argv){try{
 std::string test=argv[1];
 if(test=="rom"){
  auto t=validate_pi_transfer(0xB0000000,0x1000,0x80000400,0x100000,0);
  require(t.region==PiRegion::Rom&&t.physical==0x10001000&&t.offset==0x1000&&t.ram==0x80000400&&t.size==0x100000&&t.direction==0);
  auto physical=validate_pi_transfer(0xB0000000,0,0x400,8,0);require(physical.ram==0x80000400);
 }else if(test=="sram"){
  for(unsigned d:{0u,1u}){auto t=validate_pi_transfer(0xA8000000,0x7FFF,0x807FFFFF,1,d);require(t.region==PiRegion::Sram&&t.offset==0x7FFF&&t.direction==d);}
 }else if(test=="bounds"){
  rejects([]{validate_pi_transfer(0xB0000000,0xFFFFFF,0x80000400,2,0);});
  rejects([]{validate_pi_transfer(0xA8000000,0x7FFF,0x80000400,2,0);});
  rejects([]{validate_pi_transfer(0xA8000000,0,0x807FFFFF,2,0);});
  rejects([]{validate_pi_transfer(0xB0000000,0x1000,0x80000400,0xFFFFFFFF,0);});
 }else if(test=="policy"){
  rejects([]{validate_pi_transfer(0xB0000000,0,0x80000400,8,1);});
  rejects([]{validate_pi_transfer(0xB0000000,0,0x80000400,8,2);});
  rejects([]{validate_pi_transfer(0x06000000,0,0x80000400,8,0);});
  rejects([]{validate_pi_transfer(0xA8000000,0x8000,0x80000400,1,0);});
 }else if(test=="aliases"){
  require(normalize_pi_pointer(0xA0001000,24)==0x80001000);
  require(normalize_pi_pointer(0xFFFFFFFF80001000ull,24)==0x80001000);
  require(normalize_pi_pointer(0xFFFFFFFFA0001000ull,24)==0x80001000);
  auto t=validate_pi_transfer(0xB0000000,0,0xA0000400,8,0);require(t.ram==0x80000400);
 }else if(test=="structure_bounds"){
  require(normalize_pi_pointer(0x80800000,100,true)==0x80800000);
  require(normalize_pi_pointer(0x80800F9C,100,true)==0x80800F9C);
  rejects([]{normalize_pi_pointer(0x80800F9D,100,true);});
  rejects([]{normalize_pi_pointer(0x80800000,1);});
  rejects([]{normalize_pi_pointer(0x1000,24);});
  rejects([]{normalize_pi_pointer(0x80001001,24);});
  rejects([]{normalize_pi_pointer(0x180001000ull,24);});
  rejects([]{normalize_pi_pointer(0xFFFFFFFF00001000ull,24);});
  rejects([]{normalize_pi_pointer(0xC0001000,24);});
 }else if(test=="zero"){
  auto r=validate_pi_transfer(0xB0000000,0x1000000,0x80800000,0,0);require(r.region==PiRegion::Rom&&r.size==0);
  auto s=validate_pi_transfer(0xA8000000,0x8000,0x80800000,0,1);require(s.region==PiRegion::Sram&&s.size==0);
  rejects([]{validate_pi_transfer(0xB0000000,0x1000001,0x80000000,0,0);});
 }else if(test=="or_semantics"){
  auto t=validate_pi_transfer(0xA8000010,0x10,0x80000400,8,0);require(t.offset==0x10);
 }else if(test=="rom_alignment"){
  rejects([]{validate_pi_transfer(0xB0000000,1,0x80000400,8,0);});
  rejects([]{validate_pi_transfer(0xB0000000,0,0x80000404,8,0);});
 }else return 2;
 std::cout<<"passed";return 0;
}catch(const std::exception& e){std::cerr<<e.what();return 1;}}
''')
        cls.binary=root/'pi-tests'
        subprocess.run([shutil.which('c++') or 'c++','-std=c++20','-Wall','-Wextra','-I'+str(ROOT/'src'),str(source),'-o',str(cls.binary)],check=True,capture_output=True,text=True)

    def check_contract(self,name):
        result=subprocess.run([str(self.binary),name],capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout,'passed')

    def test_rom_read(self):self.check_contract('rom')
    def test_sram_read_and_write(self):self.check_contract('sram')
    def test_transfer_bounds_and_overflow(self):self.check_contract('bounds')
    def test_direction_device_and_rom_write_policy(self):self.check_contract('policy')
    def test_kseg_aliases(self):self.check_contract('aliases')
    def test_structure_pointer_bounds_and_sign_extension(self):self.check_contract('structure_bounds')
    def test_zero_length_preserves_completion_contract(self):self.check_contract('zero')
    def test_handle_and_device_addresses_are_ored(self):self.check_contract('or_semantics')
    def test_upstream_rom_dma_alignment(self):self.check_contract('rom_alignment')
