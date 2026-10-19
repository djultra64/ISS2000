// Original project work: djultra64.
#include "prompt_title_model.hpp"
#include "rom_image.hpp"
#include <algorithm>

namespace iss2000 {
namespace {
constexpr uint32_t memory_size=0x800000;
uint8_t byte(std::span<const uint8_t> ram,uint32_t p){return ram[(p&0x7fffff)^3];}
uint32_t word(std::span<const uint8_t> ram,uint32_t p){return uint32_t(byte(ram,p))<<24|uint32_t(byte(ram,p+1))<<16|uint32_t(byte(ram,p+2))<<8|byte(ram,p+3);}
uint16_t half(std::span<const uint8_t> ram,uint32_t p){return uint16_t(unsigned(byte(ram,p))*256+byte(ram,p+1));}
bool guest_range(uint32_t p,uint32_t n,uint32_t align=4){return p>=0x80000000&&p<=0x80800000-n&&!(p&(align-1));}
std::vector<uint8_t> bytes(std::span<const uint8_t> ram,uint32_t p,uint32_t size){std::vector<uint8_t> v(size);for(uint32_t n=0;n<size;++n)v[n]=byte(ram,p+n);return v;}
void put(std::span<uint8_t> ram,uint32_t p,uint32_t v){for(unsigned n=0;n<4;++n)ram[((p+n)&0x7fffff)^3]=uint8_t(v>>(24-8*n));}
std::optional<std::string> phrase(std::string_view name){
    std::string result(name);
    constexpr std::pair<std::string_view,std::string_view> aliases[]{
        {"+","Plus"},{"-","Minus"},{"×","Cross"},{"○","Circle"},{"□","Square"},{"△","Triangle"}
    };
    for(const auto& a:aliases)if(name==a.first)result=a.second;
    std::replace(result.begin(),result.end(),'-',' ');
    if(result.empty()||result.size()>22||result.find_first_not_of("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ")!=std::string::npos)return {};
    return "PRESS "+result;
}
bool model_matches(std::span<const uint8_t> ram,uint32_t base){
    if(!guest_range(base,0x1610,8))return false;
    const uint32_t expected[]{0,0x1610,0x228,0x1f8,0x12c0,0x41700000,0x3dcccccd,0x1e00,1,base,0x32323200};
    for(unsigned n=0;n<11;++n)if(word(ram,0x80085404+n*4)!=expected[n])return false;
    auto normalized=bytes(ram,base,0x1610);
    auto patch=[&](uint32_t p,uint32_t v){for(unsigned n=0;n<4;++n)normalized[p+n]=uint8_t(v>>(24-8*n));};
    constexpr unsigned texture_ids[]{0x16,0x16,0x18,0x18,0x16,0x19,0x16,0x19,0x16,0x18,0x1a,0x1b,0x16,0x1b,0x16,0x19,0x16,0x18,0x16,0x1b};
    std::array<uint32_t,6> texture_pointers{};
    for(unsigned n=0;n<20;++n){
        const uint32_t block=0x500+n*0xb0,table=0x12c0+n*0x28;
        if(word(ram,base+block+0x9c)!=base+n*0x40||word(ram,base+table)!=base+0x1210-n*0xb0)return false;
        const auto texture=word(ram,base+block+0x44),slot=texture_ids[n]-0x16;
        if(!texture||texture>=memory_size||(texture&7))return false;
        if(texture_pointers[slot]&&texture_pointers[slot]!=texture)return false;
        texture_pointers[slot]=texture;
        patch(block+0x44,0xc0000000+texture_ids[n]);patch(block+0x9c,n*0x40);patch(table,0x1210-n*0xb0);
    }
    return rom_detail::sha256_hex(normalized)=="9426249b731453a9059de98b51a673dc0ee018e5494843597b99da6ee8361752";
}
bool node(uint32_t p){return p>=0x80145624&&p<0x80145624+285*0x98&&(p-0x80145624)%0x98==0;}
bool model_owner(std::span<const uint8_t> ram,uint32_t model){
    const auto root=word(ram,0x800be958);
    if(!node(root)||word(ram,root+0x24)||word(ram,root+0x44)||word(ram,root+0x80)!=0x800a7490)return false;
    auto child=word(ram,root+0x48);std::array<bool,20> seen{};
    for(unsigned n=0;n<20;++n){
        if(!node(child)||word(ram,child+0x44)!=root)return false;
        const auto gdl=word(ram,child+0x24);
        if(gdl<model+0x500||gdl>=model+0x12c0||(gdl-model-0x500)%0xb0)return false;
        const auto index=(gdl-model-0x500)/0xb0;if(seen[index])return false;seen[index]=true;
        child=word(ram,child+0x4c);
    }
    return child==0;
}
}
std::optional<TitlePromptPlan> plan_pal_title_prompt(std::span<const uint8_t> ram,uint32_t begin,uint32_t end,std::string_view name){
    if(ram.size()!=memory_size)return {};
    // Original47598 starts the accepted-Start transition at phase2/timer100;
    // 4777C keeps this same title model alive until the final scene switch.
    const auto phase=word(ram,0x800be944);
    const auto timer=int32_t(word(ram,0x800be948));
    if((phase!=1&&phase!=2)||word(ram,0x800be960)!=0x80086fd0||
       (phase==1?(timer<0||timer>999):(timer < -11||timer>100)))return {};
    const auto base=word(ram,0x800a4aa4),head=word(ram,0x8009e0c8);
    if((base!=0x800d0320&&base!=0x800e0380)||(begin&7)||(end&7)||begin<base+8||end<=begin||end>base+0x10008||head<end||head>base+0x10008)return {};
    const auto frame=word(ram,0x8009e02c);
    if(!guest_range(frame,0x18)||byte(ram,frame+0x12)||half(ram,frame+0x14)!=320||half(ram,frame+0x16)!=240)return {};
    const auto text=phrase(name);if(!text)return {};
    if(word(ram,0x800bea1c)!=0x80087460||rom_detail::sha256_hex(bytes(ram,0x80087460,32))!="197e03223036a1ab8a7441afad5384f88d5cba2f9e6085c49d63c422abf0f9c6")return {};
    const auto model=word(ram,0x80085428);
    if(!model_matches(ram,model)||!model_owner(ram,model)||rom_detail::sha256_hex(bytes(ram,0x80352800,0x3000))!="237c7f53ac8b11353467cb957868f794507ca2688c93581d977dac03a4e8b765")return {};
    TitlePromptPlan plan;plan.begin_=begin;plan.end_=end;plan.base_=base;plan.model_=model;plan.physical_name_=name;
    // Original20quad projection in completed-title11 spans x89.72..229.43,
    // y160.46..178.35. The original12px font is centered within that band.
    plan.line_={int16_t((320-int(text->size())*6)/2),164,*text};
    std::array<bool,20> seen{};unsigned count=0;
    for(uint32_t p=begin;p<end;p+=8){
        if(word(ram,p)!=0xde000000)continue;
        const auto target=word(ram,p+4);
        if(target<model+0x500||target>=model+0x12c0)continue;
        if((target-model-0x500)%0xb0||count==20||p<begin+8||word(ram,p-8)!=0xda380003)return {};
        const auto matrix=word(ram,p-4);
        if(!guest_range(matrix,64,8))return {};
        const auto index=(target-model-0x500)/0xb0;if(seen[index])return {};seen[index]=true;plan.commands_[count++]=p;
    }
    if(count!=20)return {};
    return plan;
}
bool suppress_pal_title_prompt(std::span<uint8_t> ram,const TitlePromptPlan& plan){
    const auto current=plan_pal_title_prompt(ram,plan.begin_,plan.end_,plan.physical_name_);
    if(!current||current->base_!=plan.base_||current->model_!=plan.model_||current->commands_!=plan.commands_)return false;
    for(const auto p:plan.commands_){put(ram,p,0);put(ram,p+4,0);}
    return true;
}
}
