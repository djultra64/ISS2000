"""Original project work: djultra64. Original High leaf and real RT64 math."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / '.local/pal-map-bound-01/functions/func_807AA008_overlay_515890_807aa000.c'
HEADER = ROOT / '.local/deps/N64Recomp/include'
RT64 = ROOT / '.local/deps/rt64'


def load():
    spec = importlib.util.spec_from_file_location('pal_high_sprites', ROOT / 'tools/prepare_pal_high_sprites.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@unittest.skipUnless(SOURCE.is_file() and (HEADER/'recomp.h').is_file() and shutil.which('c++'),
                     'Private original High CPU source/header and C++ compiler required')
class HighSpriteTests(unittest.TestCase):
    def test_original_cpu_context_and_geometry_only_four_copy_edge_words_change(self):
        m = load()
        renderer = (RT64/'src/render/rt64_framebuffer_renderer.cpp').read_text()
        viewport = re.search(r'    RenderViewport convertViewportRect\(.*?\n    \}', renderer, re.S).group()
        common = (RT64/'src/common/rt64_common.cpp').read_text()
        methods = '\n'.join(re.search(r'    int32_t FixedRect::'+name+r'\(.*?\n    \}', common, re.S).group()
                            for name in ['left','top','right','bottom','width','height'])
        code = r'''#include "recomp.h"
#include <vector>
#include <cassert>
#include <cstring>
#include <cmath>
#include <cstdio>
#include <algorithm>
#define F3DEX_GBI_2
#include "rt64_extended_gbi.h"
using Bytes=std::vector<uint8_t>;
uint32_t word(const Bytes&r,uint32_t a){uint32_t v;std::memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
void put(Bytes&r,uint32_t a,uint32_t v){std::memcpy(r.data()+(a&0x7fffff),&v,4);}
void byte(Bytes&r,uint32_t a,uint8_t v){r[(a&0x7fffff)^3]=v;}
void half(Bytes&r,uint32_t a,uint16_t v){std::memcpy(r.data()+((a&0x7fffff)^2),&v,2);}
struct FixedRect {int ulx,uly,lrx,lry;bool isNull()const{return false;}
 int32_t left(bool)const;int32_t top(bool)const;int32_t right(bool)const;int32_t bottom(bool)const;
 int32_t width(bool,bool)const;int32_t height(bool,bool)const;};
namespace hlslpp{struct float2{float x,y;float operator[](int i)const{return i?y:x;}};}
struct RenderViewport{float x,y,width,height;};
''' + methods + '\n' + viewport + '\n' + SOURCE.read_text() + '\n' + m.derive(SOURCE.read_bytes()).decode() + r'''
recomp_context context(Bytes&r,uint32_t head=0x800D0328,uint32_t pointer=0x8009E0C8){
 recomp_context c{};c.r4=(int32_t)pointer;c.r5=32*4;c.r6=39*4;c.r7=196*4;c.r29=(int32_t)0x807ff000;
 put(r,pointer,head);put(r,0x8009E02C,0x8013B418);byte(r,0x8013B42A,1);half(r,0x8013B42C,640);half(r,0x8013B42E,544);
 half(r,0x800BDB26,0);put(r,0x807ff010,211*4);put(r,0x807ff014,0x7900);put(r,0x807ff018,0);
 put(r,0x807ff01c,4096);put(r,0x807ff020,1024);put(r,0x807ff024,0x807fe000);put(r,0x807ff028,0x8013C530);
 put(r,0x8013C538,0x00026642);byte(r,0x807fe001,8);byte(r,0x807fe002,16);return c;
}
FixedRect copyRect(const Bytes&r,uint32_t p){auto a=word(r,p),b=word(r,p+4);return{int((b>>12)&4095)&~3,int(b&4095)&~3,int((a>>12)&4095)|3,int(a&4095)|3};}
int wrap(int v,int mask,bool mirror,bool clamp,int limit){if(clamp)v=std::clamp(v,0,limit);auto mod=[](int a,int b){return(a%b+b)%b;};return mirror&&mod(v,mask*2)>=mask?(mask-1)-mod(v,mask):mod(v,mask);}
int main(){
 Bytes base(0x800000);auto c=context(base);auto old=base,fixed=base;auto a=c,b=c;
 func_807AA008_overlay_515890_807aa000(old.data(),&a);iss2000_pal_high_sprite_edges(fixed.data(),&b);
 assert(std::memcmp(&a,&b,sizeof a)==0);assert(word(old,0x8009E0C8)==0x800D0370&&word(fixed,0x8009E0C8)==0x800D0370);
 OBSERVED_CHAIN_ASSERTIONS
 unsigned changed=0;for(uint32_t p=0;p<0x800000;p+=4)if(word(old,p)!=word(fixed,p)){
  assert(p==0xd0328+36||p==0xd0328+44||p==0xd0328+60||p==0xd0328+68);++changed;
 }
 assert(changed==4);for(unsigned i=0;i<24;i+=4)assert(word(old,0x800D0328+i)==word(fixed,0x800D0328+i));
 for(unsigned i:{0u,4u,24u,28u,48u,52u})assert(word(old,0x800D0328+i)==word(fixed,0x800D0328+i));
 const auto main=copyRect(old,0x800D0328),right=copyRect(old,0x800D0340),bottom=copyRect(old,0x800D0358);
 assert(main.right(true)==78&&right.left(true)==78&&right.right(true)==80);
 assert(bottom.top(true)==422&&bottom.bottom(true)==424); // These contain real final asset pixels; truncation crops them.
 unsigned badBefore=0,badAfter=0;
 for(float s:{1.f,1.5f,720.f/544,1080.f/544,1440.f/544,2160.f/544})for(float aspect:{1.f,.75f}){
  for(bool vertical:{false,true}){
   const auto offset=vertical?48u:24u;const auto rect=copyRect(old,0x800D0328+offset);
   auto view=convertViewportRect(rect,{s,s},640,aspect,1,0,G_EX_ORIGIN_NONE,G_EX_ORIGIN_NONE);
   const int pixels=int(vertical?view.height:view.width);assert(pixels>0);
   const int extent=vertical?rect.height(true,true):rect.width(true,true);
   for(bool mirror:{false,true})for(bool clamp:{false,true})for(int j=0;j<pixels;++j){
    auto sample=[&](const Bytes&r){auto uv=word(r,0x800D0328+offset+12),deriv=word(r,0x800D0328+offset+20);
     int u=vertical?int16_t(uv):int16_t(uv>>16),d=vertical?int16_t(deriv):int16_t(deriv>>16)>>2;
     // RDP integer lrs/lrt and original renderer halfPixelOffset: pixel0 samples exactly the start UV.
     int end=((u<<7)+d*(extent<<2))>>7;float value=u/32.f+(end-u)/32.f*float(j)/pixels;
     return int(std::floor(value));};
    const int expected=vertical?15:975;
    badBefore+=wrap(sample(old),512,mirror,clamp,vertical?23:79)!=wrap(expected,512,mirror,clamp,vertical?23:79);
    badAfter+=wrap(sample(fixed),512,mirror,clamp,vertical?23:79)!=wrap(expected,512,mirror,clamp,vertical?23:79);
   }
  }
 }
 assert(badBefore>0&&badAfter==0);std::printf("Original edge samples differ:%u; corrected:%u\n",badBefore,badAfter);
 // One-cycle rectangles use exclusive right/bottom endpoints. The original
 // repair strips overlap the next sprite chunk, doubling translucent borders.
 {Bytes r(0x800000);auto ctx=context(r);put(r,0x8013C538,0x04026642);half(r,0x800BDB26,2);
  ctx.r6=40*4;put(r,0x807ff010,212*4);put(r,0x807ff01c,1024);
  auto before=r,after=r;auto x=ctx,y=ctx;
  func_807AA008_overlay_515890_807aa000(before.data(),&x);iss2000_pal_high_sprite_edges(after.data(),&y);
  assert(std::memcmp(&x,&y,sizeof x)==0);
  unsigned differences=0;
  for(uint32_t at=0;at<0x800000;at+=4)if(word(before,at)!=word(after,at)){
   assert(at==0xd0328+24||at==0xd0328+48);++differences;
  }
  assert(differences==2);
  auto rect=[&](const Bytes&ram,unsigned offset){auto a=word(ram,0x800D0328+offset),b=word(ram,0x800D0328+offset+4);
   return FixedRect{int((b>>12)&4095),int(b&4095),int((a>>12)&4095),int(a&4095)};};
  assert(rect(before,0).left(true)==64&&rect(before,0).right(true)==80);
  assert(rect(before,24).left(true)==80&&rect(before,24).right(true)==81);
  assert(rect(after,24).left(true)==80&&rect(after,24).right(true)==80);
  assert(rect(after,48).top(true)==424&&rect(after,48).bottom(true)==424);
  // Every main rectangle word and all ST/derivative words stay identical.
  for(unsigned i=0;i<72;i+=4)if(i!=24&&i!=48)assert(word(before,0x800D0328+i)==word(after,0x800D0328+i));
  for(float scale:{1.f,1080.f/524,2160.f/524})for(bool vertical:{false,true}){
   auto a=convertViewportRect(rect(after,vertical?48:24),{scale,scale},640,1,1,0,G_EX_ORIGIN_NONE,G_EX_ORIGIN_NONE);
   assert((vertical?a.height:a.width)==0);
  }
 }
 // Foreign modes, Low, wrong frame identity/dimensions, foreign head pointer,
 // unaligned/insufficient reservations preserve the whole original result.
 for(int variant=0;variant<10;++variant){Bytes r(0x800000);uint32_t head=0x800D0328,ptr=0x8009E0C8;
  if(variant==7)ptr=0x8009E0D0;if(variant==8)head+=4;if(variant==9)head=0x800E0328-64;
  auto ctx=context(r,head,ptr);switch(variant){
   case 0:put(r,0x8013C538,19u<<25);break;case 1:put(r,0x8013C538,2u<<25);break;
   case 2:byte(r,0x8013B42A,0);break;case 3:half(r,0x800BDB26,1);break;
   case 4:half(r,0x8013B42C,320);break;case 5:half(r,0x8013B42E,480);break;
   case 6:put(r,0x8009E02C,0x8013B400);break;
  }
  auto first=r,second=r;auto x=ctx,y=ctx;func_807AA008_overlay_515890_807aa000(first.data(),&x);iss2000_pal_high_sprite_edges(second.data(),&y);
  assert(first==second&&std::memcmp(&x,&y,sizeof x)==0);
 }
 for(uint32_t head:{0x800D0328u,0x800E0328u-72u,0x800E0388u,0x800F0388u-72u}){
  Bytes r(0x800000);auto ctx=context(r,head);iss2000_pal_high_sprite_edges(r.data(),&ctx);assert((word(r,head+44)>>16)==0&&uint16_t(word(r,head+68))==0);
 }
 for(unsigned offset:{0u,8u,16u,24u,32u,40u,48u,56u,64u,28u,52u}){
  auto tampered=old;put(tampered,0x800D0328+offset,word(tampered,0x800D0328+offset)^0x1000u);
  if(offset%24==0)put(tampered,0x800D0328+offset,word(tampered,0x800D0328+offset)^0x10000000u);
  auto before=tampered;assert(!iss2000_pal_high_fix_edge_words(tampered.data(),0x800D0328));assert(tampered==before);
 }
}
'''
        observed = ROOT/'.local/training-timing-01/free-training-high.rdram'
        comparison = ''
        if observed.is_file():
            ram = observed.read_bytes()
            self.assertEqual(hashlib.sha256(ram).hexdigest(), '27052af3407047ff9ad936a995cc53512ab153e0338561ef0d98fd6009a7b65e')
            words = struct.unpack_from('<18I', ram, 0xD2520)
            comparison = 'const uint32_t actual[18]={' + ','.join(hex(v)+'u' for v in words) + '};for(unsigned i=0;i<18;++i)assert(word(old,0x800D0328+i*4)==actual[i]);'
        code = code.replace('OBSERVED_CHAIN_ASSERTIONS', comparison)
        # Only this isolated original CPU fixture executes; no game launches.
        with tempfile.TemporaryDirectory(prefix='iss2000-high-edges-') as folder:
            p = Path(folder)
            (p/'test.cpp').write_bytes(code.encode())
            built = subprocess.run(['c++','-std=c++20','-O2','-I'+str(HEADER),'-I'+str(RT64/'include'),str(p/'test.cpp'),'-o',str(p/'test')],capture_output=True,text=True)
            self.assertEqual(built.returncode,0,built.stderr)
            run = subprocess.run([str(p/'test')],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)

    def test_source_rom_and_immutable_output_guards(self):
        m = load()
        rom = ROOT/'.local/inputs/pal-en-de/rom.z64'
        if not rom.is_file():self.skipTest('Private PAL ROM required')
        with self.assertRaises(ValueError):m.derive(SOURCE.read_bytes()+b'\n')
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder);receipt=m.prepare(rom,SOURCE,p/'out')
            self.assertEqual(receipt,m.prepare(rom,SOURCE,p/'out'))
            self.assertEqual(hashlib.sha256((p/'out/pal_high_sprite_edges.cpp').read_bytes()).hexdigest(),receipt['generated_sha256'])
            self.assertNotIn(b'\r',(p/'out/pal_high_sprite_edges.cpp').read_bytes())
            (p/'out/extra').write_bytes(b'preserve')
            with self.assertRaises(ValueError):m.prepare(rom,SOURCE,p/'out')
            (p/'foreign.z64').write_bytes(bytes(0x1000000))
            with self.assertRaises(ValueError):m.prepare(p/'foreign.z64',SOURCE,p/'foreign')
            self.assertFalse((p/'foreign').exists())
