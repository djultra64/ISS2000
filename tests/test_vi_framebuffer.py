"""Original project work: djultra64. Exact host VI identity, no game execution."""
from pathlib import Path
import subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class ViFramebufferTests(unittest.TestCase):
 def test_authoritative_base_history_conflicts_bounds_and_rates(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);s=p/'test.cpp';s.write_text(r'''#include "runtime/vi_framebuffer.hpp"
#include <cassert>
#include <thread>
int main(){
 iss2000::ViFramebufferRegistry r;
 assert(!r.resolve(0x27D899,320,2));
 r.record(0x27D899,320,0x13012,0x27D380);
 assert(r.resolve(0x27D899,320,2)==0x27D380);
 for(unsigned b:{0x32D000u,0x307800u,0x2E2000u})r.record(b+0x519,320,0x13012,b);
 assert(r.resolve(0x32D519,320,2)==0x32D000);
 assert(r.resolve(0x27D899,320,2)==0x27D380); // copied historical VI
 assert(!r.resolve(0x27D899,640,2));assert(!r.resolve(0x27D899,320,3));
 r.record(0x27D899,320,0x13012,0x27D000);assert(!r.resolve(0x27D899,320,2));
 r.record(0x27D899,320,0x13012,0x27D380);assert(!r.resolve(0x27D899,320,2)); // conflict never revalidates
 r.record(0x80800000,320,2,0x1000);r.record(0x1800,0,2,0x1000);
 r.record(0x1800,320,1,0x1000);r.record(0x1800,320,2,0x1801);
 assert(!r.resolve(0x1800,320,2));
 std::thread reader([&]{for(int n=0;n<10000;++n)assert(r.resolve(0x32D519,320,2)==0x32D000);});
 for(int n=0;n<10000;++n){r.record(0x307D19,320,0x13012,0x307800);}
 reader.join();
 assert(iss2000_vi_original_rate(625)==50);assert(iss2000_vi_original_rate(624)==50);
 assert(iss2000_vi_original_rate(525)==60);assert(iss2000_vi_original_rate(524)==60);
 assert(iss2000_vi_original_rate(0)==60);
 iss2000_record_vi_framebuffer(0x32D519,320,0x13012,0x32D000);
 assert(iss2000_resolve_vi_framebuffer(0x32D519,320,2)==0x32D000);
 assert(iss2000_resolve_vi_framebuffer(0x1000,320,2)==UINT32_MAX);
}''')
   result=subprocess.run(['c++','-std=c++20','-pthread','-Wall','-Wextra','-Werror','-I'+str(ROOT/'src'),str(s),str(ROOT/'src/runtime/vi_framebuffer.cpp'),'-o',str(p/'test')],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
   result=subprocess.run([str(p/'test')],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
