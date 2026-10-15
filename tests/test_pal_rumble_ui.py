"""Original project work: djultra64. Isolated original PAL menu-branch fixtures."""
from pathlib import Path
import json,shutil,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
HARNESS=r'''#include "recomp.h"
#include <array>
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
ORIGINALS
DERIVATIVES
using Bytes=std::vector<uint8_t>;
static int motor_result,validation,probes,queries,queued;
static std::vector<uint32_t> callbacks,stages,cleanup;
static uint32_t registrar_result;
static void put(Bytes& r,uint32_t a,uint32_t v){std::memcpy(r.data()+(a&0x7fffff),&v,4);}
static void byte(Bytes& r,uint32_t a,uint8_t v){r[(a&0x7fffff)^3]=v;}
static void query(uint8_t* r,recomp_context*){++queries;for(unsigned i=0;i<4;++i)r[(0xa4b42+4*i)^3]=1;}
static void motor(uint8_t*,recomp_context* c){++probes;assert(uint32_t(c->r6)<4);c->r2=(int32_t)motor_result;}
static void check(uint8_t*,recomp_context* c){c->r2=validation;}
static void noop(uint8_t*,recomp_context*){}
static void enqueue(uint8_t*,recomp_context* c){++queued;assert(uint32_t(c->r4)==0x801e334c);}
static void install(uint8_t*,recomp_context* c){callbacks.push_back(uint32_t(c->r4));registrar_result=uint32_t(c->r2);}
static void stage(uint8_t*,recomp_context* c){stages.push_back(uint32_t(c->r4));}
static void tidy(uint8_t*,recomp_context* c){cleanup.push_back(uint32_t(c->r4));}
extern "C" recomp_func_t* get_function(int32_t a){switch(uint32_t(a)){
 case 0x80004630:return query;case 0x8005f8a4:return motor;
 case 0x800072b4:return func_800072B4_resident;
 case 0x801b9654:return func_801B9654_overlay_2dee70_801ad820;
 case 0x801b96d4:return func_801B96D4_overlay_2dee70_801ad820;
 case 0x801b7d90:case 0x802c772c:case 0x802c7658:return noop;case 0x803d1234:return check;
 case 0x801ae594:return enqueue;case 0x801b3d1c:case 0x801b3e84:return install;
 case 0x803d2fd0:return func_803D2FD0_overlay_57f870_803d1a30;
 case 0x8000c7ac:return stage;case 0x801ada4c:return tidy;
 default:std::fprintf(stderr,"Unexpected call %08X\n",uint32_t(a));std::abort();}}
static auto context(){recomp_context c{};c.r29=(int32_t)0x807ff000;c.f_odd=&c.f0.u32h;return c;}
static void reset(){probes=queries=queued=0;callbacks.clear();stages.clear();cleanup.clear();registrar_result=0xdeadbeef;}
static void invoke(recomp_func_t* fn,Bytes& ram){reset();auto c=context();fn(ram.data(),&c);}
int main(int argc,char** argv){
 assert(argc==2);Bytes shared(0x35c10);FILE* f=std::fopen(argv[1],"rb");assert(f);
 assert(std::fread(shared.data(),1,shared.size(),f)==shared.size());std::fclose(f);
 const std::array<recomp_func_t*,5> originals={ORIGINAL_ENTRIES};
 const std::array<recomp_func_t*,5> derived={DERIVED_ENTRIES};
 const uint32_t next[]={0x802b56c0,0x802ba860,0x802be29c,0x802c6e60};
 for(unsigned kind=0;kind<5;++kind)for(unsigned layout=0;layout<9;++layout)
 for(int result: {0,1,4,11,-1})for(unsigned career_used:{0u,1u}){
  Bytes base(0x800000);std::memcpy(base.data()+0x1ad820,shared.data(),shared.size());
  byte(base,0x8012de54,1);byte(base,0x8012de74,layout==0?5:0);
  byte(base,0x80133658,layout);byte(base,0x8012de7e,1);
  byte(base,0x803d3480,layout%2);byte(base,0x803d4020+layout%2,career_used);
  validation=0;motor_result=result;
  auto baseline=base;invoke(originals[kind],baseline);
  assert(probes==4&&queries==1);
  const bool original_modal=queued!=0;
  if(result!=0)assert(original_modal); // Prove this fixture actually exposes the nag.
  auto changed=base;invoke(derived[kind],changed);
  assert(probes==4&&queries==1&&queued==0);
  if(kind<4){assert(callbacks.size()==1&&callbacks[0]==next[kind]&&stages.empty());
   // Original missing-motor predicate value is retained, never forged success.
   if(original_modal)assert(registrar_result==0x01000000);
  }else assert(stages.size()==1&&stages[0]==(career_used?1u:2u)&&callbacks.empty());
  if(!original_modal)assert(baseline==changed);
 }
 // Unrelated UI validation/ready/exit branches must remain identical to originals.
 for(unsigned kind=0;kind<4;++kind){
  Bytes base(0x800000);std::memcpy(base.data()+0x1ad820,shared.data(),shared.size());
  byte(base,0x8012de54,1);byte(base,0x8012de7e,1);validation=0;motor_result=11;
  if(kind==0)byte(base,0x802b6ed8,2);
  if(kind==1)validation=1;
  if(kind==2)byte(base,0x802c33c0,2);
  if(kind==3)byte(base,0x802d2228,1);
  auto original=base;invoke(originals[kind],original);
  assert(probes==0&&queries==0&&queued==0);auto oc=callbacks,os=stages,ot=cleanup;
  auto changed=base;invoke(derived[kind],changed);
  assert(original==changed&&probes==0&&queries==0&&queued==0&&callbacks==oc&&stages==os&&cleanup==ot);
 }
}
'''
@unittest.skipUnless(shutil.which('c++'),'C++ compiler required')
class OriginalRumbleUiTests(unittest.TestCase):
 def test_original_callers_skip_only_swap_modal_and_preserve_real_probes(self):
  from tools.prepare_pal_rumble_ui import PROFILES,derive,ROM_SHA256
  import hashlib
  generated=ROOT/'.local/pal-map-bound-01/functions';header=ROOT/'.local/deps/N64Recomp/include';rom=ROOT/'.local/inputs/pal-en-de/rom.z64'
  originals=[generated/(p['original']+'.c') for p in PROFILES.values()]
  extra=[generated/(n+'.c') for n in ['func_800072B4_resident','func_801B9654_overlay_2dee70_801ad820','func_801B96D4_overlay_2dee70_801ad820','func_803D2FD0_overlay_57f870_803d1a30']]
  if not all(p.is_file() for p in [rom,header/'recomp.h',*originals,*extra]):self.skipTest('Private original PAL menu/probe fixtures required')
  self.assertEqual(hashlib.sha256(rom.read_bytes()).hexdigest(),ROM_SHA256)
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);derived=[]
   for (key,_),original in zip(PROFILES.items(),originals):
    path=p/(key+'.cpp');path.write_bytes(derive(original.read_bytes(),key));derived.append(path)
   raw=rom.read_bytes()[0x2dee70:0x314a80]
   (p/'shared.bin').write_bytes(b''.join(raw[i:i+4][::-1] for i in range(0,len(raw),4)))
   objects=[]
   for index,source in enumerate([*originals,*extra]):
    target=p/(str(index)+'.o')
    built=subprocess.run(['cc','-O2','-I'+str(header),'-c',str(source),'-o',str(target)],capture_output=True,text=True)
    self.assertEqual(built.returncode,0,built.stderr);objects.append(target)
   declarations='\n'.join('extern \"C\" void '+x.stem+'(uint8_t*,recomp_context*);' for x in [*originals,*extra])
   code=HARNESS.replace('ORIGINALS',declarations).replace('DERIVATIVES','\n'.join('#include '+json.dumps(str(x)) for x in derived)).replace('ORIGINAL_ENTRIES',','.join(v['original'] for v in PROFILES.values())).replace('DERIVED_ENTRIES',','.join(v['entry'] for v in PROFILES.values()))
   (p/'check.cpp').write_text(code)
   built=subprocess.run(['c++','-std=c++20','-O2','-I'+str(header),str(p/'check.cpp'),*[str(x) for x in objects],'-o',str(p/'check')],capture_output=True,text=True)
   self.assertEqual(built.returncode,0,built.stderr)
   run=subprocess.run([str(p/'check'),str(p/'shared.bin')],capture_output=True,text=True)
   self.assertEqual(run.returncode,0,run.stderr)

