// Original project work: djultra64.
#include "pal_projected_shadow.hpp"
#include "pal_shadow_vertices.hpp"
#include <algorithm>
#include <cmath>
#include <limits>
namespace iss2000 {namespace {
using projected_shadow_detail::word;
uint8_t byte(std::span<const uint8_t>r,uint32_t a){return r[(a&0x7fffff)^3];}
void put(std::span<uint8_t>r,uint32_t a,uint32_t v){std::memcpy(r.data()+(a&0x7fffff),&v,4);}
void half(std::span<uint8_t>r,uint32_t a,int16_t v){std::memcpy(r.data()+((a&0x7fffff)^2),&v,2);}
int16_t coordinate(std::span<const uint8_t>r,uint32_t a){int16_t v;std::memcpy(&v,r.data()+((a&0x7fffff)^2),2);return v;}
float value(std::span<const uint8_t>r,uint32_t a){float v;std::memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
struct Point {float x,y,z;};
bool node(uint32_t p){return p>=0x80145624&&p<0x8014ff5c&&(p-0x80145624)%0x98==0;}
}
namespace {
bool project_ball(std::span<uint8_t>r,uint32_t root){
 const auto child=projected_shadow_detail::ball_owner(r,root);if(!child)return false;
 const auto bank=word(r,0x8009ded0),lighting=word(r,0x800839e0);if(bank>1||lighting>2||word(r,*child+0x24)!=0x802b2780)return false;
 const Point center{value(r,root),value(r,root+4),value(r,root+8)};
 if(!std::isfinite(center.x)||!std::isfinite(center.y)||!std::isfinite(center.z)||std::abs(center.x)>2500||std::abs(center.z)>2500||center.y<0||center.y>300)return false;
 // Sphere radius is the original grounded ball height (1.4 world units).
 // The floodlight generator's stronger quad is (+2,-2) at positive Z,
 // and (+2,+2) at non-positive Z. Day/weather use the players' (-.5,+.5).
 const float lx=lighting==2?2.f:-.5f,lz=lighting==2?(center.z>0?-2.f:2.f):.5f;
 const float norm=std::hypot(lx,lz),ux=lx/norm,uz=lz/norm,stretch=std::sqrt(1+norm*norm);
 std::array<std::array<int16_t,2>,16> vertices{};
 for(unsigned n=0;n<16;++n){const float angle=float(n)*0.392699081698724f;
  const float along=14*stretch*std::cos(angle),across=14*std::sin(angle);
  const float x=(center.x+center.y*lx)*10+ux*along-uz*across,z=(center.z+center.y*lz)*10+uz*along+ux*across;
  if(x<-32760||x>32760||z<-32760||z>32760)return false;
  vertices[n]={int16_t(std::lround(x)),int16_t(std::lround(z))};
 }
 const auto slot=PalProjectedShadowBase+bank*PalProjectedShadowBank+25*PalProjectedShadowSlot,dl=slot+0x580,alpha=lighting?64u:96u;
 const std::array<uint32_t,8>header{0x50534844,root,root,bank,16,dl,144,alpha};
 for(unsigned n=0;n<header.size();++n)put(r,slot+n*4,header[n]);
 for(unsigned n=0;n<16;++n){const auto p=slot+0x40+n*16;for(unsigned j=0;j<16;++j)r[((p+j)&0x7fffff)^3]=0;
  half(r,p,vertices[n][0]);half(r,p+2,1);half(r,p+4,vertices[n][1]);put(r,p+12,0xffffffff);
 }
 const auto commands=projected_shadow_detail::commands(slot,alpha,true);for(unsigned n=0;n<commands.size();++n)put(r,dl+n*4,commands[n]);
 put(r,*child+0x24,dl);return true;
}
}
void restore_pal_ball_shadow(std::span<uint8_t>r,uint64_t address){
 const auto root=uint32_t(address);if((address!=root&&address!=uint64_t(int64_t(int32_t(root))))||r.size()!=0x800000)return;
 // Restore only an authenticated projected child before running the genuine
 // callback again. Suppressed/cut scenes then retain original behavior.
 for(unsigned bank=0;bank<2;++bank)if(const auto mesh=pal_projected_shadow(r,root,bank);mesh&&mesh->ball){
  put(r,*projected_shadow_detail::ball_owner(r,root)+0x24,0x802b2780);return;
 }
}
bool project_pal_shadow(std::span<uint8_t>r,uint64_t address){
 const auto object=uint32_t(address);
 if((address!=object&&address!=uint64_t(int64_t(int32_t(object))))||!node(object)||r.size()!=0x800000||
    word(r,0x8009e02c)!=0x8013b418||byte(r,0x8013b446)!=6||(byte(r,0x8013b44c)!=4&&byte(r,0x8013b44c)!=16)||byte(r,0x8013b452)!=0||
    (word(r,object+0x28)&0x80004000)!=0x80004000)return false;
 if(word(r,object+0x7c)==0x802a472c)return project_ball(r,object);
 if(word(r,object+0x7c)!=0x80037498)return false;
 const auto root=word(r,object+0x50),bank=word(r,0x8009ded0),old_dl=word(r,object+0x24);
 if(!node(root)||bank>1||word(r,root+0x4c)!=object||(old_dl!=0x80083b90&&old_dl!=0x80083bc8&&old_dl!=0x80083d60&&old_dl!=0x80083ce0)||!verified_pal_near_shadow_list(r))return false;
 unsigned player=PalProjectedHumanCount;for(unsigned n=0;n<PalProjectedHumanCount;++n)if(word(r,0x801a07cc+n*256)==root&&word(r,root+0x84)==0x801a07cc+n*256){player=n;break;}if(player==PalProjectedHumanCount)return false;
 const auto metadata=word(r,object+0x80);
 if(metadata<0x800a5250||metadata>=0x800a5250+140*0x40||(metadata-0x800a5250)%0x40)return false;
 const auto original=word(r,metadata);if(original<0x801b0000||original>0x80700000-1280||(original&7)||word(r,object+0x5c)!=original+bank*640)return false;
 std::array<Point,11>pose;
 for(unsigned n=0;n<pose.size();++n){const auto p=0x8012aaf0+n*12;pose[n]={value(r,p),value(r,p+4),value(r,p+8)};
  if(!std::isfinite(pose[n].x)||!std::isfinite(pose[n].y)||!std::isfinite(pose[n].z)||std::abs(pose[n].x)>2500||std::abs(pose[n].z)>2500||std::abs(pose[n].y)>300)return false;
 }
 if(std::abs(pose[4].x-value(r,root))>32||std::abs(pose[4].z-value(r,root+8))>32)return false;
 float light_x=-.5f,light_z=.5f;
 if(old_dl==0x80083d60||old_dl==0x80083ce0){
  // The two/four original floodlight quads have a fixed, independently pinned
  // material/topology. Use the stronger quad's far-edge midpoint to recover
  // its actual light direction; replace the cone with the articulated pose.
  constexpr uint32_t material[]={0xe200001c,0x00504a50,0xd9ffffff,0x00200005,0xd9fefbff,0,0xe3001a01,0x20,0xfcffffff,0xfffdf8fc,0xfa000000,0xff,0xd7000000,0xffffffff,0xda380003,0x801a3f00,0xd9fffbff,0,0x01008010,0x05000000,0x06000204,0x00060204,0x06080a0c,0x000e0a0c,0xe3001a01,0x30,0xdf000000,0};
  constexpr uint32_t central[]={0xe200001c,0x00504a50,0xd9ffffff,0x00200005,0xd9fefbff,0,0xe3001a01,0x20,0xfcffffff,0xfffdf8fc,0xfa000000,0xff,0xd7000000,0xffffffff,0xda380003,0x801a3f00,0xd9fffbff,0,0x01010020,0x05000000,0x06000204,0x00060204,0x06080a0c,0x000e0a0c,0x06101214,0x00161214,0x06181a1c,0x001e1a1c,0xe3001a01,0x30,0xdf000000,0};
  if(word(r,0x800839e0)!=2||pose[5].y<.1f)return false;
  const std::span<const uint32_t> expected=old_dl==0x80083ce0?std::span<const uint32_t>(central):std::span<const uint32_t>(material);
  for(unsigned n=0;n<expected.size();++n)if(word(r,old_dl+n*4)!=expected[n])return false;
  const auto source=word(r,object+0x5c);
  unsigned strongest=0,selected=0;
  for(unsigned n=0;n<(old_dl==0x80083ce0?4u:2u);++n){const unsigned alpha=byte(r,source+n*64+15)+byte(r,source+n*64+63);if(alpha>strongest){strongest=alpha;selected=n;}}
  if(!strongest)return false;
  const auto quad=source+selected*64;
  light_x=((coordinate(r,quad+16)+coordinate(r,quad+32))*.5f-pose[5].x*10)/(pose[5].y*10);
  light_z=((coordinate(r,quad+20)+coordinate(r,quad+36))*.5f-pose[5].z*10)/(pose[5].y*10);
  if(!std::isfinite(light_x)||!std::isfinite(light_z)||std::abs(light_x)<1.5f||std::abs(light_x)>2.5f||std::abs(light_z)<1.5f||std::abs(light_z)>2.5f)return false;
 }
 // The same world-space light direction as the original: X -= Y/2,
 // Z += Y/2. Eight points per tapered capsule round each articulated segment.
 // The mesh uses its own pixel depth, one tenth of a world unit above the
 // pitch. It must not inherit the old renderer's constant far-plane depth.
 constexpr unsigned starts[]{1,0,3,2,4,5,6,5,8,5},ends[]{0,4,2,4,5,6,7,8,9,10};
 constexpr float radii[]{7,9,7,9,15,7,6,7,6,10};
 std::array<std::array<int16_t,2>,80>vertices{};
 for(unsigned part=0;part<10;++part){auto a=pose[starts[part]],b=pose[ends[part]];
  if(part==4){const float dy=b.y-a.y;b.y+=dy*.8f;} // Torso volume above the chest joint.
  const float ax=a.x*10+a.y*10*light_x,az=a.z*10+a.y*10*light_z,bx=b.x*10+b.y*10*light_x,bz=b.z*10+b.y*10*light_z;
  const float dx=bx-ax,dz=bz-az,length=std::hypot(dx,dz);const float ux=length>0.01f?dx/length:1.f,uz=length>0.01f?dz/length:0.f;
  for(unsigned n=0;n<8;++n){const bool tip=n<4;const float angle=(tip?(-90.f+60.f*float(n)):(90.f+60.f*float(n-4)))*0.017453292519943295f;
   const float along=std::cos(angle)*radii[part],across=std::sin(angle)*radii[part];
   const float x=(tip?bx:ax)+ux*along-uz*across,z=(tip?bz:az)+uz*along+ux*across;
   if(x<-32760||x>32760||z<-32760||z>32760)return false;
   vertices[part*8+n]={int16_t(std::lround(x)),int16_t(std::lround(z))};
  }
 }
 const auto slot=PalProjectedShadowBase+bank*PalProjectedShadowBank+player*PalProjectedShadowSlot,dl=slot+0x580,alpha=old_dl==0x80083b90?96u:64u;
 const std::array<uint32_t,8>header{0x50534844,object,root,bank,80,dl,352,alpha};
 for(unsigned n=0;n<header.size();++n)put(r,slot+n*4,header[n]);
 for(unsigned n=0;n<80;++n){const auto p=slot+0x40+n*16;for(unsigned j=0;j<16;++j)r[((p+j)&0x7fffff)^3]=0;
  half(r,p,vertices[n][0]);half(r,p+2,1);half(r,p+4,vertices[n][1]);put(r,p+12,0xffffffff);
 }
 const auto commands=projected_shadow_detail::commands(slot,alpha);for(unsigned n=0;n<commands.size();++n)put(r,dl+n*4,commands[n]);
 put(r,object+0x24,dl);put(r,object+0x5c,slot+0x40);return true;
}
}
