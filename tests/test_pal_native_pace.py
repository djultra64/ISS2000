"""Exact original PAL frame/stage CPU call-count regression. Work by djultra64.
External rendering, input and actor leaves are observed counters, not invented physics.
"""
from pathlib import Path
import hashlib,json,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class NativePaceIdentityTests(unittest.TestCase):
 def test_changed_original_source_is_rejected(self):
  from tools.prepare_pal_native_pace import derive
  with self.assertRaisesRegex(ValueError,'source digest mismatch'):derive(b'foreign')
 def test_invalid_rom_leaves_no_output(self):
  from tools.prepare_pal_native_pace import prepare
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'rom').write_bytes(b'foreign')
   with self.assertRaisesRegex(ValueError,'ROM digest mismatch'):prepare(p/'rom',p/'missing',p/'out')
   self.assertFalse((p/'out').exists())
 def test_receipt_idempotence_and_tampering(self):
  from tools.prepare_pal_native_pace import prepare
  rom=ROOT/'.local/inputs/pal-en-de/rom.z64';source=ROOT/'.local/pal-map-bound-01/functions/func_80000C30_resident.c'
  if not rom.is_file() or not source.is_file():self.skipTest('Private original PAL inputs required')
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'out';receipt=prepare(rom,source,p);self.assertEqual(prepare(rom,source,p),receipt)
   self.assertEqual(receipt['attribution'],'djultra64');self.assertNotIn(str(ROOT),json.dumps(receipt));target=p/receipt['file']
   self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(),receipt['generated_sha256']);self.assertNotIn(b'\r\n',target.read_bytes());self.assertIn(b'#ifdef _WIN32\n#undef RECOMP_FUNC\n#define RECOMP_FUNC __declspec(noinline)',target.read_bytes())
   target.write_bytes(target.read_bytes()+b'\n')
   with self.assertRaisesRegex(ValueError,'Refusing to alter'):prepare(rom,source,p)

