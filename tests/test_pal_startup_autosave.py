"""Original project work: djultra64. Genuine DataChange auto-save and UI queue boundary."""
from pathlib import Path
import subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class StartupAutosaveTests(unittest.TestCase):
 def test_original_save_create_completion_errors_and_first_entry_only(self):
  from tools.prepare_pal_auto_storage_ui import prepare
  from tools.prepare_pal_expansion_ui import derive as expansion
  folder=ROOT/'.local/pal-map-bound-01/functions';rom=ROOT/'.local/inputs/pal-en-de/rom.z64'
  addresses=[0x802B1CC8,0x802B1FDC,0x802B1D84,0x802B2144,0x802B2118,0x802B2868,0x802B2758,0x802B2780,0x802B27C8,0x802B22F8,
   0x80019A64,0x80019B04,0x80019B94,0x80019628,0x80019490,0x80019514,0x80004840,0x80004B58,0x80007BE0,0x801B576C,0x801B5704,0x802B1FD4,0x80041A44]
  sources=[next(folder.glob(f'func_{a:08X}_*.c'))for a in addresses]
  decl='extern "C" {\n'+'\n'.join('void '+p.stem+'(uint8_t*,recomp_context*);'for p in sources)+'\n}'
  dispatch='\n'.join(f'case 0x{a:X}:return {p.stem};'for a,p in zip(addresses,sources)if a not in [0x802B1CC8,0x802B1FDC,0x802B1D84])
  code=r'''#include "recomp.h"
#include <cassert>
#include <cstdlib>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iterator>
#include <vector>
#include <deque>
DECL
#include "pal_automatic_storage_ui.cpp"
#include "expansion.cpp"
struct Job{uint32_t address,delay;};std::deque<Job>jobs;unsigned status=0,closes=0,creates=0,writes=0,rendered=0,wait_frames=0;bool exists=false,write_failure=false,allocation_failure=false;std::vector<uint8_t>file;
void noop(uint8_t*,recomp_context*){}
void ui_resource(uint8_t*r,recomp_context*c){func_80007BE0_resident(r,c);}
void query(uint8_t*,recomp_context*c){c->r2=status;}
void free_bytes(uint8_t*,recomp_context*c){c->r2=32768;}
void close_scene(uint8_t*,recomp_context*){++closes;}
void schedule(uint8_t*,recomp_context*c){wait_frames+=uint32_t(c->r5);jobs.push_back({uint32_t(c->r4),uint32_t(c->r5)});}
void startup_schedule(uint8_t*r,recomp_context*c){iss2000_pal_storage_schedule(r,c,schedule);}
void job_replace(uint8_t*,recomp_context*c){jobs.push_front({uint32_t(c->r4),0});}
void sdk_allocate(uint8_t*rdram,recomp_context*ctx){++creates;if(allocation_failure){ctx->r2=4;return;}assert(!exists);assert(MEM_W(0x14,ctx->r29)==0x7a00);exists=true;file.resize(0x7a00);MEM_W(0,MEM_W(0x18,ctx->r29))=0;ctx->r2=0;}
void sdk_find(uint8_t*rdram,recomp_context*ctx){MEM_W(0,ctx->r6)=0;ctx->r2=exists?0:5;}
void checksum(uint8_t*,recomp_context*c){c->r2=123;}
void sdk_write(uint8_t*rdram,recomp_context*ctx){assert(exists&&ctx->r6==1&&ctx->r7==0);auto count=MEM_W(0x10,ctx->r29),src=MEM_W(0x14,ctx->r29);assert(count==0x7a00);++writes;if(write_failure){ctx->r2=4;return;}for(unsigned i=0;i<count;++i)file[i]=uint8_t(MEM_BU(i,static_cast<uint64_t>(static_cast<int64_t>(src))));ctx->r2=0;}
void clamp(uint8_t*,recomp_context*c){c->r2=c->r4;}
void render(uint8_t*,recomp_context*){++rendered;}
recomp_func_t*get_function(int32_t a){switch(uint32_t(a)){
DISPATCH
case 0x802B1FDC:return iss2000_pal_skip_expansion_notice;
case 0x802B1D84:return iss2000_pal_automatic_storage_update;
case 0x8000C474:return ui_resource;
case 0x80018E98:return query;
case 0x802B27F8:return free_bytes;
case 0x802B1670:return close_scene;
case 0x801B3960:return startup_schedule;
case 0x801B3D1C:return job_replace;
case 0x8005FAF0:return sdk_allocate;
case 0x80004930:return sdk_find;
case 0x80060140:return sdk_write;
case 0x80019D5C:return checksum;
case 0x80041B50:case 0x80048660:return render;
case 0x80009E90:case 0x80009EF0:return clamp;
case 0x8000C174:case 0x801B52D0:case 0x801AE594:case 0x803C36A0:case 0x803C37B8:
case 0x8000C5E4:case 0x8000CD3C:case 0x8000CC5C:case 0x803C3DDC:
case 0x801B7D90:case 0x801B7DC8:case 0x801B7E00:case 0x801B3B44:case 0x80017298:
case 0x80017978:case 0x80017D14:case 0x8001BF18:case 0x8001CB1C:
case 0x800197A4:case 0x80019F18:case 0x8001B5CC:case 0x8001C664:case 0x80018BDC:case 0x80018DE4:case 0x8001B93C:return noop;
default:std::fprintf(stderr,"unexpected original callee %08x\n",uint32_t(a));assert(false);return noop;}}
void switch_error(const char*,uint32_t,uint32_t){assert(false);}
recomp_context context(){recomp_context c{};c.r29=0xffffffff800a4000ull;c.r31=0xffffffff80123456ull;return c;}
int main(int argc,char**argv){assert(argc==3);std::ifstream f(argv[1],std::ios::binary);std::vector<uint8_t>rom{std::istreambuf_iterator<char>(f),{}},r(0x800000);assert(rom.size()==0x1000000);auto*rdram=r.data();
 for(unsigned i=0;i<0x4000;++i)MEM_B(i,gpr(S32(0x802b1070)))=rom[0x481680+i];
 for(unsigned i=0;i<0x1000;++i)MEM_B(i,gpr(S32(0x802dd400)))=rom[0x514950+i];
 MEM_W(0,gpr(S32(0x8009e02c)))=0x8013b418;MEM_B(0,gpr(S32(0x8013b429)))=1;MEM_B(0,gpr(S32(0x8013b428)))=32;
 MEM_W(0,gpr(S32(0x8012de84)))=0x800c2000;MEM_W(0,gpr(S32(0x800c1118)))=16;MEM_W(0,gpr(S32(0x800c111c)))=0;
 for(unsigned i=0;i<0x7a00;++i)MEM_B(i,gpr(S32(0x801661f0)))=(i*17+11)&255;
 auto draw=[&](uint32_t queue){auto q=gpr(S32(queue));MEM_W(0,q)=0x800c3000;MEM_W(4,q)=0x800c3040;MEM_B(0x484,q)=2;MEM_B(4,0xFFFFFFFF800C3000ull)=1;MEM_B(4,0xFFFFFFFF800C3040ull)=2;auto rc=context();rc.r4=q;const auto before=rendered;iss2000_pal_automatic_storage_render(rdram,&rc);assert(rc.r29==context().r29&&rc.r31==context().r31);return rendered-before;};
 const uint32_t first_queue=0x8013b418+0x5060;
 const unsigned scenario=unsigned(std::atoi(argv[2]));if(scenario>=9)MEM_B(0,0xFFFFFFFF8013B428ull)=0;status=(scenario==0||scenario==8||scenario==9)?1:(scenario==1||scenario>=4)?0:scenario==2?6:2;exists=scenario==1||(scenario>=4&&scenario!=8&&scenario!=9);write_failure=scenario==4;allocation_failure=scenario==8;file.resize(exists?0x7a00:0);if(exists)for(unsigned i=0;i<file.size();++i)file[i]=(i*17+11)&255;
 const auto original_file=file;auto c=context();iss2000_pal_automatic_storage_ui(r.data(),&c);assert(c.r29==context().r29&&c.r31==context().r31);
 if(scenario==0||scenario==8||scenario==9){assert(!jobs.empty()&&jobs.front().address==0x802b2780);assert(MEM_BU(0,gpr(S32(0x802b4819)))==5);}
 if(scenario==1||(scenario>=4&&scenario<8)){assert(!jobs.empty()&&jobs.front().address==0x802b22f8);assert(MEM_BU(0,gpr(S32(0x802b4819)))==1);}
 if(scenario==10){assert(jobs.empty()&&closes==1&&writes==0&&creates==0&&file==original_file);assert(draw(first_queue)==0);return 0;}
 if(scenario>=5&&scenario<8){
  const auto guest=scenario==5?0x8009e02cu:scenario==6?0x80143d6cu:0x802b4174u;
  const auto addr=gpr(S32(guest));const auto old=MEM_W(0,addr);MEM_W(0,addr)=0;
  assert(draw(first_queue)==2);MEM_W(0,addr)=old;assert(draw(first_queue)==2);
  assert(jobs.size()==1&&writes==0&&creates==0);return 0;
 }
 if(scenario<2||scenario==4||scenario==8||scenario==9)assert(iss2000_pal_storage_loading(rdram));
 if(scenario<2||scenario==4||scenario==8||scenario==9){const auto actual_state=MEM_BU(0,0xFFFFFFFF802B4819ull);
 for(unsigned st:{0u,1u,2u,4u,5u,15u}){MEM_B(0,0xFFFFFFFF802B4819ull)=st;for(unsigned n=0;n<12;++n)assert(draw(first_queue+n*0x488)==0);}
 MEM_B(0,0xFFFFFFFF802B4819ull)=actual_state;assert(draw(first_queue+12*0x488)==2);
 if(scenario==4||scenario==8)MEM_B(0,0xFFFFFFFF8012E688ull)=1;
 for(unsigned ticks=0;ticks<8&&!jobs.empty();++ticks){auto job=jobs.front();jobs.pop_front();auto jc=context();get_function(job.address)(r.data(),&jc);assert(jc.r29==context().r29);auto uc=context();iss2000_pal_automatic_storage_update(r.data(),&uc);}if(scenario==8){assert(jobs.empty()&&closes==0&&writes==0&&creates>0&&MEM_BU(0,0xFFFFFFFF802B4819ull)==3&&MEM_BU(0,0xFFFFFFFF8012E688ull)==1);assert(draw(first_queue)==2&&file.empty());}
 else if(scenario==4){assert(jobs.empty()&&closes==0&&writes==3&&MEM_BU(0,gpr(S32(0x802b4819)))==3);assert(draw(first_queue)==2);assert(file==original_file&&MEM_BU(0,0xFFFFFFFF8012E688ull)==1);}
 else {assert(jobs.empty()&&closes==1&&MEM_BU(0,gpr(S32(0x8012e167)))==0&&writes==((scenario==0||scenario==9)?2u:1u)&&exists&&file.size()==0x7a00);if(scenario==1)assert(file==original_file);}}
 else {assert(jobs.empty()&&writes==0&&creates==0&&closes==0);assert(MEM_BU(0,gpr(S32(0x802b4819)))==(scenario==2?9:3));assert(draw(first_queue)==2);}
 if(scenario<2||scenario==9)assert(wait_frames<=5);
 if(scenario<2||scenario==4||scenario==8||scenario==9)assert(!iss2000_pal_storage_loading(rdram));
 assert(MEM_HU(0,gpr(S32(0x800c2000)))==0); // No fabricated A/Start packet.
 // Re-entering the same real DataChange initializer must retain manual choices,
 // even if the first entry was an error. Career uses another original overlay.
 status=1;jobs.clear();MEM_B(0,0xFFFFFFFF8013B428ull)=32;MEM_B(0,0xFFFFFFFF8012E688ull)=0;auto second=context();iss2000_pal_automatic_storage_ui(r.data(),&second);assert(jobs.empty()&&MEM_BU(0,gpr(S32(0x802b4819)))==4);assert(draw(first_queue)==2);
 // Healthy descriptors remain visible outside ownership, and restored memory
 // cannot re-arm this already-consumed startup entry.
 for(unsigned st: {3u,6u,8u,9u,10u,11u,12u,13u,14u,16u}){MEM_B(0,0xFFFFFFFF802B4819ull)=st;assert(draw(first_queue)==2);}
}
'''.replace('DECL',decl).replace('DISPATCH',dispatch)
  with tempfile.TemporaryDirectory()as tmp:
   p=Path(tmp);prepare(rom,sources[0],p/'out');(p/'out/expansion.cpp').write_bytes(expansion(sources[1].read_bytes()));(p/'out/test.cpp').write_text(code)
   objects=[]
   for source in sources:
    obj=p/(source.stem+'.o');objects.append(str(obj));q=subprocess.run(['cc','-std=c17','-O1','-I'+str(ROOT/'.local/deps/N64Recomp/include'),'-c',str(source),'-o',str(obj)],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
   q=subprocess.run(['c++','-std=c++20','-O1','-I'+str(ROOT/'.local/deps/N64Recomp/include'),str(p/'out/test.cpp'),*objects,'-lm','-o',str(p/'check')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
   for scenario in ['0','1','2','3','4','5','6','7','8','9','10']:
    q=subprocess.run([str(p/'check'),str(rom),scenario],capture_output=True,text=True,timeout=10);self.assertEqual(q.returncode,0,'scenario'+scenario+':'+q.stderr)
 def test_render_source_is_pinned(self):
  from tools.prepare_pal_auto_storage_ui import derive_render,RENDER_ORIGINAL
  source=(ROOT/'.local/pal-map-bound-01/functions'/(RENDER_ORIGINAL+'.c')).read_bytes()
  self.assertIn(b'if(!hide_startup) LOOKUP_FUNC(0x80041B50)',derive_render(source))
  self.assertIn(b'if(!hide_startup) LOOKUP_FUNC(0x80048660)',derive_render(source))
  with self.assertRaises(ValueError):derive_render(source+b'\n')
