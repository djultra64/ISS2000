"""Original work: djultra64. Save terminology through genuine PAL font code."""
from pathlib import Path
import json,struct,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class StorageTextTests(unittest.TestCase):
 def test_exact_message_transaction_original_font_and_unrelated_names(self):
  from tools.prepare_pal_storage_text import prepare,profiles
  rom=ROOT/'.local/inputs/pal-en-de/rom.z64';image=rom.read_bytes();owned=profiles(image)
  g=ROOT/'.local/pal-map-bound-01/functions';h=ROOT/'.local/deps/N64Recomp/include'
  sections=json.loads((g.parent/'section-analysis.json').read_text());functions={f['vram']:(s,f)for s in sections for f in s['functions']};pending=[0x80048660];seen=set()
  while pending:
   pc=pending.pop()
   if pc in seen:continue
   seen.add(pc);s,f=functions[pc];a=s['rom']+pc-s['vram']
   for op in struct.unpack_from('>'+str(f['size']//4)+'I',image,a):
    if op>>26==3:pending.append(0x80000000|((op&0x3ffffff)<<2))
  paths={pc:next(g.glob(f'func_{pc:08X}_*.c'))for pc in seen}
  code=r'''#include "recomp.h"
#include <cassert>
#include <cstdio>
#include <cstring>
#include <vector>
DECL
#include "pal_storage_text.cpp"
extern "C" recomp_func_t*get_function(int32_t a){switch(uint32_t(a)){LOOKUP default:fprintf(stderr,"Unknown original %08x\n",uint32_t(a));assert(false);return nullptr;}}
extern "C" void do_break(uint32_t){assert(false);}extern "C" void switch_error(const char*,uint32_t,uint32_t){assert(false);}
using Bytes=std::vector<uint8_t>;
Bytes load(const char*p){FILE*f=fopen(p,"rb");assert(f);fseek(f,0,SEEK_END);size_t n=ftell(f);rewind(f);Bytes b(n);assert(fread(b.data(),1,n,f)==n);fclose(f);return b;}
void put(Bytes&r,uint32_t a,uint32_t v){memcpy(r.data()+(a&0x7fffff),&v,4);}uint32_t word(const Bytes&r,uint32_t a){uint32_t v;memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
void half(Bytes&r,uint32_t a,uint16_t v){memcpy(r.data()+((a&0x7fffff)^2),&v,2);}void byte(Bytes&r,uint32_t a,uint8_t v){r[(a&0x7fffff)^3]=v;}
int main(int argc,char**argv){assert(argc==3);auto fixture=load(argv[1]);auto expected=load(argv[2]);assert(fixture.size()==0x800000&&expected.size()==0x800000);constexpr uint32_t object=0x800a3e00;
CASES
 // The exact source/bytes are insufficient for a numeric/font-index object or
 // malformed pointer. These cases preserve the entire guest memory image.
 for(unsigned kind=0;kind<4;++kind){auto r=fixture;put(r,object+0x14,0x802dd67c);if(kind==0)byte(r,object+5,2);if(kind==1)put(r,object+0x14,0x802dd67d);if(kind==2)byte(r,0x802dd67a,0x7f);if(kind==3)put(r,object+0x14,0x001dd67c);auto before=r;assert(!iss2000_pal_storage_text(r.data(),object)&&r==before);}
 for(auto pointer:{0ull,0x00000001800a3e00ull,0xffffffff800a3e01ull,0x807ffff0ull}){auto r=fixture;assert(!iss2000_pal_storage_text(r.data(),pointer)&&r==fixture);}
 // A surname containing Pak is unrelated, and a Controller1 hardware port name
 // remains unchanged. Neither is part of obsolete storage terminology.
 for(auto source:{0x8024a92cu,0x801f2210u}){auto r=fixture;put(r,object+0x14,source);auto before=r;assert(!iss2000_pal_storage_text(r.data(),object)&&r==before);}
}
'''
  cases=[];fixture=bytearray((ROOT/'.local/training-timing-01/options38-completed.rdram').read_bytes());expected=bytearray(fixture);fixture[0xa3e00:0xa3e24]=bytes(0x24);expected[0xa3e00:0xa3e24]=bytes(0x24)
  for m in owned:
   a=m['guest']&0x7fffff
   for n,value in enumerate(m['original']):fixture[(a+n)^3]=value
   for n,value in enumerate(m['changed']):expected[(a+n)^3]=value
  for i,m in enumerate(owned):
   p=m['pointers'][0];a=m['guest']&0x7fffff;n=m['size'];variants=''.join('static constexpr uint8_t input'+str(i)+'_'+str(j)+'[]={'+','.join(map(str,b))+'};'for j,b in enumerate(m['variants']))
   for v,variant in enumerate(m['variants']):
    if v==0:cases.append(variants)
    cases.append('{auto r=fixture;for(unsigned n=0;n<'+str(n)+';++n)byte(r,0x'+f'{m["guest"]:X}'+'u+n,input'+str(i)+'_'+str(v)+'[n]);put(r,object+0x14,0x'+f'{p:X}'+');auto before=r;assert(iss2000_pal_storage_text(r.data(),object));for(unsigned n=0;n<r.size();++n)assert(r[n]==(n>='+str(a)+'&&(n^3)<'+str(a+n)+'?expected[n]:before[n]));auto applied=r;assert(iss2000_pal_storage_text(r.data(),object)&&r==applied);}')
   # Genuine entire original renderer for every one of the43 guarded messages.
   cases.append('{auto r=fixture;put(r,object+0x14,0x'+f'{p:X}'+');byte(r,object+4,2);half(r,object+0x22,0xffff);half(r,object+0xe,0);half(r,object+0x10,8);put(r,0x800a4aa4,0x800d0320);put(r,0x8009e0c8,0x800d0328);assert(iss2000_pal_storage_text(r.data(),object));recomp_context c{};c.r4=int32_t(object);c.r29=int32_t(0x800a3d00);c.f_odd=&c.f0.u32h;func_80048660_resident(r.data(),&c);const auto end=word(r,0x8009e0c8);assert(end>0x800d0328&&end<0x800e0328);unsigned rects=0;for(unsigned q=0x800d0328;q<end;q+=8){if(word(r,q)>>24==0xe4){++rects;q+=16;}}assert(rects>0);}')
  code=code.replace('DECL','\n'.join(f'extern "C" void {p.stem}(uint8_t*,recomp_context*);'for p in paths.values())).replace('LOOKUP','\n'.join(f'case 0x{pc:X}:return {p.stem};'for pc,p in paths.items())).replace('CASES','\n'.join(cases))
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);receipt=prepare(rom,p/'out');self.assertEqual(receipt,prepare(rom,p/'out'));(p/'out/test.cpp').write_text(code);(p/'original.c').write_text('\n'.join('#include '+json.dumps(str(v))for v in paths.values()));(p/'fixture.rdram').write_bytes(fixture);(p/'expected.rdram').write_bytes(expected)
   q=subprocess.run(['cc','-O1','-fno-strict-aliasing','-I'+str(h),'-c',str(p/'original.c'),'-o',str(p/'original.o')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
   q=subprocess.run(['c++','-std=c++20','-O1','-I'+str(h),str(p/'out/test.cpp'),str(p/'original.o'),'-lm','-o',str(p/'check')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
   q=subprocess.run([str(p/'check'),str(p/'fixture.rdram'),str(p/'expected.rdram')],capture_output=True,text=True,timeout=30);self.assertEqual(q.returncode,0,q.stderr)
   # Product negative control: adapter must perform the exact owned edit.
   derived=p/'out/pal_storage_text.cpp';derived.write_text(derived.read_text().replace('ram[(0x','ram[(1+0x'))
   q=subprocess.run(['c++','-std=c++20','-O1','-I'+str(h),str(p/'out/test.cpp'),str(p/'original.o'),'-lm','-o',str(p/'bad')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
   q=subprocess.run([str(p/'bad'),str(p/'fixture.rdram'),str(p/'expected.rdram')],capture_output=True,text=True);self.assertNotEqual(q.returncode,0)
   with self.assertRaises(ValueError):prepare(rom,p/'out')
 def test_source_guard_controls_and_complete_obsolete_word_inventory(self):
  from tools.prepare_pal_storage_text import profiles,change_message,generate
  from tools.prepare_pal_auto_storage_ui import encode
  image=(ROOT/'.local/inputs/pal-en-de/rom.z64').read_bytes();owned=profiles(image)
  self.assertEqual(len(owned),43)
  for m in owned:
   for n,value in enumerate(m['original']):
    if value>=0xf5:self.assertEqual(m['changed'][n:n+2],m['original'][n:n+2])
   for term in ['Controller Pak','Rumble Pak','game notes','notes','pages','note']:
    self.assertNotIn(encode(term),m['changed'])
   self.assertEqual(len(m['changed']),m['size'])
  with self.assertRaises(ValueError):generate(image[:-1])
  with self.assertRaises(ValueError):change_message(bytes([0,255,17]),['too long'])
  with self.assertRaises(ValueError):change_message(bytes([0,246,0,255,17]),['x'])
 def test_all_known_english_storage_term_occurrences_have_exact_profiles(self):
  from tools.prepare_pal_storage_text import profiles
  from tools.prepare_pal_auto_storage_ui import encode
  image=(ROOT/'.local/inputs/pal-en-de/rom.z64').read_bytes();owned=profiles(image)
  # These are the original English text domains, not a global binary replace:
  # German/French counterparts share some nouns; player surnames are unrelated.
  domains=[(0x316c18,0x316d00),(0x329820,0x329ad2),
           (0x50c3f8,0x5103d0),(0x514b56,0x515108)]
  terms=['Controller Pak','controller pak','Rumble Pak','game notes','Game notes',
         'Game note','notes','pages','Create note','Note created',
         'Note required','Play without note']
  occurrences=0
  for start,end in domains:
   for term in terms:
    token=encode(term);position=start
    while(position:=image.find(token,position,end))>=0:
     self.assertTrue(any(m['rom']<=position and position+len(token)<=m['rom']+m['size']for m in owned),f'Uncovered English storage wording{term}@{position:X}')
     occurrences+=1;position+=len(token)
  self.assertEqual(occurrences,57)