HARNESS=r'''#include "recomp.h"
#include <cassert>
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iterator>
#include <vector>
ORIGINALS
DERIVED
using Bytes=std::vector<uint8_t>;
static std::vector<uint32_t> trace;
static unsigned calls,actors,pauses;static int transition;
static uint8_t byte(const uint8_t* r,uint32_t a){return r[(a&0x7fffff)^3];}
static void byte(uint8_t* r,uint32_t a,uint8_t v){r[(a&0x7fffff)^3]=v;}
static void word(uint8_t* r,uint32_t a,uint32_t v){std::memcpy(r+(a&0x7fffff),&v,4);}
static uint16_t half(const Bytes& r,uint32_t a){uint16_t v;std::memcpy(&v,r.data()+((a&0x7fffff)^2),2);return v;}
static void external(uint8_t*,recomp_context* c){c->r2=0;}
static void actor(uint8_t*,recomp_context* c){++actors;c->r2=0;}
static void pause(uint8_t*,recomp_context* c){++pauses;c->r2=0;}
static void stage(uint8_t* r,recomp_context* c){
 ++calls;func_80002D90_resident(r,c);
 if(calls==1){
  if(transition==1||transition==8)byte(r,0x13b446,7);
  if(transition==2){byte(r,0x13b446,6);byte(r,0x13b44c,4);}
  if(transition==3)byte(r,0x13b42a,0);
  if(transition==4)byte(r,0x13b42a,1);
  if(transition==5)word(r,0x9e02c,0x8013b418);
 }
 if(calls==2&&transition==8)byte(r,0x13b446,6);
}
extern "C" recomp_func_t* get_function(int32_t a){trace.push_back(uint32_t(a));switch(uint32_t(a)){
 case 0x80002d90:return stage;
 case 0x80003410:return func_80003410_resident;
 case 0x80053a80:return func_80053A80_resident;
 case 0x80053df8:return func_80053DF8_resident;
 case 0x801e64a8:return actor;
 case 0x801dc670:return pause;
 default:return external;}}
struct Result{std::vector<uint32_t> trace;unsigned calls,actors,pauses;uint16_t tick;};
static Result run(Bytes ram,bool changed){trace.clear();calls=actors=pauses=0;auto initial=half(ram,0x13b442);recomp_context c{};c.r29=int32_t(0x800a4000);c.r31=int32_t(0x80123450);
 if(changed)iss2000_pal_native_frame_pace(ram.data(),&c);else func_80000C30_resident(ram.data(),&c);
 assert(uint32_t(c.r29)==0x800a4000&&uint32_t(c.r31)==0x80123450);
 return {trace,calls,actors,pauses,uint16_t(half(ram,0x13b442)-initial)};
}
int main(int,char** argv){std::ifstream f(argv[1],std::ios::binary);Bytes original{std::istreambuf_iterator<char>(f),{}};assert(original.size()==0x800000);
 assert(byte(original.data(),0x13b42a)==1&&byte(original.data(),0x13b446)==6&&byte(original.data(),0x13b44c)==4);
 for(unsigned mode:{0u,4u,9u})for(unsigned paused:{0u,1u})for(unsigned replay:{0u,3u}){
  auto ram=original;byte(ram.data(),0x12de74,mode);byte(ram.data(),0x13b452,paused);byte(ram.data(),0x12de27,replay);transition=0;
  auto before=run(ram,false),after=run(ram,true);assert(before.calls==2&&after.calls==1);
  assert(before.actors==(paused?0u:2u)&&after.actors==(paused?0u:1u));assert(before.pauses==(paused?2u:0u)&&after.pauses==(paused?1u:0u));assert(before.tick==(paused?0u:2u)&&after.tick==(paused?0u:1u));
  // Omit the paired duplicate stage and skeletal update; keep camera calls.
  auto reduced=before.trace;auto second=std::find(std::find(reduced.begin(),reduced.end(),0x80002d90)+1,reduced.end(),0x80002d90);auto end=std::find(second,reduced.end(),0x80001128);assert(second!=reduced.end()&&end!=reduced.end());reduced.erase(second,end);assert(after.trace==reduced);
  assert(std::count(after.trace.begin(),after.trace.end(),0x8005a690)==2);assert(std::count(after.trace.begin(),after.trace.end(),0x8000453c)==2);assert(std::count(after.trace.begin(),after.trace.end(),0x80031e74)==1);assert(std::count(after.trace.begin(),after.trace.end(),0x80001128)==2);
 }
 for(int scenario=0;scenario<9;++scenario){auto ram=original;transition=scenario;
  if(scenario==0)byte(ram.data(),0x13b42a,0);
  if(scenario==2)byte(ram.data(),0x13b446,7);
  if(scenario==4)byte(ram.data(),0x13b42a,0);
  if(scenario==5){word(ram.data(),0x9e02c,0x80100000);std::memcpy(ram.data()+0x100000,ram.data()+0x13b418,0x6000);}
  if(scenario==6)byte(ram.data(),0x6ce70,1);
  if(scenario==7)byte(ram.data(),0x13b44c,5);
  auto before=run(ram,false),after=run(ram,true);assert(before.trace==after.trace&&before.calls==after.calls&&before.tick==after.tick);
 }
}
'''
class NativePaceOriginalDriverTests(unittest.TestCase):
 def test_original_frame_stage_closure_keeps_one_steady_field_step(self):
  from tools.prepare_pal_native_pace import derive,ROM_SHA256
  folder=ROOT/'.local/pal-map-bound-01/functions';rom=ROOT/'.local/inputs/pal-en-de/rom.z64';snapshot=ROOT/'.local/training-timing-01/free-training-high.rdram';header=ROOT/'.local/deps/N64Recomp/include'
  names=['func_80000C30_resident','func_80002D90_resident','func_80003410_resident','func_80053A80_resident','func_80053DF8_resident'];sources=[folder/(n+'.c') for n in names]
  if not all(p.is_file() for p in [rom,snapshot,header/'recomp.h',*sources]):self.skipTest('Private actual HIGH Training RAM and genuine PAL CPU sources required')
  image=rom.read_bytes();self.assertEqual(hashlib.sha256(image).hexdigest(),ROM_SHA256)
  pins={'func_80000C30_resident': (6192, 1272, '6fac9fbf788c9a44cc3c11713a6e087ff764fee0c777a458f749f13f31113935', '0ea1d11a153c80b2deaa2076313cb227bbba7c03a2ce09cdfd4fb5f6be3c8136'), 'func_80002D90_resident': (14736, 264, '8e3cf4dd14e305b4ef8e06d9abccfd6ce4a00e9e80ebb3f94aae3cea68ad295f', 'fc22b4b6eef601851080e27b9a113ebdb1bd3025398a7bc653e33aa507aad8d5'), 'func_80003410_resident': (16400, 68, 'd4e8800405a746e7e9fb51e73884036ae4786211fbfa0cbf56389fad8e0938bb', '93c90531999c7d76c4d4ab94b7d3af7f9337d2b30e16646b05ac60639f243fb8'), 'func_80053A80_resident': (345728, 108, 'bf8a8d005526d9878736a72a4843fcfb5076a1110bbffe16f0e20b36e6b797be', '2900eb32cfaab8051b15cb0058faeaacba94075645f74931ac1dfb64101b5a21'), 'func_80053DF8_resident': (346616, 240, '2c02a865814cfe27a7915ca390650b73be77452740681283aa4f52857273c7ca', '8b6cd2cc4c70d94e231aaaeeb2c6afad598c4117857e7d0628ffc3e092e57e7a')}
  for name,(offset,size,body_digest,source_digest) in pins.items():
   self.assertEqual(hashlib.sha256(image[offset:offset+size]).hexdigest(),body_digest)
   self.assertEqual(hashlib.sha256((folder/(name+'.c')).read_bytes()).hexdigest(),source_digest)
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'derived.cpp').write_bytes(derive(sources[0].read_bytes()))
   (p/'check.cpp').write_text(HARNESS.replace('ORIGINALS','\n'.join('#include '+json.dumps(str(x)) for x in sources)).replace('DERIVED','#include '+json.dumps(str(p/'derived.cpp'))))
   built=subprocess.run(['c++','-std=c++20','-O2','-I'+str(header),str(p/'check.cpp'),'-o',str(p/'check')],capture_output=True,text=True);self.assertEqual(built.returncode,0,built.stderr)
   run=subprocess.run([str(p/'check'),str(snapshot)],capture_output=True,text=True);self.assertEqual(run.returncode,0,run.stderr)

