// Original project work: djultra64.
#include "pal_controller_screen.hpp"
#include "game_controls_menu.hpp"
#include "pal_sky_widescreen.hpp"
#include "rom_image.hpp"
#include <algorithm>
#include <cstring>
#include <mutex>
#include <vector>
namespace iss2000 {namespace {
#include "gdb_prompt_glyphs.inc"
std::mutex guard;bool configured=false;
uint32_t word(std::span<const uint8_t>r,uint32_t a){uint32_t v;std::memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
uint8_t byte(std::span<const uint8_t>r,uint32_t a){return r[(a&0x7fffff)^3];}
void put(std::span<uint8_t>r,uint32_t a,uint32_t v){std::memcpy(r.data()+(a&0x7fffff),&v,4);}
void sb(std::span<uint8_t>r,uint32_t a,uint8_t v){r[(a&0x7fffff)^3]=v;}
void sh(std::span<uint8_t>r,uint32_t a,uint16_t v){std::memcpy(r.data()+((a&0x7fffff)^2),&v,2);}
bool match(std::span<const uint8_t>r,uint32_t a,unsigned n,std::string_view hash){if(a<0x80000000||uint64_t(a)+n>0x80800000)return false;std::vector<uint8_t>b(n);for(unsigned i=0;i<n;++i)b[i]=byte(r,a+i);return rom_detail::sha256_hex(b)==hash;}
bool owner(std::span<const uint8_t>r){
 if(!match(r,0x802c48f4,196,"795692bca22a2b146f792ed4cd9706e68c44c882653d680161f3a2ae627ee308")||!match(r,0x802c49b8,188,"cd3ba5dec46fe04be08333834a8f44137666dd41705ff8db190a64214ed250a4"))return false;
 std::array<bool,220>seen{};auto p=word(r,0x80077390);bool found=false;
 while(p){if(p<0x801e7070||p>=0x801ed420||(p-0x801e7070)%0x74)return false;auto n=(p-0x801e7070)/0x74;if(seen[n])return false;seen[n]=true;const auto callback=word(r,p+12),pending=word(r,p+16);found|=callback==0x802c48f4||callback==0x802c48c0||((callback==0x8000cdd0||callback==0x8000c96c)&&pending==0x802c48c0);p=word(r,p);}return found;
}
int encode(char c){if(c==' ')return 0;if(c>='0'&&c<='9')return c-'0'+1;if(c>='A'&&c<='Z')return c-'A'+11;if(c>='a'&&c<='z')return c-'a'+37;return c=='.'?63:-1;}
bool text(std::string_view s,unsigned max){return !s.empty()&&s.size()<=max&&std::all_of(s.begin(),s.end(),[](char c){return encode(c)>=0;});}
const std::array<uint8_t,256>* tile(const PalControllerActionRow&a){for(const auto&g:artwork_glyphs)if(g.family==a.family&&g.label==a.physical_label)return &artwork_tiles[g.tile];return nullptr;}
std::pair<int,int> ink(std::span<const uint8_t>r,std::string_view s){
 int lo=12,hi=-1;for(char c:s){int code=encode(c);for(int y=0;y<12;++y)for(int x=0;x<6;++x){auto n=y*16+(code&1)*8+x;auto v=byte(r,0x80352800+(code/2)*96+n/2);v=n&1?v&15:v>>4;if(byte(r,0x80087460+v*2+1)&1){lo=std::min(lo,y);hi=std::max(hi,y);}}}return {lo,hi};
}
struct Rect {uint32_t at;};
std::optional<std::vector<Rect>> plan(std::span<const uint8_t>r,uint32_t begin,uint32_t end,unsigned row,bool& replace_panel){
 std::vector<Rect>out,body;uint32_t texture=0;bool panel=false;unsigned type_count=0,panel_count=0,borders=0;
 for(uint32_t p=begin;p<end;p+=8){auto a=word(r,p),b=word(r,p+4);if(a>>24==0xfd)texture=b&0x7fffff;if(a>>24!=0xe4)continue;
  if(p+24>end||word(r,p+8)!=0xe1000000||word(r,p+16)!=0xf1000000)return {};
  const unsigned x=b>>12&4095,y=b&4095,right=a>>12&4095,bottom=a&4095;
  if(texture==0x1bbd60&&x==23*4&&y==142*4&&right==300*4&&bottom==211*4){if(panel)return {};panel=true;}
  bool replace=false;
  if(texture==0x270140&&y==79*4&&bottom==95*4&&x>=87*4&&right<=298*4){replace=true;++type_count;}
  if(panel&&texture==0x240c40&&y>=140*4&&bottom<=212*4)++borders;
  if(panel&&texture!=0x240c40&&x>=30*4&&right<=302*4&&y>=145*4&&bottom<=210*4){replace=true;++panel_count;}
  if(replace){if(y==79*4)out.push_back({p});else body.push_back({p});}p+=16;
 }
 if(type_count!=8)return {};
 // Cursor has a different lower description. Its shape cannot invalidate
 // the independently recognized Config row or hide the selected host types.
 replace_panel=row<=1&&panel&&panel_count>=30&&panel_count<=60&&borders==48;
 if(replace_panel)out.insert(out.end(),body.begin(),body.end());
 return out;
}
struct Session {
 std::span<uint8_t>r;const recomp_context&caller;const PalControllerScreenFunctions&fn;
 uint32_t sp,local,object,desc,segments,resource,head,palette;uintptr_t fp_offset;
 std::array<uint8_t,0x600>saved{};
 Session(std::span<uint8_t>ram,const recomp_context&c,const PalControllerScreenFunctions&f):r(ram),caller(c),fn(f){sp=uint32_t(c.r29);local=sp-0x300;object=local+0x20;desc=local+0x60;segments=local+0x80;resource=local+0xa0;head=word(r,0x8009e0c8);fp_offset=c.f_odd?reinterpret_cast<uintptr_t>(c.f_odd)-reinterpret_cast<uintptr_t>(&c.f0):0;std::memcpy(saved.data(),r.data()+((sp-0x600)&0x7fffff),saved.size());}
 void call(recomp_func_t*f,uint32_t a,uint32_t b=0){auto c=caller;if(caller.f_odd)c.f_odd=reinterpret_cast<uint32_t*>(reinterpret_cast<uint8_t*>(&c.f0)+fp_offset);c.r29=S32(local);c.r4=S32(a);c.r5=S32(b);f(r.data(),&c);}
 void start(const std::array<const std::array<uint8_t,256>*,8>&tiles,std::array<uint32_t,8>&addresses){
  auto p=head+8;palette=p;for(unsigned i=0;i<artwork_colors.size();++i){auto c=artwork_colors[i];uint16_t v=((c>>27)&31)<<11|((c>>19)&31)<<6|((c>>11)&31)<<1|bool(c&255);sh(r,p+i*2,v);}for(unsigned i=artwork_colors.size();i<16;++i)sh(r,p+i*2,0);p+=32;
  for(unsigned n=0;n<8;++n){if(!tiles[n])continue;addresses[n]=p;for(unsigned i=0;i<128;++i)sb(r,p+i,(*tiles[n])[i*2]<<4|(*tiles[n])[i*2+1]);p+=128;}
  put(r,head,0xde010000);put(r,head+4,p);put(r,0x8009e0c8,p);
 }
 void icon(uint32_t pixels,int x,int y){
  call(fn.initialize_sprite,object);put(r,desc,0x00100010);put(r,desc+4,0x01000000);put(r,desc+8,pixels);put(r,segments,0x90101000);put(r,segments+4,0);put(r,segments+8,0);put(r,resource,114u<<16);put(r,resource+4,8u<<24);put(r,resource+8,segments);
  auto bank=word(r,0x80076ca4);put(r,0x80076ca4,desc);call(fn.construct_resource,object,resource);put(r,0x80076ca4,bank);sb(r,object+4,1);put(r,object+8,0x04026642);sb(r,object+0xc,15);put(r,object+0x34,palette);sh(r,object+0x20,x);sh(r,object+0x24,y);put(r,object+0x28,0x3f800000);put(r,object+0x2c,0x3f800000);call(fn.draw_sprite,object);
 }
 ~Session(){std::memcpy(r.data()+((sp-0x600)&0x7fffff),saved.data(),saved.size());}
};
}
bool configure_pal_controller_screen(std::span<const uint8_t>rom){std::lock_guard lock(guard);if(rom.size()!=0x1000000||rom_detail::sha256_hex(rom)!="6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf")return false;configured=true;return true;}
bool draw_pal_controller_screen(std::span<uint8_t>r,const recomp_context&caller,const PalControllerScreenView&v,const PalControllerScreenFunctions&fn){
 std::lock_guard lock(guard);
 if(!configured||r.size()!=0x800000||!fn.initialize_sprite||!fn.construct_resource||!fn.draw_sprite||!fn.draw_text||v.selected_port>=4||v.selected_action>=8||!owner(r))return false;
 for(const auto&s:v.types)if(s!="Type 1"&&s!="Type 2"&&s!="Type 3"&&s!="Type 4"&&s!="Type 5"&&s!="Free")return false;
 if(!text(v.start_footer,40)||word(r,0x8009e02c)!=0x8013b418||byte(r,0x8013b42a)||word(r,0x8013b42c)!=0x014000f0)return false;
 if(!match(r,0x80270140,0x2180,"3503b69f26c73874393615c615d91f082c4cb6c3590689fee1eb3c8dc9f536b6")||!match(r,0x802cd8d0,0x1a30,"8f114ba25bce26a023f7c2d5bbe5bd7dc9625ed657822d489b27648e2f72b2ff")||!match(r,0x80352800,0x3000,"237c7f53ac8b11353467cb957868f794507ca2688c93581d977dac03a4e8b765")||!match(r,0x80087460,32,"197e03223036a1ab8a7441afad5384f88d5cba2f9e6085c49d63c422abf0f9c6"))return false;
 if(!match(r,0x80008a54,96,"0422ab70b5a32e7152c7232f0a377142a6d169e575cc4685bc4914e8f4ceb17e")||!match(r,0x80007c2c,100,"3c6ec8b03d8957483632569fe02037f55a6f1058dee1cb5591a52e46bac352e0")||!match(r,0x80041b50,2220,"f6419f1b0a58a0e14add0def5f1a70e23cf3091ee652922f77fdbdc359b0b437")||!match(r,0x80048660,764,"2e1211ac1d08b931b3825a1c11175dcffbfa09a9108d5d703dacde3387262b31"))return false;
 const auto sp=uint32_t(caller.r29);if(sp<0x800a08d8||sp>0x800a42d8||(sp&7))return false;auto fp=reinterpret_cast<uintptr_t>(caller.f_odd),lo=reinterpret_cast<uintptr_t>(&caller.f0),hi=reinterpret_cast<uintptr_t>(&caller.f31)+sizeof(fpr);if(fp&&(fp<lo||fp>hi-4||(fp-lo)%4))return false;
 auto gfx=pal_gfx_bounds(r);if(!gfx)return false;bool replace_panel=false;auto replacements=plan(r,gfx.begin,gfx.cursor,byte(r,0x802d21e0+v.selected_port),replace_panel);if(!replacements)return false;
 std::vector<EngineTextLine>lines;std::array<const std::array<uint8_t,256>*,8>tiles{};unsigned chars=0;
 for(unsigned n=0;n<4;++n){lines.push_back({int16_t(87+n*56),81,v.types[n]});chars+=v.types[n].size();}
 if(replace_panel)for(unsigned n=0;n<8;++n){auto&a=v.actions[n];std::string label=(v.free_capture&&n==v.selected_action?"Edit ":"")+a.action;if(!text(label,14))return false;auto*t=tile(a);tiles[n]=t;const int x=38+int(n/4)*138,y=146+int(n%4)*16;int il=1,ih=14;
  if(t){il=16;ih=-1;for(unsigned i=0;i<256;++i)if((*t)[i]){il=std::min(il,int(i/16));ih=std::max(ih,int(i/16));}if(ih<il)return false;}
  else{if(!text(a.physical_label,4))return false;lines.push_back({int16_t(x),int16_t(y+2),a.physical_label});chars+=a.physical_label.size();}
  auto [tl,th]=ink(r,label);if(th<tl)return false;int text_y=y+(il+ih-tl-th+1)/2;
  lines.push_back({int16_t(x+32),int16_t(text_y),label});chars+=label.size();
 }
 if(replace_panel){lines.push_back({int16_t((320-int(v.start_footer.size())*6)/2),216,v.start_footer,8});chars+=v.start_footer.size();}
 const size_t required=1064+8*512+chars*128+lines.size()*256;if(required>gfx.end-gfx.cursor)return false;
 Session s(r,caller,fn);std::array<uint32_t,8>addresses{};s.start(tiles,addresses);for(unsigned n=0;n<8;++n)if(addresses[n])s.icon(addresses[n],42+int(n/4)*138,146+int(n%4)*16);
 for(size_t i=0;i<lines.size();i+=10)if(!draw_pal_engine_text(r,caller,std::span<const EngineTextLine>(lines).subspan(i,std::min(size_t(10),lines.size()-i)),fn.draw_text))std::abort();
 for(auto rect:*replacements)for(unsigned i=0;i<24;i+=4)put(r,rect.at+i,0);return true;
}
}
