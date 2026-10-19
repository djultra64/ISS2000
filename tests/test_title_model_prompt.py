"""Original work: djultra64. CPU guards for the original PAL title model."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
MINIZ=ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz'
MINIZ_BUILD=ROOT/'.local/runtime-deps-build/librecomp/miniz'

@unittest.skipUnless(shutil.which('c++') and (MINIZ_BUILD/'libminiz.a').is_file(),'Compiler and pinned miniz required')
class TitleModelPromptTests(unittest.TestCase):
 def test_real_title_model_requires_complete_owned_draw_before_transaction(self):
  snapshot=ROOT/'.local/title-acceptance-01/steady-title11.rdram'
  if not snapshot.is_file():self.skipTest('Private original PAL steady title snapshot required')
  self.assertTrue((ROOT/'src/runtime/prompt_title_model.cpp').is_file(),'Commercial title model adapter is not implemented')
  source=r'''
#include "runtime/prompt_title_model.hpp"
#include <fstream>
#include <iostream>
#include <source_location>
#include <stdexcept>
#include <vector>
using namespace iss2000;
void check(bool b,const std::source_location p=std::source_location::current()){if(!b)throw std::runtime_error("line "+std::to_string(p.line()));}
int main(int argc,char**argv){try{
 check(argc==2);std::vector<uint8_t> ram(0x800000);std::ifstream f(argv[1],std::ios::binary);f.read(reinterpret_cast<char*>(ram.data()),ram.size());check(bool(f));
 auto byte=[&](uint32_t p){return ram[(p&0x7fffff)^3];};
 auto word=[&](uint32_t p){return uint32_t(byte(p))<<24|uint32_t(byte(p+1))<<16|uint32_t(byte(p+2))<<8|byte(p+3);};
 auto put=[&](uint32_t p,uint32_t v){for(unsigned n=0;n<4;++n)ram[((p+n)&0x7fffff)^3]=uint8_t(v>>(24-8*n));};
 const auto original=ram;const auto start=word(0x8009e0c8),model=word(0x80085428);
 // The actual snapshot precedes its first model draw. Construct only a bounded
 // command fixture; this is a CPU ownership test, not evidence of a real draw.
 check(!plan_pal_title_prompt(ram,start,start,"Menu"));
 for(unsigned n=0;n<20;++n){put(start+n*16,0xda380003);put(start+n*16+4,0x800c0000+n*64);put(start+n*16+8,0xde000000);put(start+n*16+12,model+0x500+n*0xb0);}
 const auto end=start+20*16;put(0x8009e0c8,end);const auto ready=ram;
 auto plan=plan_pal_title_prompt(ram,start,end,"Menu");check(bool(plan));check(ram==ready);
 check(plan->line().text=="PRESS Menu"&&plan->line().x==130&&plan->line().y==164);
 // Font drawing appends commands first; suppress touches no prior GPU task,
 // model, glyph asset, frame state, matrices or appended font command.
 put(end,0xe7000000);put(end+4,0);put(0x8009e0c8,end+8);const auto with_font=ram;
 check(suppress_pal_title_prompt(ram,*plan));
 for(unsigned n=0;n<20;++n)check(word(start+n*16+8)==0&&word(start+n*16+12)==0);
 for(size_t n=0;n<ram.size();++n){bool owned=false;for(unsigned j=0;j<20;++j)if(n>=((start&0x7fffff)+j*16+8)&&n<((start&0x7fffff)+j*16+16))owned=true;if(!owned)check(ram[n]==with_font[n]);}
 check(!suppress_pal_title_prompt(ram,*plan));
 // Missing, duplicate or changed calls reject the entire transaction.
 for(unsigned variant=0;variant<8;++variant){ram=ready;
  if(variant==0)put(start+19*16+8,0);
  if(variant==1)put(start+19*16+12,model+0x500);
  if(variant==2)ram[((model+0x20)&0x7fffff)^3]^=1;
  if(variant==3)ram[(0x352800+3)^3]^=1;
  if(variant==4)put(0x800be960,0x80086fb4);
  if(variant==5)put(0x800be944,3);
  if(variant==6)ram[(0x87460+7)^3]^=1;
  if(variant==7)put(0x800bea1c,0x80087480);
  const auto foreign=ram;check(!plan_pal_title_prompt(ram,start,end,"Menu")&&ram==foreign);
 }
 ram=ready;plan=plan_pal_title_prompt(ram,start,end,"Menu");check(bool(plan));put(start+7*16+12,model+0x500);auto foreign=ram;check(!suppress_pal_title_prompt(ram,*plan)&&ram==foreign);
 // Original47598 switches to phase2/count100 after accepting Start;4777C
 // decrements through zero to -11 before its final scene switch.
 for(const auto name:{"Menu","Options","+","Enter"})for(int tick=100;tick>=-11;--tick){
  ram=ready;put(0x800be944,2);put(0x800be948,uint32_t(tick));
  auto transition=plan_pal_title_prompt(ram,start,end,name);check(bool(transition));
  check(transition->line().text==std::string("PRESS ")+(std::string(name)=="+"?"Plus":name));
  check(suppress_pal_title_prompt(ram,*transition));
 }
 ram=ready;check(plan_pal_title_prompt(ram,start,end,"+")->line().text=="PRESS Plus");
 check(plan_pal_title_prompt(ram,start,end,"Options")->line().text=="PRESS Options");
 check(plan_pal_title_prompt(ram,start,end,"×")->line().text=="PRESS Cross");
 check(!plan_pal_title_prompt(ram,start+1,end,"Menu"));check(!plan_pal_title_prompt(ram,start,end+8,"Menu"));
 check(!plan_pal_title_prompt(ram,start,end,""));check(!plan_pal_title_prompt(ram,start,end,"Bad/Control"));
 ram=original;check(!plan_pal_title_prompt(ram,start,start,"Menu"));
 return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
'''
  self.run_snapshot(source,snapshot)
 def test_completed_original_title_draw_matches_all_twenty_parts(self):
  snapshot=ROOT/'.local/title-acceptance-01/completed-title11.rdram'
  if not snapshot.is_file():self.skipTest('Private completed original PAL title draw snapshot required')
  import struct
  raw=snapshot.read_bytes()
  word=lambda p:struct.unpack_from('<I',raw,p&0x7fffff)[0]
  canonical=lambda p,n:bytes(raw[((p+j)&0x7fffff)^3] for j in range(n))
  def matrix(p):
   whole=struct.unpack('>16h',canonical(p,32));fraction=struct.unpack('>16H',canonical(p+32,32))
   return [[whole[i*4+j]+fraction[i*4+j]/65536 for j in range(4)] for i in range(4)]
  def multiply(v,m):return [sum(v[i]*m[i][j] for i in range(4)) for j in range(4)]
  projection=matrix(0xc1b00);xs=[];ys=[]
  for call in range(0xe19b0,0xe1dd9,0x38):
   self.assertEqual(word(call),0xde000000)
   model=matrix(word(call-4));vertices=word(word(call+4)+0x9c)
   for n in range(4):
    x,y,z=struct.unpack('>hhh',canonical(vertices+n*16,6))
    q=multiply(multiply([x,y,z,1],model),projection)
    xs.append(160+160*q[0]/q[3]);ys.append(120-120*q[1]/q[3])
  self.assertAlmostEqual(min(xs),89.7224,places=3)
  self.assertAlmostEqual(max(xs),229.4257,places=3)
  self.assertLessEqual(min(ys),164);self.assertGreaterEqual(max(ys),176)
  source=r'''
#include "runtime/prompt_title_model.hpp"
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>
using namespace iss2000;
void check(bool b){if(!b)throw std::runtime_error("completed original title draw guard failed");}
int main(int argc,char**argv){try{
 check(argc==2);std::vector<uint8_t> ram(0x800000);std::ifstream f(argv[1],std::ios::binary);f.read(reinterpret_cast<char*>(ram.data()),ram.size());check(bool(f));
 auto put=[&](uint32_t p,uint32_t v){for(unsigned n=0;n<4;++n)ram[((p+n)&0x7fffff)^3]=uint8_t(v>>(24-8*n));};
 // The breakpoint is at the NEXT frame's callback after cursor reset. Restore
 // only the cursor to the known end of this completed original 3D pass;
 // no model/texture/Gfx command bytes are synthesized for this regression.
 constexpr uint32_t begin=0x800e18a8,end=0x800e1e10;put(0x8009e0c8,end);
 const auto original=ram;auto plan=plan_pal_title_prompt(ram,0x800e0388,end,"Options");check(bool(plan)&&ram==original);
 // Whole-frame post00BB8 integration scans the current arena, including all
 // original earlier passes. It must find the same20 calls as the narrow span.
 check(bool(plan_pal_title_prompt(ram,begin,end,"Options")));
 check(plan->line().text=="PRESS Options"&&plan->line().y==164);
 check(suppress_pal_title_prompt(ram,*plan));unsigned changes=0;
 for(size_t n=0;n<ram.size();++n){
  bool owned=false;for(unsigned j=0;j<20;++j)if(n>=0xe19b0+j*0x38&&n<0xe19b8+j*0x38)owned=true;
  if(!owned)check(ram[n]==original[n]);
  if(ram[n]!=original[n])++changes;
 }
 check(changes>0);ram=original;
 // A foreign model parent and high-resolution framebuffer are not eligible.
 put(0x8014d82c+0x44,0x8014d82c);check(!plan_pal_title_prompt(ram,begin,end,"Menu"));
 ram=original;ram[(0x13b418+0x12)^3]=1;check(!plan_pal_title_prompt(ram,begin,end,"Menu"));
 return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
'''
  self.run_snapshot(source,snapshot)
 def run_snapshot(self,source,snapshot):
  with tempfile.TemporaryDirectory() as directory:
   folder=Path(directory);path=folder/'probe.cpp';path.write_text(source);exe=folder/'probe'
   result=subprocess.run(['c++','-std=c++20','-O1','-Wall','-Wextra','-Werror','-I'+str(ROOT/'src'),'-I'+str(MINIZ),'-I'+str(MINIZ_BUILD),str(path),str(ROOT/'src/runtime/prompt_title_model.cpp'),str(ROOT/'src/runtime/rom_image.cpp'),str(MINIZ_BUILD/'libminiz.a'),'-o',str(exe)],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
   result=subprocess.run([str(exe),str(snapshot)],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
