// Original project work: djultra64.
#include "pal_football_input.hpp"
#include <array>
#include <cstring>
#include <cstdio>
#include <mutex>
namespace iss2000 {
namespace {
thread_local PalFootballInputResult projection_result=PalFootballInputResult::Entry;
bool canonical(uint64_t address){
    const auto hi=uint32_t(address>>32),lo=uint32_t(address);
    return hi==0||(hi==0xffffffffu&&(lo&0x80000000u));
}
uint16_t half(std::span<const uint8_t> ram,uint32_t p){
    uint16_t value;std::memcpy(&value,ram.data()+((p&0x7fffff)^2),2);return value;
}
void put_half(std::span<uint8_t> ram,uint32_t p,uint16_t value){
    std::memcpy(ram.data()+((p&0x7fffff)^2),&value,2);
}
uint32_t word(std::span<const uint8_t> ram,uint32_t p){
    uint32_t value;std::memcpy(&value,ram.data()+(p&0x7fffff),4);return value;
}
void put_word(std::span<uint8_t> ram,uint32_t p,uint32_t value){
    std::memcpy(ram.data()+(p&0x7fffff),&value,4);
}
constexpr uint16_t profiles[3][6]{
    {1,8,4,0x8000,0x4000,2},
    {1,8,0x4000,0x8000,2,4},
    {0x8000,0x4000,2,4,8,1},
};
constexpr uint16_t normalized[6]{0x8000,0x4000,2,4,8,1};
struct Restore {
    std::span<uint8_t> ram;recomp_context& context;
    uint32_t object,packet,frame;uint64_t sp;
    std::array<uint8_t,32> saved;
    ~Restore() noexcept {
        put_word(ram,object+0x24,packet);
        std::memcpy(ram.data()+(frame&0x7fffff),saved.data(),saved.size());
        context.r29=sp;
    }
};
}
PalFootballInputResult pal_football_input_result() noexcept {return projection_result;}
void trace_pal_football_stage(std::span<const uint8_t> ram,const recomp_context& context,
 unsigned port,uint32_t stage,uint32_t object,uint64_t sequence,bool gamepad,
 ControllerScheme scheme,PalFootballInputResult result){
 if(port>=4)return;
 struct Key {uint32_t stage{};ControllerScheme scheme{};bool gamepad{},has_sequence{};PalFootballInputResult result{};
  bool operator==(const Key&)const=default;};
 struct PortTrace {unsigned lines{},signatures{};bool entered{};std::array<Key,8> seen{};};
 static std::mutex mutex;static std::array<PortTrace,4> traces;
 std::lock_guard lock(mutex);auto& trace=traces[port];if(trace.lines>=8)return;
 const Key key{stage,scheme,gamepad,sequence!=0,result};
 if(result==PalFootballInputResult::Entry){if(trace.entered)return;trace.entered=true;}
 else {for(unsigned i=0;i<trace.signatures;++i)if(trace.seen[i]==key)return;trace.seen[trace.signatures++]=key;}
 ++trace.lines;
 constexpr const char* schemes[]{"type1","type2","type3","type4","type5","free"};
 constexpr const char* results[]{"entry","applied","no-gamepad","no-si-sample","invalid-memory","missing-original",
  "noncanonical-context","invalid-physical-sample","invalid-object","invalid-stack","foreign-packet",
  "unknown-profile","unknown-normalization-table","invalid-bindings"};
 std::fprintf(stderr,"[Controls] stage=%08X port=%u seq=%llu gamepad=%u scheme=%s projection=%s",
  stage,port+1,static_cast<unsigned long long>(sequence),unsigned(gamepad),
  unsigned(scheme)<std::size(schemes)?schemes[unsigned(scheme)]:"invalid",
  unsigned(result)<std::size(results)?results[unsigned(result)]:"invalid-result");
 if(result!=PalFootballInputResult::Entry&&result!=PalFootballInputResult::Applied){
  std::fprintf(stderr," object=%08X sp=%016llX",object,static_cast<unsigned long long>(context.r29));
  if(ram.size()==0x800000&&object>=0x80127468&&object<=0x80127468+3*0xA8&&(object-0x80127468)%0xA8==0){
   std::fprintf(stderr," source=%08X profile=",word(ram,object+0x24));
   for(unsigned i=0;i<6;++i)std::fprintf(stderr,i?",%04X":"%04X",unsigned(half(ram,object+0x72+i*2)));
  }
 }
 std::fputc('\n',stderr);
 std::fflush(stderr);
}
bool apply_pal_football_input(std::span<uint8_t> ram,recomp_context& context,
        uint16_t held_physical,uint16_t pressed_physical,const FootballBindings& bindings,
        recomp_func_t* original){
    auto reject=[](PalFootballInputResult reason){projection_result=reason;return false;};
    if(ram.size()!=0x800000)return reject(PalFootballInputResult::InvalidMemory);
    if(!original)return reject(PalFootballInputResult::MissingOriginal);
    if(!canonical(context.r4)||!canonical(context.r29))return reject(PalFootballInputResult::NoncanonicalContext);
    if(pressed_physical&~held_physical)return reject(PalFootballInputResult::InvalidPhysicalSample);
    const auto object=uint32_t(context.r4),sp=uint32_t(context.r29);
    if(object<0x80127468||object>0x80127468+3*0xa8||(object-0x80127468)%0xa8)
        return reject(PalFootballInputResult::InvalidObject);
    if((sp&7)||sp<0x800A06F8||sp>0x800A42D8)return reject(PalFootballInputResult::InvalidStack);
    const auto port=(object-0x80127468)/0xa8,packet=0x8013B454+port*10;
    if(word(ram,object+0x24)!=packet)return reject(PalFootballInputResult::ForeignPacket);
    unsigned profile=0;
    for(;profile<3;++profile){
        bool match=true;for(unsigned i=0;i<6;++i)match&=half(ram,object+0x72+i*2)==profiles[profile][i];
        if(match)break;
    }
    if(profile==3)return reject(PalFootballInputResult::UnknownProfile);
    for(unsigned i=0;i<6;++i)if(half(ram,0x801D9A70+i*2)!=normalized[i])
        return reject(PalFootballInputResult::UnknownNormalizationTable);
    const auto held=football_guest_pad(bindings,held_physical,profile);
    const auto pressed=football_guest_pad(bindings,pressed_physical,profile);
    if(!held||!pressed)return reject(valid_football_bindings(bindings)?
        PalFootballInputResult::InvalidPhysicalSample:PalFootballInputResult::InvalidBindings);
    // Reserve a caller frame above the original normalizer's stack. The packet
    // sits beyond its16B argument area; a1KiB margin remains within main stack.
    const auto frame=sp-32,scratch=frame+16;
    Restore restore{ram,context,object,packet,frame,context.r29,{}};
    std::memcpy(restore.saved.data(),ram.data()+(frame&0x7fffff),32);
    // SI packets have stride10, so odd-numbered ports are not word aligned.
    // Preserve guest-byte order rather than memcpy'ing differently aligned RAM.
    for(unsigned n=0;n<10;++n)ram[((scratch+n)&0x7fffff)^3]=ram[((packet+n)&0x7fffff)^3];
    put_half(ram,scratch+2,uint16_t(*held|(half(ram,packet+2)&0x1f00)));
    put_half(ram,scratch+4,uint16_t(*pressed|(half(ram,packet+4)&0x1f00)));
    put_word(ram,object+0x24,scratch);
    context.r29=uint64_t(int64_t(int32_t(frame)));
    original(ram.data(),&context);
    projection_result=PalFootballInputResult::Applied;
    return true;
}
}
