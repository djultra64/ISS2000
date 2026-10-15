"""IPL television identity must be set in physical RDRAM before original boot."""
from pathlib import Path
import subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class BootEnvironmentTests(unittest.TestCase):
 def test_pal_tv_identity_and_bounded_memory(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);s=p/'test.cpp';s.write_text(r'''#include "runtime/boot_environment.hpp"
#include <array>
#include <cassert>
#include <cstring>
int main(){std::array<unsigned char,0x320>b{};b.fill(0xA5);iss2000::set_boot_tv_type(b,0);
 unsigned v=1;std::memcpy(&v,b.data()+0x300,4);assert(v==0);assert(b[0x2FF]==0xA5&&b[0x304]==0xA5);
 iss2000::set_boot_tv_type(b,1);std::memcpy(&v,b.data()+0x300,4);assert(v==1);
 try{iss2000::set_boot_tv_type({b.data(),0x303},0);return 3;}catch(const std::invalid_argument&){}
}''');r=subprocess.run(['c++','-std=c++20','-I'+str(ROOT/'src'),str(s),'-o',str(p/'test')],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
   r=subprocess.run([str(p/'test')],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