class RumbleUiIdentityTests(unittest.TestCase):
 def test_wrong_rom_or_source_is_rejected_before_output(self):
  from tools.prepare_pal_rumble_ui import PROFILES,derive,prepare
  for key in PROFILES:
   with self.assertRaisesRegex(ValueError,'source digest mismatch'):derive(b'unrelated',key)
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'rom').write_bytes(b'wrong region')
   with self.assertRaisesRegex(ValueError,'ROM digest mismatch'):prepare(p/'rom',p/'missing',p/'out')
   self.assertFalse((p/'out').exists())
 def test_generation_is_exact_idempotent_and_refuses_modified_outputs(self):
  from tools.prepare_pal_rumble_ui import PROFILES,prepare
  rom=ROOT/'.local/inputs/pal-en-de/rom.z64';generated=ROOT/'.local/pal-map-bound-01/functions'
  if not all(p.is_file() for p in [rom,*[generated/(v['original']+'.c') for v in PROFILES.values()]]):self.skipTest('Private original PAL generation inputs required')
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'out';receipt=prepare(rom,generated,out)
   self.assertEqual(prepare(rom,generated,out),receipt)
   self.assertEqual(len(list(out.glob('*.cpp'))),5)
   self.assertEqual(receipt['attribution'],'djultra64')
   self.assertNotIn(str(ROOT),json.dumps(receipt))
   target=next(out.glob('*.cpp'));target.write_bytes(target.read_bytes()+b'\n// altered\n')
   with self.assertRaisesRegex(ValueError,'Refusing to alter'):prepare(rom,generated,out)
