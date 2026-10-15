"""Original project work: djultra64. Synthetic-only original PAL LOD checks."""
from pathlib import Path
import json, shutil, subprocess, tempfile, unittest
ROOT=Path(__file__).resolve().parents[1]
HARNESS=r'''#include "recomp.h"
#include <vector>
#include <cstring>
#include <cassert>
#include <cstdlib>
#include <cstdio>
extern "C" void func_8002EB64_resident(uint8_t*,recomp_context*);
ORIGINAL_INCLUDES
DERIVED_INCLUDES
using Bytes=std::vector<uint8_t>;
static int geometry_calls,shadow_calls;static uint32_t shadow_target;
static void put(Bytes& b,uint32_t a,uint32_t v){std::memcpy(b.data()+(a&0x7fffff),&v,4);}
static uint32_t get(const Bytes& b,uint32_t a){uint32_t v;std::memcpy(&v,b.data()+(a&0x7fffff),4);return v;}
static void half(Bytes& b,uint32_t a,uint16_t v){std::memcpy(b.data()+((a&0x7fffff)^2),&v,2);}
static void geometry(uint8_t* b,recomp_context* c){++geometry_calls;func_8002EB64_resident(b,c);}
static void near_shadow(uint8_t*,recomp_context*){++shadow_calls;shadow_target=0x800368E8;}
static void medium_shadow(uint8_t*,recomp_context*){++shadow_calls;shadow_target=0x80036CB0;}
static void far_shadow(uint8_t*,recomp_context*){++shadow_calls;shadow_target=0x80036998;}
static void special_shadow(uint8_t*,recomp_context*){++shadow_calls;shadow_target=0x80036EC4;}
extern "C" recomp_func_t* get_function(int32_t address){switch(uint32_t(address)){
 case 0x8002EA50:return func_8002EA50_resident;
 case 0x8002EA18:return func_8002EA18_resident;
 case 0x8002EB64:return geometry;
 case 0x800368E8:return near_shadow;
 case 0x80036CB0:return medium_shadow;
 case 0x80036998:return far_shadow;
 case 0x80036EC4:case 0x800371A0:case 0x8003731C:return special_shadow;
 default:std::abort();}}
constexpr uint32_t state=0x801A0000,obj=0x80145624;
static recomp_context context(uint32_t argument){recomp_context c{};c.r4=(int32_t)argument;c.r29=(int32_t)0x807FF000;return c;}
static Bytes models(const Bytes& original,int type,int depth,int min_level){
 auto b=original;put(b,0x8009DEF8,1);put(b,0x8007B0F4,min_level);put(b,0x8007B0F8,100);put(b,0x8007B0FC,750);put(b,0x8009DE84,0x80300000);
 for(int i=0;i<19;++i){put(b,state+i*4,obj+i*0x98);put(b,obj+i*0x98+0x28,0x80404033);}
 half(b,obj+0x20,depth);half(b,state+0xB8,type);put(b,state+0xBC,6);return b;
}
int main(int argc,char** argv){assert(argc==2);Bytes base(0x800000);FILE* f=fopen(argv[1],"rb");assert(f);assert(fread(base.data()+0x400,1,0x6A200,f)==0x6A200);fclose(f);
 // Exercise the actual original model selector across types and depth bands.
 for(int type=0;type<7;++type)for(int depth: {0,100,200,400,600,9998})for(int min_level: {0,1,2}){
  auto b=models(base,type,depth,min_level);auto c=context(state);geometry_calls=0;
  iss2000_pal_max_detail_models(b.data(),&c);
  assert(get(b,state+0xBC)==0&&geometry_calls==1);
  auto expected=models(base,type,depth,min_level);auto e=context(state);e.r5=0;func_8002EB64_resident(expected.data(),&e);
  for(int i=0;i<19;++i)assert(get(b,obj+i*0x98+0x24)==get(expected,obj+i*0x98+0x24));
  c=context(state);iss2000_pal_max_detail_models(b.data(),&c);assert(geometry_calls==1); // Cache is truthful, no per-frame rebuild.
 }
 // A complete pre-cull retains the original no-selection path.
 auto b=models(base,1,600,2);put(b,obj+0x28,0x80004033);auto c=context(state);geometry_calls=0;iss2000_pal_max_detail_models(b.data(),&c);assert(geometry_calls==0&&get(b,state+0xBC)==6);
 // Shadow near detail must also apply to LOD floor 2. Hidden shadows stay hidden.
 for(int mode: {0,1})for(int floor: {0,1,2})for(int depth: {0,200,400,601,9998}){
  b=base;put(b,obj+0x50,0x801A1000);put(b,obj+0x80,0x801A2000);put(b,0x801A2000,0x80310000);put(b,0x801A2014,0x801A3000);half(b,0x801A3020,depth);
  put(b,0x800839E0,mode);put(b,0x8007B0F4,floor);c=context(obj);shadow_calls=0;iss2000_pal_max_detail_shadows(b.data(),&c);
  assert(shadow_calls==1&&shadow_target==0x800368E8);assert(get(b,obj+0x24)==(mode?0x80083BC8:0x80083B90));
  put(b,0x8009DF2C,1);c=context(obj);shadow_calls=0;iss2000_pal_max_detail_shadows(b.data(),&c);assert(shadow_calls==0&&get(b,obj+0x24)==0);
 }
 // Non-LOD shadow mode 2 and stage suppression must stay byte-identical.
 for(int mode: {2,3})for(int suppressed: {0,1}){
  auto a=base;put(a,obj+0x50,0x801A1000);put(a,obj+0x80,0x801A2000);put(a,0x801A2000,0x80310000);put(a,0x800839E0,mode);if(suppressed)a[(0x13B44C)^3]=6;
  b=a;auto x=context(obj),y=context(obj);func_80037498_resident(a.data(),&x);iss2000_pal_max_detail_shadows(b.data(),&y);assert(a==b);
 }
}
'''
@unittest.skipUnless(shutil.which('c++'),'C++ compiler required')
class PalMaxDetailOriginalTests(unittest.TestCase):
 def test_original_models_and_shadows_keep_maximum_existing_detail(self):
  from tools.prepare_pal_max_detail import derive
  source=ROOT/'.local/pal-map-bound-01/functions';header=ROOT/'.local/deps/N64Recomp/include';rom=ROOT/'.local/inputs/pal-en-de/rom.z64'
  names=['800300D0','80037498','8002EA50','8002EA18','8002EB64'];paths=[source/('func_'+n+'_resident.c') for n in names]
  if not all(p.is_file() for p in [*paths,header/'recomp.h',rom]):self.skipTest('Private original PAL translation fixtures required')
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);derived=[]
   for kind,path in zip(['models','shadows'],paths):
    target=p/(kind+'.cpp');target.write_bytes(derive(path.read_bytes(),kind));derived.append(target)
   resident=rom.read_bytes()[0x1000:0x6B200]
   (p/'resident.bin').write_bytes(b''.join(resident[i:i+4][::-1] for i in range(0,len(resident),4)))
   compiled=subprocess.run(['cc','-O2','-I'+str(header),'-c',str(paths[-1]),'-o',str(p/'geometry.o')],capture_output=True,text=True)
   self.assertEqual(compiled.returncode,0,compiled.stderr)
   harness=HARNESS.replace('ORIGINAL_INCLUDES','\n'.join('#include '+json.dumps(str(x)) for x in paths[:-1])).replace('DERIVED_INCLUDES','\n'.join('#include '+json.dumps(str(x)) for x in derived))
   (p/'check.cpp').write_text(harness)
   built=subprocess.run(['c++','-std=c++20','-O2','-I'+str(header),str(p/'check.cpp'),str(p/'geometry.o'),'-o',str(p/'check')],capture_output=True,text=True)
   self.assertEqual(built.returncode,0,built.stderr)
   run=subprocess.run([str(p/'check'),str(p/'resident.bin')],capture_output=True,text=True)
   self.assertEqual(run.returncode,0,run.stderr)

