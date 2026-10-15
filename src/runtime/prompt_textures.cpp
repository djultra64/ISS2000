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
    auto palette=offset(word(ram,*s+0x34),32,2);
    if(!texture||!palette)return {};
    return Layout{*descriptor,*texture,*palette,slot};
}
std::optional<std::string_view> short_label(PromptGlyphRequest request){
    // Explicit physical aliases for the original six-pixel font. Two characters
    // fit within each original16px icon cell; full names remain in Remap.
    const auto name=request.label;
    if(request.family==PromptGlyphFamily::Automatic || unsigned(request.family)>unsigned(PromptGlyphFamily::Keyboard))return {};
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
    if(viewport&~0x030Fu)return {};
    int x=int16_t(half(ram,sprite+0x20)),y=int16_t(half(ram,sprite+0x24));
    const uint32_t anchor=profile.viewport_table+(viewport&15)*16;
    if(viewport&0x100)x-=int16_t(half(ram,anchor));
    if(viewport&0x200)y-=int16_t(half(ram,anchor+4));
    return std::array<int,2>{x,y};
}
std::optional<std::string> start_phrase(PromptGlyphRequest);
PromptSpriteAction sprite_action(unsigned slot){return slot==0?PromptSpriteAction::A:slot==1?PromptSpriteAction::B:slot==2?PromptSpriteAction::CDirections:PromptSpriteAction::StartRandom;}
std::optional<PromptSpriteResult> text_fallback(const uint8_t* ram,uint64_t sprite,unsigned slot,
        const PromptTextureLayout& profile,const std::array<PromptGlyphRequest,2>& labels,
        const std::array<PromptGlyphRequest,4>* directions,const PromptGlyphRequest* start){
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
        if(slot!=2 && ((tag!=0x80&&tag!=0x90)||half(ram,p+8)!=0))return {};
        if(slot==2 && (tag!=(n==0?0x10u:n==3?0x80u:0u)||half(ram,p+8)!=n*512))return {};
        std::optional<std::string> label;
        if(slot==3)label=start_phrase(*start);
        else if(auto name=short_label(slot<2?labels[slot]:(*directions)[n]))label=std::string(*name);
        if(!label)return {};
        const int x=(*origin)[0]+int16_t(half(ram,p+4)),y=(*origin)[1]+int16_t(half(ram,p+6))+2;
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
    if(layout_.text_fallback){
        const auto& t=*layout_.text_fallback;
        if(t.viewport_table>0x800000-256||t.viewport_table%2||t.frame_pointer>0x800000-4||t.frame_pointer%4||t.font_bytes==0||t.font_bytes>0x10000||t.font_address>0x800000-t.font_bytes||!valid_hash(t.font_sha256))
            throw std::invalid_argument("Invalid prompt font layout");
    }
}
void TextureGuard::warn(){if(!warned_){std::fprintf(stderr,"[Prompts] A recognized physical prompt could not be adapted safely; inspect native prompt diagnostics.\n");warned_=true;}}
PromptSpriteResult TextureGuard::prepare_impl(uint8_t* ram,uint64_t sprite,const std::array<PromptGlyphRequest,2>& labels,
                                            const std::array<PromptGlyphRequest,4>* directions,const PromptGlyphRequest* start){
    if(!ram)return {};
    if(memory_!=ram){memory_=ram;cache_={};warned_=false;}
    bool recognized=false;const auto info=probe_layout(ram,sprite,recognized,layout_,directions!=nullptr,start!=nullptr);
    PromptSpriteResult result;
    if(!info){if(recognized){result.status=PromptSpriteStatus::RejectedKnown;warn();}return result;}
    result.action=sprite_action(info->slot);
    result.status=PromptSpriteStatus::RejectedKnown;
    const auto size=texture_size(info->slot);
    auto pixels=read_bytes(ram,info->texture,size);const auto palette=read<32>(ram,info->palette);
    const auto& hashes=expected_hashes(layout_,info->slot);
    if(rom_detail::sha256_hex(palette)!=hashes.palette){warn();return result;}
    if(info->slot==3){
        if(rom_detail::sha256_hex(pixels)!=hashes.texture){warn();return result;}
        if(auto proposal=text_fallback(ram,sprite,3,layout_,labels,directions,start))return *proposal;
        warn();return result;
    }
    auto& saved=cache_[info->slot];
    const bool ours=saved.valid&&saved.texture==info->texture&&saved.palette==info->palette&&saved.descriptor==info->descriptor&&pixels==saved.applied;
    if(!ours){
        if(rom_detail::sha256_hex(pixels)!=hashes.texture){warn();return result;}
        saved={info->descriptor,info->texture,info->palette,pixels,{},true};
    }
    auto generated=saved.original;bool available=true;
    const unsigned count=info->slot==2?4:1;
    for(unsigned cell=0;cell<count;++cell){
        const auto glyph=glyph_pixels(info->slot<2?labels[info->slot]:(*directions)[cell],palette);
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
bool TextureGuard::prepare(uint8_t* ram,uint64_t sprite,const std::array<PromptGlyphRequest,2>& labels){return prepare_impl(ram,sprite,labels,nullptr,nullptr).status==PromptSpriteStatus::Applied;}
PromptSpriteResult TextureGuard::prepare_sprite(uint8_t* ram,uint64_t sprite,const std::array<PromptGlyphRequest,2>& labels,const std::array<PromptGlyphRequest,4>& directions,std::optional<PromptGlyphRequest> start){return prepare_impl(ram,sprite,labels,&directions,start?&*start:nullptr);}
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
}
}
namespace {
PromptTextureLayout reviewed_prompt_layout(uint32_t bank_pointer){
    // Both revisions independently match these exact decoded icons/palettes.
    return {bank_pointer,{5,6},{0x01060000,0x01070000},{{
        {"53190166d2b23997025eb589b1ee4209852f05a4269fd1f89b2db54245612d1a","6dd4c784922f5eaaaac284db2080b4764d6f10ef145b89ac958fafd677c30f34"},
        {"fe9074c636d0a9c2e3f39aa2ca0a15474e2b8f3eaa0a58afa0cf4187f7b042de","8495c578169e8ce5c471d753b3af53ce08b02934cbac0ba1d954c4165c4d515e"}
    }} ,std::nullopt,std::nullopt,std::nullopt};
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
    return profile;
}
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
bool prepare_prompt_textures(uint8_t* ram,uint64_t sprite,const std::array<PromptGlyphRequest,2>& labels){
    std::lock_guard lock(prompt_mutex);return prompts && prompts->prepare(ram,sprite,labels);
}
PromptSpriteResult prepare_physical_prompt_sprite(uint8_t* ram,uint64_t sprite,
        const std::array<PromptGlyphRequest,2>& labels,const std::array<PromptGlyphRequest,4>& directions,std::optional<PromptGlyphRequest> start){
    std::lock_guard lock(prompt_mutex);return prompts?prompts->prepare_sprite(ram,sprite,labels,directions,start):PromptSpriteResult{};
}
void restore_prompt_textures(uint8_t* ram){std::lock_guard lock(prompt_mutex);if(prompts)prompts->restore(ram);}
}
