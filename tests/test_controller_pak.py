"""Persistent Controller Pak device tests, with synthetic images and no game run.
Original project work: djultra64.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
class ControllerPakTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory(prefix='iss2000-pak-')
  cls.addClassCleanup(cls.temp.cleanup)
  folder=Path(cls.temp.name)
  source=folder/'pak.cpp'
  source.write_text(r'''
#include "runtime/controller_pak.hpp"
#include <algorithm>
#include <fstream>
#include <iostream>
#include <stdexcept>
using namespace iss2000;
void require(bool ok){if(!ok)throw std::runtime_error("Controller Pak contract failed");}
PakImage load(const std::filesystem::path& p){PakImage b{};std::ifstream f(p,std::ios::binary);f.read(reinterpret_cast<char*>(b.data()),b.size());require(bool(f));return b;}
int main(int,char** argv){try{
 std::filesystem::path dir=argv[2];std::string test=argv[1];
 if(test=="format"){
  std::array<uint8_t,24> identity{};identity[0]=42;auto im=formatted_controller_pak(identity);
  for(unsigned off:{0x20u,0x60u,0x80u,0xC0u}){
   require(std::equal(im.begin()+0x20,im.begin()+0x40,im.begin()+off));
   require(im[off+0x18]==0&&im[off+0x19]==1&&im[off+0x1A]==1);
   unsigned sum=0,inv=0;for(unsigned i=0;i<28;i+=2){unsigned v=(im[off+i]<<8)|im[off+i+1];sum+=v;inv+=(~v)&0xFFFF;}
   require(unsigned((im[off+28]<<8)|im[off+29])==(sum&0xFFFF));require(unsigned((im[off+30]<<8)|im[off+31])==(inv&0xFFFF));
  }
  for(unsigned off:{0x100u,0x200u}){require(im[off+1]==0x71);for(unsigned page=5;page<128;++page)require(im[off+page*2]==0&&im[off+page*2+1]==3);}
  require(std::all_of(im.begin()+0x300,im.begin()+0x500,[](auto v){return v==0;}));
 }else if(test=="persist"){
  PakBlock block{};for(unsigned i=0;i<32;++i)block[i]=uint8_t(i*7);
  {ControllerPakStore s(dir);s.set_accessory(0,PakAccessory::Controller);require(s.write_block(0,40,block,false)==0);require(s.plugged_mask()==1);}
  {ControllerPakStore s(dir);s.set_accessory(0,PakAccessory::Controller);PakBlock read{};require(s.read_block(0,40,read)==0&&read==block);auto disk=load(s.image_path(0));require(std::equal(block.begin(),block.end(),disk.begin()+1280));}
 }else if(test=="ports"){
  ControllerPakStore s(dir);for(unsigned n=0;n<4;++n){s.set_accessory(n,PakAccessory::Controller);PakBlock b{};b[0]=uint8_t(n+1);require(s.write_block(n,50,b,false)==0);}
  require(s.plugged_mask()==15);for(unsigned n=0;n<4;++n){PakBlock b{};require(s.read_block(n,50,b)==0&&b[0]==n+1);}
 }else if(test=="policy"){
  ControllerPakStore s(dir);PakBlock b{};require(s.status(0)==1);require(s.read_block(0,40,b)==1);
  s.set_accessory(0,PakAccessory::Rumble);require(s.status(0)==0);require(s.read_block(0,40,b)==11);
  s.set_accessory(0,PakAccessory::Controller);require(s.status(0)==2);require(s.status(0)==0);
  require(s.read_block(4,40,b)==5);require(s.read_block(0,1024,b)==5);
  auto before=load(s.image_path(0));b.fill(0xAB);require(s.write_block(0,1,b,false)==0);require(load(s.image_path(0))==before);
  require(s.write_block(0,1,b,true)==0);require(load(s.image_path(0))!=before);
  b.fill(0);require(s.write_block(0,0x400,b,false)==0);b.fill(2);require(s.write_block(0,0x400,b,false)==11);
 }else if(test=="lock"){
  ControllerPakStore first(dir);bool failed=false;try{ControllerPakStore second(dir);}catch(const std::exception&){failed=true;}require(failed);
 }else if(test=="corrupt"){
  std::filesystem::create_directories(dir);PakImage original{};original.fill(0xA5);auto file=dir/"controller-pak-1.mpk";
  {std::ofstream f(file,std::ios::binary);f.write(reinterpret_cast<char*>(original.data()),original.size());}
  {ControllerPakStore s(dir);require(load(file)==original);s.set_accessory(0,PakAccessory::Controller);PakBlock b{};require(s.write_block(0,50,b,false)==0);}
  bool preserved=false;for(auto& e:std::filesystem::directory_iterator(dir))if(e.path().filename().string().find("preserved-")!=std::string::npos&&load(e.path())==original)preserved=true;require(preserved);
 }else if(test=="failure"){
  ControllerPakStore s(dir);s.set_accessory(0,PakAccessory::Controller);auto before=load(s.image_path(0));
  std::filesystem::create_directory(s.image_path(0).string()+".bak");PakBlock b{};b.fill(9);require(s.write_block(0,50,b,false)==4);require(load(s.image_path(0))==before);require(!s.last_error().empty());
  PakBlock read{};require(s.read_block(0,50,read)==0);require(std::equal(read.begin(),read.end(),before.begin()+1600));
 }else if(test.rfind("external_",0)==0){
  ControllerPakStore s(dir);s.set_accessory(0,PakAccessory::Controller);PakBlock cached{};require(s.read_block(0,50,cached)==0);
  auto path=s.image_path(0);auto original=load(path);auto changed=original;
  if(test=="external_deleted")std::filesystem::remove(path);
  else if(test=="external_truncated"){std::ofstream file(path,std::ios::binary|std::ios::trunc);file<<"external";}
  else if(test=="external_changed"){changed[2000]^=0x7F;std::ofstream file(path,std::ios::binary|std::ios::trunc);file.write(reinterpret_cast<char*>(changed.data()),changed.size());}
  else if(test=="external_symlink"){std::filesystem::rename(path,dir/"external-target.mpk");std::filesystem::create_symlink(dir/"external-target.mpk",path);}
  require(s.write_block(0,50,cached,false)==4);PakBlock after{};require(s.read_block(0,50,after)==0&&after==cached);
  if(test=="external_deleted")require(!std::filesystem::exists(path));
  else if(test=="external_truncated")require(std::filesystem::file_size(path)==8);
  else if(test=="external_changed")require(load(path)==changed);
  else require(std::filesystem::is_symlink(path)&&load(dir/"external-target.mpk")==original);
 }else if(test=="short"){
  std::filesystem::create_directories(dir);auto path=dir/"controller-pak-1.mpk";{std::ofstream f(path);f<<"original malformed pak";}
  bool failed=false;try{ControllerPakStore store(dir);}catch(const std::exception&){failed=true;}require(failed);require(std::filesystem::file_size(path)==22);
 }else return 2;
 return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
''')
  cls.exe=folder/'pak'
  subprocess.run(['c++','-std=c++20','-Wall','-Wextra','-Werror','-pthread','-I',str(ROOT/'src'),str(source),str(ROOT/'src/runtime/controller_pak.cpp'),'-o',str(cls.exe)],check=True,capture_output=True,text=True)
 def run_case(self,name):
  with tempfile.TemporaryDirectory(prefix='iss2000-pak-image-') as directory:
   subprocess.run([str(self.exe),name,directory],check=True,capture_output=True,text=True)
 def test_sdk_format_id_inode_directory(self):self.run_case('format')
 def test_canonical_bytes_persist_across_restart(self):self.run_case('persist')
 def test_four_ports_are_independent(self):self.run_case('ports')
 def test_absent_changed_wrong_device_bounds_and_force(self):self.run_case('policy')
 def test_exclusive_process_lock(self):self.run_case('lock')
 def test_corrupt_existing_image_preserved_before_sdk_changes(self):self.run_case('corrupt')
 def test_publish_error_keeps_memory_and_original_disk(self):self.run_case('failure')
 def test_identical_write_rejects_deleted_image(self):self.run_case('external_deleted')
 def test_identical_write_rejects_truncated_image(self):self.run_case('external_truncated')
 def test_identical_write_rejects_changed_image(self):self.run_case('external_changed')
 def test_identical_write_rejects_symlink_and_preserves_target(self):self.run_case('external_symlink')
 def test_wrong_size_never_reformatted(self):self.run_case('short')
if __name__=='__main__':unittest.main()
