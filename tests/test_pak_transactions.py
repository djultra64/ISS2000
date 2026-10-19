"""Original project work: djultra64. Complete saves publish atomically once."""
from pathlib import Path
import subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
CODE=r'''
#include "runtime/controller_pak.hpp"
#include <cassert>
#include <fstream>
#include <thread>
#include <sys/stat.h>
#include <cerrno>
using namespace iss2000;
unsigned syncs=0;bool reject_sync=false;
extern "C" int __real_fsync(int);
extern "C" int __wrap_fsync(int fd){++syncs;if(reject_sync){errno=EIO;return -1;}return __real_fsync(fd);}
PakImage load(const std::filesystem::path&p){PakImage out{};std::ifstream f(p,std::ios::binary);f.read((char*)out.data(),out.size());assert(f);return out;}
int main(int argc,char**argv){assert(argc==2);ControllerPakStore s(argv[1]);for(unsigned p=0;p<4;++p)s.set_accessory(p,PakAccessory::Controller);
 const auto initial=load(s.image_path(0));syncs=0;assert(s.begin_file_write(0)==0);assert(s.begin_file_write(0)==4);
 for(unsigned n=0;n<976;++n){PakBlock b{};b.fill(n%254+1);assert(s.write_block(0,n+32,b,false)==0);}
 assert(load(s.image_path(0))==initial&&syncs==0);PakBlock b{};assert(s.read_block(0,50,b)==0&&b[0]==19);
 std::thread foreign([&]{PakBlock r{};assert(s.read_block(0,50,r)==4);assert(s.write_block(0,50,r,false)==4);assert(s.finish_file_write(0,true)==4);});foreign.join();
 assert(s.finish_file_write(0,true)==0&&syncs==4);const auto saved=load(s.image_path(0));assert(saved!=initial);auto backup=s.image_path(0);backup+=".bak";assert(load(backup)==initial);
 // Failed SDK write rolls back every staged block without publishing anything.
 syncs=0;assert(s.begin_file_write(0)==0);b.fill(7);assert(s.write_block(0,50,b,false)==0);assert(s.finish_file_write(0,false)==0);assert(load(s.image_path(0))==saved&&syncs==0);assert(s.read_block(0,50,b)==0&&b[0]==19);
 // No-op save still verifies the external image, and needs no publication.
 assert(s.begin_file_write(0)==0);assert(s.finish_file_write(0,true)==0&&syncs==0);
 // Ports remain independent and a staged save cannot overwrite external edits.
 assert(s.begin_file_write(0)==0);b.fill(42);assert(s.write_block(0,50,b,false)==0);assert(s.write_block(1,50,b,false)==0);
 auto changed=saved;changed[3000]^=1;{std::ofstream f(s.image_path(0),std::ios::binary);f.write((char*)changed.data(),changed.size());}
 assert(s.finish_file_write(0,true)==4&&load(s.image_path(0))==changed);assert(s.read_block(0,50,b)==0&&b[0]==19);
 {std::ofstream f(s.image_path(0),std::ios::binary);f.write((char*)saved.data(),saved.size());}
 assert(s.begin_file_write(0)==0);b.fill(33);assert(s.write_block(0,50,b,false)==0);reject_sync=true;assert(s.finish_file_write(0,true)==4);reject_sync=false;assert(load(s.image_path(0))==saved);assert(s.read_block(0,50,b)==0&&b[0]==19);
 assert(s.finish_file_write(0,true)==5);assert(s.begin_file_write(4)==5);
}
'''
class PakTransactionTests(unittest.TestCase):
 def test_full_save_is_one_durable_commit_with_rollback_and_real_errors(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'test.cpp').write_text(CODE)
   q=subprocess.run(['c++','-std=c++20','-O1','-pthread','-Wl,--wrap=fsync','-I'+str(ROOT/'src'),str(p/'test.cpp'),str(ROOT/'src/runtime/controller_pak.cpp'),'-o',str(p/'test')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
   q=subprocess.run([str(p/'test'),str(p/'saves')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
