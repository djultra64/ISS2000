// Original project work: djultra64.
#include "pal_main_select.hpp"
#include "pal_sky_widescreen.hpp"
#include "game_controls_menu.hpp"
#include "rom_image.hpp"
#include <algorithm>
#include <cstring>
#include <vector>
namespace iss2000 {namespace {
uint32_t main_word(std::span<const uint8_t>r,uint32_t p){uint32_t v;std::memcpy(&v,r.data()+(p&0x7fffff),4);return v;}
void main_put(std::span<uint8_t>r,uint32_t p,uint32_t v){std::memcpy(r.data()+(p&0x7fffff),&v,4);}
bool main_match(std::span<const uint8_t>r,uint32_t p,unsigned n,std::string_view pin){std::vector<uint8_t>v(n);for(unsigned i=0;i<n;++i)v[i]=r[((p+i)&0x7fffff)^3];return rom_detail::sha256_hex(v)==pin;}
bool main_foreground(uint32_t texture){
 // Exact resident original Main Select title, nine labels, row grid and lamps.
 // Every one of the twelve lamp frames belongs to its row. Ball layers
 // are handled separately, before their exact original draw.
 constexpr uint32_t textures[]{0x234980,0x234a00,0x234a80,0x234b00,0x234b80,0x234c00,0x234c80,0x234d00,0x234d80,0x234e00,0x234e80,0x234f00,
  0x239640,0x23cb00,0x23db00,0x23e300,0x23eb00,0x23ef00,0x23f500,0x25cf00,0x25d700,0x25db00,0x25e300,0x25eb00,0x25ef00,0x25f700};
 return std::find(std::begin(textures),std::end(textures),texture)!=std::end(textures);
}
}
bool pal_main_select_active(std::span<const uint8_t>r,bool include_exit){
 // Original 803C2C74 maps the retained destination to nine main rows:
 // 0,5,6,7,13,2,3,4,1. It is not a unique current-scene identifier.
 // The live callback and pinned resource below establish current ownership.
 if(r.size()!=0x800000||main_word(r,0x8009e02c)!=0x8013b418||main_word(r,0x8013b42c)!=0x014000f0||r[0x13b42a^3]||
    main_word(r,0x80143d6c)!=0x803d75d4||(r[0x12de74^3]>7&&r[0x12de74^3]!=13)||
    !main_match(r,0x803c2c74,120,"72838ab507597001c8f0f9bab718e364ae6d34c83638af503cc50aa88820a621")||
    !main_match(r,0x803c29fc,96,"897e8371f015ecfce94cbdbdd2dc3127aaf7c09e9e2e5acfa5a67e52d691be7b")||
    !main_match(r,0x803d75d4,48,"807bc187cb7211ea5321b705370818e9e7bb2ea3a3c1b6489fea2d83721b300d"))return false;
 std::array<bool,220>seen{};auto node=main_word(r,0x80077390);bool found=false;
 while(node){if(node<0x801e7070||node>=0x801ed420||(node-0x801e7070)%0x74)return false;
  auto n=(node-0x801e7070)/0x74;if(seen[n])return false;seen[n]=true;
  auto callback=main_word(r,node+12),pending=main_word(r,node+16);
  found|=callback==0x803c29fc||(include_exit&&callback==0x8000c96c&&(pending==0x803c297c||pending==0x803c29fc));node=main_word(r,node);
 }return found;
}
bool lift_pal_main_select(std::span<uint8_t>r,bool wide){
 if(!pal_main_select_active(r,true)||!main_match(r,0x803d7d00,0x2000,"91fbfad1c38bc5504d7d4f91771b29a4971e3b380d8dedfb57557bee04654bac"))return false;const auto bounds=pal_gfx_bounds(r);if(!bounds)return false;
 uint32_t texture=0;bool ball=false;struct Move{uint32_t pc;unsigned delta;bool left;int inset;};std::vector<Move>rects;
 for(auto pc=bounds.begin;pc<bounds.cursor;pc+=8){auto a=main_word(r,pc),b=main_word(r,pc+4);
  // The ball's scoped LEFT alignment also owns its grid and animated figures;
  // their shared grid texture must not receive the menu rows' vertical lift.
  if(a==0x64000006){if(pc+16>bounds.cursor)return false;ball=b==0;pc+=8;continue;}
  if(a==0x64000005){if(pc+16>bounds.cursor)return false;pc+=8;continue;}
  if(a>>24==0xfd)texture=b&0x7fffff;
  if(a>>24!=0xe4)continue;if(pc+24>bounds.cursor||main_word(r,pc+8)!=0xe1000000||main_word(r,pc+16)!=0xf1000000)return false;
  if(!ball&&main_foreground(texture)){
   const bool heading=texture==0x239640||texture==0x23cb00;
   const bool left=wide&&texture!=0x23ef00&&texture!=0x23f500;
   // Original item pieces share the fixed 51+20*row vertical bands; lamps
   // change images and labels fade without changing their row. Bring the
   // upper rows in a little farther; lower lamps already touch the ball edge.
   // Pre-season's r68 leading edge was 134 logical pixels. A rigid
   // +13.5-pixel move is its requested +10%, rounded to quarter pixels.
   // Signed quarter-pixel insets keep every label/lamp piece together.
   // Euro Cup/Penalties +5%; Scenario/Training/Option +10% from r69
   // leading edges, rounded to quarter pixels. All foreground pieces agree.
   constexpr int inset_quarters[]{-30,20,16,12,-27,-31,-64,-61,-57};
   const auto row=std::clamp((int(b&4095)/4-41)/20,0,8);
   rects.push_back({pc,heading?48u:64u,left,left&&!heading?inset_quarters[row]:0});
  }
  pc+=16;
 }
 // Entry/exit lists may contain fewer rows. A whole-menu count threshold made
 // their layout switch suddenly in the middle of the original animation.
 for(auto [p,delta,left,inset]:rects){auto a=main_word(r,p),b=main_word(r,p+4);
  if(!left&&(b&4095)>=delta){main_put(r,p,a-delta);main_put(r,p+4,b-delta);}
  else{
   // LEFT anchors text and lamps to the same edge as the ball, while row
   // backgrounds keep their center alignment. Signed extended coordinates
   // also preserve a partially clipped animation endpoint. Keep the original
   // command address and its interpolation UID.
   const auto uv=main_word(r,p+12),step=main_word(r,p+20);
   main_put(r,p,0x64000002);main_put(r,p+4,(left?0u:0x04004000u)|((b>>24)&7));
   main_put(r,p+8,(uint32_t(uint16_t(int(b>>12&4095)-int(inset)))<<16)|uint16_t(int(b&4095)-int(delta)));
   main_put(r,p+12,(uint32_t(uint16_t(int(a>>12&4095)-int(inset)))<<16)|uint16_t(int(a&4095)-int(delta)));
   main_put(r,p+16,uv);main_put(r,p+20,step);
  }
 }return true;
}
bool draw_pal_main_ball(std::span<uint8_t>r,recomp_context&c,bool wide,recomp_func_t*draw){
 if(!wide||!draw||!pal_main_select_active(r,true))return false;
 const uint64_t object=c.r4;const uint32_t p=uint32_t(object),upper=uint32_t(object>>32);
 if((upper&&upper!=0xffffffffu)||p<0x8013c47c||p>=0x80140478||(p-0x8013c47c)%60||r[((p+4)&0x7fffff)^3]!=1)return false;
 const auto descriptor=main_word(r,p+20),segments=main_word(r,p+48);
 const bool owned=(descriptor==0x803d9ab8&&segments==0x803d6ee0)||
  (descriptor==0x803d9770&&segments==0x803d7030)||
  (descriptor==0x803d9890&&segments==0x803d742c)||
  (descriptor==0x803d9c68&&(segments==0x803d74e0||segments==0x803d74ec||segments==0x803d7528||segments==0x803d7534))||
  (descriptor==0x803d9c74&&(segments==0x803d7504||segments==0x803d7510||segments==0x803d751c||segments==0x803d754c))||
  (descriptor>=0x803d9ba8&&descriptor<=0x803d9c5c&&(descriptor-0x803d9ba8)%12==0&&segments==0x803d7564);
 if(!owned||!main_match(r,0x803d6ee0,0x6a0,"4ba4357ea30cab9220aeed4192af74cee15d8f7307067cc1c80768dbcbded909")||
  !main_match(r,0x803d7d00,0x2000,"91fbfad1c38bc5504d7d4f91771b29a4971e3b380d8dedfb57557bee04654bac")||
  !main_match(r,0x80041b50,2220,"f6419f1b0a58a0e14add0def5f1a70e23cf3091ee652922f77fdbdc359b0b437"))return false;
 const auto bounds=pal_gfx_bounds(r);if(!bounds||bounds.end-bounds.cursor<0x3000)return false;
 auto cursor=bounds.cursor;auto emit=[&](uint32_t a,uint32_t b){main_put(r,cursor,a);main_put(r,cursor+4,b);cursor+=8;};
 // LEFT origins anchor original coordinates to the physical left edge. The
 // full-width scoped scissor admits that edge; size, UV and animation stay real.
 emit(0xe0525464,0x10000064);emit(0x64000017,0);
 emit(0x64000005,0x01000000);emit(0,960);
 emit(0x64000006,0);emit(0,0);main_put(r,0x8009e0c8,cursor);
 draw(r.data(),&c);cursor=main_word(r,0x8009e0c8);
 if(cursor<bounds.cursor+48||cursor>bounds.end-24)std::abort();
 emit(0x64000006,0x00800800);emit(0,0);emit(0x64000018,0);
 main_put(r,0x8009e0c8,cursor);return true;
}

bool draw_pal_main_exit(std::span<uint8_t>r,const recomp_context&c,const MainExitView&view,
 const std::array<PromptGlyphRequest,3>&prompts,const PalPromptSpriteFunctions&fn){
 if(!view.available||!pal_main_select_active(r))return false;
 auto bounds=pal_gfx_bounds(r);if(!bounds||bounds.end-bounds.cursor<14000)return false;
 if(!fn.initialize_sprite||!fn.construct_resource||!fn.draw_sprite||!fn.draw_text)return false;
 const auto sp=uint32_t(c.r29);if(sp<0x800a08d8||sp>0x800a42d8||(sp&7))return false;
 const auto fp=reinterpret_cast<uintptr_t>(c.f_odd),lo=reinterpret_cast<uintptr_t>(&c.f0),hi=reinterpret_cast<uintptr_t>(&c.f31)+sizeof(fpr);
 if(fp&&(fp<lo||fp>hi-4||(fp-lo)%4))return false;
 if(!main_match(r,0x80352800,0x3000,"237c7f53ac8b11353467cb957868f794507ca2688c93581d977dac03a4e8b765")||
    !main_match(r,0x80048660,764,"2e1211ac1d08b931b3825a1c11175dcffbfa09a9108d5d703dacde3387262b31"))return false;
 for(const auto& request:prompts)if(request.port>=4||!pal_prompt_icon_available({0,0,request.family,std::string(request.label),request.port,12,12}))return false;

 PromptSpriteResult proposal;proposal.status=PromptSpriteStatus::TextFallback;
 if(!view.open){proposal.icons[0]={228,213,prompts[0].family,std::string(prompts[0].label),prompts[0].port,14,14};proposal.icon_count=1;
  // Two opaque passes one native pixel apart embolden the genuine font's
  // strokes. No substitute typeface or modified font atlas is introduced.
  proposal.lines[0]={246,213,"Exit Game",12};proposal.lines[1]={247,213,"Exit Game",12};proposal.line_count=2;return draw_pal_prompt_sprite(r,c,proposal,fn);}
 // A bounded original RDP fill panel, using the same fill-cycle sequence as
 // original019FC. No framebuffer binding, viewport, scissor or guest object changes.
 uint32_t cursor=bounds.cursor;auto emit=[&](uint32_t a,uint32_t b){main_put(r,cursor,a);main_put(r,cursor+4,b);cursor+=8;};
 emit(0xe7000000,0);emit(0xe3000a01,0x00300000);
 auto box=[&](unsigned x,unsigned y,unsigned right,unsigned bottom,uint16_t color){emit(0xf7000000,uint32_t(color)<<16|color);emit(0xf6000000|right<<14|bottom<<2,x<<14|y<<2);};
 box(38,84,282,168,0x1b9f);box(40,86,280,166,0x0843);
 if(view.yes)box(174,121,220,138,0x1b9f);else box(94,121,140,138,0x1b9f);
 emit(0xe7000000,0);emit(0xe3000a01,0);main_put(r,0x8009e0c8,cursor);
 const std::array<EngineTextLine,3>lines{{{70,96,"Are you sure you want to exit?",8},{108,123,"No"},{188,123,"Yes"}}};
 // Fill-cycle writes bypassed the original material cache; make the original
 // font emit its full material before the first text rectangle.
 const uint16_t invalid=0xffff;std::memcpy(r.data()+(0xbdb26^2),&invalid,2);
 if(!draw_pal_engine_text(r,c,lines,fn.draw_text))std::abort();
 proposal.icon_count=2;proposal.icons[0]={82,146,prompts[1].family,std::string(prompts[1].label),prompts[1].port,12,12};
 proposal.icons[1]={178,146,prompts[2].family,std::string(prompts[2].label),prompts[2].port,12,12};
 proposal.line_count=2;proposal.lines[0]={100,149,"Confirm",8};proposal.lines[1]={196,149,"Back",8};
 if(!draw_pal_prompt_sprite(r,c,proposal,fn))std::abort();return true;
}
}
