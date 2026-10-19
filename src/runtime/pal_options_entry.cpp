// Original project work: djultra64.
#include "pal_options_entry.hpp"
#include "rom_image.hpp"
#include <array>
#include <cstring>
#include <string_view>
namespace iss2000 {namespace {
uint32_t word(std::span<const uint8_t>r,uint32_t a){uint32_t v;std::memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
uint8_t byte(std::span<const uint8_t>r,uint32_t a){return r[(a&0x7fffff)^3];}
uint16_t half(std::span<const uint8_t>r,uint32_t a){uint16_t v;std::memcpy(&v,r.data()+((a&0x7fffff)^2),2);return v;}
bool canonical(uint64_t a){auto lo=uint32_t(a),hi=uint32_t(a>>32);return(hi==0||(hi==0xffffffffu&&(lo&0x80000000u)))&&(lo&0xff800003u)==0x80000000u;}
bool matches(std::span<const uint8_t>r,uint32_t a,unsigned n,std::string_view pin){std::array<uint8_t,2048>data{};if(!n||n>data.size())return false;for(unsigned i=0;i<n;++i)data[i]=byte(r,a+i);return rom_detail::sha256_hex({data.data(),n})==pin;}
bool profile(std::span<const uint8_t>r){
 if(!matches(r,0x8029F274,100,"2268b91b3288c15e3b5f126f86b53f86448fc375fba5a86f8c4330aa8ee51e17"))return false;
 if(!matches(r,0x8029F2D8,60,"6e63bea4faa4c30eb5195f1eb9238dbbff8f990af4c6037929ab33ce9d8908a8"))return false;
 if(!matches(r,0x8029F004,108,"d4c11a9236158e27e49cdf4176c05fb381ebfe4f20b347bf162dcebee3d1a25a"))return false;
 if(!matches(r,0x8029F33C,84,"75d5b90b43080c5716a5929f10f79953218747569c9cb7467422c0dee3d2d643"))return false;
 if(!matches(r,0x8029F390,84,"f5ab3aaecfbb21a941ee7fc1e17261431f3efde9798884c4ea965e78c3463191"))return false;
 return matches(r,0x802A6CC8,56,"7e4836b0818698942cb7554bb12c3f3debb9fca7eb24db38363c42b08a02f846")&&
 matches(r,0x802B08C0,20,"16a638446828a7a2cbaa64a5c7d08659116f50f8e94c72e18b07358351f0f8da")&&
 matches(r,0x802B08D4,60,"3b06d360a47f5b1261c142c2361a5b6af1d5c8ed689319a8133ec60a220a4f8d");
}
}}
namespace iss2000 {
std::optional<PalOptionsEntry>pal_options_entry(std::span<const uint8_t>r)noexcept{
 if(r.size()!=0x800000||word(r,0x8009E02C)!=0x8013B418||byte(r,0x8012DE74)!=1)return{};
 auto row=byte(r,0x802B1090);if(row>=8)return{};
 uint32_t node=word(r,0x80077390);std::array<bool,220>seen{};bool owner=false;
 while(node){if(node<0x801E7070||node>=0x801ED420||(node-0x801E7070)%0x74)return{};auto i=(node-0x801E7070)/0x74;if(i>=seen.size()||seen[i])return{};seen[i]=true;if(word(r,node+12)==0x8029F274)owner=true;node=word(r,node);}
 if(!owner)return{};
 try{if(!profile(r))return{};}catch(...){return{};}
 return PalOptionsEntry{row,row==6};
}
std::optional<PalOptionsLabel>pal_options_pc_label(std::span<const uint8_t>r,uint64_t object)noexcept{
 auto state=pal_options_entry(r);if(!state||!canonical(object))return{};auto a=uint32_t(object);
 if(a<0x8013C47C||(a-0x8013C47C)%0x3c||(a-0x8013C47C)/0x3c>=273||byte(r,a+4)!=1||byte(r,a+5)!=8||
    word(r,a+0x14)!=0x802D1C3C||word(r,a+0x30)!=0x802A6B6C||word(r,0x80076CA4)!=0x802D1C24||
    half(r,a+0x20)!=54||half(r,a+0x24)!=166||word(r,a+0x28)!=0x3F800000||word(r,a+0x2c)!=0x3F800000)return{};
 auto c=word(r,a+0x38);if(!canonical(c)||c>0x807FFFBC||half(r,c+0x20)!=6)return{};
 try{if(!matches(r,0x802A6C20,12,"6fd33899ea2034309bffe45a16630509688fc639bd086016252dea7cc116b086")||
 !matches(r,0x802D1C3C,12,"b6b260e478d097fdc6e71f3d9a354e9a75a4f08d62a46886491d8aa64c00337a")||
 !matches(r,0x802A6B6C,24,"b7d7ba0c35d3beed8d4d8ffe0578f6c2b59562c7102a01ea9be31537a6310801")||
 !matches(r,0x80277640,2048,"90b3f9638316cfb8af17d3035abea7cd746537f2c42c8991b22e3d52aa9e037e"))return{};
 }catch(...){return{};}
 return PalOptionsLabel{int(half(r,a+0x20))+int16_t(half(r,0x802A6B70)),int(half(r,a+0x24))+int16_t(half(r,0x802A6B72)),128,16,state->pc_settings};
}
}
