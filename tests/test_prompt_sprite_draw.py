"""Original work: djultra64. Real original sprite CPU, immutable task glyph payload."""
from pathlib import Path
import json,struct,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
CODE=r'''#include "runtime/prompt_sprite_draw.hpp"
#include <algorithm>
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
DECLS
using namespace iss2000;using Bytes=std::vector<uint8_t>;
namespace fixture {
#include "runtime/gdb_prompt_glyphs.inc"
}
extern "C" recomp_func_t* get_function(int32_t a){switch(uint32_t(a)){LOOKUP default:fprintf(stderr,"Unknown original %08x\n",uint32_t(a));std::abort();}}
extern "C" void do_break(uint32_t){std::abort();}extern "C" void switch_error(const char*,uint32_t,uint32_t){std::abort();}
uint32_t word(const Bytes&r,uint32_t a){uint32_t v;memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
void put(Bytes&r,uint32_t a,uint32_t v){memcpy(r.data()+(a&0x7fffff),&v,4);}
uint8_t byte(const Bytes&r,uint32_t a){return r[(a&0x7fffff)^3];}
Bytes load(const char*p){FILE*f=fopen(p,"rb");assert(f);fseek(f,0,SEEK_END);size_t n=ftell(f);rewind(f);Bytes b(n);assert(fread(b.data(),1,n,f)==n);fclose(f);return b;}
int main(int argc,char**argv){assert(argc==3);auto base=load(argv[1]);PalPromptSpriteFunctions fn{func_80008A54_resident,func_80007C2C_resident,func_80041B50_resident,func_80048660_resident};
 recomp_context c{};c.r29=int32_t(0x800a4000);c.f_odd=&c.f0.u32h;const auto caller=c;
 std::array<PromptGlyphRequest,2> ab{};std::array<PromptGlyphRequest,4> dirs{};
 const char* labels[4][3]={{"LB","LT","RB"},{"L1","L2","R1"},{"L","ZL","R"},{"Q","Left Shift","E"}};
 // Both actual SelectTeams layouts have native physical C-direction glyphs,
 // independent of the old yellow CI4 palette and shared source atlas.
 for(unsigned family=1;family<=4;++family)for(unsigned single=0;single<2;++single){auto r=single?load(argv[2]):base;
  // Completed yellow task released its live owner. Reconstruct a bounded CPU
  // task fixture from the genuine submitted cursor; no game execution/capture.
  if(single){assert(word(r,0x800a4aa4)==0&&word(r,0x8009e0c8)==0x800d81c8);put(r,0x800a4aa4,0x800d0320);}
  FILE*f=fopen(".local/team-visual-assets-01/asset_015.bin","rb");assert(f);std::vector<uint8_t>asset(0x26f40);assert(fread(asset.data(),1,asset.size(),f)==asset.size());fclose(f);
  const uint32_t bank=word(r,0x80076b30),texture=word(r,bank+8*12+8);for(unsigned n=0;n<640;++n)r[((texture+n)&0x7fffff)^3]=asset[0x20ac0+n];
  const char*physical[]{family==4?"J":"R←",family==4?"L":"R→",family==4?"I":"R↑",family==4?"K":"R↓"};for(unsigned n=0;n<4;++n)dirs[n]={PromptGlyphFamily(family),physical[n],0};
  prompt_detail::TextureGuard guard(pal_en_prompt_texture_layout());const auto before=r;
  auto result=guard.prepare_sprite(r.data(),single?0x8013cad0:0x8013d340,ab,dirs);assert(result.status==PromptSpriteStatus::TextFallback&&result.icon_count==(single?2:8)&&r==before);
  const unsigned order[]{2,3,3,1,0,1,0,2};for(unsigned n=0;n<result.icon_count;++n)assert(result.icons[n].label==physical[single?n:order[n]]&&result.icons[n].width==(single||n==3||n==4||n==5||n==6?16:12));
  assert(result.line_count==0);

  for(unsigned n=0;n<result.icon_count;++n){const bool footer=single||n==3||n==4||n==5||n==6;if(!footer)continue;
   const auto&icon=result.icons[n];const std::array<uint8_t,256>*tile=nullptr;for(const auto&g:fixture::artwork_glyphs)if(g.family==icon.family&&g.label==icon.label)tile=&fixture::artwork_tiles[g.tile];assert(tile);
   int left=16,right=-1,top=16,bottom=-1;for(unsigned i=0;i<256;++i)if((*tile)[i]){left=std::min(left,int(i%16));right=std::max(right,int(i%16));top=std::min(top,int(i/16));bottom=std::max(bottom,int(i/16));}
   // Independent original label outline bounds: actual SavedData face spans
   // x43..84 or228..269/y195..208; Training x81..122/y197..210.
   const int lo=single?81:n>=5?228:43,hi=lo+41,center=single?407:403;
   const bool previous=single?n==0:n==4||n==6;
   assert(abs(2*icon.y+top+bottom-center)<=1);
   if(previous){if(!(icon.x+right<lo))fprintf(stderr,"family%u single%u n%u x%d right%d lo%d label%s\n",family,single,n,icon.x,right,lo,icon.label.c_str());assert(icon.x+right<lo);}else assert(icon.x+left>hi);

  }
  const auto native_begin=word(r,0x8009e0c8);
  assert(draw_pal_prompt_sprite(r,c,result,fn));
  // Check the actual original font command's emitted primitive color, not
  // merely the requested tint number. RS must stay opaque black on both skins.
  unsigned rectangles=0;uint32_t primitive=~0u;
  for(auto pc=word(r,native_begin+4);pc<word(r,0x8009e0c8);pc+=8){auto op=word(r,pc);if(op==0xfa000000)primitive=word(r,pc+4);if(op>>24==0xe4){if(rectangles++>=result.icon_count)assert(primitive==0x000000ff);pc+=16;}}
  assert(rectangles==result.icon_count+2*result.line_count);
  if(single){std::array<PromptGlyphRequest,3> shoulders;for(unsigned i=0;i<3;++i)shoulders[i]={PromptGlyphFamily(family),labels[family-1][i],0};const auto native=guard.prepare_sprite(r.data(),0x8013cd64,ab,dirs,std::nullopt,shoulders);assert(native.status==PromptSpriteStatus::TextFallback&&native.icon_count==2&&native.line_count==0);for(unsigned n=0;n<2;++n)assert(native.icons[n].label==shoulders[n*2].label&&native.icons[n].y>=57&&native.icons[n].y<=58&&native.icons[n].width==16);assert(draw_pal_prompt_sprite(r,c,native,fn));}
  const auto start=guard.prepare_sprite(r.data(),single?0x8013d1d8:0x8013dc28,ab,dirs,PromptGlyphRequest{PromptGlyphFamily::Xbox,"Menu",0});assert(start.status==PromptSpriteStatus::TextFallback&&start.line_count==1);
  auto half=[&](uint32_t p){return unsigned(byte(r,p))*256+byte(r,p+1);};
  int fl=12,fh=-1;for(char ch:start.lines[0].text){unsigned code=ch==' '?0:ch>='A'&&ch<='Z'?ch-'A'+11:ch-'a'+37;for(unsigned y=0;y<12;++y)for(unsigned x=0;x<6;++x){auto n=y*16+(code&1)*8+x;auto z=byte(r,0x80352800+(code/2)*96+n/2);unsigned v=n&1?z&15:z>>4;if(byte(r,0x80087460+v*2+1)&1){fl=std::min(fl,int(y));fh=std::max(fh,int(y));}}}
  const auto enter=single?0x8013d19c:0x8013db38,segment=word(r,enter+48),font_image=word(r,word(r,enter+20)+8);int il=16,ih=-1;for(unsigned y=0;y<16;++y)for(unsigned x=0;x<32;++x){auto n=y*128+x;auto z=byte(r,font_image+n/2);if((n&1?z&15:z>>4)){il=std::min(il,int(y));ih=std::max(ih,int(y));}}
  assert(fl==0&&fh==10&&il==2&&ih==10);assert(2*start.lines[0].y+fl+fh==2*int(half(segment+6))+il+ih);
 }
 for(unsigned family=1;family<=4;++family){auto r=base;prompt_detail::TextureGuard guard(pal_en_prompt_texture_layout());std::array<PromptGlyphRequest,3> shoulders;
  for(unsigned n=0;n<3;++n)shoulders[n]={PromptGlyphFamily(family),labels[family-1][n],0};
  const auto result=guard.prepare_sprite(r.data(),0x8013d9d0,ab,dirs,std::nullopt,shoulders);assert(result.icon_count==4&&result.line_count==0);
  auto old=word(r,0x8009e0c8);assert(draw_pal_prompt_sprite(r,c,result,fn));assert(memcmp(&c,&caller,sizeof(c))==0);assert(memcmp(r.data()+0xa3a00,base.data()+0xa3a00,0x600)==0);assert(word(r,0x80076ca4)==word(base,0x80076ca4));
  assert(word(r,old)==0xde010000);auto first=word(r,old+4),end=word(r,0x8009e0c8);assert(first==old+8+32+4*128&&end<=0x800f0388);unsigned icons=0;uint32_t tex=0,palette=0;
  for(unsigned p=first;p<end;p+=8){auto op=word(r,p),a=word(r,p+4);if(op==0xfd100000)palette=a;if(op>>24==0xfd)tex=a&0x7fffff;if(op>>24!=0xe4)continue;
   assert(icons<result.icon_count);const auto& icon=result.icons[icons++];const std::array<uint8_t,256>*expected=nullptr;for(const auto&g:fixture::artwork_glyphs)if(g.family==icon.family&&g.label==icon.label)expected=&fixture::artwork_tiles[g.tile];assert(expected);
   int xmin=16,ymin=16,xmax=-1,ymax=-1;for(unsigned n=0;n<256;++n){auto packed=byte(r,tex+n/2);auto index=n&1?packed&15:packed>>4;assert(index==(*expected)[n]);if(index){xmin=std::min(xmin,int(n%16));xmax=std::max(xmax,int(n%16));ymin=std::min(ymin,int(n/16));ymax=std::max(ymax,int(n/16));}}
   for(unsigned n=0;n<13;++n){auto rgb=fixture::artwork_colors[n];uint16_t expected=((rgb>>27)&31)<<11|((rgb>>19)&31)<<6|((rgb>>11)&31)<<1|bool(rgb&255);assert(unsigned(byte(r,palette+n*2))*256+byte(r,palette+n*2+1)==expected);}
   assert(int((a>>12&4095)/4)==icon.x&&int((a&4095)/4)==icon.y);assert(((op>>12&4095)-(a>>12&4095))==icon.width*4&&(op&4095)-(a&4095)==icon.height*4);
   assert(abs(2*icon.y+ymin+ymax-117)<=1&&xmin<=xmax);p+=16;
  }assert(icons==4);
  // Private original game atlases, pool objects, old Gfx and all caller state
  // remain exact. Only task arena additions, material caches and cursor change.
  assert(memcmp(r.data()+0x210000,base.data()+0x210000,0x180000)==0);assert(memcmp(r.data()+0x13c47c,base.data()+0x13c47c,273*60)==0);
  for(unsigned variant=0;variant<7;++variant){auto bad=base;auto request=result;auto f=fn;if(variant==0)request.icons[0].label="Unsupported";if(variant==1)request.icon_count=9;if(variant==2)request.icons[0].x=310;if(variant==3)put(bad,0x80008a54,0);if(variant==4)put(bad,0x8009e0c8,0x800f0300);if(variant==5)f.draw_sprite=nullptr;if(variant==6)request.status=PromptSpriteStatus::Unrelated;auto before=bad;assert(!draw_pal_prompt_sprite(bad,c,request,f)&&bad==before);}
 }
}'''
class PromptSpriteDrawTests(unittest.TestCase):
 def test_native_region_glyph_art_palette_ink_and_transaction(self):
  self.assertTrue((ROOT/'src/runtime/prompt_sprite_draw.cpp').exists(),'Native glyph renderer is missing')
  g=ROOT/'.local/pal-map-bound-01/functions';h=ROOT/'.local/deps/N64Recomp/include';rom=ROOT/'.local/inputs/pal-en-de/rom.z64';snapshot=ROOT/'.local/hidden-test-01/team16-completed.rdram';yellow=ROOT/'.local/select-teams-54-before/yellow.rdram';asset=ROOT/'.local/team-visual-assets-01/asset_015.bin';mb=ROOT/'.local/runtime-deps-build/librecomp/miniz'
  if not all(p.is_file()for p in [rom,snapshot,yellow,asset,h/'recomp.h',mb/'libminiz.a']):self.skipTest('Private original CPU fixtures required')
  image=rom.read_bytes();sections=json.loads((g.parent/'section-analysis.json').read_text());functions={f['vram']:(s,f)for s in sections for f in s['functions']};pending=[0x80008a54,0x80007c2c,0x80041b50,0x80048660];seen=set()
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
   inc=['src','.local/deps/N64Recomp/include','.local/deps/N64ModernRuntime/librecomp/include','.local/deps/N64ModernRuntime/ultramodern/include','.local/deps/N64ModernRuntime/thirdparty','.local/deps/N64ModernRuntime/thirdparty/concurrentqueue']
   q=subprocess.run(['c++','-std=c++20','-O1','-pthread',*['-I'+str(ROOT/x)for x in inc],'-I/home/linuxbrew/.linuxbrew/include/SDL2','-I'+str(ROOT/'.local/deps/rt64/include'),'-I'+str(ROOT/'.local/deps/rt64/src/contrib'),'-I'+str(ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz'),'-I'+str(mb),str(p/'test.cpp'),str(p/'original.o'),*[str(ROOT/'src/runtime'/x)for x in ['prompt_sprite_draw.cpp','prompt_textures.cpp','pal_sky_widescreen.cpp','game_controls_menu.cpp','rom_image.cpp']],str(mb/'libminiz.a'),'-o',str(p/'test')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
   q=subprocess.run([str(p/'test'),str(snapshot),str(ROOT/'.local/select-teams-54-before/yellow.rdram')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
