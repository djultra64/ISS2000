// Original project work: djultra64.
#pragma once
#include <array>
#include <cstdint>
#include <cstring>
#include <optional>
#include <span>
namespace iss2000 {
inline constexpr uint32_t PalProjectedShadowBase=0x807e0000,PalProjectedShadowBank=0x10000,PalProjectedShadowSlot=0x800;
inline constexpr unsigned PalProjectedHumanCount=25,PalProjectedShadowCount=26;
static_assert(PalProjectedShadowCount*PalProjectedShadowSlot<=PalProjectedShadowBank);
struct PalProjectedShadow {uint32_t vertices{},display_list{};bool ball=false;};
namespace projected_shadow_detail {
inline uint32_t word(std::span<const uint8_t>r,uint32_t a){uint32_t v;std::memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
inline std::array<uint32_t,88> commands(uint32_t slot,uint32_t alpha,bool ball=false){
 std::array<uint32_t,88> out{};unsigned at=0;auto emit=[&](uint32_t a,uint32_t b){out[at++]=a;out[at++]=b;};
 emit(0xe200001c,0x005049f8);emit(0xd7000000,0xffffffff);
 emit(0xe2001d00,0);emit(0xe7000000,0);emit(0xfcffffff,0xfffdf6fb);emit(0xfa000000,alpha);emit(0xda380003,0x801a3f00);emit(0xd9fffbff,0);
 if(ball){
  emit(0x01010020,slot+0x40); // One convex sixteen-vertex projected sphere.
  for(unsigned n=1;n<14;n+=2){auto tri=[](unsigned k){return (k*2<<8)|(k+1)*2;};emit(0x06000000|tri(n),tri(n+1));}
 }else for(unsigned chunk=0;chunk<4;++chunk){const unsigned count=chunk<3?24:8;emit(0x01000000|(count<<12)|(count<<1),slot+0x40+chunk*24*16);
  for(unsigned part=0;part<count/8;++part){const unsigned first=part*8;
   for(unsigned n=1;n<=5;n+=2){auto tri=[&](unsigned k){return (first*2<<16)|((first+k)*2<<8)|(first+k+1)*2;};emit(0x06000000|tri(n),tri(n+1));}
  }
 }
 emit(0xe2001d00,0);emit(0xdf000000,0);return out;
}
inline bool model_node(uint32_t p){return p>=0x80145624&&p<0x8014ff5c&&(p-0x80145624)%0x98==0;}
inline bool part_node(uint32_t p){return p>=0x8014ff5c&&p<0x8014ff5c+900*0x60&&(p-0x8014ff5c)%0x60==0;}
inline std::optional<uint32_t> ball_owner(std::span<const uint8_t>r,uint32_t root){
 if(r.size()!=0x800000||!model_node(root)||word(r,0x802b57d0)!=root||word(r,root+0x7c)!=0x802a472c||
    (word(r,root+0x24)!=0x802b2538&&word(r,root+0x24)!=0x802b25b8)||(word(r,root+0x28)&0x80004000)!=0x80004000)return {};
 // The actual original ball callback and complete shadow material, never an
 // address alone, identify the dynamically loaded ball overlay.
 constexpr uint32_t code[]{0x27bdffd0,0xafb40020,0x0080a02d,0xafb3001c,0x3c13802b,0x267324f8,0x3c048013,0x2484de74,0xafbf0024,0xafb20018,0xafb10014,0xafb00010};
 constexpr uint32_t material[]{0xde000000,0x80086448,0xe3001201,0x2000,0xfcffffff,0xfffdf2f9,0xfa000000,0,0xe3001001,0,0xd7000002,0x80008000,0xfd900000,0x8021af80,0xf5900000,0x07094250,0xe6000000,0,0xf3000000,0x070ff400,0xe7000000,0,0xf5800400,0x00094250,0xf2000000,0x007c07c,0x01004008,0x802b2478,0x06000204,0x00000406,0xdf000000,0};
 for(unsigned n=0;n<std::size(code);++n)if(word(r,0x802a472c+n*4)!=code[n])return {};
 for(unsigned n=0;n<std::size(material);++n)if(word(r,0x802b2780+n*4)!=material[n])return {};
 const auto child=word(r,0x802b43f4),body=word(r,root+0x48);
 if(!part_node(child)||!part_node(body)||child==body||word(r,body+0x44)!=root||word(r,body+0x4c)!=child||
    word(r,child+0x44)!=root||word(r,child+0x50)!=body||word(r,child+0x4c)||word(r,child+0x48)||
    (word(r,child+0x28)&0x80004000)!=0x80004000)return {};
 return child;
}
}
inline std::optional<PalProjectedShadow> pal_projected_shadow(std::span<const uint8_t>r,uint32_t object,unsigned bank){
 if(r.size()!=0x800000||bank>1||!projected_shadow_detail::model_node(object))return {};
 using projected_shadow_detail::word;
 const auto child=projected_shadow_detail::ball_owner(r,object);const bool ball=bool(child);
 const auto dl=word(r,(ball?*child:object)+0x24),begin=PalProjectedShadowBase+bank*PalProjectedShadowBank;
 if(dl<begin+0x580||dl>=begin+PalProjectedShadowCount*PalProjectedShadowSlot||(dl-begin-0x580)%PalProjectedShadowSlot)return {};
 const auto slot=dl-0x580,alpha=word(r,slot+28),index=(slot-begin)/PalProjectedShadowSlot;
 const auto root=ball?object:word(r,object+0x50),vertices=ball?slot+0x40:word(r,object+0x5c);
 if(ball){if(index!=25)return {};}
 else if(index>=PalProjectedHumanCount||!projected_shadow_detail::model_node(root)||
    word(r,0x801a07cc+index*256)!=root||word(r,root+0x84)!=0x801a07cc+index*256)return {};
 if(word(r,slot)!=0x50534844||word(r,slot+4)!=object||word(r,slot+8)!=root||word(r,slot+12)!=bank||
    word(r,slot+16)!=(ball?16u:80u)||word(r,slot+20)!=dl||word(r,slot+24)!=(ball?144u:352u)||vertices!=slot+0x40||(alpha!=96&&alpha!=64))return {};
 const auto expected=projected_shadow_detail::commands(slot,alpha,ball);
 for(unsigned n=0;n<expected.size();++n)if(word(r,dl+n*4)!=expected[n])return {};
 return PalProjectedShadow{vertices,dl,ball};
}
// Called after the genuine original shadow callback has prepared its pose.
// Ball uses its genuine callback and attached child; originals remain available.
bool project_pal_shadow(std::span<uint8_t>,uint64_t object);
void restore_pal_ball_shadow(std::span<uint8_t>,uint64_t root);
}
