"""Original Data Change initialization probes storage without an insertion modal.
Original project work: djultra64. CPU original-code fixture; no game acceptance.
"""
from pathlib import Path
import json,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class AutomaticStorageUiTests(unittest.TestCase):
 def test_only_insert_notice_enters_genuine_probe_without_button_input(self):
  from tools.prepare_pal_auto_storage_ui import derive
  folder=ROOT/'.local/pal-map-bound-01/functions'
  original=folder/'func_802B1CC8_overlay_481680_802b1070.c'
  probe=folder/'func_802B2144_overlay_481680_802b1070.c'
  clear=folder/'func_802B2118_overlay_481680_802b1070.c'
  code=r'''#include "recomp.h"
#include <vector>
#include <cstdio>
#include <cassert>
#include <cstring>
ORIGINALS
DERIVED
unsigned state,mode,storage_status,queries;std::vector<uint32_t> calls;bool reference;
void noop(uint8_t*,recomp_context*){}
void selector(uint8_t*r,recomp_context*){r[0x2b4819^3]=state;r[0x12e167^3]=5;}
void query(uint8_t*,recomp_context*c){++queries;c->r2=storage_status;}
recomp_func_t*get_function(int32_t a){calls.push_back(uint32_t(a));switch(uint32_t(a)){
 case0x802b1fdc:return selector;
 case0x802b2144:return func_802B2144_overlay_481680_802b1070;
 case0x80018e98:return query;
 case0x802b2118:return func_802B2118_overlay_481680_802b1070;
 default:return noop;}}
void switch_error(const char*,uint32_t,uint32_t){assert(false);}
int main(){for(mode=0;mode<2;++mode)for(state=0;state<17;++state)for(storage_status=0;storage_status<8;++storage_status){
 std::vector<uint8_t> r(0x800000);r[0x12e688^3]=mode;recomp_context c{};c.r29=0xffffffff800a4000ull;calls.clear();queries=0;
 iss2000_pal_automatic_storage_ui(r.data(),&c);
 const bool normal_probe=mode==0&&state!=14&&state!=16;
 const unsigned expected_queries=unsigned(normal_probe)+unsigned((normal_probe&&state!=15&&(storage_status==2||storage_status==7))||(!normal_probe&&state==15));
 if(queries!=expected_queries)std::fprintf(stderr,"mode%u state%u status%u got%u expected%u\n",mode,state,storage_status,queries,expected_queries);assert(queries==expected_queries);
 if((mode&&state!=15)||state==14||state==16)assert(r[0x2b4819^3]==state);
 // Every automatic outcome must be produced by the real original SDK-result
 // interpreter, not a forced success, invented input or direct scene change.
 if(normal_probe){auto expected=std::vector<uint8_t>(0x800000);expected[0x2b4819^3]=state;expected[0x12e167^3]=5;recomp_context d{};d.r29=0xffffffff800a4000ull;func_802B2144_overlay_481680_802b1070(expected.data(),&d);if(expected[0x12e167^3]==5&&expected[0x2b4819^3]==15)func_802B2144_overlay_481680_802b1070(expected.data(),&d);assert(expected[0x2b4819^3]==r[0x2b4819^3]);}
 assert(r[0x12de84^3]==0); // No original input packet fabricated.
}}
'''.replace('case0x','case 0x')
  with tempfile.TemporaryDirectory()as tmp:
   p=Path(tmp);(p/'derived.cpp').write_bytes(derive(original.read_bytes()));code=code.replace('ORIGINALS','extern "C" {\n'+'\n'.join('void '+v.stem+'(uint8_t*,recomp_context*);'for v in (original,probe,clear))+'\n}').replace('DERIVED','#include '+json.dumps(str(p/'derived.cpp')));(p/'test.cpp').write_text(code)
   objects=[]
   for v in (original,probe,clear):
    obj=p/(v.stem+'.o');objects.append(str(obj))
    r=subprocess.run(['cc','-std=c17','-O1','-I'+str(ROOT/'.local/deps/N64Recomp/include'),'-c',str(v),'-o',str(obj)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
   r=subprocess.run(['c++','-std=c++20','-O1','-I'+str(ROOT/'.local/deps/N64Recomp/include'),str(p/'test.cpp'),*objects,'-lm','-o',str(p/'test')],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
   r=subprocess.run([str(p/'test')],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
   # Restore the original insertion wait as a real negative control.
   (p/'derived.cpp').write_bytes(derive(original.read_bytes()).replace(b'if (false)',b'if (ctx->r3 == ctx->r2)',1).replace(b'MEM_BU(0, 0xFFFFFFFF802B4819ull) == 15',b'false'))
   r=subprocess.run(['c++','-std=c++20','-O1','-I'+str(ROOT/'.local/deps/N64Recomp/include'),str(p/'test.cpp'),*objects,'-lm','-o',str(p/'old')],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
   r=subprocess.run([str(p/'old')],capture_output=True,text=True);self.assertNotEqual(r.returncode,0,'Original insertion wait must fail automatic-probe assertion')

 def test_real_selector_probe_retry_callback_and_guarded_wording(self):
  from tools.prepare_pal_auto_storage_ui import prepare,wording,WORDING
  from tools.prepare_pal_expansion_ui import derive as expansion
  folder=ROOT/'.local/pal-map-bound-01/functions';rom=ROOT/'.local/inputs/pal-en-de/rom.z64'
  addresses=[0x802B1CC8,0x802B1FDC,0x802B1D84,0x802B2144,0x802B2118,0x802B2868,
             0x80018E98,0x80018EE0,0x80018F4C,0x80004A04,0x80004780,0x800049A8,
             0x80004930,0x801B576C,0x801B5704,0x802B1FD4,0x803CAAF0]
  sources=[next(folder.glob(f'func_{a:08X}_*.c'))for a in addresses]
  decl='extern "C" {\n'+'\n'.join('void '+p.stem+'(uint8_t*,recomp_context*);'for p in sources)+'\n}'
  dispatch='\n'.join(f'case 0x{a:X}:return {p.stem};'for a,p in zip(addresses,sources)if a!=0x802B1FDC)
  # Exact SDK boundaries are a test model. All original selection, retries,
  # directory enumeration, status decoding and input mapping execute unchanged.
  code=r'''#include "recomp.h"
#include <cassert>
#include <cstdio>
#include <fstream>
#include <iterator>
#include <vector>
DECL
#include "pal_automatic_storage_ui.cpp"
#include "expansion.cpp"
unsigned sdk_error=0,init_error=0,attempts=0,close_calls=0,save_calls=0;bool require_no_insert=false;
void noop(uint8_t*,recomp_context*){}
void scene(uint8_t* r,recomp_context*){if(require_no_insert)assert(r[0x2b4819^3]!=15);}
void close_scene(uint8_t*,recomp_context*){++close_calls;}
void save_scene(uint8_t*,recomp_context*){++save_calls;}
void sdk_num_files(uint8_t*rdram,recomp_context*ctx){++attempts;ctx->r2=sdk_error;if(!sdk_error){MEM_W(0,ctx->r5)=16;MEM_W(0,ctx->r6)=16;}}
void sdk_init(uint8_t*,recomp_context*ctx){ctx->r2=init_error;}
void sdk_empty_state(uint8_t*,recomp_context*ctx){ctx->r2=5;}
void sdk_find_empty(uint8_t*,recomp_context*ctx){ctx->r2=5;}
void clamp(uint8_t*,recomp_context*ctx){ctx->r2=ctx->r4;}
recomp_func_t*get_function(int32_t a){switch(uint32_t(a)){
DISPATCH
case 0x802B1FDC:return iss2000_pal_skip_expansion_notice;
case 0x80060CD0:return sdk_num_files;
case 0x80060DD0:case 0x8005F8A4:case 0x8005F560:return sdk_init;
case 0x80060580:return sdk_empty_state;case 0x80060720:return sdk_find_empty;
case 0x802B1670:return close_scene;case 0x801B3960:return save_scene;
case 0x803C3DDC:return scene;case 0x80009E90:case 0x80009EF0:return clamp;
case 0x8000C174:case 0x8000C474:case 0x801B52D0:case 0x801AE594:
case 0x803C36A0:case 0x803C37B8:case 0x8000C5E4:case 0x8000CD3C:
case 0x8000CC5C:case 0x802B27F8:case 0x801B7E00:case 0x801B7D90:return noop;
default:std::fprintf(stderr,"unexpected original callee %08x\n",uint32_t(a));assert(false);return noop;}}
void switch_error(const char*,uint32_t,uint32_t){assert(false);}
std::vector<uint8_t> rom;
std::vector<uint8_t> ram(){std::vector<uint8_t>r(0x800000);for(unsigned i=0;i<0x4000;++i)r[(0x2b1070+i)^3]=rom[0x481680+i];for(unsigned i=0;i<0x1000;++i)r[(0x2dd400+i)^3]=rom[0x514950+i];r[0x13b429^3]=1;r[0x12e167^3]=5;return r;}
void writeword(std::vector<uint8_t>&r,unsigned p,unsigned v){std::memcpy(r.data()+p,&v,4);}
recomp_context context(){recomp_context c{};c.r29=0xffffffff800a4000ull;c.r31=0xffffffff80123456ull;return c;}
int main(int argc,char**argv){std::ifstream f(argv[1],std::ios::binary);rom={std::istreambuf_iterator<char>(f),{}};assert(rom.size()==0x1000000);
// The original selector+unavailable SDK status creates the original insertion
// wait on a fresh8MiB scene. v2 follows the genuine A-continuation without A.
for(unsigned acknowledged=0;acknowledged<2;++acknowledged){auto r=ram();r[0x13b428^3]=acknowledged?32:0;sdk_error=1;attempts=0;auto c=context();
iss2000_pal_automatic_storage_ui(r.data(),&c);assert(r[0x2b4819^3]==3);assert(attempts>=1);assert(c.r29==context().r29);assert(c.r31==context().r31);assert(r[0x12e67a^3]==2);}
// Error decoding and retry limit belong to the unchanged original query. Genuine
// SDK error5 triggers init; error10 then remains the repair/error screen9.
{auto r=ram();r[0x13b428^3]=32;sdk_error=5;init_error=10;auto c=context();iss2000_pal_automatic_storage_ui(r.data(),&c);assert(r[0x2b4819^3]==9);}
{auto r=ram();r[0x2b4819^3]=15;sdk_error=9;init_error=0;attempts=0;auto c=context();func_80018E98_resident(r.data(),&c);assert(c.r2==8&&attempts==3);}
// Empty actual directory results still request original creation/selection;
// no save callback is invoked until the user genuinely chooses Yes.
{auto r=ram();r[0x13b428^3]=32;sdk_error=0;attempts=0;auto c=context();iss2000_pal_automatic_storage_ui(r.data(),&c);assert(r[0x2b4819^3]==4);assert(attempts>=2);assert(save_calls==0);}
// Reproduce the observed pending state15/cachedstatus0/ack1. No-input index6
// dispatches the real original noop; the added continuation runs before scene
// update, so insertion cannot flash. The real input packet stays unchanged.
{auto r=ram();r[0x13b428^3]=32;r[0x2b4819^3]=15;writeword(r,0x12de84,0x800c2000);sdk_error=1;auto c=context();require_no_insert=true;auto input=r;iss2000_pal_automatic_storage_update(r.data(),&c);require_no_insert=false;assert(r[0x2b4819^3]==3);assert(r[0xc2000^3]==0&&r[0xc2001^3]==0);assert(c.r29==context().r29);assert(c.r31==context().r31);}
// The actual common UI flag setter can produce active4 independently of the
// separate background-animation bit. Execute that original writer, then the
// actual callback/probe chain; this reproduces the real pending-screen guard.
{auto r=ram();r[0x12e167^3]=0;r[0x2b4819^3]=15;r[0x13b428^3]=32;writeword(r,0x12de84,0x800c2000);auto c=context();func_803CAAF0_overlay_32ae00_803ac000(r.data(),&c);assert(r[0x12e167^3]==4);sdk_error=1;attempts=0;iss2000_pal_automatic_storage_update(r.data(),&c);assert(r[0x2b4819^3]==3&&attempts==1);}
for(unsigned flags:{0u,1u,2u,3u,6u,7u,8u}){auto r=ram();r[0x12e167^3]=flags;r[0x2b4819^3]=15;writeword(r,0x12de84,0x800c2000);auto c=context();attempts=0;iss2000_pal_automatic_storage_update(r.data(),&c);assert(attempts==0&&r[0x2b4819^3]==15);}
// Genuine Savequestion0 and damaged-data9 are never auto-confirmed/probed.
for(unsigned state:{0u,3u,4u,9u,10u,14u,16u}){auto r=ram();r[0x2b4819^3]=state;writeword(r,0x12de84,0x800c2000);sdk_error=1;attempts=0;auto c=context();iss2000_pal_automatic_storage_update(r.data(),&c);assert(r[0x2b4819^3]==state);assert(attempts==0);assert(save_calls==0);}
// Whole-message ownership: every original control byte and terminator remains;
// an unrelated/corrupted variant is untouched, including repeated calls.
{auto r=ram();auto before=r;storage_wording(r.data());for(unsigned p=0x2dd400;p<0x2de400;++p)if(before[p^3]>=0xf5)assert(r[p^3]==before[p^3]);assert(r!=before);auto changed=r;storage_wording(r.data());assert(r==changed);auto foreign=before;foreign[0x2dd67a^3]^=1;storage_wording(foreign.data());for(unsigned p=0x2dd67a;p<0x2dd67a+45;++p)assert(foreign[p^3]==(p==0x2dd67a?uint8_t(before[p^3]^1):before[p^3]));}
}
'''.replace('DECL',decl).replace('DISPATCH',dispatch)
  with tempfile.TemporaryDirectory()as tmp:
   p=Path(tmp);receipt=prepare(rom,sources[0],p/'out');self.assertEqual(receipt,prepare(rom,sources[0],p/'out'))
   (p/'out/expansion.cpp').write_bytes(expansion(sources[1].read_bytes()));(p/'out/test.cpp').write_text(code.replace('#include <cassert>','#include <cassert>\n#include <cstring>'))
   objects=[]
   for source in sources:
    obj=p/(source.stem+'.o');objects.append(str(obj));r=subprocess.run(['cc','-std=c17','-O1','-I'+str(ROOT/'.local/deps/N64Recomp/include'),'-c',str(source),'-o',str(obj)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
   command=['c++','-std=c++20','-O1','-I'+str(ROOT/'.local/deps/N64Recomp/include'),str(p/'out/test.cpp'),*objects,'-lm','-o',str(p/'check')]
   r=subprocess.run(command,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
   r=subprocess.run([str(p/'check'),str(rom)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
   # Removing v2's genuine state15 continuation must reproduce the failure.
   derivative=p/'out/pal_automatic_storage_ui.cpp';text=derivative.read_text();derivative.write_text(text.replace('MEM_BU(0, 0xFFFFFFFF802B4819ull) == 15','false'))
   r=subprocess.run(command,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
   r=subprocess.run([str(p/'check'),str(rom)],capture_output=True,text=True);self.assertNotEqual(r.returncode,0,'Original pending insertion request must fail without v2 continuation')
   with self.assertRaises(ValueError):prepare(rom,sources[0],p/'out')
   with self.assertRaises(ValueError):wording(bytes(0x1000000))