class PalMaxDetailIdentityTests(unittest.TestCase):
 def test_unknown_sources_and_wrong_rom_fail_before_output(self):
  from tools.prepare_pal_max_detail import derive, prepare
  for kind in ('models','shadows'):
   with self.assertRaisesRegex(ValueError,'source digest mismatch'):
    derive(b'void unrelated_generated_function() {}',kind)
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'rom').write_bytes(b'wrong revision')
   with self.assertRaisesRegex(ValueError,'ROM digest mismatch'):
    prepare(p/'rom',p/'missing_models',p/'missing_shadows',p/'output')
   self.assertFalse((p/'output').exists())
 def test_generated_output_is_idempotent_and_tamper_is_rejected(self):
  from tools.prepare_pal_max_detail import prepare, PROFILES
  source=ROOT/'.local/pal-map-bound-01/functions';rom=ROOT/'.local/inputs/pal-en-de/rom.z64'
  paths=[source/(PROFILES[k]['original']+'.c') for k in ('models','shadows')]
  if not all(p.is_file() for p in [rom,*paths]):self.skipTest('Private pinned PAL generation fixtures required')
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'output';receipt=prepare(rom,*paths,out)
   self.assertEqual(prepare(rom,*paths,out),receipt)
   self.assertEqual(receipt['revision'],'iss2000-pal-en-de-rev0')
   self.assertEqual(receipt['attribution'],'djultra64')
   file=out/'pal_max_detail_models.cpp';file.write_bytes(file.read_bytes()+b'\n// altered\n')
   with self.assertRaisesRegex(ValueError,'Refusing to alter'):
    prepare(rom,*paths,out)
