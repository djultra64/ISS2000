"""Original project work: djultra64. Actual completed Controller task and genuine original CPU closure."""
from pathlib import Path
import json,struct,shutil,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
CODE=r'''#include "runtime/pal_controller_screen.hpp"
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
DECLS
using namespace iss2000;using Bytes=std::vector<uint8_t>;
namespace artwork_fixture {
#include "runtime/gdb_prompt_glyphs.inc"
}
extern "C" recomp_func_t*get_function(int32_t a){switch(uint32_t(a)){LOOKUP default:fprintf(stderr,"Unknown original %08x\n",uint32_t(a));std::abort();}}
extern "C" void do_break(uint32_t){std::abort();}extern "C" void switch_error(const char*,uint32_t,uint32_t){std::abort();}
void func_802C48F4_overlay_40c7a0_802c3490(uint8_t*,recomp_context*){}
void func_802C49B8_overlay_40c7a0_802c3490(uint8_t*,recomp_context*){}
struct RegistryStub{recomp_func_t*find(uint32_t a){return a==0x802c48f4?func_802C48F4_overlay_40c7a0_802c3490:a==0x802c49b8?func_802C49B8_overlay_40c7a0_802c3490:nullptr;}}registry;
NATIVE_OWNER
uint32_t word(const Bytes&r,uint32_t a){uint32_t v;memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
void put(Bytes&r,uint32_t a,uint32_t v){memcpy(r.data()+(a&0x7fffff),&v,4);}
uint8_t byte(const Bytes&r,uint32_t a){return r[(a&0x7fffff)^3];}
Bytes load(const char*p){FILE*f=fopen(p,"rb");assert(f);fseek(f,0,SEEK_END);size_t n=ftell(f);rewind(f);Bytes b(n);assert(fread(b.data(),1,n,f)==n);fclose(f);return b;}
int main(int argc,char**argv){assert(argc==4);auto rom=load(argv[1]),base=load(argv[2]);auto foreign=rom;foreign[4]^=1;assert(!configure_pal_controller_screen(foreign));assert(configure_pal_controller_screen(rom));assert(!configure_pal_controller_screen(foreign));
 PalControllerScreenFunctions fn{func_80008A54_resident,func_80007C2C_resident,func_80041B50_resident,func_80048660_resident};
 recomp_context c{};c.r29=int32_t(0x800a4000);c.f_odd=&c.f0.u32h;const auto caller=c;
 PalControllerScreenView v;v.types={"Type 5","Type 2","Free","Type 4"};v.selected_port=0;v.start_footer="Press Menu to confirm";
 const char*actions[]{"Pass","Shoot","Dash","Lob","Through","OneTwo","Curve","Cursor"};
 const char*xbox[]{"X","Y","A","B","RB","LB","LT","RT"};
 for(unsigned n=0;n<8;++n)v.actions[n]={PromptGlyphFamily::Xbox,xbox[n],actions[n]};
 for(auto family:{PromptGlyphFamily::Xbox,PromptGlyphFamily::PlayStation,PromptGlyphFamily::Nintendo,PromptGlyphFamily::Keyboard}){
  const char*ps[]{"Square","Triangle","Cross","Circle","R1","L1","L2","R2"};const char*sw[]{"Y","X","B","A","R","L","ZL","ZR"};const char*kb[]{"X","A","Z","S","Q","E","I","K"};
  for(unsigned n=0;n<8;++n){v.actions[n].family=family;v.actions[n].physical_label=family==PromptGlyphFamily::Xbox?xbox[n]:family==PromptGlyphFamily::PlayStation?ps[n]:family==PromptGlyphFamily::Nintendo?sw[n]:kb[n];}
  auto r=base;const auto old_end=word(r,0x8009e0c8);assert(draw_pal_controller_screen(r,c,v,fn));assert(memcmp(&c,&caller,sizeof(c))==0);assert(memcmp(r.data()+0xa3a00,base.data()+0xa3a00,0x600)==0);
  assert(memcmp(r.data()+0x2d21e0,base.data()+0x2d21e0,0x18)==0);assert(memcmp(r.data()+0x270140,base.data()+0x270140,0x2180)==0);assert(word(r,0x80076ca4)==word(base,0x80076ca4));
  // Original task preserves authentic background/border and allotherUI; only
  // owned E4+half rectangles become six zero words, never state/texture loads.
  unsigned suppressed=0;for(unsigned p=word(base,0x800a4aa4)+8;p<old_end;p+=8){if(word(r,p)==word(base,p)&&word(r,p+4)==word(base,p+4))continue;assert(word(base,p)>>24==0xe4);for(unsigned n=0;n<24;n+=4)assert(word(r,p+n)==0);++suppressed;p+=16;}assert(suppressed>=40&&suppressed<80);assert(word(r,0x800e2dd0)==word(base,0x800e2dd0));assert(word(r,0x800e7130)==word(base,0x800e7130));
  assert(word(r,old_end)==0xde010000);auto first=word(r,old_end+4),end=word(r,0x8009e0c8);assert(first>old_end+1024&&end<=0x800f0388);unsigned icons=0;uint32_t tex=0,palette=0;
  for(unsigned p=first;p<end;p+=8){auto op=word(r,p),a=word(r,p+4);if(op==0xfd100000)palette=a;if(op>>24==0xfd)tex=a&0x7fffff;if(op>>24!=0xe4)continue;
   if(tex>=(old_end&0x7fffff)&&tex<(first&0x7fffff)){
    ++icons;const auto&request=v.actions[icons-1];const std::array<uint8_t,256>*expected=nullptr;for(const auto&g:artwork_fixture::artwork_glyphs)if(g.family==request.family&&g.label==request.physical_label)expected=&artwork_fixture::artwork_tiles[g.tile];assert(expected);for(unsigned n=0;n<256;++n){auto packed=byte(r,0x80000000+tex+n/2);assert((n&1?packed&15:packed>>4)==(*expected)[n]);}for(unsigned n=0;n<13;++n){auto rgb=artwork_fixture::artwork_colors[n];uint16_t expected=((rgb>>27)&31)<<11|((rgb>>19)&31)<<6|((rgb>>11)&31)<<1|bool(rgb&255);assert(unsigned(byte(r,palette+n*2))*256+byte(r,palette+n*2+1)==expected);}assert(((op>>12&4095)-(a>>12&4095))==64);assert((op&4095)-(a&4095)==64);assert(palette>=old_end&&palette<first);
    unsigned ymin=16,ymax=0;for(unsigned n=0;n<256;++n){auto z=byte(r,0x80000000+tex+n/2);unsigned idx=n&1?z&15:z>>4;if(idx){ymin=std::min(ymin,n/16);ymax=std::max(ymax,n/16);}}assert(ymin<=ymax);
    // Verify actual originalfont ink is centered on the actual genuine tile,
    // rather than equating spriteobject and fontobject origins/baselines.
    auto iy=(a&4095)/4;int tl=12,th=-1;for(char c:v.actions[icons-1].action){unsigned code=c>='A'&&c<='Z'?c-'A'+11:c-'a'+37;for(unsigned y=0;y<12;++y)for(unsigned x=0;x<6;++x){auto n=y*16+(code&1)*8+x;auto z=byte(r,0x80352800+(code/2)*96+n/2);unsigned v=n&1?z&15:z>>4;if(byte(r,0x80087460+v*2+1)&1){tl=std::min(tl,int(y));th=std::max(th,int(y));}}}auto ty=int(iy)+(int(ymin+ymax)-tl-th+1)/2;bool found=false;
    for(unsigned q=p+24;q<end;q+=8){if(word(r,q)>>24!=0xe4)continue;auto b=word(r,q+4);if((b>>12&4095)/4==(a>>12&4095)/4+28&&int((b&4095)/4)==ty){found=true;break;}}assert(found);
   }p+=16;
  }assert(icons==8);for(unsigned p=first;p<end;p+=8)if(word(r,p)>>24==0xe4){auto a=word(r,p),b=word(r,p+4);if((b&4095)/4>=215)assert((a&4095)/4<=225);p+=16;}
 }
 // Replay the actual original entry state:4820 queues48C0 throughCC5C,
 // which installs CDD0 with node+10 pending48C0 during the entry fade.
 uint32_t node=word(base,0x80077390);while(node&&word(base,node+12)!=0x802c48f4)node=word(base,node);assert(node);
 const uint32_t callbacks[]{0x8000cdd0,0x802c48c0,0x802c48f4,0x8000cdd0,0x802c4820};
 for(unsigned phase=0;phase<5;++phase){auto early=base;put(early,node+12,callbacks[phase]);put(early,node+16,phase==0?0x802c48c0:0x802c48c4);const auto before=early;
  const bool owned=original_controller_screen(early.data());const bool adapted=draw_pal_controller_screen(early,c,v,fn);
  assert(owned==(phase<3));assert(adapted==owned);if(!owned)assert(early==before);
 }
 // Cursor's different lower panel must not disable Config replacements.
 // Keep the actual eight Config quads and panel art; omit only lower content
 // quads to model the smaller Cursor description, without altering its state.
 {auto cursor=base;unsigned removed=0;uint32_t texture=0;
  for(auto pc=word(cursor,0x800a4aa4)+8;pc<word(cursor,0x8009e0c8);pc+=8){auto op=word(cursor,pc),b=word(cursor,pc+4);if(op>>24==0xfd)texture=b&0x7fffff;if(op>>24!=0xe4)continue;
   if(texture!=0x240c40&&(b>>12&4095)>=30*4&&(op>>12&4095)<=302*4&&(b&4095)>=145*4&&(op&4095)<=210*4&&removed++<28)for(unsigned n=0;n<24;n+=4)put(cursor,pc+n,0);pc+=16;}
  cursor[0x2d21e0^3]=2;const auto before=cursor;const auto old=word(cursor,0x8009e0c8);
  assert(draw_pal_controller_screen(cursor,c,v,fn));unsigned changed=0;
  for(auto pc=word(before,0x800a4aa4)+8;pc<old;pc+=8)if(word(cursor,pc)!=word(before,pc)){assert((word(before,pc+4)&4095)==79*4);++changed;pc+=16;}
  assert(changed==8);assert(memcmp(cursor.data()+0x2d21e0,before.data()+0x2d21e0,0x18)==0);
 }
 // Cursor and Keeper keep their own original descriptions even when their
 // rectangle count happens to resemble Config's body. Only Type values change.
 for(unsigned row:{2u,3u}){auto r=base;r[0x2d21e0^3]=row;const auto before=r;auto old=word(r,0x8009e0c8);
  assert(draw_pal_controller_screen(r,c,v,fn));unsigned changed=0;
  for(auto pc=word(before,0x800a4aa4)+8;pc<old;pc+=8)if(word(r,pc)!=word(before,pc)){assert((word(before,pc+4)&4095)==79*4);++changed;pc+=16;}assert(changed==8);
 }
 // OriginalC7EC replaces only node+12 with C96C; pending+16 remains48C0.
 // The departing page must keep its replacements until its genuine fade ends.
 {auto departing=base;put(departing,node+12,0x8000c96c);put(departing,node+16,0x802c48c0);
  assert(!original_controller_screen(departing.data()));assert(original_controller_screen(departing.data(),true));
  assert(draw_pal_controller_screen(departing,c,v,fn));
 }
 // Every rejected request leaves the ENTIRE live original RAM unchanged.
 for(unsigned n=0;n<12;++n){auto r=base;auto bad=v;auto f=fn;if(n==0)bad.types[0]="Type 6";if(n==1)bad.selected_port=4;if(n==2)bad.actions[0].action="Wrong@word";if(n==3)bad.start_footer=std::string(41,'X');if(n==4)put(r,0x80077390,0);if(n==5)put(r,0x802c48f4,0);if(n==6)put(r,0x80270140,word(r,0x80270140)^1);if(n==7)put(r,0x800e6568,0);if(n==8)put(r,0x8009e0c8,0x800f0300);if(n==9)put(r,0x80352800,word(r,0x80352800)^1);if(n==10)f.draw_text=nullptr;if(n==11)c.f_odd=reinterpret_cast<uint32_t*>(r.data());const auto before=r;bool rejected=!draw_pal_controller_screen(r,c,bad,f);if(!rejected||r!=before)fprintf(stderr,"negative%u rejected%d unchanged%d\n",n,rejected,r==before);assert(rejected&&r==before);c=caller;c.f_odd=&c.f0.u32h;}
 auto captured=base;v.free_capture=true;v.selected_action=4;assert(draw_pal_controller_screen(captured,c,v,fn));v.free_capture=false;auto r=base;v.actions[0].physical_label="LS";assert(draw_pal_controller_screen(r,c,v,fn)); // original-font fallback for real Shift alias
}
'''
class ControllerScreenTests(unittest.TestCase):
 def test_original_completed_controller_task_and_original_cpu_closure(self):
  self.assertTrue((ROOT/'src/runtime/pal_controller_screen.cpp').is_file(),'Missing original Controller renderer')
  g=ROOT/'.local/pal-map-bound-01/functions';h=ROOT/'.local/deps/N64Recomp/include';rom=ROOT/'.local/inputs/pal-en-de/rom.z64';snapshot=ROOT/'.local/ui-redesign-01/controller49-completed.rdram';mb=ROOT/'.local/runtime-deps-build/librecomp/miniz';rt64=ROOT/'.local/deps/rt64'
  if not shutil.which('c++')or not all(p.is_file()for p in [rom,snapshot,h/'recomp.h',mb/'libminiz.a']):self.skipTest('Original private PAL CPU/compiler fixtures required')
  image=rom.read_bytes();sections=json.loads((g.parent/'section-analysis.json').read_text());functions={f['vram']:(s,f)for s in sections for f in s['functions']};pending=[0x80008a54,0x80007c2c,0x80041b50,0x80048660];seen=set()
  while pending:
   pc=pending.pop()
   if pc in seen:continue
   seen.add(pc);s,f=functions[pc];a=s['rom']+pc-s['vram']
   for op in struct.unpack_from('>'+str(f['size']//4)+'I',image,a):
    if op>>26==3:pending.append(0x80000000|((op&0x3ffffff)<<2))
  native=(ROOT/'src/runtime/native_game.cpp').read_text();start=native.index('bool original_controller_screen(');opening=native.index('{',start);end=opening+1;depth=1
  while depth:
   depth+=(native[end]=='{')-(native[end]=='}');end+=1
  native_owner=native[start:end]
  paths={pc:next(g.glob(f'func_{pc:08X}_*.c'))for pc in seen};code=CODE.replace('DECLS','\n'.join(f'extern "C" void {p.stem}(uint8_t*,recomp_context*);'for p in paths.values())).replace('LOOKUP','\n'.join(f'case 0x{pc:08X}:return {p.stem};'for pc,p in paths.items()))
  code=code.replace('NATIVE_OWNER',native_owner)
  r=bytearray(snapshot.read_bytes())
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);(p/'test.cpp').write_text(code);(p/'original.c').write_text('\n'.join('#include '+json.dumps(str(v))for v in paths.values()));(p/'base.rdram').write_bytes(r)
   (p/'controller.rdram').write_bytes(r)
   q=subprocess.run(['cc','-O1','-fno-strict-aliasing','-I'+str(h),'-c',str(p/'original.c'),'-o',str(p/'original.o')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
   inc=['src','.local/deps/N64Recomp/include','.local/deps/N64ModernRuntime/librecomp/include','.local/deps/N64ModernRuntime/ultramodern/include','.local/deps/N64ModernRuntime/thirdparty','.local/deps/N64ModernRuntime/thirdparty/concurrentqueue']
   q=subprocess.run(['c++','-std=c++20','-O1','-pthread',*['-I'+str(ROOT/x)for x in inc],'-I/home/linuxbrew/.linuxbrew/include/SDL2','-I'+str(rt64/'include'),'-I'+str(rt64/'src/contrib'),'-I'+str(ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz'),'-I'+str(mb),str(p/'test.cpp'),str(p/'original.o'),*[str(ROOT/'src/runtime'/x)for x in ['pal_controller_screen.cpp','pal_sky_widescreen.cpp','game_controls_menu.cpp','rom_image.cpp']],str(mb/'libminiz.a'),'-o',str(p/'test')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
   q=subprocess.run([str(p/'test'),str(rom),str(p/'base.rdram'),str(p/'controller.rdram')],capture_output=True,text=True,timeout=30);self.assertEqual(q.returncode,0,q.stderr)
if __name__=='__main__':unittest.main()
