"""Original project work: djultra64. Synthetic RDRAM only; no GUI execution."""
from pathlib import Path
import subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class PromptTextTests(unittest.TestCase):
 def test_bounded_identity_lifecycle_and_original_font_labels(self):
  source=r'''#include "runtime/prompt_text.hpp"
#include <vector>
#include <string>
#include <cassert>
int main(){
 std::vector<uint8_t> ram(0x800000,0xAB);constexpr unsigned p=0x9D490;
 const std::string original="PRESS START";
 auto put=[&](std::string s){for(unsigned n=0;n<12;++n)ram[(p+n)^3]=n<s.size()?s[n]:0;};
 auto get=[&]{std::string s;for(unsigned n=0;n<12&&ram[(p+n)^3];++n)s+=char(ram[(p+n)^3]);return s;};
 put(original);assert(!iss2000::prepare_title_prompt(ram.data(),1,0x8009D490,"Enter"));assert(get()==original);
 iss2000::prompt_detail::TitleTextGuard guard(iss2000::us_title_prompt_layout());
 assert(!guard.prepare(ram.data(),0,0x8009D490,"Enter"));assert(get()==original);
 assert(!guard.prepare(ram.data(),1,0x12348009D490ULL,"Enter"));assert(get()==original);
 assert(guard.prepare(ram.data(),1,0xFFFFFFFF8009D490ULL,"Enter"));assert(get()=="PRESS ENTER");
 assert(guard.prepare(ram.data(),1,0x8009D490,"Options"));assert(get()=="OPTIONS");
 assert(guard.prepare(ram.data(),1,0x8009D490,"+"));assert(get()=="PRESS PLUS");
 assert(guard.prepare(ram.data(),1,0x8009D490,"Cross"));assert(get()=="PRESS CROSS");
 assert(!guard.prepare(ram.data(),1,0x8009D490,"Unknown unsupported label"));assert(get()==original);
 assert(ram[(p-1)^3]==0xAB&&ram[(p+12)^3]==0xAB);
 put("OTHER TEXT");assert(!guard.prepare(ram.data(),1,0x8009D490,"Menu"));assert(get()=="OTHER TEXT");
 put(original);assert(guard.prepare(ram.data(),1,0x8009D490,"Menu"));assert(get()=="PRESS MENU");
 std::vector<uint8_t> other(0x800000);assert(!guard.prepare(other.data(),1,0x8009D490,"Menu"));assert(get()=="PRESS MENU");
 assert(!guard.prepare(nullptr,1,0x8009D490,"Menu"));
 auto layout=iss2000::pal_en_title_prompt_layout();
 iss2000::prompt_detail::TitleTextGuard pal(layout);layout.text_offset=0x9D490;
 constexpr unsigned pp=0x9AB98;
 for(unsigned n=0;n<12;++n)ram[(pp+n)^3]=n<original.size()?original[n]:0;
 auto stable=ram;assert(!pal.prepare(ram.data(),1,0x8009D490,"+"));assert(ram==stable);
 assert(pal.prepare(ram.data(),1,0x8009AB98,"+"));
 const std::string plus="PRESS PLUS";
 for(unsigned n=0;n<12;++n)assert(ram[(pp+n)^3]==(n<plus.size()?plus[n]:0));
 for(size_t n=0;n<ram.size();++n)if(n<pp||n>=pp+12)assert(ram[n]==stable[n]);
 iss2000::configure_title_prompt(iss2000::pal_en_title_prompt_layout());
 assert(!iss2000::prepare_title_prompt(ram.data(),1,0x8009D490,"Enter"));
 // A separately constructed guard cannot claim another guard's patched bytes.
 assert(!iss2000::prepare_title_prompt(ram.data(),1,0x8009AB98,"Enter"));
 for(unsigned n=0;n<12;++n)ram[(pp+n)^3]=n<original.size()?original[n]:0;
 assert(iss2000::prepare_title_prompt(ram.data(),1,0x8009AB98,"Options"));

}
'''
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'test.cpp').write_text(source)
   subprocess.run(['c++','-std=c++20','-I'+str(ROOT/'src'),str(p/'test.cpp'),str(ROOT/'src/runtime/prompt_text.cpp'),'-o',str(p/'test')],check=True,capture_output=True)
   result=subprocess.run([str(p/'test')],text=True,capture_output=True)
   self.assertEqual(result.returncode,0,result.stderr)
