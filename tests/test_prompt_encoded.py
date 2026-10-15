"""Original project work: djultra64. Bounded encoded-menu text over synthetic RAM."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
MINIZ=ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz'
MINIZ_BUILD=ROOT/'.local/runtime-deps-build/librecomp/miniz'
SOURCE=r'''
#include "runtime/prompt_encoded.hpp"
#include "runtime/rom_image.hpp"
#include <algorithm>
#include <cassert>
#include <cstring>
#include <string>
#include <vector>
using namespace iss2000;
using Bytes=std::vector<uint8_t>;
void word(Bytes& r,size_t p,uint32_t value){std::memcpy(r.data()+p,&value,4);}
void put(Bytes& r,size_t p,const Bytes& data){for(size_t n=0;n<data.size();++n)r[(p+n)^3]=data[n];}
Bytes get(const Bytes& r,size_t p,size_t size){Bytes result(size);for(size_t n=0;n<size;++n)result[n]=r[(p+n)^3];return result;}
int main(int argc,char** argv){
 assert(argc==2);const std::string mode=argv[1];
 Bytes ram(0x800000,0xA5),original(40,0);
 // Prefix includes color, two-byte glyph and newline; suffix includes newline/end.
 const Bytes prefix{0xFF,0x03,0x0B,0xF6,0x20,0xFF,0x10,0};
 std::copy(prefix.begin(),prefix.end(),original.begin());
 original[8]=0x0B;original[32]=0xFF;original[33]=0x10;
 original[38]=0xFF;original[39]=0x11;
 put(ram,0x10000,original);word(ram,0x2000+0x14,0x80010000);ram[(0x2000+5)^3]=0;
 EncodedPromptLayout layout{{{0x10000,40,rom_detail::sha256_hex(original),{{8,24,0,"Press ","."}}}}};
 EncodedPromptGuard guard(layout);layout.messages[0].source_offset=0x60000;
 const std::array<std::string_view,3> labels{"B","A","Options"};
 if(mode=="disabled"){
  auto before=ram;assert(!prepare_encoded_menu_prompt(ram,0x80002000,labels));assert(ram==before);
  configure_encoded_menu_prompts(EncodedPromptLayout{{{0x10000,40,rom_detail::sha256_hex(original),{{8,24,0,"Press ","."}}}}});
  assert(prepare_encoded_menu_prompt(ram,0x80002000,labels));return 0;
 }
 if(mode=="control_operand"){
  EncodedPromptLayout unsafe{{{0x10000,40,rom_detail::sha256_hex(original),{{1,1,0,"",""}}}}};
  EncodedPromptGuard bad(unsafe);auto before=ram;assert(!bad.prepare(ram,0x80002000,labels));assert(ram==before);return 0;
 }
 if(mode=="reject"){
  for(auto ptr:{0x807FFFF0ull,0x1000080002000ull,0x1000ull}){
   auto before=ram;assert(!guard.prepare(ram,ptr,labels));assert(ram==before);
  }
  ram[(0x2000+5)^3]=1;auto before=ram;assert(!guard.prepare(ram,0x80002000,labels));assert(ram==before);
  ram[(0x2000+5)^3]=0;word(ram,0x2000+0x14,0x80010001);before=ram;
  assert(!guard.prepare(ram,0x80002000,labels));assert(ram==before);
  word(ram,0x2000+0x14,0x80010000);ram[0x10000^3]^=1;before=ram;
  assert(!guard.prepare(ram,0x80002000,labels));assert(ram==before);return 0;
 }
 auto before=ram;assert(guard.prepare(ram,0xFFFFFFFF80002000ull,labels));
 const Bytes wanted{0x1A,0x36,0x29,0x37,0x37,0,0x0C,0x3F}; // Press B.
 auto actual=get(ram,0x10000,40);
 assert(std::equal(wanted.begin(),wanted.end(),actual.begin()+8));
 assert(std::all_of(actual.begin()+16,actual.begin()+32,[](uint8_t b){return b==0;}));
 for(size_t n=0;n<ram.size();++n)if(n<0x10008||n>=0x10020)assert(ram[n]==before[n]);
 auto patched=ram;assert(guard.prepare(ram,0x80002000,labels));assert(ram==patched);
 if(mode=="reload"){
  put(ram,0x10000,original);assert(guard.prepare(ram,0x80002000,labels));assert(ram==patched);
  ram[0x10000^3]=0x55;auto foreign=ram;assert(!guard.prepare(ram,0x80002000,labels));assert(ram==foreign);
  return 0;
 }
 if(mode=="remap"){
  auto names=labels;names[0]="Cross";assert(guard.prepare(ram,0x80002000,names));
  const Bytes cross{0x1A,0x36,0x29,0x37,0x37,0,0x0D,0x36,0x33,0x37,0x37,0x3F};
  actual=get(ram,0x10008,24);assert(std::equal(cross.begin(),cross.end(),actual.begin()));
  names[0]="+";assert(guard.prepare(ram,0x80002000,names));
  const Bytes plus{0x1A,0x36,0x29,0x37,0x37,0,0x1A,0x30,0x39,0x37,0x3F};
  actual=get(ram,0x10008,24);assert(std::equal(plus.begin(),plus.end(),actual.begin()));
  names[0]="Unbound";assert(guard.prepare(ram,0x80002000,names));
  const Bytes unbound{0x0D,0x33,0x32,0x38,0x36,0x33,0x30,0,0x39,0x32,0x26,0x33,0x39,0x32,0x28};
  actual=get(ram,0x10008,24);assert(std::equal(unbound.begin(),unbound.end(),actual.begin()));
 }
 if(mode=="unsupported"){
  auto names=labels;names[0]="Label exceeding available original capacity";
  assert(!guard.prepare(ram,0x80002000,names));assert(ram==before);
  assert(guard.prepare(ram,0x80002000,labels));names[0]="\xFF";
  assert(!guard.prepare(ram,0x80002000,names));assert(ram==before);
 }
}
'''
@unittest.skipUnless(shutil.which('c++') and (MINIZ/'miniz.h').is_file() and (MINIZ_BUILD/'libminiz.a').is_file(),'Pinned miniz and compiler required')
class EncodedPromptTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.temp.cleanup)
  p=Path(cls.temp.name);(p/'test.cpp').write_text(SOURCE);cls.binary=p/'test'
  result=subprocess.run(['c++','-std=c++20','-Wall','-Wextra','-Werror','-pthread','-I'+str(ROOT/'src'),'-I'+str(MINIZ),'-I'+str(MINIZ_BUILD),str(p/'test.cpp'),str(ROOT/'src/runtime/prompt_encoded.cpp'),str(ROOT/'src/runtime/rom_image.cpp'),str(MINIZ_BUILD/'libminiz.a'),'-o',str(cls.binary)],capture_output=True,text=True)
  if result.returncode:raise AssertionError(result.stderr)
 def run_case(self,name):
  result=subprocess.run([str(self.binary),name],capture_output=True,text=True)
  self.assertEqual(result.returncode,0,result.stderr)
 def test_changes_only_selected_instruction_and_preserves_original_control_bytes(self):self.run_case('controls')
 def test_revision_source_type_address_and_whole_message_hash_fail_closed(self):self.run_case('reject')
 def test_original_reload_and_foreign_replacement_preserve_ownership(self):self.run_case('reload')
 def test_remapping_and_family_changes_update_the_physical_name(self):self.run_case('remap')
 def test_unsupported_or_oversized_labels_restore_only_owned_bytes(self):self.run_case('unsupported')
 def test_edit_cannot_claim_second_byte_of_an_original_control(self):self.run_case('control_operand')
 def test_global_hook_requires_explicit_configuration(self):self.run_case('disabled')
