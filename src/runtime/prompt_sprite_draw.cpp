// Original integration work: djultra64. Artwork: greatdocbrown, CC0-1.0.
#include "prompt_sprite_draw.hpp"
#include "game_controls_menu.hpp"
#include "pal_sky_widescreen.hpp"
#include "rom_image.hpp"
#include <algorithm>
#include <cstring>
#include <cstdlib>
namespace iss2000 {namespace {
#include "gdb_prompt_glyphs.inc"
uint32_t word(std::span<const uint8_t>r,uint32_t a){uint32_t v;std::memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
uint8_t byte(std::span<const uint8_t>r,uint32_t a){return r[(a&0x7fffff)^3];}
void put(std::span<uint8_t>r,uint32_t a,uint32_t v){std::memcpy(r.data()+(a&0x7fffff),&v,4);}
void sb(std::span<uint8_t>r,uint32_t a,uint8_t v){r[(a&0x7fffff)^3]=v;}
void sh(std::span<uint8_t>r,uint32_t a,uint16_t v){std::memcpy(r.data()+((a&0x7fffff)^2),&v,2);}
bool match(std::span<const uint8_t>r,uint32_t a,unsigned n,std::string_view pin){std::vector<uint8_t>b(n);for(unsigned i=0;i<n;++i)b[i]=byte(r,a+i);return rom_detail::sha256_hex(b)==pin;}
const std::array<uint8_t,256>* tile(const PromptSpriteIcon&i){for(const auto&g:artwork_glyphs)if(g.family==i.family&&g.label==i.label)return &artwork_tiles[g.tile];return nullptr;}
int encode(char c){if(c==' ')return 0;if(c>='0'&&c<='9')return c-'0'+1;if(c>='A'&&c<='Z')return c-'A'+11;if(c>='a'&&c<='z')return c-'a'+37;return c=='.'?63:-1;}
struct Session {
 std::span<uint8_t>r;const recomp_context&caller;const PalPromptSpriteFunctions&fn;
 uint32_t sp,local,object,desc,segments,resource,head,palette;uintptr_t fp_offset;
 std::array<uint8_t,0x600> saved{};
 Session(std::span<uint8_t>a,const recomp_context&c,const PalPromptSpriteFunctions&f):r(a),caller(c),fn(f){sp=uint32_t(c.r29);local=sp-0x300;object=local+0x20;desc=local+0x60;segments=local+0x80;resource=local+0xa0;head=word(r,0x8009e0c8);fp_offset=c.f_odd?reinterpret_cast<uintptr_t>(c.f_odd)-reinterpret_cast<uintptr_t>(&c.f0):0;std::memcpy(saved.data(),r.data()+((sp-0x600)&0x7fffff),saved.size());}
 void call(recomp_func_t*f,uint32_t a,uint32_t b=0){auto c=caller;if(caller.f_odd)c.f_odd=reinterpret_cast<uint32_t*>(reinterpret_cast<uint8_t*>(&c.f0)+fp_offset);c.r29=S32(local);c.r4=S32(a);c.r5=S32(b);f(r.data(),&c);}
 void start(std::span<const std::array<uint8_t,256>*const>tiles,std::array<uint32_t,8>&addresses){
  auto p=head+8;palette=p;for(unsigned i=0;i<16;++i){auto c=i<artwork_colors.size()?artwork_colors[i]:0u;uint16_t v=((c>>27)&31)<<11|((c>>19)&31)<<6|((c>>11)&31)<<1|bool(c&255);sh(r,p+i*2,v);}p+=32;
  for(unsigned n=0;n<tiles.size();++n){addresses[n]=p;for(unsigned i=0;i<128;++i)sb(r,p+i,(*tiles[n])[i*2]<<4|(*tiles[n])[i*2+1]);p+=128;}
  put(r,head,0xde010000);put(r,head+4,p);put(r,0x8009e0c8,p);
 }
 void icon(uint32_t pixels,const PromptSpriteIcon&i){
  call(fn.initialize_sprite,object);put(r,desc,0x00100010);put(r,desc+4,0x01000000);put(r,desc+8,pixels);put(r,segments,0x90101000);put(r,segments+4,0);put(r,segments+8,0);put(r,resource,114u<<16);put(r,resource+4,8u<<24);put(r,resource+8,segments);
  auto bank=word(r,0x80076ca4);put(r,0x80076ca4,desc);call(fn.construct_resource,object,resource);put(r,0x80076ca4,bank);sb(r,object+4,1);put(r,object+8,0x04426642);sb(r,object+0xc,15);put(r,object+0x34,palette);sh(r,object+0x20,i.x);sh(r,object+0x24,i.y);
  const float sx=i.width/16.f,sy=i.height/16.f;uint32_t bits;std::memcpy(&bits,&sx,4);put(r,object+0x28,bits);std::memcpy(&bits,&sy,4);put(r,object+0x2c,bits);call(fn.draw_sprite,object);
 }
 ~Session(){std::memcpy(r.data()+((sp-0x600)&0x7fffff),saved.data(),saved.size());}
};
}
bool pal_prompt_icon_available(const PromptSpriteIcon&i){return tile(i)!=nullptr;}
bool draw_pal_prompt_sprite(std::span<uint8_t>r,const recomp_context&caller,const PromptSpriteResult&v,const PalPromptSpriteFunctions&fn){
 if(r.size()!=0x800000||v.status!=PromptSpriteStatus::TextFallback||!v.icon_count||v.icon_count>v.icons.size()||v.line_count>v.lines.size()||!fn.initialize_sprite||!fn.construct_resource||!fn.draw_sprite||(v.line_count&&!fn.draw_text))return false;
 if(word(r,0x8009e02c)!=0x8013b418||byte(r,0x8013b42a)||word(r,0x8013b42c)!=0x014000f0)return false;
 if(!match(r,0x80008a54,96,"0422ab70b5a32e7152c7232f0a377142a6d169e575cc4685bc4914e8f4ceb17e")||!match(r,0x80007c2c,100,"3c6ec8b03d8957483632569fe02037f55a6f1058dee1cb5591a52e46bac352e0")||!match(r,0x80041b50,2220,"f6419f1b0a58a0e14add0def5f1a70e23cf3091ee652922f77fdbdc359b0b437"))return false;
 const auto sp=uint32_t(caller.r29);if(sp<0x800a08d8||sp>0x800a42d8||(sp&7))return false;auto fp=reinterpret_cast<uintptr_t>(caller.f_odd),lo=reinterpret_cast<uintptr_t>(&caller.f0),hi=reinterpret_cast<uintptr_t>(&caller.f31)+sizeof(fpr);if(fp&&(fp<lo||fp>hi-4||(fp-lo)%4))return false;
 unsigned required=40+v.icon_count*(128+1024);std::array<const std::array<uint8_t,256>*,8>tiles{};
 for(unsigned n=0;n<v.icon_count;++n){const auto&i=v.icons[n];if(i.port>=4||i.x<0||i.y<0||i.width<8||i.width>16||i.height!=i.width||i.x+i.width>320||i.y+i.height>240||!(tiles[n]=tile(i)))return false;}
 std::array<EngineTextLine,8>lines;
 for(unsigned n=0;n<v.line_count;++n){const auto&l=v.lines[n];if(l.text.empty()||l.text.size()>40||l.x<0||l.y<0||l.x+6*l.text.size()>320||(l.height!=8&&l.height!=12)||(l.palette!=0&&l.palette!=4)||l.y+l.height+(l.height==8)>240||!std::all_of(l.text.begin(),l.text.end(),[](char c){return encode(c)>=0;}))return false;required+=128*l.text.size()+256;lines[n]={l.x,l.y,l.text,l.height,l.palette};}
 if(v.line_count&&(!match(r,0x80048660,764,"2e1211ac1d08b931b3825a1c11175dcffbfa09a9108d5d703dacde3387262b31")||!match(r,0x80352800,0x3000,"237c7f53ac8b11353467cb957868f794507ca2688c93581d977dac03a4e8b765")))return false;
 auto gfx=pal_gfx_bounds(r);if(!gfx||required>gfx.end-gfx.cursor)return false;
 Session session(r,caller,fn);std::array<uint32_t,8>addresses{};session.start({tiles.data(),v.icon_count},addresses);for(unsigned n=0;n<v.icon_count;++n)session.icon(addresses[n],v.icons[n]);
 if(v.line_count&&!draw_pal_engine_text(r,caller,{lines.data(),v.line_count},fn.draw_text))std::abort();if(word(r,0x8009e0c8)>gfx.end)std::abort();return true;
}
}
