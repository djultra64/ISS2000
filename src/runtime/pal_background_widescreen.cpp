// Original project work: djultra64.
#include "pal_background_widescreen.hpp"
#include "pal_sky_widescreen.hpp"
#include "rom_image.hpp"
#include <array>
#include <algorithm>
#include <utility>
#include <cstdlib>
#include <cstring>
#include <string_view>
namespace iss2000 {
namespace {
thread_local bool background_scope_active{};
uint32_t word(std::span<const uint8_t> r,uint32_t a){uint32_t v;std::memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
uint8_t byte(std::span<const uint8_t> r,uint32_t a){return r[(a&0x7fffff)^3];}
uint16_t half(std::span<const uint8_t> r,uint32_t a){uint16_t v;std::memcpy(&v,r.data()+((a&0x7fffff)^2),2);return v;}
void put(std::span<uint8_t> r,uint32_t a,uint32_t v){std::memcpy(r.data()+(a&0x7fffff),&v,4);}
bool canonical(uint64_t a){
    const auto lo=uint32_t(a),hi=uint32_t(a>>32);
    return (hi==0 || (hi==0xffffffffu && (lo&0x80000000u))) &&
        (lo&0xff800003u)==0x80000000u;
}
struct Profile {
    PalBackgroundKind kind;
    uint32_t bank_pointer,bank_base,descriptor,segments;
    uint8_t layer;
    uint16_t descriptor_bytes,segment_bytes;
    std::string_view descriptors_sha256,segments_sha256;
};
// Each exact descriptor/segment extent matches original PAL ROM bytes.
// Only proven background-role resources are admitted; canvas size alone is
// insufficient because original foreground panels can also span the screen.
constexpr Profile profiles[]={
    {PalBackgroundKind::CommonMenu,0x80076B1C,0x803D7D00,0x803D7EF8,0x803E41A0,1,480,480,
     "34ede3cc6958fa54d20b6301edaf3b95dbe87e66808bad5b116c83a041c7b21c",
     "9b78280caca47bc92111b9021d7fcb32092157791dc312d86d8d587c56f6d74d"},
    // Original common-menu backdrop animation, fixed slots3/4. These are
    // background lettering layers, advanced by803C3E20/803C3EA0, not UI labels.
    {PalBackgroundKind::MenuHorizontalWatermark,0x80076B1C,0x803D7D00,0x803D7EB0,0x803E4CF8,2,36,144,
     "7403110d1535cd258ef7a0efa83e68a96f3d1b27f676b2c28b5297538a3a5f32",
     "e10b1f3d04a8fb4310a83b8f815c1b1225927223bef1ffd1ed5caa5c4ccce39d"},
    {PalBackgroundKind::MenuVerticalWatermark,0x80076B1C,0x803D7D00,0x803D7ED4,0x803E4D88,2,36,144,
     "380a6c45d675a857893afa7017e1cba724fad3a577b4a0283ab899207878bd8f",
     "8d15a841e11fefddc41ce0cc15451a0e7418242451c9ca6afbefc1c5d84276ec"},
    // Blue pre-season menu uses the same original moving atlas/slots with
    // independently pinned fourteen-piece word layouts.
    {PalBackgroundKind::MenuHorizontalWatermark,0x80076B1C,0x803D7D00,0x803D7EB0,0x803E4728,2,36,168,
     "7403110d1535cd258ef7a0efa83e68a96f3d1b27f676b2c28b5297538a3a5f32",
     "8e2055d47544168d003a311e218ba59bbea05c1f207d36bfb29d5693e6aade41"},
    {PalBackgroundKind::MenuVerticalWatermark,0x80076B1C,0x803D7D00,0x803D7ED4,0x803E47D0,2,36,168,
     "380a6c45d675a857893afa7017e1cba724fad3a577b4a0283ab899207878bd8f",
     "65506acf8a4bdce0f7fc1f816c3342d5a41fc96027f5741541c86d72c73ecfa2"},
    {PalBackgroundKind::Career,0x80076C3C,0x8022EE64,0x8022EE64,0x8023E71C,1,480,480,
     "fc722848a18965ce6fa1c2af5dcc527ef366588c4d5de71cf6273b04dcfea654",
     "e9da7634ae5a7ad1677e39aa078fc8c06ee0fba1f5df1099ad752f1681731976"},
    // Original 80047558 constructs this full-screen RGBA16 image in slot 0,
    // layer 0. Its only caller is the original intro script flag 0x40 path.
    {PalBackgroundKind::ScriptedImage,0,0,0x80086FEC,0x80086BC0,0,480,480,
     "d74beb9a6de9303dabcf36e13a89b8ac1e8eab56de5bec8a5687f5b02b25e920",
     "556e4522bcfbcb36c1aad8022baf84240a25e27218b94603bef2a47a066fea61"},
    // Original 801ECC08 resource 8: slot 0, layer 11, RGB 0, material 19.
    // All 150 segments reuse one descriptor; never read 150 descriptors.
    {PalBackgroundKind::ScreenCover,0x80076B14,0x801F6EE0,0x801F6EE0,0x801EF7CC,11,12,1800,
     "3994a58dce3c1980e3ad0e2baad0be285e87f97e7e2ff9d07e6797e24b18581e",
     "48a6a13d079a50342d5b1b855429a6691dba3d6db6c44004a79895f175b90798"},
    // Original scene802B7CA8 installs table802BB80C; its first subscript
    // creates resource12, layer3, palette49/index8, material2, at origin0.
    {PalBackgroundKind::SceneImage,0x80076BDC,0x803D62D8,0x803D6428,0x802BB640,3,456,456,
     "8c8881f9b97da6282feb9f0793158e7f6b91656f81dda01740e0468829fe68ac",
     "8726cbc84f7d7b37675467afa5d22f5dcd839144c9b5bf56562ae504350ec253"},
    // Original two scene tables request this full-canvas globe/logo image,
    // then select a palette through802B5DB4 or802B6800 before higher widgets.
    {PalBackgroundKind::GlobeImage,0x80076BB0,0x803D5B58,0x803D5B58,0x802B8D40,5,240,240,
     "38ccedf543017759458d107b1a5a941c6ac98bc43f1db0affeda799e4f376da2",
     "efd22cc7cdb57ab288e8f80787638cbe6f7d3f8e257f60dafe9a7a529f159a40"},
    // OriginalCareer mode2 parent script uses resourcebank113/index29.
    // Its90rectangles repeat three plain gradient cells from asset112.
    {PalBackgroundKind::GradientCover,0x80076C74,0x8022FB6C,0x8022FC8C,0x802406FC,1,12,1080,
     "1cf0f8189dfb6ef62b0efe3e43f5072cd8048ea1689e36c6eb7d442a33638f55",
     "3ee17bf5c65b5df9b62d73ec83766425a03da151aa60155c928686fad698733c"},
    // Original80235C50 result backdrop: only white atlas cells, slot107,
    // layer11, RGB0, alpha96 and material19. Higher result UI is separate.
    {PalBackgroundKind::ResultCover,0x80076AE4,0x80259900,0x8025A014,0x80260848,11,12,2160,
     "96c3becb728fa34099053c54b3680e0155e7286a39e42a382c0e3989277cd643",
     "8e2096d8b25a837c69ff94a79a70ac9a902b86e61da4f9577c83281ac13898d0"}
};
bool matches(std::span<const uint8_t> r,uint32_t a,unsigned bytes,std::string_view expected){
    std::array<uint8_t,2160> original_order{};
    if(bytes==0 || bytes>original_order.size())return false;
    for(unsigned i=0;i<bytes;++i)original_order[i]=byte(r,a+i);
    return rom_detail::sha256_hex({original_order.data(),bytes})==expected;
}
// The palette is selected by the actual original scene callback, not by a
// generic palette-range test. Pin each scene's resource and first script call.
bool globe_owner(std::span<const uint8_t> r,uint32_t palette){
    if(word(r,0x8007690C)!=0x803D52F0 || word(r,0x803D52F0)!=0x803D3E10 ||
       !matches(r,0x8009CB78,48,"9d1b6c58ac55fb3d340b7d3447f3bf744e0d3fecd31f4a0777ba2bed0c0ebffa"))return false;
    unsigned index;
    if(word(r,0x80143D6C)==0x802B926C){
        const auto state=byte(r,0x802BBE11);
        index=state==1?1:state==3?2:state==2?3:state==4?5:0;
        if(!matches(r,0x802B92FC,12,"bf8a75c29c1c45fe18ede8fdb4d801a55193ed99b5cc5a5d4fc8db62c022ad0b") ||
           !matches(r,0x802B933C,24,"f6f9fc7d562d83c9b18b18eb561d4c6816a7ab55ffce45df4a24fd9254332253") ||
           !matches(r,0x802B9534,12,"b6c512f2f090222dd6a1c602a285221329f6c7173eb7427e96bf9d0ab885f25e"))return false;
    }else if(word(r,0x80143D6C)==0x802BA394){
        index=byte(r,0x802BA36C)==0?6:7;
        if(!matches(r,0x802BA58C,12,"bf8a75c29c1c45fe18ede8fdb4d801a55193ed99b5cc5a5d4fc8db62c022ad0b") ||
           !matches(r,0x802BA658,20,"a964d112ecd28f8d72dd813fa56f284f328c98aa6b8cdcca564c8ba56c12b166") ||
           !matches(r,0x802BA7FC,8,"4796f00c8a70792f3d5b0261529ca84ac07094b75627c933131ea6821be7992e"))return false;
    }else return false;
    return palette==0x803D3E10+index*32;
}
// The original emitter clips its (4,2)..(324,258) menu canvas before our
// (-4,-2) alignment. Recover only the four right / ten bottom tile boundaries
// needed to cover320x240, sampling their existing in-bounds texture columns.
// Validate the complete original40-tile stream first; a changed draw path gets
// no guessed coordinates and never a partially repaired edge.
bool repair_common_menu_edges(std::span<uint8_t> r,uint32_t begin,uint32_t cursor,uint32_t palette) noexcept {
    if(cursor<begin || cursor-begin>0x3000)return false;
    std::array<std::pair<uint32_t,uint32_t>,40> patches{};
    unsigned images=0,palettes=0,rects=0;
    for(auto pc=begin;pc<cursor;pc+=8){
        if(cursor-pc<8)return false;
        const auto command=word(r,pc),value=word(r,pc+4),op=command>>24;
        if(op==0xFD){
            if(command==0xFD100000){
                if(images!=rects || palettes!=images || palettes>=40 || value!=palette)return false;
                ++palettes;
            }else if(command==0xFD500000){
                if(images!=rects || palettes!=images+1 || images>=40 || value!=word(r,0x803D7EF8+images*12+8))return false;
                ++images;
            }else return false;
        }else if(op==0xE4){
            if(rects>=40 || images!=rects+1 || palettes!=images || cursor-pc<24)return false;
            const auto descriptor=0x803D7EF8+rects*12,segment=0x803E41A0+rects*12;
            const unsigned x=half(r,segment+4),y=half(r,segment+6),width=half(r,descriptor),height=half(r,descriptor+2);
            if(width!=32 || height!=64 || x<4 || x>292 || y<2 || y>194)return false;
            const unsigned old_right=std::min(x+width-1,319u),old_bottom=std::min(y+height-1,239u);
            if(command!=(0xE4000000u|(old_right*4)<<12|old_bottom*4) || value!=((x*4)<<12|y*4) ||
               word(r,pc+8)!=0xE1000000 || word(r,pc+12) || word(r,pc+16)!=0xF1000000 || word(r,pc+20)!=0x10000400)return false;
            const unsigned right=std::min(x+width-1,323u),bottom=std::min(y+height-1,241u);
            patches[rects++]={pc,0xE4000000u|(right*4)<<12|bottom*4};pc+=16;
        }else if(op==0xDE){
            if(command!=0xDE000000 || value!=0x8009CB78)return false;
        }else if(op!=0xE2 && op!=0xE3 && op!=0xE6 && op!=0xE7 && op!=0xE8 && op!=0xF0 && op!=0xF2 && op!=0xF3 && op!=0xF5 && op!=0xFA)return false;
    }
    if(images!=40 || palettes!=40 || rects!=40)return false;
    for(const auto& [address,value]:patches)put(r,address,value);
    return true;
}
// Insert a constant-U edge strip before each original outermost image tile.
// Original center commands follow unchanged and redraw the one-pixel overlap.
// The outer one-pixel guard is clipped by the original full-viewport scissor.
// Validate the complete original stream before moving any command.
bool edge_extension(PalBackgroundKind kind){return kind==PalBackgroundKind::ScriptedImage || kind==PalBackgroundKind::SceneImage || kind==PalBackgroundKind::GlobeImage;}
bool extend_image_edges(std::span<uint8_t> r,uint32_t begin,uint32_t& cursor,uint32_t end,PalBackgroundKind kind,uint32_t palette) noexcept {
    const bool scene=kind==PalBackgroundKind::SceneImage;
    const bool globe=kind==PalBackgroundKind::GlobeImage,ci=scene||globe;
    const unsigned count=globe?20:scene?38:40;
    if(cursor<begin || cursor-begin>0x3000 || end-cursor<400)return false;
    struct Edge {uint32_t position,y,height,t;bool right;};
    std::array<Edge,16> edges{};unsigned edge_count=0,rects=0,images=0,palettes=0;
    const unsigned material_prefix=word(r,begin)>>24==0xDE?8:0;
    bool color=false,opacity=false;
    for(uint32_t p=begin;p<cursor;p+=8){
        const auto a=word(r,p),b=word(r,p+4);const auto op=a>>24;
        if(op==0xFD){
            if(ci && a==0xFD100000){
                if(palettes!=images || images!=rects || palettes>=count || b!=palette)return false;
                ++palettes;
            }else{
                if(images>=count || (ci && palettes!=images+1) ||
                   a!=(ci?0xFD500000u:0xFD100000u) ||
                   b!=word(r,(globe?0x803D5B58u:scene?0x803D6428u:0x80086FECu)+12*images+8))return false;
                ++images;
            }
        }else if(op==0xDE){
            if(p!=begin || a!=0xDE000000 || b!=(scene?0x8009CC20u:0x8009CB78u))return false;
        }else if(op==0xE4){
            if(rects>=count || images!=rects+1 || cursor-p<24)return false;
            // CI8 geometry comes only from the exact hashed 38-record scene
            // list, including its two 128x16 bottom tiles. No bbox admission.
            const auto segment=(globe?0x802B8D40u:0x802BB640u)+12*rects;
            const unsigned x=ci?half(r,segment+4):rects<35?(rects/7)*64:(rects-35)*64;
            const unsigned y=ci?half(r,segment+6):rects<35?(rects%7)*32:224;
            const unsigned w=ci?byte(r,segment+1):64,h=ci?byte(r,segment+2):y==224?16:32;
            const auto t=ci?0u:y==224?0x7e00u:0x7c00u;
            const unsigned right=scene?(x+w<319?x+w:319):x+w-1;
            const unsigned bottom=scene?(y+h<239?y+h:239):globe?(y+h-1<239?y+h-1:239):y+h-1;
            if(a!=(0xE4000000|(right*4<<12)|(bottom*4)) || b!=(x*4<<12|y*4) ||
               word(r,p+8)!=0xE1000000 || word(r,p+12)!=t ||
               word(r,p+16)!=0xF1000000 || word(r,p+20)!=(scene?0x04000400u:0x10000400u))return false;
            if(x==0 || x+w==320){
                if(edge_count==edges.size() || (x!=0 && w!=64))return false;
                edges[edge_count++]={p,y,globe?(h<240-y?h:240-y):h,t,x!=0};
            }
            ++rects;p+=16;
        }else if(scene && op==0xFA){
            if(color || p!=begin+material_prefix || a!=0xFA000000 || b!=0xFFFFFFFF)return false;
            color=true;
        }else if(scene && op==0xE2){
            if(!color || opacity || p!=begin+material_prefix+8 || a!=0xE2001E01 || b!=1)return false;
            opacity=true;
        }else if(ci && (op==0xE8 || op==0xF0)){
            // Original CI8 palette-load commands; the following exact FD and
            // rectangle checks retain the texture, UV and scene ownership.
        }else if(op!=0xE3 && op!=0xF5 && op!=0xE6 && op!=0xE7 && op!=0xF3 && op!=0xF2)return false;
    }
    if((scene && (!color || !opacity)) || rects!=count || images!=count || (ci && palettes!=count) || edge_count!=(globe?12u:16u))return false;
    for(unsigned i=edge_count;i-->0;){
        const auto& e=edges[i];const auto p=e.position;
        std::memmove(r.data()+(p&0x7fffff)+24,r.data()+(p&0x7fffff),cursor-p);
        // Public gEXTextureRectangle: LEFT->NONE or NONE->RIGHT origins;
        // zero horizontal texture step reads only source column 0 or 63.
        const uint32_t words[]={0x64000002,e.right?0x02004000u:0x04000000u,
            ((e.right?1276u:65532u)<<16)|(e.y*4),4u<<16|((e.y+e.height)*4),
            (e.right?2016u:0u)<<16|e.t,0x00000400};
        for(unsigned n=0;n<6;++n)put(r,p+4*n,words[n]);
        cursor+=24;
    }
    return true;
}

}
PalBackgroundKind pal_background_kind(std::span<const uint8_t> r,bool wide,uint64_t object) noexcept {
    if(!wide || r.size()!=0x800000 || !canonical(object) ||
       word(r,0x8009E02C)!=0x8013B418 || byte(r,0x8013B42A)!=0 ||
       half(r,0x8013B42C)!=320 || half(r,0x8013B42E)!=240)return PalBackgroundKind::None;
    const auto a=uint32_t(object);
    // Original8000924C dispatches273 records from context+1064, stride3C.
    if(a<0x8013C47C || (a-0x8013C47C)%0x3c || (a-0x8013C47C)/0x3c>=273 ||
       byte(r,a+4)!=1 ||
       (half(r,a+0x1c)&0x7fff)!=0 || word(r,a+0x28)!=0x3f800000 ||
       word(r,a+0x2c)!=0x3f800000 || word(r,a+0x18)!=0 ||
       (word(r,a+8)&0x40400000)!=0)return PalBackgroundKind::None;
    for(const auto& p:profiles){
        const auto x=int16_t(half(r,a+0x20)),y=int16_t(half(r,a+0x24));
        const bool horizontal=p.kind==PalBackgroundKind::MenuHorizontalWatermark;
        const bool vertical=p.kind==PalBackgroundKind::MenuVerticalWatermark;
        if(horizontal||vertical){
            // Original wrap checks use the previous position, allowing a final
            // two-pixel step beyond the threshold before resetting next tick.
            if((horizontal&&(a!=0x8013C530||y||x< -562||x>100)) ||
               (vertical&&(a!=0x8013C56C||x||y< -100||y>442)) ||
               word(r,a+0x34) || (word(r,a+8)&0xfe000000u)!=0x26000000u)continue;
        }else if(x||y)continue;
        if(byte(r,a+5)!=p.layer || word(r,a+0x14)!=p.descriptor || word(r,a+0x30)!=p.segments ||
           (p.bank_pointer && word(r,p.bank_pointer)!=p.bank_base) ||
           (p.kind==PalBackgroundKind::ScriptedImage && a!=0x8013C47C))continue;
        if(p.kind==PalBackgroundKind::ScreenCover &&
           (a!=0x8013C47C || byte(r,a+0xe)!=0 || byte(r,a+0xf)!=0 || byte(r,a+0x10)!=0 ||
            (word(r,a+8)&0xfe000000u)!=0x26000000u))continue;
        if(p.kind==PalBackgroundKind::SceneImage &&
           (word(r,0x80143D6C)!=0x802BB80C || word(r,a+0x34)!=0x803D50F0 ||
            (word(r,a+8)&0xfe000000u)!=0x04000000u))continue;
        if(p.kind==PalBackgroundKind::GlobeImage && (word(r,a+8)&0xfe000000u)!=0)continue;
        if(p.kind==PalBackgroundKind::GradientCover){
            const auto context=word(r,0x801FD5F0);
            if(!canonical(context) || context>0x807FFFE0 || byte(r,context+0x1e)!=2 ||
               word(r,0x80077164)!=0x802464B0 || word(r,a+0x34)!=0x8022C6B0 ||
               (word(r,a+8)&0xfe000000u)!=0)continue;
        }
        if(p.kind==PalBackgroundKind::ResultCover &&
           (a!=0x8013DD90 || word(r,0x80143D6C)!=0x80261E68 ||
            byte(r,a+0xe)!=0 || byte(r,a+0xf)!=0 || byte(r,a+0x10)!=0 || byte(r,a+0x11)!=96 ||
            (word(r,a+8)&0xfe000000u)!=0x26000000u))continue;
        try {
            if(p.kind==PalBackgroundKind::ResultCover &&
               (!matches(r,0x80263434,12,"d530472ace4713f82720125c684b4f37fe87d37aa100e49dedef454e1ff57852") ||
                !matches(r,0x80212580,2048,"35e8058d9cf3294bb9087c5c938e512d99fd144053a6c5cff8176df8c134c5ef")))continue;
            if(p.kind==PalBackgroundKind::GradientCover &&
               (!matches(r,0x8024660C,12,"c95b6322f1aa25728435c94ade11b2d8288cb44d33a0bdcd4ee15b7a3d747bea") ||
                !matches(r,0x80252898,12,"7b49759cbcaf074cec03f190224d1b8853eda6cef3cb567de7511dadd1e04dbc") ||
                !matches(r,0x802537A8,44,"a1d98cd421d88d368389d9b8245b7f5fbc262f81f0a5c87d84b3b2d29f16ca31") ||
                !matches(r,0x80267E80,1536,"a2852969732b125557203608db9e13bc14093477ba28d191156ed3489226d094")))continue;
            if(p.kind==PalBackgroundKind::GlobeImage && !globe_owner(r,word(r,a+0x34)))continue;
            if(p.kind==PalBackgroundKind::SceneImage &&
               (!matches(r,0x802BB89C,12,"e7bd4998813b324abb3e523f2b50b6e4084493ced2a3b08f2a8205d63ecc7a61") ||
                !matches(r,0x802BB9FC,28,"db75911fb7e122824e25b24eb3e47afef0b3a0358b7149a3b59b3b3550423940") ||
                !matches(r,0x802BBAA4,12,"e625aad4b3400e1c4734e3e20eb4c1b66f55c0a4c7721339447f8aa15317dbd3") ||
                !matches(r,0x8009CC20,40,"e2bb1ad014f6e9f89c3c8fbfb8daf9d7ba74bce2b5766b4787e0a034138402ce")))continue;
            if(matches(r,p.descriptor,p.descriptor_bytes,p.descriptors_sha256) &&
               matches(r,p.segments,p.segment_bytes,p.segments_sha256))return p.kind;
        }catch(...){return PalBackgroundKind::None;}
    }
    return PalBackgroundKind::None;
}
PalBackgroundScope::PalBackgroundScope(std::span<uint8_t> r,bool wide,uint64_t object) noexcept {
    if(background_scope_active)return;
    kind=pal_background_kind(r,wide,object);
    if(kind==PalBackgroundKind::None)return;
    const auto b=pal_gfx_bounds(r);
    // The 40-image paths fit below 256 bytes per tile plus 256 prolog bytes.
    // ScreenCover binds one image once, then emits 150 original 32-byte
    // rectangle groups: 4,880 bytes in the genuine constructor/draw fixture.
    // 12 KiB bounds those paths and material-cache differences; both edge
    // image families reserve 13 KiB with their 384 edge-strip bytes.
    // The genuine CI8 scene emits 5,496 bytes; the20-tile CI4 image2,888.
    if(!b || b.end-b.cursor<(edge_extension(kind)?0x3400u:0x3000u))return;
    ram=r;begin=b.cursor;end=b.end;palette=word(r,uint32_t(object)+0x34);
    const uint32_t prefix[]={0xE0525464,0x10000064,0x64000017,0,
        0x64000005,0x01000000,0,960,0x64000033,edge_extension(kind)?2u:1u};
    for(unsigned i=0;i<10;++i)put(r,begin+4*i,prefix[i]);
    unsigned prefix_size=40;
    if(kind==PalBackgroundKind::CommonMenu){
        // Original canvas begins at x=4,y=2. Align this background alone to0,0;
        // retain its tile UVs and restore ordinary rectangle alignment below.
        const uint32_t align[]={0x64000006,0x00800800,0xfff0fff8,0xfff0fff8};
        for(unsigned i=0;i<4;++i)put(r,begin+40+4*i,align[i]);
        prefix_size+=16;
    }
    put(r,0x8009E0C8,begin+prefix_size);background_scope_active=true;active=true;
}
PalBackgroundScope::~PalBackgroundScope(){
    if(!active)return;
    const auto b=pal_gfx_bounds(ram);
    if(!background_scope_active || !b || b.end!=end || b.cursor<begin+40 || end-b.cursor<(kind==PalBackgroundKind::CommonMenu?32u:16u))std::abort();
    // Every original sprite and other native aspect scope starts atAUTO.
    // Preserve the exact prior scissor by popping its real RT64 stack entry.
    auto cursor=b.cursor;
    // A changed original output path receives no speculative strips. The center
    // still draws at its original aspect and the real state stack is balanced.
    if(edge_extension(kind))extend_image_edges(ram,begin+40,cursor,end,kind,palette);
    if(kind==PalBackgroundKind::CommonMenu){
        repair_common_menu_edges(ram,begin+56,cursor,palette);
        const uint32_t align[]={0x64000006,0x00800800,0,0};
        for(unsigned i=0;i<4;++i)put(ram,cursor+4*i,align[i]);
        cursor+=16;
    }
    const uint32_t suffix[]={0x64000033,0,0x64000018,0};
    for(unsigned i=0;i<4;++i)put(ram,cursor+4*i,suffix[i]);
    put(ram,0x8009E0C8,cursor+16);background_scope_active=false;
}
PalScreenFillScope::PalScreenFillScope(std::span<uint8_t> r,bool wide) noexcept {
    if(background_scope_active || !wide || r.size()!=0x800000 ||
       word(r,0x8009E02C)!=0x8013B418 || byte(r,0x8013B42A)!=0 ||
       half(r,0x8013B42C)!=320 || half(r,0x8013B42E)!=240)return;
    const auto b=pal_gfx_bounds(r);
    // Original019FC emits48bytes, or56with01B2C's FF registration. The
    // balanced56-byte scope fits alongside either branch within128bytes.
    if(!b || b.end-b.cursor<128)return;
    ram=r;begin=b.cursor;end=b.end;
    const uint32_t prefix[]={0xE0525464,0x10000064,0x64000017,0,
        0x64000005,0x01000000,0,960,0x64000033,1};
    for(unsigned i=0;i<10;++i)put(r,begin+4*i,prefix[i]);
    put(r,0x8009E0C8,begin+40);background_scope_active=true;active=true;
}
PalScreenFillScope::~PalScreenFillScope(){
    if(!active)return;
    const auto b=pal_gfx_bounds(ram);
    if(!background_scope_active || !b || b.end!=end || b.cursor<begin+40 || end-b.cursor<16)std::abort();
    const uint32_t suffix[]={0x64000033,0,0x64000018,0};
    for(unsigned i=0;i<4;++i)put(ram,b.cursor+4*i,suffix[i]);
    put(ram,0x8009E0C8,b.cursor+16);background_scope_active=false;
}

bool extend_pal_intro_canvas(std::span<uint8_t> r,bool wide,uint64_t descriptor,
    uint64_t palette,uint64_t segments,uint64_t alpha,uint64_t original_begin) noexcept {
    if(background_scope_active || !wide || r.size()!=0x800000 || alpha>255 ||
       !canonical(descriptor) || !canonical(palette) || !canonical(segments) ||
       !canonical(original_begin) || (original_begin&7) ||
       word(r,0x8009E02C)!=0x8013B418 || byte(r,0x8013B42A)!=0 ||
       half(r,0x8013B42C)!=320 || half(r,0x8013B42E)!=240)return false;
    struct IntroProfile {
        uint32_t descriptor,palette,segments,texture,uv;
        unsigned descriptor_bytes,segment_bytes,texture_bytes,output_bytes;
        std::string_view descriptors_hash,palette_hash,segments_hash,texture_hash,output_hash;
    };
    // Original CI8 logo canvases and their separate plain-white fullcanvas.
    // The selected final-texture texel has an all-white3x3 neighborhood, so
    // bilinear filtering cannot import logo lettering into either side.
    static constexpr IntroProfile intro[]={
        {0x801B7608,0x801AE080,0x801AE280,0x801B27C8,0x00200020,120,1956,1024,4536,
         "aab1fcd86fcbdd941e2334a6ed4d2749bd0a463cbd3c9da1e300644f8d4627a7",
         "3aa3adc2b8b1fd0973aeda578e7f9ca1d41db832455e0433743811ba32161c41",
         "04f9384565d8553a7cfd3f1e2983a2befa1df60cb21ef0bde1f54f726083c2bf",
         "5df920b8aa5547b6225628b91498d0eb1289e6fbcfd7bc9df8dfb82cceb625b4",
         "7c20ae859cf6c524f033714de52642e947b8c0c25b10ce708c81372c2bbcbe79"},
        {0x801B7680,0x801B2BC8,0x801B2DC8,0x801B6448,0x00400020,96,1152,2048,2816,
         "27489e48ef07b50c1dd7511101d48984b4c544061df150f1ee42dc0607a6005b",
         "65d445cb775bd34d73afd10a6ee2c862806a0119c352548a91a894254933adac",
         "701ef379ff51c3e5d8c3a6f0bd6c8b42e6903603eef7074e7360fc218521038e",
         "1cdd16c0fa77bc05efa4c012232fa4ae1729b0a0406b3808792832b100e424aa",
         "7116090a307b9c026e71787d7e384317f28204a6acdbefd8c058ced65bf4c8b2"},
        {0x801B76E0,0x801B7048,0x801B7248,0x801B6C48,0x00200020,12,960,1024,2040,
         "90df21c3ce66cddb5b0c02400cdde707b3c961b1ceba837dd3ae08b385672ffb",
         "c3df945e59726a4213bdb00cd4f2d97ad8a61e0dc06682efabe094d9e3ed163a",
         "61365ed118b6f525cdd79365adafde6307674107840519258f41d00eff589367",
         "5a648d8015900d89664e00e125df179636301a2d8fa191c1aa2bd9358ea53a69",
         "caf89248faf39c25452d9994c50b8728b6bd4eebb60904e1eec35ff7adfb6acb"}
    };
    const auto b=pal_gfx_bounds(r);const auto begin=uint32_t(original_begin),cursor=word(r,0x801B77C0);
    if(!b || begin<b.begin || begin<b.cursor || cursor<begin || cursor>b.end ||
       (cursor&7) || b.end-cursor<104)return false;
    try {
        if(!matches(r,0x801ADD44,816,"25346a1c6b0a1cc4c83a982cb919d54a0d9e137e2658c0ba39766cf797ede7ff") ||
           !matches(r,0x801B7710,144,"3540590540d401f79cc0decd0a340273a28557b3ff75a884c61f221715c4d172"))return false;
        for(const auto& p:intro){
            if(uint32_t(descriptor)!=p.descriptor || uint32_t(palette)!=p.palette ||
               uint32_t(segments)!=p.segments || cursor-begin!=p.output_bytes)continue;
            if(word(r,begin)!=0xDE000000 || word(r,begin+4)!=0x801B7710 ||
               word(r,begin+8)!=0xFA000000 || word(r,begin+12)!=(0xFFFFFF00u|uint32_t(alpha)) ||
               !matches(r,p.descriptor,p.descriptor_bytes,p.descriptors_hash) ||
               !matches(r,p.palette,512,p.palette_hash) ||
               !matches(r,p.segments,p.segment_bytes,p.segments_hash) ||
               !matches(r,p.texture,p.texture_bytes,p.texture_hash))return false;
            // Complete original output pin proves texture/palette binding,
            // every rectangle/UV/step and final bound texture. Only the
            // original fade alpha varies, normalized in this local copy.
            std::array<uint8_t,4536> output{};
            for(unsigned i=0;i<p.output_bytes;++i)output[i]=byte(r,begin+i);
            output[15]=255;
            if(rom_detail::sha256_hex({output.data(),p.output_bytes})!=p.output_hash)return false;
            const uint32_t commands[]={
                0xE0525464,0x10000064,0x64000017,0,
                0x64000005,0x01000000,0,960,0x64000033,2,
                0x64000002,0x04000000,0xFFFC0000,960,p.uv,0,
                0x64000002,0x02004000,0x05000000,0x000403C0,p.uv,0,
                0x64000033,0,0x64000018,0};
            for(unsigned i=0;i<26;++i)put(r,cursor+4*i,commands[i]);
            put(r,0x801B77C0,cursor+104);return true;
        }
    }catch(...){return false;}
    return false;
}

}
