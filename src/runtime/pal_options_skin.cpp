// Original project work: djultra64.
#include "pal_options_skin.hpp"
#include "pal_options_row_font.hpp"
#include "pal_options_entry.hpp"
#include "pal_background_widescreen.hpp"
#include "game_controls_menu.hpp"
#include "pal_sky_widescreen.hpp"
#include "rom_image.hpp"
#include <array>
#include <algorithm>
#include <cstring>
#include <mutex>
#include <optional>
namespace iss2000 {namespace {
using Bytes=std::vector<uint8_t>;
// greatdocbrown Gamepad UI, CC0; exact palette used by the Controller screen.
constexpr std::array<uint32_t,13> glyph_colors{0x00000000,0x14182EFF,0x686F99FF,0x404973FF,0x4FA4B8FF,0x2C354DFF,0x63AB3FFF,0xF0B541FF,0xE64539FF,0xF5FFE8FF,0xA3A7C2FF,0xDFE0E8FF,0xFF5277FF};
std::array<uint8_t,32> glyph_palette(){std::array<uint8_t,32> p{};for(unsigned i=0;i<glyph_colors.size();++i){auto c=glyph_colors[i];uint16_t v=((c>>27)&31)<<11|((c>>19)&31)<<6|((c>>11)&31)<<1|bool(c&255);p[i*2]=v>>8;p[i*2+1]=v;}return p;}
uint32_t be(std::span<const uint8_t>r,size_t a){return uint32_t(r[a])<<24|uint32_t(r[a+1])<<16|uint32_t(r[a+2])<<8|r[a+3];}
uint32_t word(std::span<const uint8_t>r,uint32_t a){uint32_t v;std::memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
uint8_t byte(std::span<const uint8_t>r,uint32_t a){return r[(a&0x7fffff)^3];}
void put(std::span<uint8_t>r,uint32_t a,uint32_t v){std::memcpy(r.data()+(a&0x7fffff),&v,4);}
void sb(std::span<uint8_t>r,uint32_t a,uint8_t v){r[(a&0x7fffff)^3]=v;}
void sh(std::span<uint8_t>r,uint32_t a,uint16_t v){std::memcpy(r.data()+((a&0x7fffff)^2),&v,2);}
void copy(std::span<uint8_t>r,uint32_t a,std::span<const uint8_t>v){for(unsigned i=0;i<v.size();++i)sb(r,a+i,v[i]);}
Bytes unpack(std::span<const uint8_t>rom,unsigned id){
 const unsigned table=0x972bc+(id-1)*8;size_t start=be(rom,table)&0x7fffffff,end=be(rom,table+4),p=start;Bytes out;
 if(start>=end||end>rom.size())return{};
 while(p+4<=end){const size_t b=p;uint32_t h=be(rom,p);p+=4;if(h>>28||h<4||b+h>end)return{};const size_t stop=b+h;
  auto read=[&]()->unsigned{if(p>=stop)throw 1;return rom[p++];};
  try{while(p<stop){auto t=read();if(t<128){auto d=((t<<8)|read())&1023;auto n=(t>>2)+2;if(!d||d>out.size())return{};while(n--)out.push_back(out[out.size()-d]);}
   else if(t<160){auto n=t&31;while(n--)out.push_back(read());}
   else if(t<224){auto n=(t&31)+2,v=read();out.insert(out.end(),n,uint8_t(v));}
   else{auto n=t==255?read()+2:(t&31)+2;out.insert(out.end(),n,0);}if(out.size()>0x40000)return{};}}
  catch(...){return{};}p=(p+15)&~size_t(15);
 }return out;
}
struct Cache {bool ready=false;std::string font_sha;Bytes row_font,font,grid,frame,white,orange,green,bullet,bullet_green,bullet_orange;std::array<unsigned,56>advance{};std::vector<std::pair<std::string,PalOptionsRowBitmap>>body_rows;};
Cache cache;std::mutex cache_mutex;
int glyph(char c){if(c>='A'&&c<='Z')return c-'A';if(c>='a'&&c<='z')return c-'a'+26;if(c=='?')return 52;if(c=='1')return 53;if(c=='2')return 54;if(c=='/')return 55;return-1;}
float width(std::string_view s,float scale){float n=0;for(char c:s){if(c==' ')n+=6*scale;else{auto g=glyph(c);if(g<0)return-1;n+=cache.advance[g]*scale;}}return n;}
bool match(std::span<const uint8_t>r,uint32_t a,unsigned n,std::string_view pin){Bytes data(n);for(unsigned i=0;i<n;++i)data[i]=byte(r,a+i);return rom_detail::sha256_hex(data)==pin;}
bool owner(std::span<const uint8_t>r,PalOptionsSkinOwner o){
 if(o==PalOptionsSkinOwner::Options)return pal_options_entry(r).has_value();
 if(!match(r,0x802c48f4,196,"795692bca22a2b146f792ed4cd9706e68c44c882653d680161f3a2ae627ee308")||!match(r,0x802c49b8,188,"cd3ba5dec46fe04be08333834a8f44137666dd41705ff8db190a64214ed250a4"))return false;
 std::array<bool,220>seen{};auto node=word(r,0x80077390);bool found=false;
 while(node){if(node<0x801e7070||node>=0x801ed420||(node-0x801e7070)%0x74)return false;auto i=(node-0x801e7070)/0x74;if(i>=seen.size()||seen[i])return false;seen[i]=true;found|=word(r,node+12)==0x802c48f4;node=word(r,node);}return found;
}
struct Session {
 std::span<uint8_t>r;const recomp_context&caller;const PalOptionsSkinFunctions&fn;uint32_t sp{},local{},object{},desc{},segments{},resource{},row_font{},font{},grid{},frame{},white{},orange{},green{},bullet{},bullet_green{},bullet_orange{},begin{},limit{};uintptr_t fp_offset{};std::array<uint8_t,0x600>saved{};std::vector<uint32_t>row_textures,glyph_textures;uint32_t glyph_tlut{};bool live=false;
 Session(std::span<uint8_t>a,const recomp_context&c,const PalOptionsSkinFunctions&f):r(a),caller(c),fn(f){}
 bool preflight(unsigned required){
  if(!cache.ready||r.size()!=0x800000||!fn.initialize_sprite||!fn.construct_resource||!fn.draw_sprite)return false;
  if(word(r,0x8009e02c)!=0x8013b418||byte(r,0x8013b42a)!=0||word(r,0x8013b42c)!=0x014000f0||word(r,0x8013b430)!=0x802e2000)return false;
  if(!match(r,0x80008a54,96,"0422ab70b5a32e7152c7232f0a377142a6d169e575cc4685bc4914e8f4ceb17e")||!match(r,0x80007c2c,100,"3c6ec8b03d8957483632569fe02037f55a6f1058dee1cb5591a52e46bac352e0")||!match(r,0x80041b50,2220,"f6419f1b0a58a0e14add0def5f1a70e23cf3091ee652922f77fdbdc359b0b437"))return false;
  if(!match(r,0x8022ce40,8192,cache.font_sha))return false;
  sp=uint32_t(caller.r29);if(sp<0x800a08d8||sp>0x800a42d8||(sp&7))return false;
  auto p=reinterpret_cast<uintptr_t>(caller.f_odd),lo=reinterpret_cast<uintptr_t>(&caller.f0),hi=reinterpret_cast<uintptr_t>(&caller.f31)+sizeof(fpr);
  if(p&&(p<lo||p>hi-4||(p-lo)%4))return false;fp_offset=p?p-lo:0;
  auto bounds=pal_gfx_bounds(r);if(!bounds||required>bounds.end-bounds.cursor)return false;
  begin=bounds.cursor;limit=bounds.end;local=sp-0x300;object=local+0x20;desc=local+0x60;segments=local+0x80;resource=local+0x240;return true;
 }
 void start(std::span<const PalOptionsRowBitmap* const>rows={},std::span<const prompt_detail::PixelBytes>glyphs={}){
  std::memcpy(saved.data(),r.data()+((sp-0x600)&0x7fffff),saved.size());live=true;
  // Real F3DEX2 branch skips original pixel/palette payload. The task cursor
  // advances beyond it before any original sprite calls allocate commands.
  auto p=begin+8;row_font=p;copy(r,p,cache.row_font);p+=cache.row_font.size();font=0x8022ce40;grid=p;copy(r,p,cache.grid);p+=cache.grid.size();frame=p;copy(r,p,cache.frame);p+=cache.frame.size();white=p;copy(r,p,cache.white);p+=32;orange=p;copy(r,p,cache.orange);p+=32;green=p;copy(r,p,cache.green);p+=32;bullet=p;copy(r,p,cache.bullet);p+=cache.bullet.size();bullet_green=p;copy(r,p,cache.bullet_green);p+=32;bullet_orange=p;copy(r,p,cache.bullet_orange);p+=32;
  for(const auto* row:rows){row_textures.push_back(p);copy(r,p,row->pixels);p+=row->pixels.size();}
  if(!glyphs.empty()){glyph_tlut=p;copy(r,p,glyph_palette());p+=32;for(const auto&g:glyphs){glyph_textures.push_back(p);copy(r,p,g);p+=g.size();}}
  p=(p+7)&~7u;
  put(r,begin,0xde010000);put(r,begin+4,p);put(r,0x8009e0c8,p);
 }
 recomp_context context(uint32_t a,uint32_t b=0){auto c=caller;if(caller.f_odd)c.f_odd=reinterpret_cast<uint32_t*>(reinterpret_cast<uint8_t*>(&c.f0)+fp_offset);c.r29=S32(local);c.r4=S32(a);c.r5=S32(b);return c;}
 void call(recomp_func_t*f,uint32_t a,uint32_t b=0){auto c=context(a,b); // Rebase after return-by-value, independently of copy elision.
  if(caller.f_odd)c.f_odd=reinterpret_cast<uint32_t*>(reinterpret_cast<uint8_t*>(&c.f0)+fp_offset);f(r.data(),&c);
 }
 void sprite(uint32_t texture,unsigned tw,unsigned th,uint32_t format,uint32_t palette,int x,int y,unsigned w,unsigned h,unsigned u=0,unsigned v=0,float scale=1,bool selected=false){
  call(fn.initialize_sprite,object);put(r,desc,tw<<16|th);put(r,desc+4,format);put(r,desc+8,texture);
  put(r,segments,0x90000000|w<<16|h<<8);put(r,segments+4,0);put(r,segments+8,u*32<<16|v*32);
  put(r,resource,114u<<16);put(r,resource+4,8u<<24);put(r,resource+8,segments);
  auto bank=word(r,0x80076ca4);put(r,0x80076ca4,desc);call(fn.construct_resource,object,resource);put(r,0x80076ca4,bank);
  sb(r,object+4,1);put(r,object+8,0x04026642);
  // Original4250C accepts a per-object CI4 palette only at selector15.
  // Descriptor palette indices use the shared TLUT and do not read +34.
  if((format&0x07000000u)==0x01000000u)sb(r,object+0xc,15);
  put(r,object+0x34,palette);sh(r,object+0x20,uint16_t(x));sh(r,object+0x24,uint16_t(y));uint32_t bits;std::memcpy(&bits,&scale,4);put(r,object+0x28,bits);put(r,object+0x2c,bits);
  if(selected){sb(r,object+0xe,255);sb(r,object+0xf,180);sb(r,object+0x10,24);}call(fn.draw_sprite,object);
 }
 void text(std::string_view s,int x,int y,float scale,bool selected){float at=float(x);for(char c:s){if(c==' '){at+=6*scale;continue;}auto g=unsigned(glyph(c));auto atlas=g/16,cell=g%16;sprite(font+atlas*2048,128,32,0x03000000,white,int(at+.5f),y,16,16,(cell%8)*16,(cell/8)*16,scale,selected);at+=cache.advance[g]*scale;}}
 void bar(int x,int y,bool selected,unsigned cells=14,bool selector=true){
  // The original grid is extended by repeating middle cells; neither glyphs
  // nor the grid cell aspect is stretched. One genuine sprite list per pass.
  for(unsigned pass=0;pass<(selected?2u:1u);++pass){
   call(fn.initialize_sprite,object);put(r,desc,(pass?96u:128u)<<16|16);put(r,desc+4,0x01010000);put(r,desc+8,pass?frame:grid);
   for(unsigned n=0;n<cells;++n){put(r,segments+n*12,(n==0?0x10u:n==cells-1?0x80u:0u)<<24|0x00101000);put(r,segments+n*12+4,n*16<<16);put(r,segments+n*12+8,(n==cells-1?(pass?32u:112u):n?(pass?0u:16u):0u)*32<<16);}
   put(r,resource,114u<<16);put(r,resource+4,4u<<24);put(r,resource+8,segments);
   auto bank=word(r,0x80076ca4);put(r,0x80076ca4,desc);call(fn.construct_resource,object,resource);put(r,0x80076ca4,bank);
   sb(r,object+4,1);put(r,object+8,0x04026642);sb(r,object+0xc,15);put(r,object+0x34,green);sb(r,object+0x11,pass?128:selector?204:255);sh(r,object+0x20,x);sh(r,object+0x24,y);call(fn.draw_sprite,object);
  }
  if(selector)sprite(bullet,16,16,0x01030000,selected?bullet_orange:bullet_green,x-8,y,16,16);
 }
 ~Session(){if(live){if(word(r,0x8009e0c8)>limit)std::abort();std::memcpy(r.data()+((sp-0x600)&0x7fffff),saved.data(),saved.size());}}
};
}
bool configure_pal_options_skin(std::span<const uint8_t>rom){std::lock_guard lock(cache_mutex);
 if(rom.size()!=0x1000000||rom_detail::sha256_hex(rom)!="6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf")return false;
 if(cache.ready)return true;
 auto common=unpack(rom,0x15),options=unpack(rom,0x42);
 if(common.size()!=0x26f40||rom_detail::sha256_hex(common)!="2a00a6356e10fb53d1a6fa23c9061b3a3265edacb7aae393b47c60b1248f4c27"||options.size()!=0x2c00||rom_detail::sha256_hex(options)!="5dbf56dd71d5c280fc0fad104003a23898312e4fd9468a76fd023db8d221a3e8")return false;
 auto row=pal_options_row_bitmap(options,"PC Settings");if(!row)return false;
 Cache c;c.row_font=std::move(row->pixels);c.font.assign(common.begin()+0x1a740,common.begin()+0x1c740);c.font_sha=rom_detail::sha256_hex(c.font);c.grid.assign(options.begin()+0x1900,options.begin()+0x1d00);c.frame.assign(options.begin()+0x1d00,options.begin()+0x2000);
 for(const auto* label:{"Graphics","Controls","Save options","Cancel","Aspect","Resolution","Framerate limit","Filtering","Screen","Back","Controller type","Vibration","Player"}){auto bitmap=pal_options_row_bitmap(options,label);if(!bitmap)return false;c.body_rows.emplace_back(label,std::move(*bitmap));}
 c.white.assign(rom.begin()+0x35e3e0,rom.begin()+0x35e400);c.orange.assign(rom.begin()+0x353890,rom.begin()+0x3538b0);c.green.assign(rom.begin()+0x35c820,rom.begin()+0x35c840);
 for(unsigned g=0;g<56;++g){unsigned right=0;for(unsigned y=0;y<16;++y)for(unsigned x=0;x<16;++x){unsigned p=g/16*4096+(g%16/8*16+y)*128+(g%8*16+x);auto v=c.font[p/2];v=p&1?v&15:v>>4;if(v>=8)right=std::max(right,x+1);}c.advance[g]=std::clamp(right,5u,15u);}
 c.bullet.assign(common.begin()+0x22780,common.begin()+0x22800);c.bullet_green.assign(rom.begin()+0x3539f0,rom.begin()+0x353a10);c.bullet_orange.assign(rom.begin()+0x353a10,rom.begin()+0x353a30);
 c.ready=true;cache=std::move(c);return true;
}
bool pal_options_skin_text_supported(std::string_view s){std::lock_guard lock(cache_mutex);return cache.ready&&!s.empty()&&s.size()<=40&&width(s,1)>=0;}
bool draw_pal_options_skin_label(std::span<uint8_t>r,const recomp_context&caller,std::string_view text,int x,int y,bool selected,const PalOptionsSkinFunctions&fn){
 std::lock_guard lock(cache_mutex);if(!cache.ready||text!="PC Settings"||x<0||y<0||x+128>320||y+16>240||!owner(r,PalOptionsSkinOwner::Options))return false;
 Session s(r,caller,fn);if(!s.preflight(5000))return false;s.start();
 // Original row words are CI4 bitmaps at unit scale, with their original
 // palette-index outlines. The separate title alphabet has different metrics.
 s.sprite(s.row_font,128,16,0x01000000,selected?s.orange:s.white,x,y,128,16);return true;
}
bool draw_pal_options_skin(std::span<uint8_t>r,const recomp_context&caller,const PalOptionsSkinView&v,PalOptionsSkinOwner o,bool wide,const PalOptionsSkinFunctions&fn){
 std::lock_guard lock(cache_mutex);if(!cache.ready||r.size()!=0x800000||v.rows.empty()||v.rows.size()>8||v.selected>=v.rows.size()||v.help.size()>4||v.shortcuts.size()>3||!fn.draw_text||!owner(r,o))return false;
 std::string_view title=v.title;std::string number;
 if(title.size()>2&&title[title.size()-2]==' '&&title.back()>='0'&&title.back()<='9'){number=std::string(title.substr(title.size()-1));title=title.substr(0,title.size()-2);}
 if(title.empty()||title.size()>24||width(title,1)<0||width(title,1)>210)return false;
 const unsigned help_y=v.shortcuts.empty()?180+(4-unsigned(v.help.size()))*12:184;
 if(!v.help.empty()&&(help_y<50+(v.rows.size()-1)*19+22||(!v.shortcuts.empty()&&v.help.size()>1)))return false;
 // Device preferences share the authentic Options row face. Football scheme
 // editing is owned separately by the original pre-match Controller screen.
 const bool row_face=v.title=="PC Settings"||v.title=="Graphics"||v.title=="Controls"||title=="Player";
 unsigned chars=title.size();std::vector<EngineTextLine>secondary;
 std::vector<prompt_detail::PixelBytes> glyphs;unsigned footer_width=0;
 for(const auto& shortcut:v.shortcuts){
  if(shortcut.label.empty()||shortcut.label.size()>16)return false;for(char c:shortcut.label)if(!((c>='A'&&c<='Z')||(c>='a'&&c<='z')||c==' '))return false;
  const auto p=glyph_palette();auto pixels=prompt_detail::glyph_pixels({shortcut.family,shortcut.button,0},p);if(!pixels)return false;
  const auto text_width=width(shortcut.label,.75f);if(text_width<0)return false;
  glyphs.push_back(*pixels);footer_width+=20+unsigned(text_width+.999f)+12;chars+=shortcut.label.size();
 }
 // Each item reserves a12px gap for the next item. The last gap is not
 // drawn: Graphics occupies302px, not314px, inside the304px footer plate.
 if(footer_width&&footer_width-12>304)return false;
 std::vector<const PalOptionsRowBitmap*>row_bitmaps;
 const int title_x=int((320-width(title,1)-(number.empty()?0:12))/2);
 if(!number.empty())secondary.push_back({int16_t(title_x+width(title,1)+6),24,number,8,0});
 for(unsigned i=0;i<v.rows.size();++i){
  const auto&a=v.rows[i];float w;
  if(row_face){
   const PalOptionsRowBitmap* bitmap=nullptr;
   for(const auto& [label,value]:cache.body_rows)if(label==a.label){bitmap=&value;break;}
   if(!bitmap)return false; // Whole-page preflight, before any guest writes.
   row_bitmaps.push_back(bitmap);w=bitmap->advance;
  }else{w=width(a.label,.75f);chars+=a.label.size();}
  if(a.label.empty()||a.label.size()>32||w<0||w>128||a.value.size()>18)return false;
  if(!a.value.empty()&&276-int(a.value.size()*6)<67+w+8)return false;
  if(!a.value.empty())secondary.push_back({int16_t(276-a.value.size()*6),int16_t(54+i*19),a.value,8,0});
 }
 for(unsigned i=0;i<v.help.size();++i){if(v.help[i].empty()||v.help[i].size()>40)return false;secondary.push_back({24,int16_t(help_y+i*12),v.help[i],uint8_t(v.shortcuts.empty()?8:12),0});}
 // Validate the same supported secondary alphabet before emitting any commands.
 for(const auto&line:secondary)for(char c:line.text)if(!(c==' '||c=='.'||(c>='0'&&c<='9')||(c>='A'&&c<='Z')||(c>='a'&&c<='z')))return false;
 if(pal_background_kind(r,true,0x8013c47c)!=PalBackgroundKind::CommonMenu)return false;
 unsigned secondary_chars=0;for(const auto&line:secondary)secondary_chars+=line.text.size();
 if(!match(r,0x80048660,764,"2e1211ac1d08b931b3825a1c11175dcffbfa09a9108d5d703dacde3387262b31")||!match(r,0x80352800,12288,"237c7f53ac8b11353467cb957868f794507ca2688c93581d977dac03a4e8b765"))return false;
 Session s(r,caller,fn);if(!s.preflight(16000+unsigned(glyphs.size())*2048+chars*128+unsigned(v.rows.size())*800+unsigned(row_bitmaps.size())*1024+secondary_chars*128+unsigned(secondary.size())*256))return false;s.start(row_bitmaps,glyphs);
 {PalBackgroundScope background(r,wide,0x8013c47c);s.call(fn.draw_sprite,0x8013c47c);}
 // Reuse the original common heading plate, separately from its old word sprites.
 if(word(r,0x8013c5a8+0x14)==0x803d80d8&&word(r,0x8013c5a8+0x30)==0x803e54d8)s.call(fn.draw_sprite,0x8013c5a8);
 s.text(title,title_x,20,1,false);
 for(unsigned i=0;i<v.rows.size();++i){
  auto y=50+int(i)*19;s.bar(54,y,i==v.selected);
  if(row_face)s.sprite(s.row_textures[i],128,16,0x01000000,i==v.selected?s.orange:s.white,67,y+1,128,16);
  else s.text(v.rows[i].label,67,y+1,.75f,i==v.selected);
 }
 if(!v.shortcuts.empty()){
  if(!v.help.empty())s.bar(8,182,false,19,false);
  s.bar(8,206,false,19,false);
  int x=int((320-(footer_width-12))/2);
  for(unsigned n=0;n<v.shortcuts.size();++n){const auto&shortcut=v.shortcuts[n];
   s.sprite(s.glyph_textures[n],16,16,0x01000000,s.glyph_tlut,x,206,16,16);
   // The original italic common-menu alphabet is clearer at12px than the
   // former8px instruction text. Its visual ink center matches the16px icon.
   s.text(shortcut.label,x+20,209,.75f,false);x+=20+int(width(shortcut.label,.75f)+.999f)+12;
  }
 }
 for(size_t i=0;i<secondary.size();i+=10)if(!draw_pal_engine_text(r,caller,std::span<const EngineTextLine>(secondary).subspan(i,std::min(size_t(10),secondary.size()-i)),fn.draw_text))std::abort();return true;
}
}
