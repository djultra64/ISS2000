// Original project work: djultra64.
#include "pal_menu_audio.hpp"
#include "rom_image.hpp"
#include <array>
#include <cstring>
#include <optional>
#include <string_view>
#include <vector>
namespace iss2000 {namespace {
std::optional<uint16_t> sound_id(PalMenuSound sound){
    switch(sound){
    case PalMenuSound::Navigate:return 0x101;
    case PalMenuSound::Accept:case PalMenuSound::Back:return 0x100;
    case PalMenuSound::Error:return 0x152;
    }
    return {};
}
bool canonical(uint64_t address){
    const auto high=uint32_t(address>>32),low=uint32_t(address);
    return high==0||(high==0xffffffffu&&(low&0x80000000u));
}
bool code_matches(std::span<const uint8_t> ram,uint32_t at,unsigned size,std::string_view hash){
    std::vector<uint8_t> bytes(size);
    for(unsigned n=0;n<size;++n)bytes[n]=ram[(at+n)^3];
    return rom_detail::sha256_hex(bytes)==hash;
}
struct StackRestore {
    uint8_t* at;std::array<uint8_t,64> bytes;
    explicit StackRestore(uint8_t* pointer):at(pointer){std::memcpy(bytes.data(),at,bytes.size());}
    ~StackRestore(){std::memcpy(at,bytes.data(),bytes.size());}
};
}
PalMenuAudioResult play_pal_menu_sound(std::span<uint8_t> ram,const recomp_context& caller,
        PalMenuSound sound,recomp_func_t* original){
    const auto id=sound_id(sound);
    if(ram.size()!=0x800000||!id||!original||!canonical(caller.r29))return PalMenuAudioResult::Rejected;
    const auto sp=uint32_t(caller.r29);
    if((sp&7)||sp<0x800A0318||sp>0x800A42D8)return PalMenuAudioResult::Rejected;
    const auto fp=reinterpret_cast<uintptr_t>(caller.f_odd),low=reinterpret_cast<uintptr_t>(&caller.f0),
        high=reinterpret_cast<uintptr_t>(&caller.f31)+sizeof(fpr);
    if(fp&&(fp<low||fp>high-sizeof(uint32_t)||(fp-low)%sizeof(uint32_t)))return PalMenuAudioResult::Rejected;
    if(!code_matches(ram,0x4C59C,0x24,"5af93833c6f436f25ef89d524e4ba9ba724635d2c0b3f8a080c1a7b0e0dde9f6")||
       !code_matches(ram,0x4C608,0x120,"e22c64bec799b553b249b586c54796c2d4a859cbba6a1590a56343dd7cf0dc17"))return PalMenuAudioResult::Rejected;
    const auto count=ram[0x9DEA4^3];
    if(count>8||ram[0x9E07C^3])return PalMenuAudioResult::Rejected;
    bool pending=false;
    for(unsigned n=0;n<count;++n){uint32_t command;std::memcpy(&command,ram.data()+0x166198+n*4,4);pending|=uint16_t(command)==*id;}
    StackRestore restore(ram.data()+((sp-64)&0x7FFFFF));
    auto context=caller;
    if(fp)context.f_odd=reinterpret_cast<uint32_t*>(reinterpret_cast<uint8_t*>(&context.f0)+(fp-low));
    context.r4=*id;
    original(ram.data(),&context);
    // These outcomes mirror the original leaf's full-before-dedup ordering.
    if(count==8)return PalMenuAudioResult::Full;
    return pending?PalMenuAudioResult::AlreadyPending:PalMenuAudioResult::Queued;
}
}
