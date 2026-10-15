// Original project work: djultra64. Procedural UI glyphs contain no game assets.
#include "prompt_textures.hpp"
#include "rom_image.hpp"
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <mutex>
#include <memory>
#include <stdexcept>
#include <utility>

namespace iss2000 {
namespace prompt_detail {
namespace {
std::optional<uint32_t> offset(uint64_t address,uint32_t bytes,uint32_t alignment=1){
    const auto lo=uint32_t(address),hi=uint32_t(address>>32);
    if(hi!=0&&!(hi==0xFFFFFFFFu&&(lo&0x80000000u)))return {};
    if((lo&0xE0000000u)!=0x80000000u&&(lo&0xE0000000u)!=0xA0000000u)return {};
    auto p=lo&0x1FFFFFFFu;
    if(p>0x800000u||bytes>0x800000u-p||(p&(alignment-1)))return {};
    return p;
}
uint8_t byte(const uint8_t* ram,uint32_t p){return ram[p^3u];}
uint32_t word(const uint8_t* ram,uint32_t p){
    return uint32_t(byte(ram,p))<<24|uint32_t(byte(ram,p+1))<<16|uint32_t(byte(ram,p+2))<<8|byte(ram,p+3);
}
template<size_t N> std::array<uint8_t,N> read(const uint8_t* ram,uint32_t p){
    std::array<uint8_t,N> bytes{};for(size_t n=0;n<N;++n)bytes[n]=byte(ram,p+uint32_t(n));return bytes;
}
void write(uint8_t* ram,uint32_t p,const PixelBytes& bytes){for(size_t n=0;n<bytes.size();++n)ram[(p+uint32_t(n))^3u]=bytes[n];}
struct Layout {uint32_t descriptor,texture,palette;unsigned slot;};
std::optional<Layout> probe_layout(const uint8_t* ram,uint64_t sprite,bool& recognized_slot,const PromptTextureLayout& profile){
    auto s=offset(sprite,0x38,4);if(!s)return {};
    auto bank=offset(word(ram,profile.bank_pointer),(std::max(profile.descriptor_indices[0],profile.descriptor_indices[1])+1)*12,4);if(!bank)return {};
    auto descriptor=offset(word(ram,*s+0x14),12,4);if(!descriptor)return {};
    unsigned slot;
    if(*descriptor==*bank+profile.descriptor_indices[0]*12)slot=0;
    else if(*descriptor==*bank+profile.descriptor_indices[1]*12)slot=1;
    else return {};
    recognized_slot=true;
    if(word(ram,*descriptor)!=0x00100010u || word(ram,*descriptor+4)!=profile.descriptor_attributes[slot])return {};
    auto texture=offset(word(ram,*descriptor+8),128);
    auto palette=offset(word(ram,*s+0x34),32,2);
    if(!texture||!palette)return {};
    return Layout{*descriptor,*texture,*palette,slot};
}
constexpr std::array<std::array<uint8_t,7>,26> letters{{
 {{14,17,17,31,17,17,17}},{{30,17,17,30,17,17,30}},{{14,17,16,16,16,17,14}},
 {{30,17,17,17,17,17,30}},{{31,16,16,30,16,16,31}},{{31,16,16,30,16,16,16}},
 {{14,17,16,23,17,17,15}},{{17,17,17,31,17,17,17}},{{14,4,4,4,4,4,14}},
 {{7,2,2,2,18,18,12}},{{17,18,20,24,20,18,17}},{{16,16,16,16,16,16,31}},
 {{17,27,21,21,17,17,17}},{{17,25,21,19,17,17,17}},{{14,17,17,17,17,17,14}},
 {{30,17,17,30,16,16,16}},{{14,17,17,17,21,18,13}},{{30,17,17,30,20,18,17}},
 {{15,16,16,14,1,1,30}},{{31,4,4,4,4,4,4}},{{17,17,17,17,17,17,14}},
 {{17,17,17,17,17,10,4}},{{17,17,17,21,21,21,10}},{{17,17,10,4,10,17,17}},
 {{17,17,10,4,4,4,4}},{{31,1,2,4,8,16,31}}
}};
}
std::optional<PixelBytes> glyph_pixels(std::string_view label){
    PixelBytes result{};
    auto pixel=[&](int x,int y,uint8_t value=1){
        if(x<0||x>=16||y<0||y>=16)return;
        auto i=unsigned(y*16+x)/2;
        if(x&1)result[i]=uint8_t((result[i]&0xF0u)|value);
        else result[i]=uint8_t((result[i]&0x0Fu)|(value<<4));
    };
    auto line=[&](int x0,int y0,int x1,int y1){
        int dx=std::abs(x1-x0),sx=x0<x1?1:-1,dy=-std::abs(y1-y0),sy=y0<y1?1:-1,error=dx+dy;
        while(true){pixel(x0,y0);if(x0==x1&&y0==y1)break;int twice=2*error;if(twice>=dy){error+=dy;x0+=sx;}if(twice<=dx){error+=dx;y0+=sy;}}
    };
    // SDL raw aliases and family-specific friendly names describe the same
    // physical button. Normalize spelling without changing face-button letters.
    std::string compact;
    for(unsigned char c:label){
        if(c>='A'&&c<='Z')compact.push_back(char(c-'A'+'a'));
        else if((c>='a'&&c<='z')||(c>='0'&&c<='9'))compact.push_back(char(c));
    }
    if(compact=="leftshoulder")label="LB";
    else if(compact=="rightshoulder")label="RB";
    else if(compact=="leftstick"||compact=="leftstickpress")label="LS";
    else if(compact=="rightstick"||compact=="rightstickpress")label="RS";
    else if(compact=="back")label="View";
    else if(compact=="start")label="Menu";
    else if(compact=="guide")label="Home";
    else if(compact=="misc1")label="Capture";
    else if(compact=="paddle1")label="P1";
    else if(compact=="paddle2")label="P2";
    else if(compact=="paddle3")label="P3";
    else if(compact=="paddle4")label="P4";
    int direction=0;
    bool stick_arrow=label.starts_with("R")&&label.size()>1;
    if(label=="↑"||label=="D↑"||label=="R↑"||compact=="dpup"||compact=="dpadup")direction=1;
    if(label=="↓"||label=="D↓"||label=="R↓"||compact=="dpdown"||compact=="dpaddown")direction=2;
    if(label=="←"||label=="D←"||label=="R←"||compact=="dpleft"||compact=="dpadleft")direction=3;
    if(label=="→"||label=="D→"||label=="R→"||compact=="dpright"||compact=="dpadright")direction=4;
    auto circle=[&]{
        for(int y=2;y<14;++y)for(int x=2;x<14;++x){
            int d=(2*x-15)*(2*x-15)+(2*y-15)*(2*y-15);if(d>=90&&d<=140)pixel(x,y);
        }
    };
    if(direction){
        if(stick_arrow)circle();
        auto arrow_pixel=[&](int x,int y){
            if(direction==2)y=15-y;
            else if(direction==3){int old=x;x=y;y=15-old;}
            else if(direction==4){int old=x;x=15-y;y=old;}
            pixel(x,y);
        };
        for(int y=4;y<=12;++y){arrow_pixel(7,y);arrow_pixel(8,y);}
        for(int n=0;n<4;++n){arrow_pixel(7-n,4+n);arrow_pixel(8+n,4+n);}
        return result;
    }
    if(compact=="dpad"){
        for(int n=3;n<=12;++n){pixel(7,n);pixel(8,n);pixel(n,7);pixel(n,8);}return result;
    }
    if(label=="+"||label=="-"){
        for(int n=3;n<=12;++n){pixel(n,7);pixel(n,8);if(label=="+"){pixel(7,n);pixel(8,n);}}return result;
    }
    if(label=="Menu"||label=="Options"){
        for(int y:{4,7,10}){for(int x=4;x<=12;++x)pixel(x,y);if(label=="Options")pixel(2,y);}return result;
    }
    if(label=="View"){
        for(int n=3;n<=10;++n){pixel(n,3);pixel(n,10);pixel(3,n);pixel(10,n);}
        for(int n=6;n<=13;++n){pixel(n,6);pixel(n,13);pixel(6,n);pixel(13,n);}return result;
    }
    if(label=="Share"){
        line(3,8,3,13);line(3,13,12,13);line(12,13,12,8);
        line(7,10,7,2);line(7,2,4,5);line(7,2,10,5);return result;
    }
    if(label=="Home"){
        line(2,7,7,2);line(7,2,13,7);line(4,6,4,13);line(4,13,11,13);line(11,13,11,6);
        line(7,13,7,9);line(7,9,9,9);line(9,9,9,13);return result;
    }
    if(label=="Xbox"){
        circle();line(4,4,11,11);line(11,4,4,11);return result;
    }
    if(label=="Microphone"){
        line(6,3,9,3);line(6,3,6,8);line(9,3,9,8);line(6,8,9,8);
        line(4,7,4,10);line(4,10,7,12);line(7,12,11,10);line(11,10,11,7);
        line(7,12,7,14);line(5,14,10,14);return result;
    }
    if(label=="Capture"){
        for(int n=3;n<=12;++n){pixel(n,4);pixel(n,12);pixel(3,n);pixel(12,n);}
        for(int y=6;y<=10;++y){
            for(int x=5;x<=10;++x){int d=(x-7)*(x-7)+(y-8)*(y-8);if(d>=3&&d<=7)pixel(x,y);}
        }
        return result;
    }
    if(label=="Touchpad"||compact=="touchpad"){
        for(int x=2;x<=13;++x){pixel(x,3);pixel(x,12);}for(int y=3;y<=12;++y){pixel(2,y);pixel(13,y);}
        for(int y=5;y<=10;y+=2){for(int x=4;x<=11;x+=2)pixel(x,y);}
        return result;
    }
    if(label=="×"||label=="Cross"){
        for(int n=4;n<=11;++n){pixel(n,n);pixel(n+1,n);pixel(15-n,n);pixel(14-n,n);}return result;
    }
    if(label=="○"||label=="Circle"){
        for(int y=2;y<14;++y){
            for(int x=2;x<14;++x){int d=(2*x-15)*(2*x-15)+(2*y-15)*(2*y-15);if(d>=65&&d<=130)pixel(x,y);}
        }
        return result;
    }
    if(label=="□"||label=="Square"){
        for(int n=3;n<=12;++n){pixel(n,3);pixel(n,12);pixel(3,n);pixel(12,n);}return result;
    }
    if(label=="△"||label=="Triangle"){line(8,3,2,12);line(2,12,13,12);line(13,12,8,3);return result;}
    if(label=="Return"||label=="Enter"){
        line(11,4,11,9);line(11,9,4,9);line(4,9,7,6);line(4,9,7,12);return result;
    }
    if(label.empty()||label.size()>2)return {};
    for(char c:label)if((c<'A'||c>'Z')&&(c<'0'||c>'9'))return {};
    for(int y=1;y<=14;++y)for(int x=1;x<=14;++x)pixel(x,y,(x==1||x==14||y==1||y==14)?1:15);
    int left=(16-int(label.size()*6-1))/2;
    constexpr std::array<std::array<uint8_t,7>,10> digits{{
        {{14,17,19,21,25,17,14}},{{4,12,4,4,4,4,14}},{{14,17,1,2,4,8,31}},
        {{30,1,1,14,1,1,30}},{{2,6,10,18,31,2,2}},{{31,16,16,30,1,1,30}},
        {{14,16,16,30,17,17,14}},{{31,1,2,4,8,8,8}},{{14,17,17,14,17,17,14}},{{14,17,17,15,1,1,14}}
    }};
    for(size_t n=0;n<label.size();++n){
        auto rows=label[n]>='A'?letters[unsigned(label[n]-'A')]:digits[unsigned(label[n]-'0')];
        for(int y=0;y<7;++y)for(int x=0;x<5;++x)
            if(rows[unsigned(y)]&(1u<<(4-x)))pixel(left+int(n)*6+x,4+y);
    }
    return result;
}
TextureGuard::TextureGuard(PromptTextureLayout layout):layout_(std::move(layout)){
    if(layout_.bank_pointer>0x800000-4 || layout_.bank_pointer%4 ||
       layout_.descriptor_indices[0]==layout_.descriptor_indices[1])
        throw std::invalid_argument("Invalid prompt texture layout");
    for(const auto index:layout_.descriptor_indices)
        if(index>=1024)throw std::invalid_argument("Invalid prompt descriptor index");
    for(const auto& hashes:layout_.expected)
        for(const auto* hash:{&hashes.texture,&hashes.palette})
            if(hash->size()!=64 || hash->find_first_not_of("0123456789abcdef")!=std::string::npos)
                throw std::invalid_argument("Invalid prompt asset hash");
}
void TextureGuard::warn(){if(!warned_){std::fprintf(stderr,"[Prompts] Unrecognized A/B icon layout, bytes, palette or label; original memory preserved.\n");warned_=true;}}
bool TextureGuard::prepare(uint8_t* ram,uint64_t sprite,const std::array<std::string_view,2>& labels){
    if(!ram)return false;
    if(memory_!=ram){memory_=ram;cache_={};warned_=false;}
    bool recognized_slot=false;
    auto info=probe_layout(ram,sprite,recognized_slot,layout_);
    if(!info){if(recognized_slot)warn();return false;} // Ordinary unrelated sprites are silent.
    auto& saved=cache_[info->slot];
    auto pixels=read<128>(ram,info->texture);
    auto palette=read<32>(ram,info->palette);
    if(rom_detail::sha256_hex(palette)!=layout_.expected[info->slot].palette){warn();return false;}
    bool ours=saved.valid&&saved.texture==info->texture&&saved.palette==info->palette&&saved.descriptor==info->descriptor&&pixels==saved.applied;
    if(!ours){
        if(rom_detail::sha256_hex(pixels)!=layout_.expected[info->slot].texture){warn();return false;}
        saved={info->descriptor,info->texture,info->palette,pixels,{},true};
    }
    auto generated=glyph_pixels(labels[info->slot]);
    if(!generated){if(ours)write(ram,info->texture,saved.original);saved.valid=false;warn();return false;}
    saved.applied=*generated;write(ram,info->texture,*generated);return true;
}
void TextureGuard::restore(uint8_t* ram){
    if(!ram||ram!=memory_)return;
    auto bank=offset(word(ram,layout_.bank_pointer),(std::max(layout_.descriptor_indices[0],layout_.descriptor_indices[1])+1)*12,4);
    for(unsigned slot=0;slot<cache_.size();++slot){
        auto& saved=cache_[slot];if(!saved.valid)continue;
        bool same=bank&&saved.descriptor==*bank+layout_.descriptor_indices[slot]*12
            &&word(ram,saved.descriptor)==0x00100010u
            &&word(ram,saved.descriptor+4)==layout_.descriptor_attributes[slot]
            &&offset(word(ram,saved.descriptor+8),128)==saved.texture;
        if(same&&read<128>(ram,saved.texture)==saved.applied
            &&rom_detail::sha256_hex(read<32>(ram,saved.palette))==layout_.expected[slot].palette)
            write(ram,saved.texture,saved.original);
        saved.valid=false;
    }
}
}
namespace {
PromptTextureLayout reviewed_prompt_layout(uint32_t bank_pointer){
    // Both revisions independently match these exact decoded icons/palettes.
    return {bank_pointer,{5,6},{0x01060000,0x01070000},{{
        {"53190166d2b23997025eb589b1ee4209852f05a4269fd1f89b2db54245612d1a","6dd4c784922f5eaaaac284db2080b4764d6f10ef145b89ac958fafd677c30f34"},
        {"fe9074c636d0a9c2e3f39aa2ca0a15474e2b8f3eaa0a58afa0cf4187f7b042de","8495c578169e8ce5c471d753b3af53ce08b02934cbac0ba1d954c4165c4d515e"}
    }}};
}
}
PromptTextureLayout us_prompt_texture_layout(){return reviewed_prompt_layout(0x79650);}
PromptTextureLayout pal_en_prompt_texture_layout(){return reviewed_prompt_layout(0x76B30);}
namespace {
std::mutex prompt_mutex;
std::unique_ptr<prompt_detail::TextureGuard> prompts;
}
void configure_prompt_textures(const PromptTextureLayout& layout){
    auto candidate=std::make_unique<prompt_detail::TextureGuard>(layout);
    std::lock_guard lock(prompt_mutex);
    if(prompts)throw std::logic_error("Prompt textures are already configured");
    prompts=std::move(candidate);
}
bool prepare_prompt_textures(uint8_t* ram,uint64_t sprite,const std::array<std::string_view,2>& labels){
    std::lock_guard lock(prompt_mutex);return prompts && prompts->prepare(ram,sprite,labels);
}
void restore_prompt_textures(uint8_t* ram){std::lock_guard lock(prompt_mutex);if(prompts)prompts->restore(ram);}
}
