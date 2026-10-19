// Original project work: djultra64.
#include "pal_menu_avatar.hpp"
#include <array>
#include <cstring>
namespace iss2000 {namespace {
uint32_t word(std::span<const uint8_t>r,uint32_t a){uint32_t v;std::memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
uint8_t byte(std::span<const uint8_t>r,uint32_t a){return r[(a&0x7fffff)^3];}
int16_t half(std::span<const uint8_t>r,uint32_t a){int16_t v;std::memcpy(&v,r.data()+((a&0x7fffff)^2),2);return v;}
bool record(uint32_t p,unsigned index){const auto base=index?0x8014FF5Cu:0x80145624u,stride=index?0x60u:0x98u,count=index?900u:285u;
 return p>=base&&p<base+stride*count&&(p-base)%stride==0;}
std::optional<uint32_t> physical(uint64_t a){auto low=uint32_t(a);if(a!=low&&a!=uint64_t(int64_t(int32_t(low))))return {};
 if(low<0x800000)return low;
 if((low>=0x80000000&&low<0x80800000)||(low>=0xA0000000&&low<0xA0800000))return low&0x7fffff;
 return {};}
}
std::optional<PalMenuAvatarProof> verified_pal_menu_avatar(std::span<const uint8_t>r) noexcept {
 if(r.size()!=0x800000 || word(r,0x8009E02C)!=0x8013B418 || byte(r,0x8013B446)!=6 || byte(r,0x8013B44C)!=7 ||
 byte(r,0x8013B452)!=0 || byte(r,0x8013B42A)!=0 || word(r,0x8013B42C)!=0x014000F0)return {};
 constexpr std::array<uint32_t,15> owner={0x3C01C0EBu,0x34213333u,0x44810000u,0x3C01C140u,0x3421CCCDu,0x44811000u,0x3C014301u,0x3421F333u,0x44812000u,0x3C02801Au,0x2442081Cu,0xE4400000u,0xE4420004u,0x03E00008u,0xE4440008u};
 // Select Teams uses the same original19-node model-state rig, but has a
 // different overlay and scheduler owner. Validate the original owner's code
 // and active callback, never infer ownership from the shared scene alone.
 constexpr std::array<uint32_t,16> team_owner={0x27BDFFD8u,0xAFB20018u,0x0080902Du,0xAFB3001Cu,0x00A0982Du,0xAFBF0024u,0xAFB40020u,0xAFB10014u,0x0C0F0F77u,0xAFB00010u,0x0C0F1009u,0x00000000u,0x0C0A8B61u,0x00000000u,0x3C07802Bu,0x24E7C7E4u};
 // Training's yellow single-team selector is another original overlay, not
 // the blue two-team selector. Keep its active dispatch/code identity separate.
 constexpr std::array<uint32_t,16> single_team_owner={0x27BDFFE0u,0xAFB00010u,0x0080802Du,0xAFB10014u,0xAFBF0018u,0x0C0F0F77u,0x00A0882Du,0x0C0F1009u,0x00000000u,0x3C02802Bu,0x94420912u,0x30420010u,0x10400003u,0x00000000u,0x3C01802Bu,0xA4200912u};
 bool preparation=true,teams=true,single_team=true;
 for(unsigned i=0;i<owner.size();++i)preparation&=word(r,0x802BDA2C+i*4)==owner[i];
 for(unsigned i=0;i<team_owner.size();++i)teams&=word(r,0x802A0C48+i*4)==team_owner[i];
 for(unsigned i=0;i<single_team_owner.size();++i)single_team&=word(r,0x802A8434+i*4)==single_team_owner[i];
 if(!preparation&&!teams&&!single_team)return {};
 std::array<bool,220> seen{};bool found=false,teams_active=false;auto p=word(r,0x80077390);
 while(p){if(p<0x801E7070||p>=0x801ED420||(p-0x801E7070)%0x74)return {};
 const auto n=(p-0x801E7070)/0x74;if(seen[n])return {};seen[n]=true;teams_active|=teams&&word(r,p+12)==0x802A0C48;found|=(preparation&&word(r,p+12)==0x802BDA2C)||(teams&&word(r,p+12)==0x802A0C48)||(single_team&&word(r,p+12)==0x802A8434);p=word(r,p);}
 if(!found)return {};
 PalMenuAvatarProof proof;proof.models.scene=0x607;
 // Only Select Teams owns model-state one. A nonzero second root requires a
 // complete independent19-node rig; never join arbitrary allocated models.
 proof.models.record_count=teams_active&&word(r,0x801A08CC)?38:19;
 for(unsigned rig=0;rig<proof.models.record_count/19;++rig){
  const auto state=0x801A07CC+rig*0x100;
  for(unsigned joint=0;joint<19;++joint){const unsigned i=rig*19+joint;const auto object=word(r,state+joint*4);
   if(!record(object,joint) || (word(r,object+0x28)&0x80400000)!=0x80400000)return {};
   for(unsigned previous=0;previous<i;++previous)if(proof.models.records[previous]==object)return {};
   proof.models.records[i]=object;
   for(unsigned bank=0;bank<2;++bank){const auto matrix=word(r,object+0x18+bank*4),base=0x800A7848+bank*0x5100;
    if(matrix<base||matrix>base+0x5100-64||(matrix-base)%64)return {};
    proof.matrices[i][bank]=matrix&0x7fffff;}
  }
  const auto root=proof.models.records[rig*19];
  if(word(r,root+0x84)!=state || word(r,root+0x48)!=proof.models.records[rig*19+1])return {};
  // Parent/child/sibling links stay within this rig, including with two avatars.
  for(unsigned joint=1;joint<19;++joint)for(unsigned offset:{0x44u,0x48u,0x4Cu,0x50u}){
   const auto link=word(r,proof.models.records[rig*19+joint]+offset);
   if(link){bool member=false;for(unsigned n=0;n<19;++n)member|=proof.models.records[rig*19+n]==link;if(!member)return {};}
  }
 }
 if(teams_active){
  const auto vertices=word(r,0x800BD9D8),display=word(r,0x800BD9E0);
  const auto span=[](uint32_t a,uint32_t bytes){return !(a&7)&&a>=0x801B0000&&a<=0x80700000-bytes;};
  bool topology=span(vertices,30*16)&&span(display,0xD8)&&word(r,display)==0xDE000000&&word(r,display+4)==0x80084488;
  for(unsigned row=0;topology&&row<4;++row){const auto block=display+8+row*48;
   topology=word(r,block)==0x0100C018&&word(r,block+4)==vertices+row*96;
   for(unsigned column=0;topology&&column<5;++column){const auto a=column*2,b=(column+1)*2,c=(column+6)*2,d=(column+7)*2;
    topology=word(r,block+8+column*8)==(0x06000000u|(a<<16)|(b<<8)|c)&&word(r,block+12+column*8)==((b<<16)|(d<<8)|c);}
  }
  topology=topology&&word(r,display+200)==0xE3001801&&word(r,display+204)==0xC0&&word(r,display+208)==0xDF000000&&!word(r,display+212);
  // Original six-by-five flag grid. Its wind producer changes Z and vertex
  // shades only; altered XY/UV/topology cannot authorize a different mesh.
  constexpr std::array<int16_t,6> u={0,576,1216,1792,2432,3072};
  for(unsigned n=0;topology&&n<30;++n){const auto v=vertices+n*16;
   topology=half(r,v)==-300+int(n%6)*120&&half(r,v+2)==-200+int(n/6)*100&&
    half(r,v+4)>=-80&&half(r,v+4)<=80&&half(r,v+6)==0&&half(r,v+8)==u[n%6]&&half(r,v+10)==-63+int(n/6)*512;}
  for(unsigned i=0;topology&&i<2;++i){const auto object=word(r,0x802ACD78+i*4),texture=record(object,0)?word(r,object+0x5C):0,palette=record(object,0)?word(r,object+0x88):0;
   if(!record(object,0)||(word(r,object+0x28)&0x80400000)!=0x80400000||word(r,object+0x24)!=display||
      word(r,object+0x44)||word(r,object+0x48)||word(r,object+0x84)||!span(texture,768)||!span(palette,512))continue;
   bool distinct=true,matrices=true;for(auto rig:proof.models.records)distinct&=rig!=object;
   if(i)distinct&=proof.models.vertex_models[0].record!=object;
   for(unsigned bank=0;bank<2;++bank){const auto m=word(r,object+0x18+bank*4),base=0x800A7848+bank*0x5100;matrices&=m>=base&&m<=base+0x5100-64&&(m-base)%64==0;}
   if(!distinct||!matrices)continue;
   uint64_t key=14695981039346656037ULL;
   for(auto address:{object+0x54,object+0x5C,object+0x88})for(unsigned n=0;n<4;++n){key^=byte(r,address+n);key*=1099511628211ULL;}
   for(unsigned n=0;n<768;++n){key^=byte(r,texture+n);key*=1099511628211ULL;}
   for(unsigned n=0;n<512;++n){key^=byte(r,palette+n);key*=1099511628211ULL;}
   proof.models.vertex_models[i]={object,0,key?key:1};
  }
 }
 return proof;
}
std::optional<unsigned> pal_menu_avatar_task_bank(std::span<const uint8_t>r,uint64_t root,const PalMenuAvatarProof&proof) noexcept {
 if(r.size()!=0x800000||proof.models.scene!=0x607)return {};
 std::array<uint32_t,16>segments{};std::array<bool,16>known{};known[0]=true;
 auto resolve=[&](uint64_t a)->std::optional<uint32_t>{if(a>=0x80000000)return physical(a);
  if(a>=0x10000000)return {};
  const auto segment=unsigned(a>>24);if(!known[segment])return {};
  const uint64_t result=segments[segment]+(a&0xffffff);if(result>=r.size())return {};return uint32_t(result);};
 auto first=resolve(root);if(!first)return {};uint32_t pc=*first,half1=0;uint64_t observed=0;
 if(proof.models.record_count!=19&&proof.models.record_count!=38)return {};
 const uint64_t required=(uint64_t(1)<<proof.models.record_count)-1;
 std::array<uint32_t,31>returns{};unsigned depth=0;std::optional<unsigned>bank;bool extended=false;
 for(unsigned budget=0;budget<16384;++budget){if(pc%8||pc>r.size()-8)return {};const auto w=word(r,pc),v=word(r,pc+4),op=w>>24;
  if(w==0xE0525464){if(v!=0x10000064)return {};extended=true;}
  if(op==0x64){if(!extended)return {};unsigned slots=0;
   if(w==0x64000033&&v<=2)slots=1;
   if((w==0x64000017||w==0x64000018)&&!v)slots=1;
   if(w==0x64000005&&!(v&0xFC000000))slots=2;
   if(w==0x64000006&&!(v&0xFF000000))slots=2;
   if(w==0x64000002&&!(v&0xF0000000))slots=3;
   if(!slots||pc>r.size()-slots*8)return {};
   pc+=slots*8;budget+=slots-1;continue;
  }
  if(op==0xE1)half1=v;
  if(op==0xDB&&((w>>16)&255)==6){auto base=physical(v);const auto offset=w&65535;if(!base||offset%4||offset/4>=16)return {};segments[offset/4]=*base;known[offset/4]=true;}
  else if(op==0xDE){if(w!=0xDE000000&&w!=0xDE010000)return {};auto target=resolve(v);if(!target)return {};
   if(w==0xDE000000){if(depth>=returns.size())return {};returns[depth++]=pc+8;}pc=*target;continue;}
  else if(op==0xDF){if(w!=0xDF000000||v)return {};if(!depth)return observed==required?bank:std::optional<unsigned>{};pc=returns[--depth];continue;}
  else if(op==0xDA){if((w&0x00FFFFF8)!=0x00380000)return {};auto matrix=resolve(v);if(!matrix||*matrix%8||*matrix>r.size()-64)return {};
   if((w&6)==2)for(unsigned i=0;i<proof.models.record_count;++i)for(unsigned b=0;b<2;++b)if(*matrix==proof.matrices[i][b]){if(bank&&*bank!=b)return {};bank=b;observed|=uint64_t(1)<<i;}}
  else if(op==0xDD){auto code=physical(v),data=physical(half1);if(w!=0xDD0007FF||!code||!data||
   !((*code==0x69AD0&&*data==0x99EF0)||(*code==0x6AE60&&*data==0x9A310)))return {};}
  else if(op==3||op==4||!(op<=2||(op>=5&&op<=8)||(op>=0xD7&&op<=0xDC)||op>=0xE0))return {};
  pc+=8;
 }
 return {};
}
}
