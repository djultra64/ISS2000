// Original integration work: djultra64. Artwork: greatdocbrown, CC0-1.0.
#include "prompt_textures.hpp"
#include "rom_image.hpp"
#include <algorithm>
#include <climits>
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
void write(uint8_t* ram,uint32_t p,std::span<const uint8_t> bytes){for(size_t n=0;n<bytes.size();++n)ram[(p+uint32_t(n))^3u]=bytes[n];}
std::vector<uint8_t> read_bytes(const uint8_t* ram,uint32_t p,uint32_t size){
    std::vector<uint8_t> bytes(size);for(uint32_t n=0;n<size;++n)bytes[n]=byte(ram,p+n);return bytes;
}
uint16_t half(const uint8_t* ram,uint32_t p){return uint16_t((unsigned(byte(ram,p))<<8)|byte(ram,p+1));}
uint32_t maximum_index(const PromptTextureLayout& profile){
    auto n=std::max(profile.descriptor_indices[0],profile.descriptor_indices[1]);
    if(profile.c_directions)n=std::max(n,profile.c_directions->descriptor_index);
    if(profile.start_random)n=std::max(n,profile.start_random->descriptor_index);
    return n;
}
uint32_t descriptor_index(const PromptTextureLayout& p,unsigned slot){return slot<2?p.descriptor_indices[slot]:slot==2?p.c_directions->descriptor_index:p.start_random->descriptor_index;}
uint32_t descriptor_attributes(const PromptTextureLayout& p,unsigned slot){return slot<2?p.descriptor_attributes[slot]:slot==2?p.c_directions->descriptor_attributes:p.start_random->descriptor_attributes;}
const PromptAssetHashes& expected_hashes(const PromptTextureLayout& p,unsigned slot){return slot<2?p.expected[slot]:slot==2?p.c_directions->expected:p.start_random->expected;}
uint32_t texture_size(unsigned slot){return slot<2?128u:slot==2?640u:768u;}
uint32_t dimensions(unsigned slot){return slot<2?0x00100010u:slot==2?0x00500010u:0x00600010u;}
struct Layout {uint32_t descriptor,texture,palette;unsigned slot;};
std::optional<Layout> probe_layout(const uint8_t* ram,uint64_t sprite,bool& recognized_slot,
                                 const PromptTextureLayout& profile,bool include_directions,bool include_start){
    auto s=offset(sprite,0x38,4);if(!s)return {};
    auto bank=offset(word(ram,profile.bank_pointer),(maximum_index(profile)+1)*12,4);if(!bank)return {};
    auto descriptor=offset(word(ram,*s+0x14),12,4);if(!descriptor)return {};
    unsigned slot=4;
    for(unsigned n=0;n<2;++n)if(*descriptor==*bank+profile.descriptor_indices[n]*12)slot=n;
    if(include_directions&&profile.c_directions&&*descriptor==*bank+profile.c_directions->descriptor_index*12)slot=2;
    if(include_start&&profile.start_random&&*descriptor==*bank+profile.start_random->descriptor_index*12)slot=3;
    if(slot==4)return {};
    recognized_slot=true;
    if(word(ram,*descriptor)!=dimensions(slot) || word(ram,*descriptor+4)!=descriptor_attributes(profile,slot))return {};
    auto texture=offset(word(ram,*descriptor+8),texture_size(slot));
    // The exact Start descriptor is I4 (03030000), not color indexed.
    // Original4250C does not read its unused sprite+34 palette override.
    auto palette=slot==3?std::optional<uint32_t>{0}:offset(word(ram,*s+0x34),32,2);
    if(!texture||!palette)return {};
    return Layout{*descriptor,*texture,*palette,slot};
}
std::optional<std::string_view> short_label(PromptGlyphRequest request){
    // Explicit physical aliases for the original six-pixel font. Two characters
    // fit within each original16px icon cell; full names remain in Remap.
    const auto name=request.label;
    if(request.family==PromptGlyphFamily::Automatic || unsigned(request.family)>unsigned(PromptGlyphFamily::Keyboard))return {};
    if(request.family==PromptGlyphFamily::Keyboard&&name=="Left Shift")return "LS";
    if(name.size()==1 && ((name[0]>='A'&&name[0]<='Z')||(name[0]>='0'&&name[0]<='9')))return name;
    constexpr std::array<std::pair<std::string_view,std::string_view>,52> aliases{{
        {"Paddle 1","P1"},{"Paddle 2","P2"},{"Paddle 3","P3"},{"Paddle 4","P4"},
        {"paddle1","P1"},{"paddle2","P2"},{"paddle3","P3"},{"paddle4","P4"},
        {"PS","PS"},{"Xbox","XB"},{"Home","HM"},{"Capture","CP"},{"Share","SH"},{"Touch pad","TP"},{"Microphone","MC"},{"Mic","MC"},
        {"×","X"},{"Cross","X"},{"○","O"},{"Circle","O"},{"□","SQ"},{"Square","SQ"},{"△","TR"},{"Triangle","TR"},
        {"R←","RL"},{"R→","RR"},{"R↑","RU"},{"R↓","RD"},
        {"D←","DL"},{"D→","DR"},{"D↑","DU"},{"D↓","DD"},
        {"Menu","MN"},{"Options","OP"},{"Start","ST"},{"+","PL"},{"-","MI"},
        {"Left trigger","LT"},{"Right trigger","RT"},{"Touchpad","TP"},{"Return","EN"},{"Enter","EN"},{"Escape","ES"},{"View","VW"},{"Left stick","LS"},{"Right stick","RS"},{"Unbound","NA"},{"Space","SP"},{"Tab","TB"},{"Backspace","BS"},{"Down","DN"},{"Left","LF"}
    }};
    auto found=std::find_if(aliases.begin(),aliases.end(),[&](const auto& pair){return pair.first==name;});
    if(found!=aliases.end())return found->second;
    for(auto plain:{"LT","RT","LB","RB","LS","RS","L1","L2","L3","R1","R2","R3","ZL","ZR","PS","Up"})if(name==plain)return name;
    if(request.family==PromptGlyphFamily::Keyboard && name.size()==2&&name[0]=='F'&&name[1]>='1'&&name[1]<='9')return name;
    return {};
}
std::optional<std::array<int,2>> sprite_origin(const uint8_t* ram,uint32_t sprite,const PromptTextFallbackLayout& profile){
    const auto flags=word(ram,sprite+8);
    if(flags&(1u<<30))return {}; // A second texture has separate ownership/geometry.
    if((flags&(1u<<22)) && (word(ram,sprite+0x28)!=0x3F800000u||word(ram,sprite+0x2C)!=0x3F800000u))return {};
    const uint16_t viewport=half(ram,sprite+0x1C);
    // Clipped/flipped/wrapped draw modes require their own original-font proof.
    // Original80041B50 consumes only low viewport/anchor bits and clipping
    // bits2000/4000. Career sets8000; that bit is not a geometry input.
    if(viewport&~0x830Fu)return {};
    int x=int16_t(half(ram,sprite+0x20)),y=int16_t(half(ram,sprite+0x24));
    const uint32_t anchor=profile.viewport_table+(viewport&15)*16;
    if(viewport&0x100)x-=int16_t(half(ram,anchor));
    if(viewport&0x200)y-=int16_t(half(ram,anchor+4));
    return std::array<int,2>{x,y};
}
// Original801DF7B0 selects these exact prefix consumers, all using atlas141.
// Their neighboring action-label objects and original assets remain untouched.
struct SetplayConsumer {uint32_t address,bytes;const char* hash;};
constexpr std::array<SetplayConsumer,5> setplay_consumers{{
    {0x25EEA4,180,"84c3d983c5f32eb6d86d48da323564a9dce0399e09c9d91dffda4635cbdc8a84"},
    {0x25F384,144,"863d17b347b299924715b2fc806e9a11f0905b634f282ea1db5078cd7fae8866"},
    {0x25F84C,144,"601b536664bf9835db98ea7bc137acc44f78dac87a4cde484b459ba549ed7b5c"},
    {0x25FBAC,72,"f7d5b652cce51d4386b70260ee4ff995c99e526875d7359d4522a746441e366c"},
    {0x260230,84,"1e6ff687e9a6a191553f20e9dc911026df67f399479396cac7c7026897f5dd2d"}
}};
std::optional<PromptFontImageLayout> setplay_image(const uint8_t* ram,uint64_t sprite,
        const PromptTextureLayout& layout){
    if(!ram)return {};
    const auto object=offset(sprite,0x38,4);if(!object||!layout.field_setplay)return {};
    auto image=*layout.field_setplay;const auto consumer=word(ram,*object+0x30);
    if(consumer==(0x80000000u|image.consumer_address))return image;
    if(image.consumer_address!=0x25EA00||image.descriptor_index!=141||image.bank_pointer!=0x76AE4)return {};
    for(const auto& variant:setplay_consumers)if(consumer==(0x80000000u|variant.address)){
        image.consumer_address=variant.address;image.consumer_bytes=variant.bytes;
        image.consumer_sha256=variant.hash;return image;
    }
    return {};
}
// The owned field instruction images have a proven High path. Their
// coordinates stay in original logical320x240 space: original49158 doubles
// glyph rectangles and halves texture derivatives after font layout.
bool field_video_ready(const uint8_t* ram,uint32_t frame,uint32_t object,
        const PromptTextFallbackLayout& font,const PromptFontImageLayout& image){
    const auto mode=byte(ram,frame+0x12);
    if(mode==0)return half(ram,frame+0x14)==320&&half(ram,frame+0x16)==240;
    const bool start=image.consumer_address==0x25FC90;
    const bool pause=image.consumer_address==0x25EA00||
        std::any_of(setplay_consumers.begin(),setplay_consumers.end(),[&](const auto& v){return image.consumer_address==v.address;});
    if(mode!=1||frame!=0x13B418||font.frame_pointer!=0x9E02C||font.font_address!=0x352800||
       image.bank_pointer!=0x76AE4||(!start&&!pause)||
       object!=(start?0x13CF08u:0x13D8E0u)||byte(ram,object+4)!=1||byte(ram,object+5)!=(start?11:9)||
       half(ram,frame+0x14)!=640||half(ram,frame+0x16)!=544||word(ram,frame+0x18)!=0x80700000||
       byte(ram,frame+0x2E)!=6||byte(ram,frame+0x34)!=4||byte(ram,frame+0x3A)!=(pause?1:0))return false;
    return rom_detail::sha256_hex(read_bytes(ram,0x7AA008,0x2B4))==
        "62ff104079488a6d81386c421054368bde897818652c8d1365a597881342fe50"&&
        rom_detail::sha256_hex(read_bytes(ram,0x49158,0x2FC))==
        "bc5700fdd66b4771aaf2ef0ff78db7ffa409fc98f0240a049e0fc3227a209312";
}
bool handicap_consumer(const uint8_t* ram,uint64_t sprite,const PromptTextureLayout& layout){
    const auto object=offset(sprite,0x38,4);
    return ram&&object&&layout.bank_pointer==0x76B30&&word(ram,*object+48)==0x802AAFC0;
}
bool handicap_ready(const uint8_t* ram,uint64_t sprite,const PromptTextureLayout& layout){
    if(!handicap_consumer(ram,sprite,layout)||!layout.text_fallback)return false;
    const auto object=*offset(sprite,0x38,4);const auto& font=*layout.text_fallback;
    const auto origin=sprite_origin(ram,object,font);
    const auto bank=offset(word(ram,0x76B30),14*12,4);if(!bank)return false;
    const auto d=*bank+13*12;const auto texture=offset(word(ram,d+8),512);
    return origin&&(*origin)[0]==0&&(*origin)[1]==0&&byte(ram,object+4)==1&&byte(ram,object+5)==9&&
        word(ram,font.frame_pointer)==0x8013B418&&byte(ram,0x13B42A)==0&&word(ram,0x13B42C)==0x014000F0&&
        byte(ram,0x13B446)==6&&byte(ram,0x13B44C)==7&&word(ram,object+20)==(0x80000000u|d)&&
        word(ram,d)==0x00400010&&word(ram,d+4)==0x01090000&&texture&&
        rom_detail::sha256_hex(read_bytes(ram,*texture,512))=="c39348d1f605c8fc3cb4bf7c5ccf73e048368f6cb814a867441b3025fccabbda"&&
        rom_detail::sha256_hex(read_bytes(ram,0x2AAFC0,24))=="1b67dc38f067a3d9fd73104d9a93eee93d4ad5b9b5168db6111d373784c19e3a"&&
        rom_detail::sha256_hex(read_bytes(ram,font.font_address,font.font_bytes))==font.font_sha256;
}
struct ReplayConsumer {
    uint32_t object,index,dimensions,attributes,texture_bytes,address,bytes;
    const char* texture_hash;const char* consumer_hash;
};
constexpr std::array<ReplayConsumer,3> replay_consumers{{
    {0x13E1C8,23,0x00700018,0x01000000,1344,0x25BCA0,48,
     "bc49789bb8d21f3ad688796c70d9daf17ac7155504ada070acda2663ea14dc16",
     "eaedf29bf3b5dd9bd64c3d59dbe0f3e1e561bb984aa25da258934ae5aa4eba75"},
    {0x13E204,249,0x00500018,0x03030000,960,0x25BCD0,60,
     "af794ec8a6a1d9474fb68f6b59bad7b4a102371c9d481597193f711dfc9c9ce2",
     "e3228e17faf698ed8cb6071db3cc532453970b3ec2e65909b80c9bb50cc01672"},
    {0x13E0D8,249,0x00500018,0x03030000,960,0x25BE74,12,
     "af794ec8a6a1d9474fb68f6b59bad7b4a102371c9d481597193f711dfc9c9ce2",
     "8f6879b0e43eccbbd49ee7c19924a150fdac71ba5088f1948c3c07d2e5e1748c"}
}};
const ReplayConsumer* replay_consumer(const uint8_t* ram,uint64_t sprite,const PromptTextureLayout& layout){
    if(!ram)return nullptr;
    const auto object=offset(sprite,0x38,4);
    if(!object||!layout.field_setplay||layout.field_setplay->consumer_address!=0x25EA00)return nullptr;
    for(const auto& p:replay_consumers)if(*object==p.object&&word(ram,*object+0x30)==(0x80000000u|p.address))return &p;
    return nullptr;
}
bool replay_ready(const uint8_t* ram,const ReplayConsumer& p,const PromptTextureLayout& layout){
    if(!layout.text_fallback)return false;
    const auto& font=*layout.text_fallback;
    if(font.frame_pointer!=0x9E02C||word(ram,font.frame_pointer)!=0x8013B418||
       byte(ram,0x13B446)!=6||byte(ram,0x13B44C)!=4||byte(ram,p.object+4)!=1||byte(ram,p.object+5)!=11)return false;
    const auto origin=sprite_origin(ram,p.object,font);if(!origin||(*origin)[0]||(*origin)[1])return false;
    const auto mode=byte(ram,0x13B42A);
    if(mode==0){if(word(ram,0x13B42C)!=0x014000F0)return false;}
    else if(mode!=1||word(ram,0x13B42C)!=0x02800220||word(ram,0x13B430)!=0x80700000||
        rom_detail::sha256_hex(read_bytes(ram,0x7AA008,0x2B4))!="62ff104079488a6d81386c421054368bde897818652c8d1365a597881342fe50"||
        rom_detail::sha256_hex(read_bytes(ram,0x49158,0x2FC))!="bc5700fdd66b4771aaf2ef0ff78db7ffa409fc98f0240a049e0fc3227a209312")return false;
    const auto bank=offset(word(ram,0x76AE4),(p.index+1)*12,4);if(!bank)return false;
    const auto d=*bank+p.index*12;const auto texture=offset(word(ram,d+8),p.texture_bytes);
    return word(ram,p.object+20)==(0x80000000u|d)&&word(ram,d)==p.dimensions&&word(ram,d+4)==p.attributes&&texture&&
        rom_detail::sha256_hex(read_bytes(ram,*texture,p.texture_bytes))==p.texture_hash&&
        rom_detail::sha256_hex(read_bytes(ram,p.address,p.bytes))==p.consumer_hash&&
        rom_detail::sha256_hex(read_bytes(ram,font.font_address,font.font_bytes))==font.font_sha256&&
        rom_detail::sha256_hex(read_bytes(ram,0x1E7E58,408))=="9bf28d5f53e3b19c6e0c10173b48d811047e55208839cf9657d20e56beb4d97e";
}
std::optional<std::string> start_phrase(PromptGlyphRequest);
PromptSpriteAction sprite_action(unsigned slot){return slot==0?PromptSpriteAction::A:slot==1?PromptSpriteAction::B:slot==2?PromptSpriteAction::CDirections:PromptSpriteAction::StartRandom;}
std::optional<PromptSpriteResult> text_fallback(const uint8_t* ram,uint64_t sprite,unsigned slot,
        const PromptTextureLayout& profile,const std::array<PromptGlyphRequest,2>& labels,
        const std::array<PromptGlyphRequest,4>* directions,const PromptGlyphRequest* start,uint16_t expected_u=0){
    if(!profile.text_fallback)return {};
    const auto& text=*profile.text_fallback;
    const auto frame=offset(word(ram,text.frame_pointer),0x18,4);
    if(!frame||byte(ram,*frame+0x12)!=0||half(ram,*frame+0x14)!=320||half(ram,*frame+0x16)!=240)return {};
    if(rom_detail::sha256_hex(read_bytes(ram,text.font_address,text.font_bytes))!=text.font_sha256)return {};
    const auto s=offset(sprite,0x38,4);if(!s)return {};
    const auto origin=sprite_origin(ram,*s,text);if(!origin)return {};
    const unsigned count=slot==2?4:1;
    const auto segments=offset(word(ram,*s+0x30),count*12,2);if(!segments)return {};
    if(slot==2 && (!directions||rom_detail::sha256_hex(read_bytes(ram,*segments,48))!=profile.c_directions->fallback_segments_sha256))return {};
    if(slot==3){
        const auto hash=rom_detail::sha256_hex(read_bytes(ram,*segments,12));
        if(!start||std::find(profile.start_random->consumer_sha256.begin(),profile.start_random->consumer_sha256.end(),hash)==profile.start_random->consumer_sha256.end())return {};
    }
    PromptSpriteResult result;result.status=PromptSpriteStatus::TextFallback;
    result.action=sprite_action(slot);
    for(unsigned n=0;n<count;++n){
        const auto p=*segments+n*12;const unsigned tag=byte(ram,p);
        if(byte(ram,p+1)!=(slot==3?96:16)||byte(ram,p+2)!=16||half(ram,p+10)!=0)return {};
        if(slot!=2 && ((tag!=0x80&&tag!=0x90)||half(ram,p+8)!=expected_u))return {};
        if(slot==2 && (tag!=(n==0?0x10u:n==3?0x80u:0u)||half(ram,p+8)!=n*512))return {};
        std::optional<std::string> label;
        if(slot==3)label=start_phrase(*start);
        else if(auto name=short_label(slot<2?labels[slot]:(*directions)[n]))label=std::string(*name);
        if(!label)return {};
        const int x=(*origin)[0]+int16_t(half(ram,p+4)),y=(*origin)[1]+int16_t(half(ram,p+6))+(slot==3?-1:2);
        if(x<0||y<0||x+int(label->size())*6>320||y+12>240)return {};
        result.lines[n]={int16_t(x),int16_t(y),std::string(*label)};
    }
    result.line_count=uint8_t(count);return result;
}
#include "gdb_prompt_glyphs.inc"
std::optional<std::string> start_phrase(PromptGlyphRequest request){
    if(request.family==PromptGlyphFamily::Automatic||unsigned(request.family)>unsigned(PromptGlyphFamily::Keyboard))return {};
    const auto source=request.label;std::string name(source);
    const bool artist=std::any_of(artwork_glyphs.begin(),artwork_glyphs.end(),[&](const auto& g){return g.family==request.family&&g.label==source;});
    if(!artist&&!short_label(request))return {};
    constexpr std::array<std::pair<std::string_view,std::string_view>,12> aliases{{
        {"+","Plus"},{"-","Minus"},{"×","Cross"},{"○","Circle"},{"□","Square"},{"△","Triangle"},
        {"Return","Enter"},{"Microphone","Mic"},{"Left stick","LS"},{"Right stick","RS"},{"Unbound","Unbound"},{"Escape","Esc"}
    }};
    for(const auto& alias:aliases)if(source==alias.first)name=alias.second;
    if(name.size()>9){if(auto brief=short_label(request))name=*brief;else return {};}
    if(name.empty()||name.find_first_not_of("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ")!=std::string::npos)return {};
    return name+" Random";
}
}
std::optional<PixelBytes> glyph_pixels(PromptGlyphRequest request,std::span<const uint8_t,32> palette){
    const auto glyph=std::find_if(artwork_glyphs.begin(),artwork_glyphs.end(),[&](const auto& candidate){
        return candidate.family==request.family && candidate.label==request.label;
    });
    if(glyph==artwork_glyphs.end())return {};
    struct Color {int r,g,b;bool opaque;};
    std::array<Color,16> target{};int transparent=-1;
    for(unsigned n=0;n<target.size();++n){
        const unsigned value=(unsigned(palette[n*2])<<8)|palette[n*2+1];
        target[n]={int(((value>>11)&31)*255/31),int(((value>>6)&31)*255/31),int(((value>>1)&31)*255/31),bool(value&1)};
        if(!target[n].opaque && transparent<0)transparent=int(n);
    }
    if(transparent<0)return {};
    auto luminance=[](const Color& c){return c.r*77+c.g*150+c.b*29;};
    std::array<uint8_t,artwork_colors.size()> mapping{};
    for(unsigned n=0;n<artwork_colors.size();++n){
        const auto value=artwork_colors[n];Color source{int(value>>24),int((value>>16)&255),int((value>>8)&255),bool(value&255)};
        if(!source.opaque){mapping[n]=uint8_t(transparent);continue;}
        int best=-1,best_luma=INT_MAX;uint64_t best_rgb=UINT64_MAX;
        for(unsigned i=0;i<target.size();++i){
            if(!target[i].opaque)continue;
            const auto& c=target[i];const int luma=std::abs(luminance(source)-luminance(c));
            const int r=source.r-c.r,g=source.g-c.g,b=source.b-c.b;
            const uint64_t rgb=uint64_t(r*r)*77+uint64_t(g*g)*150+uint64_t(b*b)*29;
            if(luma<best_luma || (luma==best_luma && rgb<best_rgb)){best=int(i);best_luma=luma;best_rgb=rgb;}
        }
        if(best<0)return {};
        mapping[n]=uint8_t(best);
    }
    PixelBytes pixels{};const auto& tile=artwork_tiles[glyph->tile];
    for(unsigned n=0;n<pixels.size();++n)pixels[n]=uint8_t((mapping[tile[n*2]]<<4)|mapping[tile[n*2+1]]);
    return pixels;
}
std::optional<PixelBytes> glyph_pixels(PromptGlyphRequest request,
        std::span<const uint8_t,32> palette,std::span<const uint8_t,128> original_cell){
    auto source=glyph_pixels(request,palette);if(!source)return {};
    auto index=[](auto pixels,unsigned x,unsigned y){const auto p=pixels[y*8+x/2];return (x&1)?p&15:p>>4;};
    auto opaque=[&](unsigned i){return (palette[i*2+1]&1)!=0;};
    struct Bounds {unsigned left{16},top{16},right{},bottom{};};
    auto bounds=[&](auto pixels){Bounds b;
        for(unsigned y=0;y<16;++y)for(unsigned x=0;x<16;++x)if(opaque(index(pixels,x,y))){
            b.left=std::min(b.left,x);b.top=std::min(b.top,y);
            b.right=std::max(b.right,x);b.bottom=std::max(b.bottom,y);}
        return b;};
    const auto target=bounds(original_cell),art=bounds(*source);
    if(target.left==16||art.left==16)return {};
    const unsigned sw=art.right-art.left+1,sh=art.bottom-art.top+1;
    const unsigned tw=target.right-target.left+1,th=target.bottom-target.top+1;
    unsigned width=sw,height=sh;
    if(sw>tw||sh>th){
        if(tw*sh<=th*sw){width=tw;height=std::max(1u,sh*tw/sw);}
        else{height=th;width=std::max(1u,sw*th/sh);}
    }
    const unsigned left=target.left+(tw-width)/2,top=target.top+(th-height)/2;
    unsigned transparent=0;while(transparent<16&&opaque(transparent))++transparent;
    if(transparent==16)return {};
    PixelBytes result;result.fill(uint8_t(transparent*17));
    // Center-sampled nearest neighbor retains only authentic source pixels.
    for(unsigned y=0;y<height;++y)for(unsigned x=0;x<width;++x){
        const auto color=index(*source,art.left+(2*x+1)*sw/(2*width),art.top+(2*y+1)*sh/(2*height));
        auto& out=result[(top+y)*8+(left+x)/2];
        out=uint8_t(((left+x)&1)?(out&0xF0)|color:(out&0x0F)|(color<<4));
    }
    return result;
}
namespace {
std::optional<PixelBytes> cell_glyph(PromptGlyphRequest request,
        std::span<const uint8_t,32> palette,std::span<const uint8_t> original,
        unsigned row_bytes,unsigned cell){
    if(row_bytes<8||cell*8+8>row_bytes||original.size()<row_bytes*16)return {};
    PixelBytes pixels;
    for(unsigned y=0;y<16;++y)std::copy_n(original.begin()+y*row_bytes+cell*8,8,pixels.begin()+y*8);
    return glyph_pixels(request,palette,pixels);
}
}
TextureGuard::TextureGuard(PromptTextureLayout layout):layout_(std::move(layout)){
    auto valid_hash=[](const std::string& hash){return hash.size()==64&&hash.find_first_not_of("0123456789abcdef")==std::string::npos;};
    if(layout_.bank_pointer>0x800000-4 || layout_.bank_pointer%4 ||
       layout_.descriptor_indices[0]==layout_.descriptor_indices[1] || maximum_index(layout_)>=1024)
        throw std::invalid_argument("Invalid prompt texture layout");
    if(layout_.c_directions&&(layout_.c_directions->descriptor_index==layout_.descriptor_indices[0]||layout_.c_directions->descriptor_index==layout_.descriptor_indices[1]||!valid_hash(layout_.c_directions->fallback_segments_sha256)))
        throw std::invalid_argument("Invalid direction prompt layout");
    for(unsigned slot=0;slot<(layout_.c_directions?3u:2u);++slot){
        const auto& h=expected_hashes(layout_,slot);
        if(!valid_hash(h.texture)||!valid_hash(h.palette))throw std::invalid_argument("Invalid prompt asset hash");
    }
    if(layout_.start_random){
        const auto& st=*layout_.start_random;
        if(st.descriptor_index==layout_.descriptor_indices[0]||st.descriptor_index==layout_.descriptor_indices[1]||
           (layout_.c_directions&&st.descriptor_index==layout_.c_directions->descriptor_index)||
           !valid_hash(st.expected.texture)||!valid_hash(st.expected.palette)||
           std::any_of(st.consumer_sha256.begin(),st.consumer_sha256.end(),[&](const auto& hash){return !valid_hash(hash);}))
            throw std::invalid_argument("Invalid Start image layout");
    }
    if(layout_.ab_pair){
        const auto& p=*layout_.ab_pair;
        if(p.bank_pointer>0x800000-4||p.bank_pointer%4||p.descriptor_index>=1024||!valid_hash(p.expected.texture)||!valid_hash(p.expected.palette))
            throw std::invalid_argument("Invalid A/B pair layout");
    }
    for(const auto* hint:{&layout_.country_shoulders,&layout_.name_directions,&layout_.name_ab[0],&layout_.name_ab[1]})if(*hint){
        const auto& p=**hint;
        if(p.bank_pointer>0x800000-4||p.bank_pointer%4||p.descriptor_index>=1024||
           !valid_hash(p.expected.texture)||!valid_hash(p.expected.palette)||!valid_hash(p.consumer_sha256))
            throw std::invalid_argument("Invalid packed prompt layout");
    }
    if(layout_.team_regions){
        const auto& p=*layout_.team_regions;
        if(p.bank_pointer>0x800000-4||p.bank_pointer%4||p.descriptor_index>=1023||
           p.consumer_address>0x800000-60||p.consumer_address%4||p.owner_mode_address>=0x800000||
           !valid_hash(p.texture_sha256[0])||!valid_hash(p.texture_sha256[1])||
           !valid_hash(p.palette_sha256)||!valid_hash(p.consumer_sha256)||
           p.font_tint_address>0x800000-48||!valid_hash(p.font_tint_sha256)||p.font_tint_selector!=4||
           (p.single_consumer_address&&(p.single_consumer_address>0x800000-24||p.single_consumer_address%4||!valid_hash(p.single_consumer_sha256))))
            throw std::invalid_argument("Invalid region prompt layout");
    }
    for(const auto& candidate:layout_.team_directions)if(candidate){const auto&p=*candidate;
        if(!layout_.c_directions||p.segments==0||p.segments>8||p.consumer_address>0x800000-p.segments*12||p.consumer_address%4||!valid_hash(p.consumer_sha256))throw std::invalid_argument("Invalid team direction prompt layout");}
    for(const auto* candidate:{&layout_.field_start,&layout_.field_setplay})if(*candidate){
        const auto& p=**candidate;
        if(p.bank_pointer>0x800000-4||p.bank_pointer%4||p.descriptor_index>=1024||
           p.texture_bytes==0||p.texture_bytes>0x10000||
           p.consumer_bytes!=(candidate==&layout_.field_start?36u:120u)||
           (candidate==&layout_.field_setplay&&(p.owner_port_address==0||p.owner_port_address>=0x800000))||
           p.consumer_address>0x800000-p.consumer_bytes||p.consumer_address%4||
           !valid_hash(p.texture_sha256)||!valid_hash(p.consumer_sha256))
            throw std::invalid_argument("Invalid field instruction image layout");
    }
    if(layout_.text_fallback){
        const auto& t=*layout_.text_fallback;
        if(t.viewport_table>0x800000-256||t.viewport_table%2||t.frame_pointer>0x800000-4||t.frame_pointer%4||t.font_bytes==0||t.font_bytes>0x10000||t.font_address>0x800000-t.font_bytes||!valid_hash(t.font_sha256))
            throw std::invalid_argument("Invalid prompt font layout");
    }
}
void TextureGuard::warn(){if(!warned_){std::fprintf(stderr,"[Prompts] A recognized physical prompt could not be adapted safely; inspect native prompt diagnostics.\n");warned_=true;}}
std::optional<PromptSpriteResult> TextureGuard::prepare_pair(uint8_t* ram,uint64_t sprite,
                                                        const std::array<PromptGlyphRequest,2>& labels){
    if(!layout_.ab_pair)return {};
    const auto& profile=*layout_.ab_pair;
    const auto object=offset(sprite,0x38,4);if(!object)return {};
    const auto bank=offset(word(ram,profile.bank_pointer),(profile.descriptor_index+1)*12,4);if(!bank)return {};
    const auto descriptor=offset(word(ram,*object+0x14),12,4);
    if(!descriptor||*descriptor!=*bank+profile.descriptor_index*12)return {};
    PromptSpriteResult result;result.status=PromptSpriteStatus::RejectedKnown;
    if(word(ram,*descriptor)!=0x00200010u||word(ram,*descriptor+4)!=profile.descriptor_attributes){warn();return result;}
    const auto texture=offset(word(ram,*descriptor+8),256),palette_address=offset(word(ram,*object+0x34),32,2);
    const auto segment=offset(word(ram,*object+0x30),12,2);
    if(!texture||!palette_address||!segment){warn();return result;}
    const auto tag=byte(ram,*segment);const auto u=half(ram,*segment+8);
    if((tag!=0x80&&tag!=0x90)||byte(ram,*segment+1)!=16||byte(ram,*segment+2)!=16||half(ram,*segment+10)!=0||(u!=0&&u!=512)){warn();return result;}
    const unsigned action=u/512;result.action=action==0?PromptSpriteAction::A:PromptSpriteAction::B;
    const auto palette=read<32>(ram,*palette_address);const auto pixels=read_bytes(ram,*texture,256);
    if(rom_detail::sha256_hex(palette)!=profile.expected.palette){warn();return result;}
    auto& saved=pair_cache_;
    const bool ours=saved.valid&&saved.descriptor==*descriptor&&saved.texture==*texture&&saved.palette==*palette_address&&pixels==saved.applied;
    if(!ours){
        if(rom_detail::sha256_hex(pixels)!=profile.expected.texture){warn();return result;}
        saved={*descriptor,*texture,*palette_address,pixels,{},true};
    }
    const auto a=cell_glyph(labels[0],palette,saved.original,16,0),b=cell_glyph(labels[1],palette,saved.original,16,1);
    if(!a||!b){
        if(ours)write(ram,*texture,saved.original);
        saved.valid=false;
        if(auto proposal=text_fallback(ram,sprite,action,layout_,labels,nullptr,nullptr,u))return *proposal;
        warn();return result;
    }
    auto generated=saved.original;
    for(unsigned row=0;row<16;++row){
        std::copy_n(a->begin()+row*8,8,generated.begin()+row*16);
        std::copy_n(b->begin()+row*8,8,generated.begin()+row*16+8);
    }
    saved.applied=std::move(generated);write(ram,*texture,saved.applied);result.status=PromptSpriteStatus::Applied;return result;
}
void TextureGuard::restore_pair(uint8_t* ram){
    auto& saved=pair_cache_;if(!saved.valid||!layout_.ab_pair)return;
    const auto& profile=*layout_.ab_pair;
    const auto bank=offset(word(ram,profile.bank_pointer),(profile.descriptor_index+1)*12,4);
    const bool same=bank&&saved.descriptor==*bank+profile.descriptor_index*12
        &&word(ram,saved.descriptor)==0x00200010u
        &&word(ram,saved.descriptor+4)==profile.descriptor_attributes
        &&offset(word(ram,saved.descriptor+8),256)==saved.texture;
    if(same&&read_bytes(ram,saved.texture,256)==saved.applied
       &&rom_detail::sha256_hex(read<32>(ram,saved.palette))==profile.expected.palette)
        write(ram,saved.texture,saved.original);
    saved.valid=false;
}
bool TextureGuard::font_image_ready(const uint8_t* ram,uint64_t sprite,const PromptFontImageLayout& p) const{
    if(!ram||!layout_.text_fallback)return false;
    const auto& font=*layout_.text_fallback;
    const auto object=offset(sprite,0x38,4);if(!object)return false;
    const auto bank=offset(word(ram,p.bank_pointer),(p.descriptor_index+1)*12,4);
    if(!bank||word(ram,*object+0x14)!=(0x80000000u|(*bank+p.descriptor_index*12))||
       word(ram,*object+0x30)!=(0x80000000u|p.consumer_address))return false;
    const auto d=*bank+p.descriptor_index*12;
    const auto texture=offset(word(ram,d+8),p.texture_bytes);
    if(word(ram,d)!=p.dimensions||word(ram,d+4)!=p.descriptor_attributes||!texture||
       rom_detail::sha256_hex(read_bytes(ram,*texture,p.texture_bytes))!=p.texture_sha256||
       rom_detail::sha256_hex(read_bytes(ram,p.consumer_address,p.consumer_bytes))!=p.consumer_sha256)return false;
    const auto frame=offset(word(ram,font.frame_pointer),0x18,4);
    if(!frame||!field_video_ready(ram,*frame,*object,font,p)||
       rom_detail::sha256_hex(read_bytes(ram,font.font_address,font.font_bytes))!=font.font_sha256)return false;
    const auto origin=sprite_origin(ram,*object,font);
    return origin&&(*origin)[0]==0&&(*origin)[1]==0;
}
std::optional<unsigned> TextureGuard::sprite_port(const uint8_t* ram,uint64_t sprite,
        std::optional<unsigned> active_port) const{
    if(active_port&&*active_port<4&&handicap_ready(ram,sprite,layout_))return active_port;
    if(const auto p=replay_consumer(ram,sprite,layout_);p&&active_port&&*active_port<4&&replay_ready(ram,*p,layout_))return active_port;
    if(const auto image=setplay_image(ram,sprite,layout_);image&&font_image_ready(ram,sprite,*image)){
        // Original801DDD5C records the controller that opened pause as port+1.
        const auto selected=byte(ram,layout_.field_setplay->owner_port_address);
        return selected>=1&&selected<=4?std::optional<unsigned>{selected-1}:std::nullopt;
    }
    // This single tooltip is global: original801DDD5C accepts Start on every
    // port. Other menu sprites retain their independently defined ownership.
    if(active_port&&*active_port<4&&layout_.field_start&&font_image_ready(ram,sprite,*layout_.field_start))return active_port;
    return {};
}
std::optional<PromptSpriteResult> TextureGuard::prepare_field_pause(uint8_t* ram,uint64_t sprite,
        const std::array<PromptGlyphRequest,3>* shoulders){
    const auto image=setplay_image(ram,sprite,layout_);
    if(!image||!shoulders)return {};
    const auto& p=*image;const auto object=offset(sprite,0x38,4);
    if(!object||word(ram,*object+0x30)!=(0x80000000u|p.consumer_address))return {};
    const auto bank=offset(word(ram,p.bank_pointer),(p.descriptor_index+1)*12,4);
    if(!bank||word(ram,*object+0x14)!=(0x80000000u|(*bank+p.descriptor_index*12)))return {};
    PromptSpriteResult result;result.status=PromptSpriteStatus::RejectedKnown;result.action=PromptSpriteAction::SetplayControls;
    const auto owner=sprite_port(ram,sprite);if(!owner)return result;
    if((*shoulders)[1].port!=*owner||(*shoulders)[2].port!=*owner)return result;
    const auto z=short_label((*shoulders)[1]),r=short_label((*shoulders)[2]);
    if(!z||!r||z->size()>2||r->size()>2)return result;
    // Original action-label object is separate. Keep its text and all atlas
    // bytes intact; replace only this exact four-prefix sprite transaction.
    // Original font2 Y2/3 emits8px rows starting one pixel below inputY.
    result.lines={{{int16_t(109+(40-int(z->size())*6)/2),191,std::string(*z),8},
                   {int16_t(109+(40-int(r->size())*6)/2),199,std::string(*r),8},
                   {74,207,"1 2 Pass Button",8},{86,215,"T Pass Button",8}}};
    result.line_count=4;
    // Center each replacement inside the original prefix cell. Logical action
    // labels remain short enough to preserve the adjacent original action text.
    auto line=[&](int left,int right,int y,std::string label){
        result.lines[result.line_count++]={int16_t(left+(right-left-int(label.size())*6)/2),int16_t(y),std::move(label),8};
    };
    if(p.consumer_address!=0x25EA00){
        result.line_count=0;
        switch(p.consumer_address){
        case 0x25EEA4:
            line(27,62,191,std::string(*z));line(27,62,199,std::string(*r));
            line(28,89,206,"1 2 Pass");line(27,86,215,"T Pass");
            line(130,186,199,"Dash");line(207,242,191,std::string(*z));break;
        case 0x25F384:
            line(27,62,191,std::string(*r));line(28,90,199,"1 2 Pass");
            line(27,86,207,"T Pass");line(207,242,191,std::string(*z));
            line(150,206,207,"Dash");break;
        case 0x25F84C:
            line(45,80,191,std::string(*z));line(45,80,199,std::string(*r));
            line(38,100,206,"1 2 Pass");line(37,96,215,"T Pass");
            line(182,238,199,"Dash");break;
        case 0x25FBAC:
            line(117,152,191,std::string(*z));line(109,168,207,"T Pass");break;
        case 0x260230:
            line(101,137,194,std::string(*r));line(94,157,203,"1 2 Pass");
            line(97,157,212,"T Pass");break;
        default:return result;
        }
    }
    result.status=PromptSpriteStatus::TextFallback;return result;
}
std::optional<PromptSpriteResult> TextureGuard::prepare_field_start(uint8_t* ram,uint64_t sprite,
        const PromptGlyphRequest* start){
    if(!layout_.field_start||!start)return {};
    const auto& p=*layout_.field_start;const auto object=offset(sprite,0x38,4);
    if(!object||word(ram,*object+0x30)!=(0x80000000u|p.consumer_address))return {};
    const auto bank=offset(word(ram,p.bank_pointer),(p.descriptor_index+1)*12,4);
    if(!bank||word(ram,*object+0x14)!=(0x80000000u|(*bank+p.descriptor_index*12)))return {};
    PromptSpriteResult result;result.status=PromptSpriteStatus::RejectedKnown;result.action=PromptSpriteAction::StartControls;
    // I4 ownership ignores unused sprite palette overrides.
    if(start->port>=4||!font_image_ready(ram,sprite,p))return result;
    auto phrase=start_phrase(*start);if(!phrase)return result;
    phrase->resize(phrase->size()-7); // The shared formatter's owned " Random" suffix.
    if(start->label=="Return")*phrase="Return";
    if(phrase->size()>8){const auto brief=short_label(*start);if(!brief)return result;*phrase=*brief;}
    if(phrase->empty()||phrase->size()>8)return result;
    // The owned Start cell is116..164,y19..27. Font17..29 stays inside
    // its original panel band; separate GameControls starts at172,y19.
    result.lines[0]={int16_t(116+(48-int(phrase->size())*6)/2),17,std::move(*phrase)};
    result.line_count=1;result.status=PromptSpriteStatus::TextFallback;return result;
}
std::optional<PromptSpriteResult> TextureGuard::prepare_regions(uint8_t* ram,uint64_t sprite,
        const std::array<PromptGlyphRequest,3>* shoulders){
    if(!layout_.team_regions||!shoulders)return {};
    const auto& p=*layout_.team_regions;
    const auto object=offset(sprite,0x38,4);if(!object)return {};
    // Other original consumers share these atlases; the exact fixed consumer
    // address identifies this region control before classifying a known prompt.
    const bool single=p.single_consumer_address&&word(ram,*object+0x30)==(0x80000000u|p.single_consumer_address);
    if(!single&&word(ram,*object+0x30)!=(0x80000000u|p.consumer_address))return {};
    const auto bank=offset(word(ram,p.bank_pointer),(p.descriptor_index+2)*12,4);
    if(!bank||word(ram,*object+0x14)!=(0x80000000u|(*bank+(p.descriptor_index+unsigned(single))*12)))return {};
    PromptSpriteResult result;result.status=PromptSpriteStatus::RejectedKnown;result.action=PromptSpriteAction::Shoulders;
    // Original callbacks802A135C/802A14F0 route both card indices to port0
    // only for mode1. Other modes require separately proven per-card owners.
    if(byte(ram,p.owner_mode_address)!=p.owner_mode_value||
       ((*shoulders)[0].port!=0||(*shoulders)[2].port!=0))return result;
    if(rom_detail::sha256_hex(read_bytes(ram,single?p.single_consumer_address:p.consumer_address,single?24:60))!=(single?p.single_consumer_sha256:p.consumer_sha256)||
       rom_detail::sha256_hex(read_bytes(ram,p.font_tint_address,48))!=p.font_tint_sha256)return result;
    const auto palette=offset(word(ram,*object+0x34),32,2);
    if(!palette||rom_detail::sha256_hex(read<32>(ram,*palette))!=p.palette_sha256)return result;
    for(unsigned n=0;n<2;++n){
        const uint32_t d=*bank+(p.descriptor_index+n)*12;
        if(word(ram,d)!=0x00800020||word(ram,d+4)!=0x01000000)return result;
        const auto texture=offset(word(ram,d+8),2048);
        if(!texture||rom_detail::sha256_hex(read_bytes(ram,*texture,2048))!=p.texture_sha256[n])return result;
    }
    if(!layout_.text_fallback)return result;
    const auto& font=*layout_.text_fallback;const auto frame=offset(word(ram,font.frame_pointer),0x18,4);
    if(!frame||byte(ram,*frame+0x12)||half(ram,*frame+0x14)!=320||half(ram,*frame+0x16)!=240||
       rom_detail::sha256_hex(read_bytes(ram,font.font_address,font.font_bytes))!=font.font_sha256)return result;
    const auto origin=sprite_origin(ram,*object,font);
    if(!origin||(*origin)[0]||(*origin)[1])return result;
    // Native-size outlined glyphs flank the unchanged heading. Align visible
    // artwork ink, since shoulder tiles have different transparent top padding.
    bool has_art=true;std::array<std::string_view,3> brief;
    // The visible region instructions intentionally name only the two bumper
    // actions. Z remains bound and usable, without duplicating this prompt.
    for(unsigned n:{0u,2u}){const auto label=short_label((*shoulders)[n]);if(!label||label->size()>2)return result;brief[n]=*label;
        has_art&=std::any_of(artwork_glyphs.begin(),artwork_glyphs.end(),[&](const auto& g){
            return g.family==(*shoulders)[n].family&&g.label==(*shoulders)[n].label;});}
    // Rare optional remaps such as rear paddles have no licensed tile. Retain
    // truthful physical names through the original font instead of inventing art.
    const int xs[]{44,128,179,263},single_xs[]{101,184};
    if(!has_art){
        for(unsigned n=0;n<(single?2u:4u);++n){const auto label=brief[(n%2)*2];
            result.lines[n]={int16_t((single?single_xs[n]:xs[n])+(16-int(label.size())*6)/2),int16_t(single?60:53),std::string(label),12,p.font_tint_selector};}
        result.line_count=single?2:4;result.status=PromptSpriteStatus::TextFallback;return result;}
    for(unsigned n=0;n<(single?2u:4u);++n){const auto& request=(*shoulders)[(n%2)*2];
        const auto tile=std::find_if(artwork_glyphs.begin(),artwork_glyphs.end(),[&](const auto&g){return g.family==request.family&&g.label==request.label;});
        int top=16,bottom=-1;for(unsigned i=0;i<256;++i)if(artwork_tiles[tile->tile][i]){top=std::min(top,int(i/16));bottom=std::max(bottom,int(i/16));}
        const int y=((single?131:117)-top-bottom)/2;
        result.icons[n]={int16_t(single?single_xs[n]:xs[n]),int16_t(y),request.family,std::string(request.label),request.port,16,16};}
    result.icon_count=single?2:4;result.status=PromptSpriteStatus::TextFallback;return result;
}
std::optional<PromptSpriteResult> TextureGuard::prepare_packed(uint8_t* ram,uint64_t sprite,
        const std::array<PromptGlyphRequest,2>& labels,const std::array<PromptGlyphRequest,4>* directions,const std::array<PromptGlyphRequest,3>* shoulders){
    const auto object=offset(sprite,0x38,4);if(!object)return {};
    for(unsigned kind=0;kind<4;++kind){
        const bool name=kind==1,face=kind>=2,image=name||face;
        const auto& candidate=face?layout_.name_ab[kind-2]:name?layout_.name_directions:layout_.country_shoulders;
        if(!candidate || (!face && (name?!directions:!shoulders)))continue;
        const auto& p=*candidate;
        const auto bank=offset(word(ram,p.bank_pointer),(p.descriptor_index+1)*12,4);
        if(!bank || word(ram,*object+0x14)!=(0x80000000u|(*bank+p.descriptor_index*12)))continue;
        PromptSpriteResult rejected;rejected.status=PromptSpriteStatus::RejectedKnown;
        rejected.action=face?(kind==2?PromptSpriteAction::A:PromptSpriteAction::B):name?PromptSpriteAction::CDirections:PromptSpriteAction::Shoulders;
        const auto descriptor=*bank+p.descriptor_index*12;
        const uint32_t size=face?128:name?512:1024,consumer_size=face?12:name?48:24;
        if(word(ram,descriptor)!=p.dimensions||word(ram,descriptor+4)!=p.descriptor_attributes)return rejected;
        const auto texture=offset(word(ram,descriptor+8),size),palette=offset(word(ram,*object+0x34),32,2);
        const auto segments=offset(word(ram,*object+0x30),consumer_size,2);
        if(!texture||!palette||!segments ||
           rom_detail::sha256_hex(read_bytes(ram,*segments,consumer_size))!=p.consumer_sha256)return rejected;
        const auto colors=read<32>(ram,*palette);
        if(rom_detail::sha256_hex(colors)!=p.expected.palette)return rejected;
        const auto pixels=read_bytes(ram,*texture,size);
        auto& saved=face?name_ab_cache_[kind-2]:name_cache_;
        const bool ours=image&&saved.valid&&saved.descriptor==descriptor&&saved.texture==*texture&&
            saved.palette==*palette&&pixels==saved.applied;
        if(!ours&&rom_detail::sha256_hex(pixels)!=p.expected.texture)return rejected;
        if(image){
            if(!ours)saved={descriptor,*texture,*palette,pixels,{},true};
            auto generated=saved.original;bool available=true;
            // The original four-cell image is Right,Left,Up,Down; requests are
            // logical Left,Right,Up,Down. Preserve every original segment UV.
            constexpr unsigned actions[]={1,0,2,3};
            for(unsigned cell=0;cell<(face?1u:4u);++cell){
                auto glyph=cell_glyph(face?labels[kind-2]:(*directions)[actions[cell]],colors,saved.original,face?8:32,cell);
                if(!glyph){available=false;break;}
                for(unsigned y=0;y<16;++y)std::copy_n(glyph->begin()+y*8,8,generated.begin()+y*(face?8:32)+cell*8);
            }
            if(available){saved.applied=std::move(generated);write(ram,*texture,saved.applied);
                auto result=rejected;result.status=PromptSpriteStatus::Applied;return result;}
            if(ours)write(ram,*texture,saved.original);
            saved.valid=false;
        }
        if(!layout_.text_fallback)return rejected;
        const auto& text=*layout_.text_fallback;
        const auto frame=offset(word(ram,text.frame_pointer),0x18,4);
        if(!frame||byte(ram,*frame+0x12)!=0||half(ram,*frame+0x14)!=320||half(ram,*frame+0x16)!=240||
           rom_detail::sha256_hex(read_bytes(ram,text.font_address,text.font_bytes))!=text.font_sha256)return rejected;
        const auto origin=sprite_origin(ram,*object,text);if(!origin)return rejected;
        auto result=rejected;result.status=PromptSpriteStatus::TextFallback;
        result.line_count=name?4:1;
        if(face){
            const auto label=short_label(labels[kind-2]);if(!label)return rejected;
            result.lines[0]={int16_t((*origin)[0]+int16_t(half(ram,*segments+4))),
                int16_t((*origin)[1]+int16_t(half(ram,*segments+6))+2),std::string(*label)};
        }else if(name){
            constexpr unsigned actions[]={1,0,3,2}; // Exact original consumer order.
            for(unsigned n=0;n<4;++n){
                const auto label=short_label((*directions)[actions[n]]);if(!label)return rejected;
                const auto segment=*segments+n*12;
                result.lines[n]={int16_t((*origin)[0]+int16_t(half(ram,segment+4))),
                    int16_t((*origin)[1]+int16_t(half(ram,segment+6))+2),std::string(*label)};
            }
        }else{
            std::string label;
            for(const auto& request:*shoulders){auto brief=short_label(request);if(!brief)return rejected;
                if(!label.empty())label+=' ';
                label+=*brief;}
            result.lines[0]={int16_t((*origin)[0]+int16_t(half(ram,*segments+4))),
                int16_t((*origin)[1]+int16_t(half(ram,*segments+6))+byte(ram,*segments+2)+2),std::move(label)};
        }
        for(unsigned n=0;n<result.line_count;++n){const auto& line=result.lines[n];
            if(line.x<0||line.y<0||line.x+line.text.size()*6>320||line.y+12>240)return rejected;}
        return result;
    }
    return {};
}
void TextureGuard::restore_name(uint8_t* ram){
    for(unsigned kind=0;kind<3;++kind){
        auto& saved=kind?name_ab_cache_[kind-1]:name_cache_;
        const auto& candidate=kind?layout_.name_ab[kind-1]:layout_.name_directions;
        if(!saved.valid||!candidate)continue;
        const auto& p=*candidate;const uint32_t size=kind?128:512;
        const auto bank=offset(word(ram,p.bank_pointer),(p.descriptor_index+1)*12,4);
        if(bank&&saved.descriptor==*bank+p.descriptor_index*12&&word(ram,saved.descriptor)==p.dimensions&&
           word(ram,saved.descriptor+4)==p.descriptor_attributes&&
           offset(word(ram,saved.descriptor+8),size)==saved.texture&&read_bytes(ram,saved.texture,size)==saved.applied&&
           rom_detail::sha256_hex(read<32>(ram,saved.palette))==p.expected.palette)
            write(ram,saved.texture,saved.original);
        saved.valid=false;
    }
}
PromptSpriteResult TextureGuard::prepare_impl(uint8_t* ram,uint64_t sprite,const std::array<PromptGlyphRequest,2>& labels,
                                            const std::array<PromptGlyphRequest,4>* directions,const PromptGlyphRequest* start,
                                            const std::array<PromptGlyphRequest,3>* shoulders){
    if(!ram)return {};
    if(memory_!=ram){memory_=ram;cache_={};pair_cache_={};name_cache_={};name_ab_cache_={};warned_=false;}
    if(handicap_consumer(ram,sprite,layout_)){
        PromptSpriteResult result;result.status=PromptSpriteStatus::RejectedKnown;result.action=PromptSpriteAction::Shoulders;
        if(!start||start->port>=4||!shoulders||!handicap_ready(ram,sprite,layout_))return result;
        std::array<std::string,3> names;
        for(unsigned n=0;n<3;++n){const auto& request=(*shoulders)[n];const auto label=short_label(request);
            if(request.port!=start->port||!label)return result;
            names[n]=*label;
        }
        const auto left=names[0]+" "+names[1];
        if(left.size()*6>32||names[2].size()*6>32)return result;
        result.lines[0]={int16_t(20+(32-int(left.size())*6)/2),217,left};
        result.lines[1]={int16_t(275+(32-int(names[2].size())*6)/2),217,names[2]};
        result.line_count=2;result.status=PromptSpriteStatus::TextFallback;return result;
    }
    if(const auto p=replay_consumer(ram,sprite,layout_)){
        PromptSpriteResult result;result.status=PromptSpriteStatus::RejectedKnown;
        if(!start||start->port>=4||!replay_ready(ram,*p,layout_))return result;
        const auto port=start->port;
        auto line=[&](int x,int y,std::string text){result.lines[result.line_count++]={int16_t(x),int16_t(y),std::move(text),8};};
        if(p->object==0x13E0D8){
            auto label=start_phrase(*start);if(!label)return result;
            label->resize(label->size()-7);
            if(start->label=="Return")*label="Return";
            if(label->size()>8)return result;
            // Original Cancel text/arrow is a separate object. Only Start's
            // original48px cell is replaced, through the original font.
            line(240+(48-int(label->size())*6)/2,15,*label);
        }else if(p->object==0x13E204){
            if(!shoulders||(*shoulders)[1].port!=port||(*shoulders)[2].port!=port)return result;
            const auto z=short_label((*shoulders)[1]),r=short_label((*shoulders)[2]);if(!z||!r)return result;
            line(44,13,std::string(*r));line(44,33,std::string(*z));
        }else{
            if(!directions||labels[0].port!=port||labels[1].port!=port)return result;
            const auto a=short_label(labels[0]),b=short_label(labels[1]);if(!a||!b)return result;
            line(71,16,std::string(*a));line(71,24,std::string(*b));line(44,23,"Move");
            constexpr int xs[]{116,140,128,128},ys[]{22,22,13,31};
            for(unsigned n=0;n<4;++n){const auto& request=(*directions)[n];const auto label=short_label(request);
                if(request.port!=port||!label)return result;
                line(xs[n],ys[n],std::string(*label));}
        }
        result.status=PromptSpriteStatus::TextFallback;return result;
    }
    if(auto pause=prepare_field_pause(ram,sprite,shoulders))return *pause;
    if(auto field=prepare_field_start(ram,sprite,start))return *field;
    if(auto regions=prepare_regions(ram,sprite,shoulders))return *regions;
    if(auto packed=prepare_packed(ram,sprite,labels,directions,shoulders))return *packed;
    if(auto pair=prepare_pair(ram,sprite,labels))return *pair;
    bool recognized=false;const auto info=probe_layout(ram,sprite,recognized,layout_,directions!=nullptr,start!=nullptr);
    PromptSpriteResult result;
    if(!info){if(recognized){result.status=PromptSpriteStatus::RejectedKnown;warn();}return result;}
    result.action=sprite_action(info->slot);
    result.status=PromptSpriteStatus::RejectedKnown;
    const auto size=texture_size(info->slot);
    auto pixels=read_bytes(ram,info->texture,size);
    const auto& hashes=expected_hashes(layout_,info->slot);
    if(info->slot==3){
        if(rom_detail::sha256_hex(pixels)!=hashes.texture){warn();return result;}
        if(auto proposal=text_fallback(ram,sprite,3,layout_,labels,directions,start))return *proposal;
        warn();return result;
    }
    const auto palette=read<32>(ram,info->palette);
    if(rom_detail::sha256_hex(palette)!=hashes.palette){warn();return result;}
    auto& saved=cache_[info->slot];
    const bool ours=saved.valid&&saved.texture==info->texture&&saved.palette==info->palette&&saved.descriptor==info->descriptor&&pixels==saved.applied;
    if(!ours){
        if(rom_detail::sha256_hex(pixels)!=hashes.texture){warn();return result;}
        saved={info->descriptor,info->texture,info->palette,pixels,{},true};
    }
    if(info->slot==2&&directions&&layout_.text_fallback){
        const auto object=offset(sprite,0x38,4);const auto consumer=object?offset(word(ram,*object+0x30),12,2):std::nullopt;
        for(const auto& candidate:layout_.team_directions)if(candidate&&consumer&&*consumer==candidate->consumer_address){
            const auto& p=*candidate;const auto& font=*layout_.text_fallback;
            const auto frame=offset(word(ram,font.frame_pointer),0x18,4);
            const auto origin=sprite_origin(ram,*object,font);
            if(!frame||byte(ram,*frame+0x12)||half(ram,*frame+0x14)!=320||half(ram,*frame+0x16)!=240||
               !origin||(*origin)[0]||(*origin)[1]||byte(ram,0x12de56)!=1||
               rom_detail::sha256_hex(read_bytes(ram,font.font_address,font.font_bytes))!=font.font_sha256||
               rom_detail::sha256_hex(read_bytes(ram,*consumer,p.segments*12))!=p.consumer_sha256)return result;
            // Palette4 is the original opaque black native-font tint. Verify it
            // before using the physical glyphs on either SelectTeams skin.
            if(!layout_.team_regions||rom_detail::sha256_hex(read_bytes(ram,layout_.team_regions->font_tint_address,48))!=layout_.team_regions->font_tint_sha256)return result;
            const bool single=p.segments==2;
            for(unsigned n=0;n<p.segments;++n){const auto segment=*consumer+n*12;
                const unsigned direction=half(ram,segment+8)/512;if(direction>=4)return result;const auto& request=(*directions)[direction];
                const auto tile=std::find_if(artwork_glyphs.begin(),artwork_glyphs.end(),[&](const auto&g){return g.family==request.family&&g.label==request.label;});
                if(request.port!=0||tile==artwork_glyphs.end())return result;
                const bool footer=single||n==3||n==4||n==5||n==6;
                int x=half(ram,segment+4),y=half(ram,segment+6);const unsigned size=footer?16:12;
                if(footer){
                    const bool left=direction==0;const bool second=!single&&n>=5;
                    const int label_left=single?82:second?229:44;
                    x=left?label_left-19:label_left+44;
                    int top=16,bottom=-1;for(unsigned i=0;i<256;++i)if(artwork_tiles[tile->tile][i]){top=std::min(top,int(i/16));bottom=std::max(bottom,int(i/16));}
                    y=((single?407:403)-top-bottom)/2;
                }
                result.icons[n]={int16_t(x),int16_t(y),request.family,std::string(request.label),request.port,uint8_t(size),uint8_t(size)};
            }
            result.icon_count=uint8_t(p.segments);result.status=PromptSpriteStatus::TextFallback;return result;
        }
    }
    auto generated=saved.original;bool available=true;
    const unsigned count=info->slot==2?4:1;
    for(unsigned cell=0;cell<count;++cell){
        const auto glyph=cell_glyph(info->slot<2?labels[info->slot]:(*directions)[cell],palette,saved.original,info->slot<2?8:40,cell);
        if(!glyph){available=false;break;}
        if(info->slot<2)std::copy(glyph->begin(),glyph->end(),generated.begin());
        else for(unsigned row=0;row<16;++row)std::copy_n(glyph->begin()+row*8,8,generated.begin()+row*40+cell*8);
    }
    if(!available){
        // A full C transaction is atomic; restore only bytes still owned by us.
        if(ours)write(ram,info->texture,saved.original);
        saved.valid=false;
        if(auto proposal=text_fallback(ram,sprite,info->slot,layout_,labels,directions,start))return *proposal;
        warn();return result;
    }
    saved.applied=std::move(generated);write(ram,info->texture,saved.applied);result.status=PromptSpriteStatus::Applied;return result;
}
bool TextureGuard::prepare(uint8_t* ram,uint64_t sprite,const std::array<PromptGlyphRequest,2>& labels){return prepare_impl(ram,sprite,labels,nullptr,nullptr,nullptr).status==PromptSpriteStatus::Applied;}
PromptSpriteResult TextureGuard::prepare_sprite(uint8_t* ram,uint64_t sprite,const std::array<PromptGlyphRequest,2>& labels,const std::array<PromptGlyphRequest,4>& directions,std::optional<PromptGlyphRequest> start,std::optional<std::array<PromptGlyphRequest,3>> shoulders){return prepare_impl(ram,sprite,labels,&directions,start?&*start:nullptr,shoulders?&*shoulders:nullptr);}
void TextureGuard::restore(uint8_t* ram){
    if(!ram||ram!=memory_)return;
    auto bank=offset(word(ram,layout_.bank_pointer),(maximum_index(layout_)+1)*12,4);
    for(unsigned slot=0;slot<(layout_.c_directions?3u:2u);++slot){
        auto& saved=cache_[slot];if(!saved.valid)continue;
        const auto size=texture_size(slot);
        bool same=bank&&saved.descriptor==*bank+descriptor_index(layout_,slot)*12
            &&word(ram,saved.descriptor)==dimensions(slot)
            &&word(ram,saved.descriptor+4)==descriptor_attributes(layout_,slot)
            &&offset(word(ram,saved.descriptor+8),size)==saved.texture;
        if(same&&read_bytes(ram,saved.texture,size)==saved.applied
            &&rom_detail::sha256_hex(read<32>(ram,saved.palette))==expected_hashes(layout_,slot).palette)
            write(ram,saved.texture,saved.original);
        saved.valid=false;
    }
    restore_pair(ram);
    restore_name(ram);
}
}
namespace {
PromptTextureLayout reviewed_prompt_layout(uint32_t bank_pointer){
    // Both revisions independently match these exact decoded icons/palettes.
    return {bank_pointer,{5,6},{0x01060000,0x01070000},{{
        {"53190166d2b23997025eb589b1ee4209852f05a4269fd1f89b2db54245612d1a","6dd4c784922f5eaaaac284db2080b4764d6f10ef145b89ac958fafd677c30f34"},
        {"fe9074c636d0a9c2e3f39aa2ca0a15474e2b8f3eaa0a58afa0cf4187f7b042de","8495c578169e8ce5c471d753b3af53ce08b02934cbac0ba1d954c4165c4d515e"}
    }} ,std::nullopt,std::nullopt,std::nullopt,std::nullopt};
}
}
PromptTextureLayout us_prompt_texture_layout(){return reviewed_prompt_layout(0x79650);}
PromptTextureLayout pal_en_prompt_texture_layout(){
    auto profile=reviewed_prompt_layout(0x76B30);
    profile.c_directions=PromptDirectionStripLayout{8,0x010A0000,
        {"d36021674ebafd8b1692386877ab990103b19c747979cbeef86d803f8c4a644e","9e591d8246bb991a8afaf791cc716f7697d23d9c008c822f18dd17c1682b34cf"},
        "3e0509f2dee89c473e451037c3a58bd0808e174b60aaa4d266f01fa396458621"};
    profile.text_fallback=PromptTextFallbackLayout{0x13C37C,0x352800,0x3000,0x9E02C,
        "237c7f53ac8b11353467cb957868f794507ca2688c93581d977dac03a4e8b765"};
    profile.start_random=PromptStartImageLayout{1,0x03030000,
        {"5b452ff00298dc6d5015627e9de020fa8aa655e14b3282fa69d2ab11b146e99e","b893ae3ef4c5ee2d11c62c06f3a35b7319328f53ef9e8724faaf707d795794a2"},
        {"1f591ec6e6f04c2117262b3afaceebf0059ae95089655142f465ddf98d3f5fbd",
         "8198269896413885239bc9c1fb4ada83587e54a41c286666124c8572ec1a38c4",
         "1f9e9485697ea8879fd20b1d4ed1d6353f2b9bf8b1401fcde855dc0b84d6db4d"}};
    profile.ab_pair=PromptPairStripLayout{0x76C54,19,0x010A0000,
        {"c62537a1c45ff4cfd489a6fd4b08451caea827b3a36f79444fe78ee8180a80a3","3eff1d2aa46ae1715ad68a79a0efb7e288c116f8bbff8c287fd4be95e7ab3375"}};
    profile.country_shoulders=PromptPackedHintLayout{0x76C80,11,0x00800010,0x01030000,
        {"8fda1c5c8ca05884a12afabef3f9345cda6797c53d1f0cdd112ea9cc692d4321","7590dca4ae435f5bfedb21ea242231d34871847502b4a5f087b26f62bd8c4390"},
        "d30478fc454983e266340ea9b649a272ad7f34ab2b32b8b0e9dd2bec92c19c90"};
    profile.name_directions=PromptPackedHintLayout{0x76C80,2,0x00400010,0x01320000,
        {"14ae1010194afa4df48b5b03ad50f3fdaa67fd956346d6d7b341ff1f64ea6f77","37a077a2c354c75881af94d897efd1d6e640d08ee17152c45684cc6edcbec7e6"},
        "cdfaa6af8d477f8682a3d1a26cfbd4754abc310320d34dc7a9d80e30d3b89c3c"};
    profile.name_ab[0]=PromptPackedHintLayout{0x76C80,0,0x00100010,0x01300000,
        {"545d023679e76e79c3398c2d00f847868017f120f69190d5d48879c32ebedde8","b921ce5ddb456cf3d90ee3870d560638bd8ca4b7d40d38e61b7ac87ba15e160c"},
        "9c81cf4e00f9353abaa69e4e6388930b2abbc8cab249c1e0899862be064bf9d1"};
    profile.name_ab[1]=PromptPackedHintLayout{0x76C80,1,0x00100010,0x01310000,
        {"2392c695da5ef20c906f872a4b5b78a27613c3ef0d2845ece6da3a0f1c7350a8","d67f367922c38b39beb6998ee8b4a7c14763e84acfac00111afdb8e56934a466"},
        "1423cb9e500dc316667eb6a01cacb49883ffeb20a04427631b151ffb1816ff72"};
    profile.team_regions=PromptRegionHintLayout{0x76B90,119,0x1BE700,
        {"8497c4763cd547894fb2dda288d556fec428ae6b31c03649c7754dcdf8b92a66",
         "fb24572f6c33949f99b36ecfcea6ae217ff0fcb56fed1c098ec02048c3d2d1f0"},
        "2794e70b9cd0d469942c5c75107ffd718904f228434eee0fd9a94dcd491d5e7f",
        "f8786aedbfc5c23e6c76b68a11992998f4282ae8dda75ab86dd7dab7750a1a1a",0x12DE56,1,
        0x876B0,"9e9815495c5e7239bbb7278da97e9ca4b07581d82b43a29378a2985f5bd6681d",4,
        0x2AE8DC,"8f765ff4f806e996a05d3a6b961438b7f031d4d9ec3813667cf05f72982e969f"};
    profile.team_directions[0]=PromptTeamDirectionLayout{0x1BE5E0,8,"5f16490a12b687c7580f4a32f3483538fdf9f9f4f659c9577da0b54a3675c8e3"};
    profile.team_directions[1]=PromptTeamDirectionLayout{0x2AEA80,2,"a686fb096dab54c443b39f81091bf74a1e22e474747bd31836895825a2fdfad3"};
    profile.field_start=PromptFontImageLayout{0x76AE4,142,0x00400038,0x030F0000,
        1792,0x25FC90,36,
        "32bff5e761ac0082d6348e3a026c2c192f3b2cc022e76aca23132c9b87186d7a",
        "6b02ed26e70b9dcab0973eb9bb70c954c9840575de664b2521c4bd208910a3e9"};
    profile.field_setplay=PromptFontImageLayout{0x76AE4,141,0x00400040,0x030F0000,
        2048,0x25EA00,120,
        "dcf8d8a47caae28fb5d1d447f95865f4515d22acf4aa8ad69eaee02ecf402133",
        "f530533100a8f28842669d215a9f43fa0583a5cd4d91eaa664993a47a2b4f15b",0x12DE37};
    return profile;
}
namespace {
std::mutex prompt_mutex;
std::unique_ptr<prompt_detail::TextureGuard> prompts;
}
std::optional<unsigned> physical_prompt_sprite_port(const uint8_t* ram,uint64_t sprite,std::optional<unsigned> active_port){
    std::lock_guard lock(prompt_mutex);
    return prompts?prompts->sprite_port(ram,sprite,active_port):std::nullopt;
}
void configure_prompt_textures(const PromptTextureLayout& layout){
    auto candidate=std::make_unique<prompt_detail::TextureGuard>(layout);
    std::lock_guard lock(prompt_mutex);
    if(prompts)throw std::logic_error("Prompt textures are already configured");
    prompts=std::move(candidate);
}
bool prepare_prompt_textures(uint8_t* ram,uint64_t sprite,const std::array<PromptGlyphRequest,2>& labels){
    std::lock_guard lock(prompt_mutex);return prompts && prompts->prepare(ram,sprite,labels);
}
PromptSpriteResult prepare_physical_prompt_sprite(uint8_t* ram,uint64_t sprite,
        const std::array<PromptGlyphRequest,2>& labels,const std::array<PromptGlyphRequest,4>& directions,std::optional<PromptGlyphRequest> start,std::optional<std::array<PromptGlyphRequest,3>> shoulders){
    std::lock_guard lock(prompt_mutex);return prompts?prompts->prepare_sprite(ram,sprite,labels,directions,start,shoulders):PromptSpriteResult{};
}
void restore_prompt_textures(uint8_t* ram){std::lock_guard lock(prompt_mutex);if(prompts)prompts->restore(ram);}
}
