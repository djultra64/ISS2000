"""Original project work: djultra64. Shared allocator-model interpolation path."""
from pathlib import Path
import subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
SOURCE=r'''#include "runtime/transform_runtime.hpp"
#include "runtime/rt64_transform_bridge.hpp"
#include <cassert>
#include <cstring>
#include <string>
#include <vector>
using namespace iss2000;
using Bytes=std::vector<uint8_t>;
void word(Bytes&r,uint32_t a,uint32_t v){memcpy(r.data()+a,&v,4);}
void cmd(Bytes&r,uint32_t a,uint32_t w,uint32_t v=0){word(r,a,w);word(r,a+4,v);}
int main(int argc,char**argv){assert(argc==2);std::string mode=argv[1];auto l=us_transform_layout();TransformRuntime rt(l);Bytes r(0x800000);
 r[l.scene_bytes[0]^3]=6;r[l.scene_bytes[1]^3]=mode=="607"?7:6;
 auto build=[&](unsigned bank,uint32_t record,uint32_t matrix){word(r,l.bank_selector,bank);word(r,l.arena_cursor,l.arena_base+bank*l.arena_size);word(r,l.arena_end,l.arena_base+(bank+1)*l.arena_size);rt.observe_frame(r);rt.observe_allocation(record);word(r,record-0x80000000+0x28,0x80000000);word(r,l.arena_cursor,matrix);auto o=rt.observe_matrix_before(r,record,TransformMatrixBuilder::Unconditional25710);word(r,record-0x80000000+0x18+bank*4,matrix);word(r,record-0x80000000+0x28,0x80400000);word(r,l.arena_cursor,matrix+64);rt.observe_matrix_after(r,o);};
 const auto root=0x80148104u,child=0x80152A3Cu,m0=l.arena_base,m1=l.arena_base+l.arena_size;
 build(0,root,m0); // One actual tracked allocator identity is sufficient, no19-node whitelist.
 cmd(r,0x1000,0xDA380007,0x12340); // Original static/unknown projection cannot identify a model bank.
 cmd(r,0x1008,0xDA380003,m0);cmd(r,0x1010,0xDF000000);
 if(mode=="wrong_projection")cmd(r,0x1000,0xDA380007,l.perspective_matrices[1]);
 if(mode=="nested"){cmd(r,0x1000,0xDB060004,0x2000);cmd(r,0x1008,0xDE000000,0x01000000);cmd(r,0x1010,0xDF000000);cmd(r,0x2000,0xDA380003,m0);cmd(r,0x2008,0xDF000000);}
 if(mode=="extensions"){cmd(r,0x1000,0xE0525464,0x10000064);cmd(r,0x1008,0x64000002,0);cmd(r,0x1010,0xDA380003,m1);cmd(r,0x1018,0xDD0007FF,0x12340);cmd(r,0x1020,0xDA380003,m0);cmd(r,0x1028,0xDF000000);}
 if(mode=="mixed"){build(1,child,m1);cmd(r,0x1010,0xDA380003,m1);cmd(r,0x1018,0xDF000000);}
 if(mode=="released")rt.observe_release(root);
 if(mode=="reused"){rt.observe_release(root);rt.observe_allocation(root);}
 if(mode=="malformed"){cmd(r,0x1010,0x04000000);cmd(r,0x1018,0xDF000000);}
 if(mode=="ucode"){cmd(r,0x1000,0xE1000000,l.microcodes[1].data);cmd(r,0x1008,0xDD0007FF,l.microcodes[1].code);cmd(r,0x1010,0xDA380003,m0);cmd(r,0x1018,0xDF000000);}
 if(mode=="unknown_ucode"){cmd(r,0x1010,0xDD0007FF,0x12340);cmd(r,0x1018,0xDF000000);}
 word(r,l.bank_selector,1); // Publication must use task references, not this mutable global.
 const auto before=r;TransformTaskFingerprint fp{0x1000,l.microcodes[0].code,l.microcodes[0].data,32};rt.submit_metadata(r,1,fp);auto s=rt.consume_metadata(fp);assert(s&&r==before);
 const bool rejected=mode=="mixed"||mode=="released"||mode=="reused"||mode=="malformed"||mode=="unknown_ucode";
 if(rejected){assert(s->bank==2&&!s->lookup(m0));return 0;}
 assert(s->bank==0&&s->lookup(m0)&&"Every scene needs genuine allocator-owned model metadata");
 const auto id=s->lookup(m0)->id;
 for(bool perspective:{false,true}){auto v=select_rt64_transform(s.get(),true,m0,false,true,perspective);assert(v.kind==TransformSelection::Kind::Model&&v.id==id&&!v.vertices);assert(select_rt64_transform(s.get(),true,0x12340,false,true,perspective).kind==TransformSelection::Kind::Ignore);assert(select_rt64_transform(s.get(),true,0x12340,false,false,perspective).kind==TransformSelection::Kind::Ignore);assert(select_rt64_transform(s.get(),true,0x12340,true,true,perspective).kind==TransformSelection::Kind::Ignore);}
 rt.observe_release(root);rt.observe_allocation(root);assert(s->lookup(m0)->id==id);rt.submit_metadata(r,1,fp);auto stale=rt.consume_metadata(fp);assert(stale&&!stale->lookup(m0));
}
'''
class GlobalModelInterpolationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory();p=Path(cls.temp.name);(p/'test.cpp').write_text(SOURCE);cls.exe=p/'test'
  q=subprocess.run(['c++','-std=c++20','-O1','-Wall','-Wextra','-Werror','-Wno-maybe-uninitialized','-pthread','-I'+str(ROOT/'src'),str(p/'test.cpp'),*[str(ROOT/'src/runtime'/n) for n in ('transform_runtime.cpp','transform_tracker.cpp','graphics_task_bank.cpp','pal_menu_avatar.cpp')],'-o',str(cls.exe)],capture_output=True,text=True)
  if q.returncode:raise RuntimeError(q.stderr)
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def test_original_allocator_models_publish_in_any_scene_and_orthographic_views(self):
  for mode in ('606','607','ucode','wrong_projection','nested','extensions'):
   with self.subTest(mode=mode):
    q=subprocess.run([str(self.exe),mode],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
 def test_mixed_banks_stale_owners_and_unproven_control_flow_fail_closed(self):
  for mode in ('mixed','released','reused','malformed','unknown_ucode'):
   with self.subTest(mode=mode):
    q=subprocess.run([str(self.exe),mode],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
