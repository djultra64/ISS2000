"""Original project work: djultra64. PAL Options ownership and original row6 resource."""
from pathlib import Path
import ast,hashlib,json,shutil,struct,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
CODE=r'''#include "recomp.h"
#include "runtime/pal_options_entry.hpp"
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
DECLS
using namespace iss2000;using Bytes=std::vector<uint8_t>;
extern "C" recomp_func_t* get_function(int32_t a){switch(uint32_t(a)){LOOKUP default:std::abort();}}
uint32_t word(const Bytes&r,uint32_t a){uint32_t v;memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
void put(Bytes&r,uint32_t a,uint32_t v){memcpy(r.data()+(a&0x7fffff),&v,4);}
void byte(Bytes&r,uint32_t a,uint8_t v){r[(a&0x7fffff)^3]=v;}
void half(Bytes&r,uint32_t a,uint16_t v){memcpy(r.data()+((a&0x7fffff)^2),&v,2);}
void call(Bytes&r,uint32_t fn,uint32_t a=0,uint32_t b=0){recomp_context c{};c.r4=int32_t(a);c.r5=int32_t(b);c.r29=int32_t(0x807ff000);c.f_odd=&c.f0.u32h;get_function(fn)(r.data(),&c);}
int main(int argc,char**argv){assert(argc==2);Bytes base(0x800000);auto*f=fopen(argv[1],"rb");assert(f&&fread(base.data(),1,base.size(),f)==base.size());fclose(f);
 const uint32_t object=0x8013c47c,context=0x807f0000;
 // Isolated ordinary scheduler inputs, using the exact original220-node pool.
 put(base,0x80077390,0x801e7070);put(base,0x801e7070,0x801e70e4);put(base,0x801e70e4,0);put(base,0x801e70f0,0x8029f274);put(base,0x801ed420,0x801e7070);byte(base,0x8012de74,1);
 for(unsigned row=0;row<8;++row){auto r=base;byte(r,0x802b1090,row);call(r,0x80008a54,object);put(r,object+0x38,context);call(r,0x801ad90c,context);half(r,context+0x20,row);byte(r,object+4,1);
  call(r,0x80007be0,0x802a6bb4);call(r,0x8029f070,object);call(r,0x8029f004,0,object);
  auto before=r;auto state=pal_options_entry(r);assert(state&&state->row==row&&state->pc_settings==(row==6)&&r==before);
  auto label=pal_options_pc_label(r,object);assert(bool(label)==(row==6));if(label){assert(label->x==67&&label->y==167&&label->width==128&&label->height==16);assert(word(r,object+0x14)==0x802d1c3c&&word(r,object+0x30)==0x802a6b6c);}
  auto up=r;call(up,0x8029f33c);assert(up[(0x2b1090)^3]==(row+7)%8);auto down=r;call(down,0x8029f390);assert(down[(0x2b1090)^3]==(row+1)%8);
  if(row==6){for(auto[a,v]:{std::pair{object+0x30,0x802a6b84u},std::pair{object+0x14,0x802d1c30u},std::pair{0x80076ca4u,0x802d1c30u}}){auto changed=r;put(changed,a,v);assert(!pal_options_pc_label(changed,object));}
   for(auto a:{0x802a6b6cu+23,0x802d1c3cu+11,0x80277640u+2047}){auto changed=r;byte(changed,a,changed[(a&0x7fffff)^3]^255);assert(!pal_options_pc_label(changed,object));}
   auto changed=r;half(changed,context+0x20,5);assert(!pal_options_pc_label(changed,object));assert(!pal_options_pc_label(r,0x123456788013c47cULL));}
 }
 for(auto[a,v]:{std::pair{0x80077390u,0u},std::pair{0x801e70e4u,0x801e7070u},std::pair{0x801e70f0u,0x802c48f4u},std::pair{0x8009e02cu,0x8013b400u}}){auto r=base;put(r,a,v);auto before=r;assert(!pal_options_entry(r)&&r==before);}
 for(auto a:{0x8029f274u,0x8029f2d8u+59,0x802a6cc8u+55,0x802b08d4u+59}){auto r=base;byte(r,a,r[(a&0x7fffff)^3]^255);auto before=r;assert(!pal_options_entry(r)&&r==before);}
 for(auto row:{8u,255u}){auto r=base;byte(r,0x802b1090,row);assert(!pal_options_entry(r));}
 auto r=base;byte(r,0x8012de74,5);assert(!pal_options_entry(r));
}
'''
class PalOptionsEntryTests(unittest.TestCase):
 def test_original_resource_position_navigation_and_exact_owner_guards(self):
  self.assertTrue((ROOT/'src/runtime/pal_options_entry.hpp').is_file(),'Missing bounded originalOptions helper')
  if not shutil.which('c++'):self.skipTest('Compiler required')
  header=ROOT/'.local/deps/N64Recomp/include';generated=ROOT/'.local/pal-map-bound-01/functions';snapshot=ROOT/'.local/pal-acceptance/mainmenu09.rdram';rompath=ROOT/'.local/inputs/pal-en-de/rom.z64'
  if not all(p.is_file()for p in [header/'recomp.h',snapshot,rompath]):self.skipTest('PrivatePAL originalfixture required')
  ns=[('80008A54','resident'),('80007BE0','resident'),('80007BF8','resident'),('80007C2C','resident'),('8004C59C','resident'),('8004C608','resident'),('801AD90C','overlay_2dee70_801ad820'),('801B0000','overlay_2dee70_801ad820'),('801B0038','overlay_2dee70_801ad820'),('801B3D1C','overlay_2dee70_801ad820'),('801B7E00','overlay_2dee70_801ad820'),('8029F070','overlay_3b47e0_8029eea0'),('8029F004','overlay_3b47e0_8029eea0'),('8029F33C','overlay_3b47e0_8029eea0'),('8029F390','overlay_3b47e0_8029eea0')]
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);objects=[]
   for a,owner in ns:
    source=generated/f'func_{a}_{owner}.c';obj=p/f'{a}.o';built=subprocess.run(['cc','-O2','-I'+str(header),'-c',str(source),'-o',str(obj)],capture_output=True,text=True);self.assertEqual(built.returncode,0,built.stderr);objects.append(obj)
   code=CODE.replace('DECLS','\n'.join(f'extern "C" void func_{a}_{o}(uint8_t*,recomp_context*);'for a,o in ns)).replace('LOOKUP','\n'.join(f'case0x{a}:return func_{a}_{o};'.replace('case0x','case 0x')for a,o in ns));(p/'test.cpp').write_text(code)
   miniz=ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz';mb=ROOT/'.local/runtime-deps-build/librecomp/miniz'
   built=subprocess.run(['c++','-std=c++20','-O2','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-I'+str(ROOT/'src'),'-I'+str(header),'-I'+str(miniz),'-I'+str(mb),str(p/'test.cpp'),str(ROOT/'src/runtime/pal_options_entry.cpp'),str(ROOT/'src/runtime/rom_image.cpp'),*[str(o)for o in objects],'-o',str(p/'test')],capture_output=True,text=True);self.assertEqual(built.returncode,0,built.stderr)
   rom=rompath.read_bytes();self.assertEqual(hashlib.sha256(rom).hexdigest(),'6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf');r=bytearray(snapshot.read_bytes());sections=json.loads((ROOT/'.local/pal-map-bound-01/section-analysis.json').read_text());sections=sections if isinstance(sections,list)else sections['sections']
   for ro in [0x3b47e0,0x49d610,0x2dee70]:
    s=next(s for s in sections if s['rom']==ro)
    for i,v in enumerate(rom[ro:ro+s['load_size']]):r[((s['vram']+i)&0x7fffff)^3]=v
   decoder=next(n for n in ast.parse((ROOT/'.local/team-visual-assets-01/probe_assets.py').read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='decode');env={};exec(compile(ast.Module(body=[decoder],type_ignores=[]),'decoder','exec'),env);a,b=struct.unpack_from('>II',rom,0x972bc+(0x42-1)*8);a&=0x7fffffff;data,_=env['decode'](rom[a:b],a);self.assertEqual(hashlib.sha256(data).hexdigest(),'5dbf56dd71d5c280fc0fad104003a23898312e4fd9468a76fd023db8d221a3e8')
   for i,v in enumerate(data):r[((0x80276940+i)&0x7fffff)^3]=v
   (p/'base.rdram').write_bytes(r);run=subprocess.run([str(p/'test'),str(p/'base.rdram')],capture_output=True,text=True);self.assertEqual(run.returncode,0,run.stderr)
