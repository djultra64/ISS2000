"""Original project work: djultra64. Saved Data labels through genuine original CPU sprites."""
from pathlib import Path
import json,struct,shutil,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
CODE=r'''#include "runtime/pal_team_saved_data.hpp"
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string_view>
#include <vector>
DECLS
using namespace iss2000;using Bytes=std::vector<uint8_t>;
extern "C" recomp_func_t*get_function(int32_t a){switch(uint32_t(a)){LOOKUP default:fprintf(stderr,"Unknown original %08x\n",uint32_t(a));std::abort();}}
extern "C" void do_break(uint32_t){std::abort();}extern "C" void switch_error(const char*,uint32_t,uint32_t){std::abort();}
uint32_t word(const Bytes&r,uint32_t a){uint32_t v;memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
void put(Bytes&r,uint32_t a,uint32_t v){memcpy(r.data()+(a&0x7fffff),&v,4);}
uint8_t byte(const Bytes&r,uint32_t a){return r[(a&0x7fffff)^3];}
Bytes load(const char*p){FILE*f=fopen(p,"rb");assert(f);fseek(f,0,SEEK_END);size_t n=ftell(f);rewind(f);Bytes b(n);assert(fread(b.data(),1,n,f)==n);fclose(f);return b;}
unsigned pixel(const Bytes&r,uint32_t a,unsigned width,unsigned x,unsigned y){unsigned n=y*width+x;auto p=byte(r,a+n/2);return n&1?p&15:p>>4;}
int main(int argc,char**argv){assert(argc==3);auto base=load(argv[1]);put(base,0x800a4aa4,0x800d0320);put(base,0x8009e0c8,0x800d0328);
 const uint32_t objects[]{0x8013d8e0,0x8013d91c,0x8013cd64,0x8013cda0};
 for(unsigned k=0;k<4;++k){auto r=base;if(k==1)put(r,0x8013d91c+48,0x801be0f4);recomp_context c{};c.r4=int32_t(objects[k]);c.r29=int32_t(0x800a4000);c.f_odd=&c.f0.u32h;const auto caller=c;
  auto label=pal_team_saved_data_label(r,c.r4);assert(label&&label->text==(k<2?"Saved Data":"Load Saved Data"));
  assert(label->width==(k<2?40:80)&&label->height==(k<2?12:8));assert(label->x>=0&&label->y>=0&&label->x+label->width<=320&&label->y+label->height<=240);
  if(k>=2){const unsigned strip=word(base,objects[k]+48);const int left=int16_t((byte(base,strip+4)<<8)|byte(base,strip+5));assert(label->x>=left+4&&label->x+label->width<=left+84);}
  assert(draw_pal_team_saved_data(r,c,func_80041B50_resident));assert(memcmp(&c,&caller,sizeof(c))==0);assert(memcmp(r.data()+0xa3a00,base.data()+0xa3a00,0x600)==0);
  assert(memcmp(r.data()+0x270140,base.data()+0x270140,0x8d00)==0);assert(word(r,objects[k]+48)==(k==1?0x801be0f4:word(base,objects[k]+48)));assert(memcmp(r.data()+0x1be000,base.data()+0x1be000,0x2000)==0);assert(memcmp(r.data()+0x3db400,base.data()+0x3db400,0x2000)==0);
  const auto head=0x800d0328u;assert(word(r,head)==0xde010000);const auto first=word(r,head+4),end=word(r,0x8009e0c8);assert(first>head&&end>first&&end<=0x800e0328);
  // Payload is the literal original six-pixel native font2 glyphs, copied at
  // unit scale. Only the genuine original sprite renderer applies scaling.
  const auto image=head+8;unsigned at=0;for(char ch:label->text){unsigned code=ch==' '?0:ch>='A'&&ch<='Z'?ch-'A'+11:ch-'a'+37;
   for(unsigned y=0;y<12;++y)for(unsigned x=0;x<6;++x)assert(pixel(r,image,128,at+x,y)==pixel(base,0x80352800+(code/2)*96,16,(code&1)*8+x,y));at+=6;}
  for(unsigned y=0;y<16;++y)for(unsigned x=0;x<128;++x)if(y>=12||x>=at)assert(pixel(r,image,128,x,y)==0);
  unsigned rects=0;uint32_t texture=0;for(unsigned p=first;p<end;p+=8){auto a=word(r,p),b=word(r,p+4);if(a>>24==0xfd)texture=b&0x7fffff;if(a>>24!=0xe4)continue;
   ++rects;assert(texture==(image&0x7fffff));const int x=(b>>12&4095)/4,y=(b&4095)/4,rx=(a>>12&4095)/4,by=(a&4095)/4;
   assert(x>=label->x-1&&y>=label->y-1&&rx<=label->x+label->width+1&&by<=label->y+label->height+1);assert(rx-x==label->width&&by-y==label->height);p+=16;}
  assert(rects==(k<2?5u:1u)); // four original dark-blue outline passes and fill
 }
 {auto r=base;recomp_context c{};c.r4=int32_t(0x8013d91c);c.r29=int32_t(0x800a4000);assert(!pal_team_saved_data_label(r,c.r4));assert(!draw_pal_team_saved_data(r,c,func_80041B50_resident));assert(r==base);}
 // Alpha remains the actual original object alpha; RGB fade multiplies the
 // original cyan and blue colors instead of overriding transition dimming.
 for(unsigned alpha:{0u,127u,255u}){auto r=base;r[(0x13d8e0+17)^3]=alpha;for(unsigned i=0;i<3;++i)r[(0x13d8e0+14+i)^3]=128;
  recomp_context c{};c.r4=int32_t(0x8013d8e0);c.r29=int32_t(0x800a4000);c.f_odd=&c.f0.u32h;assert(draw_pal_team_saved_data(r,c,func_80041B50_resident));
  unsigned colors=0;uint32_t last=0;for(unsigned p=word(r,0x800d032c);p<word(r,0x8009e0c8);p+=8)if(word(r,p)>>24==0xfa){++colors;last=word(r,p+4);assert((last&255)==alpha);}assert(colors==5&&last==((uint32_t(115*128/255)<<24)|(uint32_t(255*128/255)<<16)|(uint32_t(255*128/255)<<8)|alpha));
 }
 // Upper strips and lower captions can fade, but original source/geometry,
 // owner, font, framebuffer, stack and complete Gfx budget remain required.
 for(unsigned n=0;n<13;++n){auto r=base;recomp_context c{};c.r4=int32_t(objects[0]);c.r29=int32_t(0x800a4000);c.f_odd=&c.f0.u32h;
  if(n==0)c.r4=int32_t(0x8013d958);if(n==1)put(r,0x802a0c48,0);if(n==2)put(r,0x80077390,0);if(n==3)put(r,0x8013d8e0+48,0x801be094);if(n==4)put(r,0x80352800,word(r,0x80352800)^1);if(n==5)put(r,0x80271940,word(r,0x80271940)^1);if(n==6)put(r,0x803dc4e0,word(r,0x803dc4e0)^1);if(n==7)put(r,0x8009e0c8,0x800e0300);if(n==8)c.r29=0x800a0300;if(n==9)c.f_odd=reinterpret_cast<uint32_t*>(r.data());if(n==10)r[0x13b42a^3]=1;if(n==11)put(r,0x8013d8e0+8,word(r,0x8013d8e0+8)|0x40000000);if(n==12)put(r,0x80041b50,0);
  auto before=r;assert(!draw_pal_team_saved_data(r,c,func_80041B50_resident));assert(r==before);
 }
 auto training=load(argv[2]);put(training,0x800a4aa4,0x800d0320);put(training,0x8009e0c8,0x800d0328);recomp_context c{};c.r4=int32_t(0x8013ca94);c.r29=int32_t(0x800a4000);c.f_odd=&c.f0.u32h;
 auto label=pal_team_saved_data_label(training,c.r4);assert(label&&label->text=="Saved Data"&&label->x==82&&label->y==198&&label->width==40&&label->height==12);const auto before=training;
 assert(draw_pal_team_saved_data(training,c,func_80041B50_resident));assert(memcmp(training.data()+0x13ca94,before.data()+0x13ca94,60)==0);assert(memcmp(training.data()+0x270140,before.data()+0x270140,0x8d00)==0);
}
'''
class TeamSavedDataTests(unittest.TestCase):
 def test_original_team_captions_use_exact_resident_glyphs_and_original_sprite_commands(self):
  self.assertTrue((ROOT/'src/runtime/pal_team_saved_data.cpp').is_file(),'Missing genuine original-font Saved Data sprite adapter')
  g=ROOT/'.local/pal-map-bound-01/functions';h=ROOT/'.local/deps/N64Recomp/include';rom=ROOT/'.local/inputs/pal-en-de/rom.z64';snapshot=ROOT/'.local/hidden-test-01/team16-completed.rdram';mb=ROOT/'.local/runtime-deps-build/librecomp/miniz'
  if not shutil.which('c++')or not all(p.is_file()for p in[rom,snapshot,h/'recomp.h',mb/'libminiz.a']):self.skipTest('Original private PAL CPU/compiler fixtures required')
  image=rom.read_bytes();sections=json.loads((g.parent/'section-analysis.json').read_text());functions={f['vram']:(s,f)for s in sections for f in s['functions']};pending=[0x80041b50];seen=set()
  while pending:
   pc=pending.pop()
   if pc in seen:continue
   seen.add(pc);s,f=functions[pc];a=s['rom']+pc-s['vram']
   for op in struct.unpack_from('>'+str(f['size']//4)+'I',image,a):
    if op>>26==3:pending.append(0x80000000|((op&0x3ffffff)<<2))
  paths={pc:next(g.glob(f'func_{pc:08X}_*.c'))for pc in seen};code=CODE.replace('DECLS','\n'.join(f'extern "C" void {p.stem}(uint8_t*,recomp_context*);'for p in paths.values())).replace('LOOKUP','\n'.join(f'case 0x{pc:08X}:return {p.stem};'for pc,p in paths.items()))
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);(p/'test.cpp').write_text(code);(p/'original.c').write_text('\n'.join('#include '+json.dumps(str(v))for v in paths.values()))
   q=subprocess.run(['cc','-O1','-fno-strict-aliasing','-I'+str(h),'-c',str(p/'original.c'),'-o',str(p/'original.o')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
   q=subprocess.run(['c++','-std=c++20','-O1','-pthread','-I'+str(ROOT/'src'),'-I'+str(h),'-I'+str(ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz'),'-I'+str(mb),str(p/'test.cpp'),str(p/'original.o'),*[str(ROOT/'src/runtime'/x)for x in['pal_team_saved_data.cpp','pal_sky_widescreen.cpp','rom_image.cpp']],str(mb/'libminiz.a'),'-o',str(p/'test')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
   q=subprocess.run([str(p/'test'),str(snapshot),str(ROOT/'.local/select-teams-54-before/yellow.rdram')],capture_output=True,text=True,timeout=30);self.assertEqual(q.returncode,0,q.stderr)
if __name__=='__main__':unittest.main()