class NativePaceOriginalAnimationTests(unittest.TestCase):
 def test_genuine_skeletal_phase_matches_low_for_each_native_field_task(self):
  # The old actor counter fixture did not execute the pose-advancing geometry
  # closure. Execute that closure and the production maximum-detail derivative.
  # Final pose baking is an explicit observer: this test measures original
  # animation clocks/scripts, not joint matrices or a rendered reference image.
  from tools.prepare_pal_native_pace import derive,ROM_SHA256
  from tools.prepare_pal_max_detail import derive as model_derive
  folder=ROOT/'.local/pal-map-bound-01/functions';rom=ROOT/'.local/inputs/pal-en-de/rom.z64';snapshot=ROOT/'.local/training-timing-01/free-training-high43-completed.rdram';header=ROOT/'.local/deps/N64Recomp/include'
  names=['80000C30','80002D90','80003410','80053A80','80053DF8','80031E74','80031194','800300D0','8002F448','8002EA50','8002EA18','8002EB64']
  paths={n:folder/f'func_{n}_resident.c' for n in names}
  if not all(p.is_file() for p in [rom,snapshot,header/'recomp.h',*paths.values()]):self.skipTest('Private original PAL code and completed HIGH Training RAM required')
  image=rom.read_bytes();self.assertEqual(hashlib.sha256(image).hexdigest(),ROM_SHA256)
  pins={
   '8002EA18':(0x2F618,56,'fa4c016bbd48ad0f86d488257e23335accf14b6bf1e99052613af47a8e1ae598','e88006f11d81568b2c25d640ee7b39e18d2bba1a8b6e642e426009104ec62db5'),
   '8002EA50':(0x2F650,180,'2652ff565cd34e243af08f767813cb9b2039383cab932a5a2e6b10f9ddd30a96','1e13012d0e65962dedf706c9f1ca1e7c770de18f4ef5e2876e074df757b5b799'),
   '8002EB64':(0x2F764,880,'46beb3df2c5e8f468a6e0fa30f4a17c51ee666bd42bbb29bad06f121c1eb7e8d','861fb021826d28f9ea5daf5a284aaa1d4bf8a2f677d7483e23b7e66b1316776c'),
   '8002F448':(0x30048,200,'4d738132ab1165cbddef541b0c4b9bfa12952a9e0592521ed31e631bc9c2ba67','8d13dcc3102bb8b660a1adcf9808d6110ea03de42da967013dcbf43d47c9c4fa'),
   '800300D0':(0x30CD0,1632,'e13fdb5abe618af2f90892ef1057d26eb1364087ec7f8c5d28de5f7beddd6aae','348e924ccc8cdccdd814c4ec86d3da8707d4b6fafe7c592bc7323a9c71697acb'),
   '80031194':(0x31D94,24,'9c7035a36fb36f88c0135bfaf4a31f785f8cdc7e90c8ea75d52526c6c5f12f40','344fad27bf41b14f85c18b47049611bd65d343590f79d5b4479dd645772f95e0'),
   '80031E74':(0x32A74,280,'ed71d3126529db896a4b3f9ce2e0ee79e171d1fd804a22c23a87384e8f2ef000','c0ca9bf4e12665d3dd355f324cc7adabe1287ba8476f7c7cfcd063e04c309483')}
  for name,(offset,size,body,source) in pins.items():
   self.assertEqual(hashlib.sha256(image[offset:offset+size]).hexdigest(),body)
   self.assertEqual(hashlib.sha256(paths[name].read_bytes()).hexdigest(),source)
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'pace.cpp').write_bytes(derive(paths['80000C30'].read_bytes()));(p/'models.cpp').write_bytes(model_derive(paths['800300D0'].read_bytes(),'models'))
   code=HARNESS[:HARNESS.index('int main(int,char** argv)')]
   code=code.replace('ORIGINALS','extern "C" void func_8002EB64_resident(uint8_t*,recomp_context*);\n'+'\n'.join('#include '+json.dumps(str(path)) for name,path in paths.items() if name!='8002EB64'))
   code=code.replace('DERIVED','#include '+json.dumps(str(p/'pace.cpp'))+'\n#include '+json.dumps(str(p/'models.cpp')))
   actual='\n'.join(f' case 0x{n.lower()}:return func_{n}_resident;' for n in ['80031E74','80031194','8002F448','8002EA50','8002EA18','8002EB64'])
   code=code.replace(' case 0x80002d90:return stage;',actual+'\n case 0x800300d0:return iss2000_pal_max_detail_models;\n case 0x80002d90:return stage;')
   code=code.replace('uint16_t tick;};','uint16_t tick;Bytes ram;};').replace('c.r31=int32_t(0x80123450);','c.r31=int32_t(0x80123450);c.f_odd=&c.f0.u32h;')
   code=code.replace('uint16_t(half(ram,0x13b442)-initial)};','uint16_t(half(ram,0x13b442)-initial),std::move(ram)};')
   code+=r'''
static uint32_t word(const Bytes&r,uint32_t a){uint32_t v;std::memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
int main(int,char**argv){std::ifstream f(argv[1],std::ios::binary);Bytes original{std::istreambuf_iterator<char>(f),{}};assert(original.size()==0x800000);
 auto low=original;byte(low.data(),0x13b42a,0);auto high=original;
 // Negative control: unchanged HIGH has two pose passes, and the original
 // captured model's in-range phase advances twice as far as original LOW.
 const auto baseline=run(low,false),old=run(high,false);
 assert(std::count(old.trace.begin(),old.trace.end(),0x80031e74)==2);
 assert(word(old.ram,0x801a08cc+0x84)!=word(baseline.ram,0x801a08cc+0x84));
 for(unsigned task=0;task<25;++task){
  auto a=run(low,true),b=run(high,true);assert(a.calls==1&&b.calls==1);
  assert(std::count(a.trace.begin(),a.trace.end(),0x80031e74)==1);
  assert(std::count(b.trace.begin(),b.trace.end(),0x80031e74)==1);
  assert(std::count(a.trace.begin(),a.trace.end(),0x8002f448)==std::count(b.trace.begin(),b.trace.end(),0x8002f448));
  for(unsigned i=0;i<35;++i)for(unsigned field:{0x80u,0x84u,0xd0u,0xd4u,0xd8u,0xdcu}){
   const auto at=0x801a07cc+i*0x100+field;
   if(word(a.ram,at)!=word(b.ram,at))std::fprintf(stderr,"task%u model%u field%X Low=%08X High=%08X\n",task,i,field,word(a.ram,at),word(b.ram,at));
   assert(word(a.ram,at)==word(b.ram,at));
  }
  low=std::move(a.ram);high=std::move(b.ram);
 }
}
'''
   (p/'check.cpp').write_text(code)
   compiled=subprocess.run(['cc','-O2','-I'+str(header),'-c',str(paths['8002EB64']),'-o',str(p/'geometry.o')],capture_output=True,text=True);self.assertEqual(compiled.returncode,0,compiled.stderr)
   built=subprocess.run(['c++','-std=c++20','-O2','-I'+str(header),str(p/'check.cpp'),str(p/'geometry.o'),'-o',str(p/'check')],capture_output=True,text=True);self.assertEqual(built.returncode,0,built.stderr)
   run=subprocess.run([str(p/'check'),str(snapshot)],capture_output=True,text=True,timeout=10);self.assertEqual(run.returncode,0,run.stderr)
