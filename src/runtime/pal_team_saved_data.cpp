// Original project work: djultra64.
#include "pal_team_saved_data.hpp"
#include "pal_sky_widescreen.hpp"
#include "rom_image.hpp"
#include <array>
#include <bit>
#include <cstring>
#include <cstdlib>
#include <vector>
namespace iss2000 {namespace {
uint32_t word(std::span<const uint8_t>r,uint32_t a){uint32_t v;std::memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
uint8_t byte(std::span<const uint8_t>r,uint32_t a){return r[(a&0x7fffff)^3];}
int16_t half(std::span<const uint8_t>r,uint32_t a){return int16_t(uint16_t(byte(r,a))<<8|byte(r,a+1));}
void put(std::span<uint8_t>r,uint32_t a,uint32_t v){std::memcpy(r.data()+(a&0x7fffff),&v,4);}
void sb(std::span<uint8_t>r,uint32_t a,uint8_t v){r[(a&0x7fffff)^3]=v;}
void sh(std::span<uint8_t>r,uint32_t a,uint16_t v){std::memcpy(r.data()+((a&0x7fffff)^2),&v,2);}
bool match(std::span<const uint8_t>r,uint32_t a,unsigned size,std::string_view pin){std::vector<uint8_t>b(size);for(unsigned i=0;i<size;++i)b[i]=byte(r,a+i);return rom_detail::sha256_hex(b)==pin;}
bool owner(std::span<const uint8_t>r,bool training){
 const uint32_t callback=training?0x802a8434u:0x802a0c48u;
 if(!match(r,callback,64,training?"3f0bfa2f9c094599200636a6588037d0062b2dd69110bb33ae9220a6e3725c28":"1cb1769e3ad816e07fd9fb81daa98804ad0848dcfc7d4b00be8a72e6f984bb3e"))return false;
 std::array<bool,220>seen{};uint32_t p=word(r,0x80077390);bool found=false;
 while(p){if(p<0x801e7070||p>=0x801ed420||(p-0x801e7070)%0x74)return false;auto i=(p-0x801e7070)/0x74;if(i>=seen.size()||seen[i])return false;seen[i]=true;found|=word(r,p+12)==callback;p=word(r,p);}return found;
}
bool pool(uint32_t p){return p>=0x8013c9e0&&p<=0x8013d9d0&&(p-0x8013c9e0)%60==0;}
unsigned code(char c){return c==' '?0:c>='A'&&c<='Z'?unsigned(c-'A'+11):unsigned(c-'a'+37);}
std::array<uint8_t,1024> bitmap(std::span<const uint8_t>r,std::string_view text){
 std::array<uint8_t,1024> out{};unsigned at=0;
 for(char c:text){const unsigned g=code(c);for(unsigned y=0;y<12;++y)for(unsigned x=0;x<6;++x){
  const unsigned source=y*16+(g&1)*8+x;const auto packed=byte(r,0x80352800+(g/2)*96+source/2);
  const auto v=source&1?packed&15:packed>>4;unsigned dest=y*128+at+x;out[dest/2]|=uint8_t(v<<(dest&1?0:4));
 }at+=6;}return out;
}
std::array<uint8_t,3> color(std::span<const uint8_t>r,unsigned index){
 const auto v=uint16_t(half(r,0x803dc4e0+index*2));const auto expand=[](unsigned x){return uint8_t(x<<3|x>>2);};return {expand(v>>11),expand(v>>6&31),expand(v>>1&31)};
}
}
std::optional<PalTeamSavedDataLabel> pal_team_saved_data_label(std::span<const uint8_t>r,uint64_t sprite){
 if(r.size()!=0x800000)return {};
 const auto p=uint32_t(sprite),hi=uint32_t(sprite>>32);if((hi!=0&&hi!=0xffffffffu)||!pool(p))return {};
 const auto script=word(r,p+48);const bool training=script==0x802aea74;const bool lower=script==0x801be0f4||training;
 const bool upper=script==0x801bf0d8||script==0x801bf0e4;
 if(!lower&&!upper)return {};
 if(byte(r,p+4)!=1||(word(r,p+8)&0x40000000)||half(r,p+0x1c)!=0||
    word(r,p+0x28)!=0x3f800000||word(r,p+0x2c)!=0x3f800000||!owner(r,training))return {};
 if(word(r,0x8009e02c)!=0x8013b418||byte(r,0x8013b42a)!=0||word(r,0x8013b42c)!=0x014000f0)return {};
 if(!match(r,0x80352800,0x3000,"237c7f53ac8b11353467cb957868f794507ca2688c93581d977dac03a4e8b765"))return {};
 int x=half(r,p+32),y=half(r,p+36);PalTeamSavedDataLabel out;
 if(lower){
  if(training?(word(r,p+20)!=0x803db42c||!match(r,script,12,"aba889a5c545459263b6e7a579d7b1202777ef2b104cc550d346c8bfeea3f2a4")||!match(r,0x803db42c,12,"e449be061279512cbba068d7902dc153f9c5916d03c1d5f5d8e8e9b057c71a58")):(word(r,p+20)!=0x803db408||!match(r,script,48,"c0aa41264ceef721adcc9a1168042830fb948ef063bc2dbcc637c4575aed23bb")||!match(r,0x803db408,48,"6095caf47b12fb402421b24ec4dd33930614c63fd06f2f2ae7034b7590f30356")))return {};
  if(
     !match(r,0x80271140,4096,"7b2044cb2c31579ba6ca5e7a3d8130a2e16496c698fbaec6644699b9aa888075")||
     !match(r,0x80272140,4096,"7b2044cb2c31579ba6ca5e7a3d8130a2e16496c698fbaec6644699b9aa888075")||
     !match(r,0x803dc4e0,32,"2794e70b9cd0d469942c5c75107ffd718904f228434eee0fd9a94dcd491d5e7f"))return {};
  out={"Saved Data",int16_t(training?x+half(r,script+4)+4:x-7),int16_t(training?y+half(r,script+6)+2:y+6),40,12};
 }else{
  if(word(r,p+20)!=0x803db510||!match(r,0x803db510,12,"84b229ecadb5fa0ae885d21c09bab5facfc612bf70c1ffe013c50c4101b88173")||
     !match(r,0x802768c0,384,"ea428124fa2b1ecab80bf796ef31c71572da2a5446c38d37d3ddd0ad2e8110e0")||
     !match(r,script,12,script==0x801bf0d8?"84677d5cf69da9efa01d4ffca5059d98e49dba1baaa632ac18672a0196e9d680":"4004e499f661a2cd31aea2df1b8e4e473f5710eb81aa0c5874cdea7c177bf660"))return {};
  out={"Load Saved Data",int16_t(x+half(r,script+4)+4),int16_t(y+half(r,script+6)),80,8};
 }
 if(out.x<1||out.y<1||out.x+out.width+1>320||out.y+out.height+1>240)return {};return out;
}
bool draw_pal_team_saved_data(std::span<uint8_t>r,const recomp_context&caller,recomp_func_t*draw){
 const auto label=pal_team_saved_data_label(r,caller.r4);if(!label||!draw)return false;
 if(!match(r,0x80041b50,2220,"f6419f1b0a58a0e14add0def5f1a70e23cf3091ee652922f77fdbdc359b0b437"))return false;
 const uint32_t sp=uint32_t(caller.r29);if(sp<0x800a08d8||sp>0x800a42d8||(sp&7))return false;
 const auto fp=reinterpret_cast<uintptr_t>(caller.f_odd),lo=reinterpret_cast<uintptr_t>(&caller.f0),hi=reinterpret_cast<uintptr_t>(&caller.f31)+sizeof(fpr);
 if(fp&&(fp<lo||fp>hi-4||(fp-lo)%4))return false;
 const bool lower=label->text=="Saved Data";auto bounds=pal_gfx_bounds(r);
 // A 1KiB task-owned image, the real G_DL skip, and a conservative complete
 // material/rectangle budget for all five original outline/fill sprite passes.
 if(!bounds||bounds.end-bounds.cursor<(lower?4096u:2048u))return false;
 const auto pixels=bitmap(r,label->text);const uint32_t head=bounds.cursor,image=head+8,first=image+pixels.size();
 const uint32_t local=sp-0x300,object=local+0x20,desc=local+0x60,segments=local+0x80;
 std::array<uint8_t,0x600>saved{};std::memcpy(saved.data(),r.data()+((sp-0x600)&0x7fffff),saved.size());
 for(unsigned i=0;i<pixels.size();++i)sb(r,image+i,pixels[i]);put(r,head,0xde010000);put(r,head+4,first);put(r,0x8009e0c8,first);
 // Copy the complete original object, including its current parent/fade alpha.
 for(unsigned i=0;i<60;++i)sb(r,object+i,byte(r,uint32_t(caller.r4)+i));
 put(r,desc,0x00800010);put(r,desc+4,0x03000000);put(r,desc+8,image);
 put(r,segments,0x90000000|uint32_t(label->text.size()*6)<<16|12u<<8);put(r,segments+4,0);put(r,segments+8,0);
 put(r,object+20,desc);put(r,object+48,segments);put(r,object+8,word(r,object+8)|0x04400000u);
 put(r,object+0x28,std::bit_cast<uint32_t>(float(label->width)/float(label->text.size()*6)));put(r,object+0x2c,lower?0x3f800000:0x3f2aaaab);
 auto call=[&](int dx,int dy,std::array<uint8_t,3>rgb){
  sh(r,object+32,uint16_t(label->x+dx));sh(r,object+36,uint16_t(label->y+dy));for(unsigned i=0;i<3;++i)sb(r,object+14+i,lower?uint8_t(unsigned(rgb[i])*byte(r,uint32_t(caller.r4)+14+i)/255):rgb[i]);
  auto context=caller;if(fp)context.f_odd=reinterpret_cast<uint32_t*>(reinterpret_cast<uint8_t*>(&context.f0)+(fp-lo));context.r29=S32(local);context.r4=S32(object);draw(r.data(),&context);
 };
 if(lower){const auto blue=color(r,15);call(-1,0,blue);call(1,0,blue);call(0,-1,blue);call(0,1,blue);call(0,0,color(r,1));}
 else call(0,0,{byte(r,object+14),byte(r,object+15),byte(r,object+16)});
 if(word(r,0x8009e0c8)>bounds.end)std::abort();
 std::memcpy(r.data()+((sp-0x600)&0x7fffff),saved.data(),saved.size());return true;
}
}
