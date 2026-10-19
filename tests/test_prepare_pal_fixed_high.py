"""Original project work: djultra64. Genuine memory detection and original High default."""
import importlib.util,hashlib,json,shutil,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class FixedHighTests(unittest.TestCase):
 def load(self):
  self.assertTrue((ROOT/'tools/prepare_pal_fixed_high.py').is_file(),'Missing SHA-pinned High initializer derivative')
  spec=importlib.util.spec_from_file_location('pal_fixed_high',ROOT/'tools/prepare_pal_fixed_high.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 def test_genuine_memory_detection_low_boot_and_original_high_transition(self):
  m=self.load();g=ROOT/'.local/pal-map-bound-01/functions';h=ROOT/'.local/deps/N64Recomp/include';rom=ROOT/'.local/inputs/pal-en-de/rom.z64'
  if not all(p.is_file()for p in [g/'func_80008C30_resident.c',h/'recomp.h',rom])or not shutil.which('c++'):self.skipTest('Private original PAL CPU/compiler required')
  ns=['func_'+a+'_resident' for a in ['80008C30','80008CBC','80008E34','80001D44','80001E40','80002D08','80043324','8005D8D0','80062270']]
  image=rom.read_bytes();fixture=bytearray(0x800000)
  for i,v in enumerate(image[0x1000:0x101000]):fixture[(0x400+i)^3]=v
  # Zero canonical BSS context, as original08BB0 does before calling08C30.
  fixture[0x13b418:0x165d78]=bytes(0x2a960)
  code=r'''#include "recomp.h"
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
DECLS
extern "C" void iss2000_pal_fixed_high_initializer(uint8_t*,recomp_context*);
using Bytes=std::vector<uint8_t>;
uint32_t word(const Bytes&r,uint32_t a){uint32_t v;memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
uint16_t half(const Bytes&r,uint32_t a){uint16_t v;memcpy(&v,r.data()+((a&0x7fffff)^2),2);return v;}
void put(Bytes&r,uint32_t a,uint32_t v){memcpy(r.data()+(a&0x7fffff),&v,4);}
uint8_t byte(const Bytes&r,uint32_t a){return r[(a&0x7fffff)^3];}
bool low_capacity=false;int vi_mode=0,features=0,black=0,mask=0,init_calls=0;unsigned expected_default=0;
void capacity(uint8_t*r,recomp_context*c){if(low_capacity)c->r2=0x400000;else func_80062270_resident(r,c);}
// SDK recorders cover only host hardware effects, never video state or buffers.
void intmask(uint8_t*,recomp_context*c){++mask;c->r2=1;}
void mode(uint8_t*,recomp_context*c){++vi_mode;assert(uint32_t(c->r4)==0x80099040);}
void feature(uint8_t*,recomp_context*c){++features;assert(c->r4==0x4a);}
void blank(uint8_t*,recomp_context*c){++black;assert(c->r4==1);}
void init(uint8_t*r,recomp_context*c){++init_calls;assert(r[0x13b429^3]==!low_capacity);assert(r[0x13b42a^3]==0);assert(r[0x13b42b^3]==expected_default);func_80008CBC_resident(r,c);}
extern "C" recomp_func_t*get_function(int32_t a){switch(uint32_t(a)){case 0x80062270:return capacity;case 0x80008cbc:return init;case 0x80058440:return intmask;case 0x8005eec0:return mode;case 0x8005ef10:return feature;case 0x8005f500:return blank;LOOKUP default:fprintf(stderr,"Unexpected %08x\n",uint32_t(a));std::abort();}}
void call(Bytes&r,recomp_func_t*f,uint32_t a=0){recomp_context c{};c.r29=int32_t(0x807ff000);c.r4=int32_t(a);c.f_odd=&c.f0.u32h;f(r.data(),&c);assert(uint32_t(c.r29)==0x807ff000);}
int main(int argc,char**argv){assert(argc==2);Bytes base(0x800000);FILE*f=fopen(argv[1],"rb");assert(f&&fread(base.data(),1,base.size(),f)==base.size());fclose(f);put(base,0x8009e02c,0x8013b418);put(base,0x8006cfb4,0x8005d8d0);base[0x6ce70^3]=base[0x6ce71^3]=0;
 for(unsigned language:{0u,1u})for(bool small:{false,true}){low_capacity=small;auto original=base,derived=base;put(original,0x8013b428,language<<30);put(derived,0x8013b428,language<<30);original[0x133676^3]=derived[0x133676^3]=language;expected_default=0;call(original,func_80008C30_resident);expected_default=!small;call(derived,iss2000_pal_fixed_high_initializer);
 assert(byte(derived,0x8013b429)==!small&&byte(derived,0x8013b42a)==0&&byte(derived,0x8013b42b)==!small);
 assert(half(derived,0x8013b42c)==320&&half(derived,0x8013b42e)==240&&word(derived,0x8013b430)==0x802e2000);
 auto compare=derived;compare[0x13b42b^3]=0;assert(compare==original); // entire8MiB; no language/preference changes.
 call(original,func_80001D44_resident,1);assert(byte(original,0x8006ce71)==0);
 call(derived,func_80001D44_resident,1);assert(byte(derived,0x8006ce71)==!small);assert(byte(derived,0x8013b42a)==0);
 if(!small){assert(byte(derived,0x8006ce70)==40);call(derived,func_80001E40_resident);assert(byte(derived,0x8013b42a)==1);assert(half(derived,0x8013b42c)==640&&half(derived,0x8013b42e)==544&&word(derived,0x8013b430)==0x80700000);assert(word(derived,0x801a07b8)==0x80500000&&word(derived,0x801a07c0)==0x805aa000&&word(derived,0x801a07c8)==0x80654000);}
 }assert(init_calls==8&&vi_mode==2&&features==2&&black==2&&mask==8);}
'''
  code=code.replace('DECLS','\n'.join(f'extern "C" void {n}(uint8_t*,recomp_context*);'for n in ns)).replace('LOOKUP','\n'.join(f'case 0x{n[5:13]}:return {n};'for n in ns if n[5:13]not in ['80062270','80008CBC']))
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);(p/'base.rdram').write_bytes(fixture);(p/'test.cpp').write_text(code);(p/'derived.cpp').write_bytes(m.derive((g/'func_80008C30_resident.c').read_bytes()));(p/'original.c').write_text('#include "recomp.h"\n// Model the original KSEG0/KSEG1 physical RAM alias used by osGetMemSize.\n#undef MEM_W\n#define MEM_W(offset,reg) (*(int32_t*)(rdram+((uint32_t(reg)+uint32_t(offset))&0x1fffffff)))\n'.replace('uint32_t(reg)','((uint32_t)(reg))').replace('uint32_t(offset)','((uint32_t)(offset))')+'\n'.join('#include '+json.dumps(str((ROOT/'.local/pal-map-01/functions'if n[5:13]=='80062270'else g)/(n+'.c')))for n in ns))
   for args in [['cc','-O1','-I'+str(h),'-c',str(p/'original.c'),'-o',str(p/'original.o')],['c++','-std=c++20','-O1','-I'+str(h),str(p/'test.cpp'),str(p/'derived.cpp'),str(p/'original.o'),'-o',str(p/'test')],[str(p/'test'),str(p/'base.rdram')]]:
    r=subprocess.run(args,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
 def test_revision_source_and_existing_output_guards(self):
  m=self.load();rom=ROOT/'.local/inputs/pal-en-de/rom.z64';source=ROOT/'.local/pal-map-bound-01/functions/func_80008C30_resident.c'
  if not all(p.is_file()for p in [rom,source]):self.skipTest('PrivatePAL inputs required')
  with self.assertRaises(ValueError):m.derive(source.read_bytes()+b'\n')
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);receipt=m.prepare(rom,source,p/'result');self.assertEqual(receipt,m.prepare(rom,source,p/'result'));self.assertEqual(receipt['entry'],'iss2000_pal_fixed_high_initializer');self.assertTrue((p/'result/pal_fixed_high_initializer.cpp').is_file());(p/'result/extra').write_text('preserve')
   with self.assertRaises(ValueError):m.prepare(rom,source,p/'result')
   (p/'bad.z64').write_bytes(bytes(0x1000000))
   with self.assertRaises(ValueError):m.prepare(p/'bad.z64',source,p/'foreign')
   self.assertFalse((p/'foreign').exists())

 def test_genuine_selector_resources_row_one_high_and_original_commit(self):
  import struct
  rom=ROOT/'.local/inputs/pal-en-de/rom.z64';g=ROOT/'.local/pal-map-bound-01/functions';h=ROOT/'.local/deps/N64Recomp/include';snapshot=ROOT/'.local/training-timing-01/options38-completed.rdram'
  if not all(p.is_file()for p in [rom,snapshot,h/'recomp.h'])or not shutil.which('c++'):self.skipTest('Private originalPAL selector fixture required')
  image=rom.read_bytes();self.assertEqual(hashlib.sha256(image).hexdigest(),self.load().ROM_SHA256)
  sections=json.loads((g.parent/'section-analysis.json').read_text());section=next(s for s in sections if s['rom']==0x3b47e0)
  fixture=bytearray(snapshot.read_bytes())
  for n,v in enumerate(image[section['rom']:section['rom']+section['load_size']]):fixture[((section['vram']+n)&0x7fffff)^3]=v
  ns=['func_80007BE0_resident','func_80007BF8_resident','func_80007C2C_resident','func_802A5F4C_overlay_3b47e0_8029eea0','func_801B0000_overlay_2dee70_801ad820','func_801B0038_overlay_2dee70_801ad820']
  commit=(g/'func_802A63DC_overlay_3b47e0_8029eea0.c').read_text().split('{',1)[1].rsplit('}',1)[0]
  # Genuine original commit up to its unchanged persistence/loading boundary.
  # No SDK or Pak calls are replaced or claimed to execute in this fixture.
  code=r'''#include "recomp.h"
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
DECLS
extern "C" recomp_func_t*get_function(int32_t a){switch(uint32_t(a)){LOOKUP default:std::abort();}}
void commit(uint8_t*rdram,recomp_context*ctx){COMMIT}
using Bytes=std::vector<uint8_t>;
uint32_t word(const Bytes&r,uint32_t a){uint32_t v;memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
uint16_t half(const Bytes&r,uint32_t a){uint16_t v;memcpy(&v,r.data()+((a&0x7fffff)^2),2);return v;}
void put(Bytes&r,uint32_t a,uint32_t v){memcpy(r.data()+(a&0x7fffff),&v,4);}
void byte(Bytes&r,uint32_t a,uint8_t v){r[(a&0x7fffff)^3]=v;}
void call(Bytes&r,uint32_t f,uint32_t a,uint32_t b){recomp_context c{};c.r29=int32_t(0x807ff000);c.r4=int32_t(a);c.r5=int32_t(b);c.f_odd=&c.f0.u32h;get_function(f)(r.data(),&c);}
int main(int argc,char**argv){assert(argc==2);Bytes base(0x800000);FILE*f=fopen(argv[1],"rb");assert(f&&fread(base.data(),1,base.size(),f)==base.size());fclose(f);
 // Exact Resolution resources: row0 Low at(136,112), row1 High at(136,89).
 // Labels are index133, distinct from Language index134.
 for(unsigned row=0;row<2;++row){auto r=base;const uint32_t wordObject=0x8013c47c,bar=wordObject+0x3c,context=0x807f0000;
  call(r,0x80007be0,0x802b03c8,0);call(r,0x80007bf8,wordObject,row?4:3);call(r,0x80007bf8,bar,1);
  assert(word(r,wordObject+20)==0x802d22c0&&word(r,wordObject+48)==(row?0x802b0368u:0x802b0374u));
  assert(half(r,word(r,wordObject+48)+4)==136&&half(r,word(r,wordObject+48)+6)==(row?89:112));
  put(r,bar+0x38,context);byte(r,0x802b10f0,row);call(r,0x802a5f4c,bar,0);
  assert(half(r,bar+0x20)==77&&half(r,bar+0x24)==(row?87:111));
  byte(r,0x802b10f0,row);put(r,0x8013b428,0xe1234567);recomp_context c{};c.r29=int32_t(0x807ff000);commit(r.data(),&c);
  assert(word(r,0x8013b428)==(0xe1234500u|row));
 }
}
'''
  code=code.replace('DECLS','\n'.join(f'extern "C" void {n}(uint8_t*,recomp_context*);'for n in ns)).replace('LOOKUP','\n'.join(f'case 0x{n[5:13]}:return {n};'for n in ns)).replace('COMMIT',commit)
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);(p/'base.rdram').write_bytes(fixture);(p/'test.cpp').write_text(code);(p/'original.c').write_text('\n'.join('#include '+json.dumps(str(g/(n+'.c')))for n in ns))
   result=subprocess.run(['cc','-O1','-I'+str(h),'-c',str(p/'original.c'),'-o',str(p/'original.o')],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
   result=subprocess.run(['c++','-std=c++20','-O1','-I'+str(h),str(p/'test.cpp'),str(p/'original.o'),'-o',str(p/'test')],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
   result=subprocess.run([str(p/'test'),str(p/'base.rdram')],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
