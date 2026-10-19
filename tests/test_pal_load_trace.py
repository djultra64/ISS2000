"""Diagnostic-only original continuations, no game/window execution. Work by djultra64."""
from pathlib import Path
import hashlib,json,re,shutil,struct,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
CODE=r'''#include "pal_load_trace.hpp"
#include <cassert>
#include <cstring>
#include <fstream>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>
using namespace iss2000;
DECLS
extern "C" recomp_func_t*get_function(int32_t pc){switch(uint32_t(pc)){LOOKUP default:throw std::runtime_error("Unexpected original CPU call");}}
extern "C" void do_break(uint32_t){throw std::runtime_error("Original break");}
extern "C" void switch_error(const char*,uint32_t,uint32_t){throw std::runtime_error("Original switch");}
FILE*logfile=nullptr;recomp_func_t*target=nullptr;unsigned calls=0;bool throwing=false;
std::string contents(){if(!logfile)return {};auto at=ftell(logfile);rewind(logfile);std::string s;char b[256];while(auto n=fread(b,1,sizeof b,logfile))s.append(b,n);fseek(logfile,at,SEEK_SET);return s;}
void observed(uint8_t*r,recomp_context*c){++calls;if(logfile){auto text=contents();assert(text.find(" enter ")!=std::string::npos&&text.find(" return ")==std::string::npos);}target(r,c);if(throwing)throw std::runtime_error("Original failure");}
void sw(std::vector<uint8_t>&r,uint32_t a,uint32_t v){memcpy(r.data()+(a&0x7fffff),&v,4);}uint32_t word(const std::vector<uint8_t>&r,uint32_t a){uint32_t v;memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
int main(int,char**argv){std::ifstream in(argv[1],std::ios::binary);std::vector<uint8_t>base((std::istreambuf_iterator<char>(in)),{});assert(base.size()==0x800000);const std::string mode=argv[2];
 const bool ready=mode=="ready";target=ready?func_802C53A4_overlay_40c7a0_802c3490:func_802BE3E4_overlay_401910_802b8500;
 auto actual=base,expected=base;const auto node=0x801e70e4u;sw(actual,0x801ed420,node);sw(expected,0x801ed420,node);
 for(unsigned p=0;p<4;++p){actual[(0x2d21e4+p)^3]=expected[(0x2d21e4+p)^3]=p%3;}
 recomp_context a{},e{};a.r4=e.r4=uint64_t(int64_t(int32_t(node)));a.r29=e.r29=uint64_t(int64_t(int32_t(0x800a3f80)));a.r31=e.r31=0xffffffff80123450ull;a.f_odd=&a.f0.u32h;e.f_odd=&e.f0.u32h;
 target(expected.data(),&e);
 throwing=mode=="throw";if(mode!="disabled"){logfile=tmpfile();assert(logfile);}bool threw=false;
 try{trace_pal_load_transition(ready?PalLoadTracePoint::ControllerReady:PalLoadTracePoint::TrainingBegin,actual.data(),&a,observed,logfile);}catch(const std::runtime_error&error){assert(std::string(error.what())=="Original failure");threw=true;}
 assert(calls==1&&threw==throwing&&actual==expected);e.f_odd=&a.f0.u32h;assert(memcmp(&a,&e,sizeof a)==0);
 if(logfile){auto text=contents();assert(text.find(ready?"ControllerReady":"BeginTraining")!=std::string::npos);assert(text.find(ready?"802C53A4":"802BE3E4")!=std::string::npos);assert(text.find(throwing?" throw ":" return ")!=std::string::npos);assert(text.find(" enter ")==text.rfind(" enter "));fclose(logfile);}
 if(!ready)assert(word(actual,node+0xc)==0x8000e4f8&&actual[0xa4fa0^3]==1);return 0;
}
'''
class PalLoadTraceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  g=ROOT/'.local/pal-map-bound-01/functions';h=ROOT/'.local/deps/N64Recomp/include';cls.snapshot=ROOT/'.local/ui-redesign-01/training-prep49-completed.rdram';rom=ROOT/'.local/inputs/pal-en-de/rom.z64'
  if not cls.snapshot.exists()or not rom.exists()or not shutil.which('c++'):raise unittest.SkipTest('Private PAL CPU fixture required')
  image=rom.read_bytes();assert hashlib.sha256(image).hexdigest()=='6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf'
  ram=cls.snapshot.read_bytes();sections=json.loads((g.parent/'section-analysis.json').read_text())
  # Bind diagnostic entrypoints to actual settled prep RAM, not merely an
  # unrelated overlay that reuses the same guest address.
  for pc,suffix in [(0x802be154,'overlay_401910_802b8500'),(0x802be1b8,'overlay_401910_802b8500'),(0x802be29c,'overlay_401910_802b8500'),(0x802be3e4,'overlay_401910_802b8500'),(0x802c53a4,'overlay_40c7a0_802c3490')]:
   section=next(v for v in sections if v['name']==suffix);f=next(v for v in section['functions']if v['vram']==pc);offset=section['rom']+pc-section['vram']
   assert image[offset:offset+f['size']]==bytes(ram[((pc+n)&0x7fffff)^3]for n in range(f['size']))
  assert struct.unpack_from('<I',ram,0x2c3350)[0]==0x802be1b8
  # Exact resident + live support/prep owners; no cross-overlay address aliases.
  suffixes=['resident','overlay_2dee70_801ad820','overlay_401910_802b8500','overlay_40c7a0_802c3490'];paths={int(p.stem.split('_')[1],16):p for suffix in suffixes for p in g.glob('func_*_'+suffix+'.c')}
  selected={};pending=[0x802be3e4,0x802c53a4]
  while pending:
   pc=pending.pop()
   if pc in selected:continue
   p=paths[pc];selected[pc]=p;pending.extend(int(x,16)for x in re.findall(r'LOOKUP_FUNC\(0x([0-9A-F]+)\)',p.read_text()))
  cls.temp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.temp.cleanup);d=Path(cls.temp.name);cls.binary=d/'test'
  source=CODE.replace('DECLS','\n'.join('extern "C" void '+p.stem+'(uint8_t*,recomp_context*);'for p in selected.values())).replace('LOOKUP','\n'.join(f'case 0x{pc:x}:return {p.stem};'for pc,p in selected.items()))
  (d/'test.cpp').write_text(source);(d/'original.c').write_text('\n'.join('#include '+json.dumps(str(p))for p in selected.values()))
  q=subprocess.run(['cc','-O1','-I'+str(h),'-c',str(d/'original.c'),'-o',str(d/'original.o')],capture_output=True,text=True);assert q.returncode==0,q.stderr
  q=subprocess.run(['c++','-std=c++20','-O1','-I'+str(ROOT/'src/runtime'),'-I'+str(h),str(d/'test.cpp'),str(d/'original.o'),'-o',str(cls.binary)],capture_output=True,text=True);assert q.returncode==0,q.stderr
 def case(self,mode):
  q=subprocess.run([str(self.binary),str(self.snapshot),mode],capture_output=True,text=True,timeout=8);self.assertEqual(q.returncode,0,q.stderr)
 def test_genuine_begin_training_continuation_runs_once_with_identical_context_and_RAM(self):self.case('begin')
 def test_all_four_genuine_controller_profiles_preserve_original_ready_outputs(self):self.case('ready')
 def test_original_exception_is_reported_then_propagated_without_state_changes(self):self.case('throw')
 def test_unavailable_log_does_not_suppress_original_execution(self):self.case('disabled')
if __name__=='__main__':unittest.main()
