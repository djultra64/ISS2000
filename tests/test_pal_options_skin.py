"""Original project work: djultra64. Authentic original menu alphabet and sprite chains."""
from pathlib import Path
import json,struct,shutil,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
CODE=r'''#include "runtime/pal_options_skin.hpp"
#include "runtime/pal_options_row_font.hpp"
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
DECLS
using namespace iss2000;using Bytes=std::vector<uint8_t>;
extern "C" recomp_func_t*get_function(int32_t a){switch(uint32_t(a)){LOOKUP default:fprintf(stderr,"Unknown original %08x\n",uint32_t(a));std::abort();}}
extern "C" void do_break(uint32_t){std::abort();}extern "C" void switch_error(const char*,uint32_t,uint32_t){std::abort();}
uint32_t word(const Bytes&r,uint32_t a){uint32_t v;memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
void put(Bytes&r,uint32_t a,uint32_t v){memcpy(r.data()+(a&0x7fffff),&v,4);}
Bytes load(const char*p){FILE*f=fopen(p,"rb");assert(f);fseek(f,0,SEEK_END);size_t n=ftell(f);rewind(f);Bytes b(n);assert(fread(b.data(),1,n,f)==n);fclose(f);return b;}
int main(int argc,char**argv){assert(argc==4);auto rom=load(argv[1]);auto badrom=rom;badrom[4]^=1;assert(!configure_pal_options_skin(badrom));assert(configure_pal_options_skin(rom));assert(!configure_pal_options_skin(badrom));
 for(auto text:{"PC Settings","Graphics","Display","Controls","Button mapping","Vibration","Screen","Fullscreen","Windowed","Save","Cancel","Controller type","Restore defaults","Xbox","PlayStation","Nintendo","Keyboard"})assert(pal_options_skin_text_supported(text));assert(!pal_options_skin_text_supported("Invented@font"));
 auto base=load(argv[2]);put(base,0x800a4aa4,0x800d0320);put(base,0x8009e0c8,0x800d0328);const PalOptionsSkinFunctions fn{func_80008A54_resident,func_80007C2C_resident,func_80041B50_resident,func_80048660_resident};
 recomp_context c{};c.r29=int32_t(0x800a4000);c.f_odd=&c.f0.u32h;const auto caller=c;
 PalOptionsSkinView v{"Graphics",{{"Aspect","16 by 9"},{"Resolution","1080p"},{"Framerate limit","120"},{"Screen","Fullscreen"},{"Back",""}},2,{"Left and Right change","Z select. X back"}};
 for(bool wide:{false,true}){auto r=base;auto before=r;assert(draw_pal_options_skin(r,c,v,PalOptionsSkinOwner::Options,wide,fn));assert(memcmp(&caller,&c,sizeof(c))==0);assert(word(r,0x80076ca4)==word(before,0x80076ca4));assert(memcmp(r.data()+0xa3a00,before.data()+0xa3a00,0x600)==0);assert(memcmp(r.data()+0x13b418,before.data()+0x13b418,0x2a960)==0);
  auto p=0x800d0328u;assert(word(r,p)==0xde010000);const auto first=word(r,p+4),end=word(r,0x8009e0c8);assert(first>p+2048&&first<end&&end<=0x800e0328);assert(memcmp(r.data()+0x22ce40,before.data()+0x22ce40,8192)==0);unsigned rects=0,fonts=0,frame_rects=0;uint32_t current_texture=0;
  for(p=first;p<end;p+=8){auto a=word(r,p);if(a>>24==0xe4){++rects;if(current_texture==0xd0b30){auto u=word(r,p+12)>>16;assert(u==0||u==1024);++frame_rects;}p+=16;}if(a>>24==0xfd){auto texture=word(r,p+4)&0x7fffff;current_texture=texture;if(texture>=0x22ce40&&texture<0x22ee40)++fonts;}}
  // Native help remains inside the PAL visible viewport, including its final row.
  for(unsigned pc=first;pc+16<end;pc+=8)if(word(r,pc)>>24==0xe4){auto b=word(r,pc+4),a=word(r,pc);if(((b>>12)&0xfff)/4==24&&((b&0xfff)/4)>170)assert((a&0xfff)/4<=225);}
  // Only the heading uses the resident header alphabet. Every noncontrols
  // body row is an exact original-row CI4 bitmap rather than scaled letters.
  assert(rects>90&&fonts==8&&frame_rects>0);
  // Verify the complete original sprite closure emitted each owned CI4 TLUT,
  // not merely that the correct source palette was copied into unused memory.
  // Original4250C uses object+C=15 for the custom pointer in object+34.
  unsigned grid_palettes=0,green_bullets=0,orange_bullets=0;
  for(auto q=first;q<end;q+=8){if(word(r,q)>>24==0xe4){q+=16;continue;}if(word(r,q)!=0xfd100000)continue;auto palette=word(r,q+4);if(palette<0x800d0328||palette+32>first)continue;
   auto exact=[&](uint32_t ro){for(unsigned n=0;n<32;++n)if(r[((palette+n)&0x7fffff)^3]!=rom[ro+n])return false;return true;};
   if(exact(0x35c820))++grid_palettes;if(exact(0x3539f0))++green_bullets;if(exact(0x353a10))++orange_bullets;
  }
  assert(grid_palettes>=6&&green_bullets==4&&orange_bullets==1);
  Bytes original_rows(0x2c00);for(unsigned n=0;n<original_rows.size();++n)original_rows[n]=before[(0x276940+n)^3];
  std::vector<unsigned> actual_row_draws(v.rows.size());uint32_t active_palette=0;
  for(auto q=first;q<end;q+=8){
   auto op=word(r,q);if(op>>24==0xe4){q+=16;continue;}if(op>>24!=0xfd)continue;
   auto address=word(r,q+4);if(op==0xfd100000){active_palette=address;continue;}
   if(address<0x800d0328||address+1024>first)continue;
   Bytes actual(1024);for(unsigned n=0;n<actual.size();++n)actual[n]=r[((address+n)&0x7fffff)^3];
   for(unsigned row=0;row<v.rows.size();++row){auto expected=pal_options_row_bitmap(original_rows,v.rows[row].label);assert(expected);if(actual!=expected->pixels)continue;
    ++actual_row_draws[row];auto palette_rom=row==v.selected?0x353890u:0x35e3e0u;
    for(unsigned n=0;n<32;++n)assert(r[((active_palette+n)&0x7fffff)^3]==rom[palette_rom+n]);
   }
  }
  for(auto count:actual_row_draws)assert(count==1); // actual original CI4 draw for every whole row

 }
 // The PC Settings main page also preflights and draws its exact row-face labels.
 {auto r=base;PalOptionsSkinView main{"PC Settings",{{"Graphics",""},{"Controls",""},{"Save options",""},{"Cancel",""}},0,{"Z select","X back"}};assert(draw_pal_options_skin(r,c,main,PalOptionsSkinOwner::Options,true,fn));
  auto bad=base;main.rows[2].label="Unproven row";const auto untouched=bad;assert(!draw_pal_options_skin(bad,c,main,PalOptionsSkinOwner::Options,true,fn)&&bad==untouched);
 }
 // Physical glyphs and text share one baseline row in the original engine.
 for(auto family:{PromptGlyphFamily::Xbox,PromptGlyphFamily::PlayStation,PromptGlyphFamily::Nintendo,PromptGlyphFamily::Keyboard}){
  auto r=base;auto page=v;page.help.clear();const char* west=family==PromptGlyphFamily::PlayStation?"Square":family==PromptGlyphFamily::Nintendo?"Y":"X";
  // Match the full three-action Graphics footer emitted by native_game.cpp.
  const char* south=family==PromptGlyphFamily::Keyboard?"Z":family==PromptGlyphFamily::PlayStation?"Cross":family==PromptGlyphFamily::Nintendo?"B":"A";
  page.help={"Options saved"};page.shortcuts={{family,south,"Change"},{family,west,"Apply and save"},{family,family==PromptGlyphFamily::Keyboard?"Escape":family==PromptGlyphFamily::PlayStation?"Circle":family==PromptGlyphFamily::Nintendo?"A":"B","Back"}};
  assert(draw_pal_options_skin(r,c,page,PalOptionsSkinOwner::Options,true,fn));
  unsigned footer_glyphs=0;auto first=word(r,0x800d032c),end=word(r,0x8009e0c8);
  for(auto q=first;q+16<end;q+=8)if(word(r,q)>>24==0xe4){auto a=word(r,q),b=word(r,q+4);if((b&0xfff)==206*4&&((a>>12&0xfff)-(b>>12&0xfff))==64&&(a&0xfff)-(b&0xfff)==64)++footer_glyphs;q+=16;}
  assert(footer_glyphs>=3);
  // All three icons fit the existing opaque plate, including the rightmost Back.
  unsigned bounded_icons=0;uint32_t image=0;const auto glyph_begin=(first&0x7fffff)-3*128;
  for(auto q=first;q+16<end;q+=8){auto a=word(r,q),b=word(r,q+4);if(a>>24==0xfd)image=b&0x7fffff;if(a>>24!=0xe4)continue;
   if(image>=glyph_begin&&image<glyph_begin+3*128&&(b&0xfff)==206*4&&((a>>12&0xfff)-(b>>12&0xfff))==64&&(a&0xfff)-(b&0xfff)==64){assert(((b>>12)&0xfff)>=8*4&&((a>>12)&0xfff)<=312*4);++bounded_icons;}q+=16;
  }assert(bounded_icons==3);
  auto invalid=base;page.shortcuts[0].button="Unrecognized";auto before=invalid;assert(!draw_pal_options_skin(invalid,c,page,PalOptionsSkinOwner::Options,true,fn)&&invalid==before);
  page.shortcuts[0].button=south;for(auto& shortcut:page.shortcuts)shortcut.label="Apply and save";
  assert(!draw_pal_options_skin(invalid,c,page,PalOptionsSkinOwner::Options,true,fn)&&invalid==before);
 }
 auto controller=load(argv[3]);put(controller,0x800a4aa4,0x800d0320);put(controller,0x8009e0c8,0x800d0328);

 auto device_page=[&](const PalOptionsSkinView& page){auto r=base;assert(draw_pal_options_skin(r,c,page,PalOptionsSkinOwner::Options,true,fn));
  assert(memcmp(&caller,&c,sizeof(c))==0);assert(memcmp(r.data()+0x13b418,base.data()+0x13b418,0x2a960)==0);
  const auto first=word(r,0x800d032c),end=word(r,0x8009e0c8);std::vector<unsigned>drawn(page.rows.size());uint32_t image=0,palette=0;unsigned title_glyphs=0;
  Bytes original(0x2c00);for(unsigned n=0;n<original.size();++n)original[n]=base[(0x276940+n)^3];
  for(auto q=first;q+16<end;q+=8){auto op=word(r,q),arg=word(r,q+4);
   if(op==0xfd100000){palette=arg;continue;}
   if(op>>24==0xfd){image=arg;if((arg&0x7fffff)>=0x22ce40&&(arg&0x7fffff)<0x22ee40)++title_glyphs;}
   if(op>>24!=0xe4)continue;
   const auto x=((arg>>12)&0xfff)/4,y=(arg&0xfff)/4;
   if(x==67&&y>=51&&(y-51)%19==0&&(y-51)/19<page.rows.size()){
    unsigned row=(y-51)/19;assert(image>=0x800d0328&&image+1024<=first);auto expected=pal_options_row_bitmap(original,page.rows[row].label);assert(expected);
    for(unsigned n=0;n<1024;++n)assert(r[((image+n)&0x7fffff)^3]==expected->pixels[n]);
    assert(((op>>12)&0xfff)-(arg>>12&0xfff)==512&&(op&0xfff)-(arg&0xfff)==64);
    const unsigned ro=row==page.selected?0x353890:0x35e3e0;for(unsigned n=0;n<32;++n)assert(r[((palette+n)&0x7fffff)^3]==rom[ro+n]);++drawn[row];
   }
   q+=16;
  }
  for(auto n:drawn)assert(n==1);
  assert(title_glyphs==(page.title=="Controls"?8:6)); // no header-font body letters
  auto bad=base;auto invalid=page;invalid.rows[0].label="Unproven row";auto before=bad;assert(!draw_pal_options_skin(bad,c,invalid,PalOptionsSkinOwner::Options,true,fn)&&bad==before);
 };
 device_page({"Controls",{{"Player","1"},{"Player","2"},{"Player","3"},{"Player","4"},{"Back",""}},3,{"Z select","X back"}});
 const char* families[]={"Auto","Xbox","PlayStation","Nintendo"};
 for(unsigned port=1;port<=4;++port)device_page({"Player "+std::to_string(port),{{"Controller type",families[port-1]},{"Vibration",port%2?"On":"Off"},{"Back",""}},port%3,{"Left and Right change","Z select","X back"}});
 PalOptionsSkinView remap{"Button mapping",{{"Button A","Cross"},{"Button B","Circle"},{"Start","Options"},{"Z","Left trigger"},{"L","L1"},{"R","R1"}},1,{"Family Auto PlayStation","Cross edit. Circle cancel","Page 1 of 3"}};
 for(auto mode:{PalOptionsSkinOwner::Options,PalOptionsSkinOwner::Controller}){auto r=mode==PalOptionsSkinOwner::Options?base:controller;assert(draw_pal_options_skin(r,c,remap,mode,true,fn));auto bad=r;put(bad,0x80077390,0);auto before=bad;assert(!draw_pal_options_skin(bad,c,remap,mode,true,fn)&&bad==before);}
 auto appended=base;put(appended,0x8009e0c8,0x800d43a8);assert(draw_pal_options_skin_label(appended,c,"PC Settings",67,167,false,fn));assert(draw_pal_options_skin(appended,c,v,PalOptionsSkinOwner::Options,true,fn));auto longremap=base;put(longremap,0x8009e0c8,0x800d43a8);assert(draw_pal_options_skin(longremap,c,remap,PalOptionsSkinOwner::Options,true,fn));
 auto r=base;assert(draw_pal_options_skin_label(r,c,"PC Settings",67,167,false,fn));assert(memcmp(&caller,&c,sizeof(c))==0);
 // Main Options label samples one original CI4 row image at unit scale,
 // rather than eleven rescaled title-glyph sprites.
 unsigned row_images=0,row_rectangles=0;const auto row_end=word(r,0x8009e0c8);uint32_t tex=0;
 for(unsigned pc=word(r,0x800d032c);pc+16<row_end;pc+=8){auto a=word(r,pc),b=word(r,pc+4);if(a>>24==0xfd)tex=b&0x7fffff;if(a>>24==0xe4){++row_rectangles;assert(((a>>12)&0xfff)-((b>>12)&0xfff)==128*4);assert((a&0xfff)-(b&0xfff)==16*4);if(tex==0xd0330)++row_images;}}
 assert(row_images==1&&row_rectangles==1);

 for(unsigned n=0;n<9;++n){auto r=base;auto invalid=v;if(n==0)invalid.title="Bad@word";if(n==1)invalid.rows[0].label="Unproven letters";if(n==2)invalid.rows[0].value=std::string(40,'A');if(n==3)invalid.selected=99;if(n==4)put(r,0x8009e0c8,0x800e02f0);if(n==5)put(r,0x80041b50,0);if(n==6)put(r,0x80077390,0);if(n==8)put(r,0x8022ce40,word(r,0x8022ce40)^1);if(n==7)c.f_odd=reinterpret_cast<uint32_t*>(r.data());auto before=r;assert(!draw_pal_options_skin(r,c,invalid,PalOptionsSkinOwner::Options,true,fn));assert(r==before);c=caller;c.f_odd=&c.f0.u32h;}
}
'''
class OptionsSkinTests(unittest.TestCase):
 def test_original_alphabet_constructor_background_and_complete_skin(self):
  self.assertTrue((ROOT/'src/runtime/pal_options_skin.cpp').is_file(),'Missing original Options skin')
  g=ROOT/'.local/pal-map-bound-01/functions';h=ROOT/'.local/deps/N64Recomp/include';rom=ROOT/'.local/inputs/pal-en-de/rom.z64';snapshot=ROOT/'.local/training-timing-01/options38-completed.rdram';mb=ROOT/'.local/runtime-deps-build/librecomp/miniz';rt64=ROOT/'.local/deps/rt64'
  if not shutil.which('c++')or not all(p.is_file()for p in [rom,snapshot,h/'recomp.h',mb/'libminiz.a']):self.skipTest('Original private PAL CPU/compiler fixtures required')
  image=rom.read_bytes();sections=json.loads((g.parent/'section-analysis.json').read_text());functions={f['vram']:(s,f)for s in sections for f in s['functions']};pending=[0x80008a54,0x80007c2c,0x80041b50,0x80048660];seen=set()
  while pending:
   pc=pending.pop()
   if pc in seen:continue
   seen.add(pc);s,f=functions[pc];a=s['rom']+pc-s['vram']
   for op in struct.unpack_from('>'+str(f['size']//4)+'I',image,a):
    if op>>26==3:pending.append(0x80000000|((op&0x3ffffff)<<2))
  paths={pc:next(g.glob(f'func_{pc:08X}_*.c'))for pc in seen};code=CODE.replace('DECLS','\n'.join(f'extern "C" void {p.stem}(uint8_t*,recomp_context*);'for p in paths.values())).replace('LOOKUP','\n'.join(f'case 0x{pc:08X}:return {p.stem};'for pc,p in paths.items()))
  r=bytearray(snapshot.read_bytes())
  for ro in [0x3b47e0,0x49d610]:
   s=next(s for s in sections if s['rom']==ro)
   for i,v in enumerate(image[ro:ro+s['load_size']]):r[((s['vram']+i)&0x7fffff)^3]=v
  def put(a,v):struct.pack_into('<I',r,a&0x7fffff,v)
  put(0x80077390,0x801e7070);put(0x801e7070,0);put(0x801e707c,0x8029f274);r[0x12de74^3]=1;r[0x2b1090^3]=6
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);(p/'test.cpp').write_text(code);(p/'original.c').write_text('\n'.join('#include '+json.dumps(str(v))for v in paths.values()));(p/'base.rdram').write_bytes(r)
   controller=bytearray(r);section=next(s for s in sections if s['rom']==0x40c7a0)
   for i,v in enumerate(image[section['rom']:section['rom']+section['load_size']]):controller[((section['vram']+i)&0x7fffff)^3]=v
   struct.pack_into('<I',controller,0x1e707c,0x802c48f4);struct.pack_into('<I',controller,0x76ca4,0)
   (p/'controller.rdram').write_bytes(controller)
   q=subprocess.run(['cc','-O1','-fno-strict-aliasing','-I'+str(h),'-c',str(p/'original.c'),'-o',str(p/'original.o')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
   inc=['src','.local/deps/N64Recomp/include','.local/deps/N64ModernRuntime/librecomp/include','.local/deps/N64ModernRuntime/ultramodern/include','.local/deps/N64ModernRuntime/thirdparty','.local/deps/N64ModernRuntime/thirdparty/concurrentqueue']
   q=subprocess.run(['c++','-std=c++20','-O1','-pthread',*['-I'+str(ROOT/x)for x in inc],'-I/home/linuxbrew/.linuxbrew/include/SDL2','-I'+str(rt64/'include'),'-I'+str(rt64/'src/contrib'),'-I'+str(ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz'),'-I'+str(mb),str(p/'test.cpp'),str(p/'original.o'),*[str(ROOT/'src/runtime'/x)for x in ['pal_options_skin.cpp','pal_options_row_font.cpp','pal_options_entry.cpp','pal_background_widescreen.cpp','pal_sky_widescreen.cpp','game_controls_menu.cpp','rom_image.cpp','prompt_textures.cpp']],str(mb/'libminiz.a'),'-o',str(p/'test')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
   q=subprocess.run([str(p/'test'),str(rom),str(p/'base.rdram'),str(p/'controller.rdram')],capture_output=True,text=True,timeout=30);self.assertEqual(q.returncode,0,q.stderr)
if __name__=='__main__':unittest.main()
