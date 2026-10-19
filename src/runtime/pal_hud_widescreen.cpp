// Original project work: djultra64.
#include "pal_hud_widescreen.hpp"
#include "pal_sky_widescreen.hpp"
#include "rom_image.hpp"
#include <array>
#include <cstdlib>
#include <cstring>
namespace iss2000 {
namespace {
thread_local bool hud_scope_active{};
uint32_t word(std::span<const uint8_t> r,uint32_t a){uint32_t v;std::memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
uint8_t byte(std::span<const uint8_t> r,uint32_t a){return r[(a&0x7fffff)^3];}
void put(std::span<uint8_t> r,uint32_t a,uint32_t v){std::memcpy(r.data()+(a&0x7fffff),&v,4);}
bool canonical(uint64_t address){
    const auto lo=uint32_t(address),hi=uint32_t(address>>32);
    return (hi==0 || (hi==0xffffffffu && (lo&0x80000000u))) &&
        (lo&0xff800003u)==0x80000000u;
}
bool verified_video(std::span<const uint8_t> r){
    const auto mode=byte(r,0x8013B42A);
    if(mode==0)return true; // Preserve the reviewed original Low path.
    if(mode!=1 || word(r,0x8013B42C)!=0x02800220 ||
       word(r,0x8013B430)!=0x80700000)return false;
    // The original High sprite leaf doubles rectangles and halves derivatives.
    // Bind its complete original body, not just an otherwise reusable mode bit.
    std::array<uint8_t,0x2B4> body{};
    for(unsigned i=0;i<body.size();++i)body[i]=byte(r,0x807AA008+i);
    try{return rom_detail::sha256_hex(body)==
        "62ff104079488a6d81386c421054368bde897818652c8d1365a597881342fe50";
    }catch(...){return false;}
}
bool match_scene(std::span<const uint8_t> r,bool wide){
    return wide && r.size()==0x800000 && word(r,0x8009E02C)==0x8013B418 &&
        byte(r,0x8013B446)==6 && byte(r,0x8013B44C)==4 &&
        byte(r,0x8013B452)==0 && byte(r,0x8012DE27)<=1 &&
        verified_video(r) && word(r,0x80143D6C)==0x80261E68;
}
// Pinned VI source extents are232 visible Low rows and524 visible High rows.
// High's original radar ends at452; Low already ends at226. These offsets
// align their lower edges near698/720 without moving Low beyond its VI crop.
int radar_bottom_offset(bool high){return high?224:-4;}
PalHudPlacement placement(PalHudGroup group,bool high){
    auto result=[&]() -> PalHudPlacement {switch(group){
    case PalHudGroup::Score:return {group,0,-24,4};
    case PalHudGroup::Clock:return {group,0x400,-1284,0};
    // Quarter-screen origins center each complete 94-pixel player envelope
    // between its screen edge and the unchanged radar (native x120..200).
    // RDP first adds the native origin (80/240), so offset -93/-226
    // makes original centers 73/246 become viewport coordinates 60/260.
    // This preserves the midpoint at every host aspect/VI crop and scale.
    case PalHudGroup::LeftPlayer:return {group,0x100,-372,-28};
    case PalHudGroup::RightPlayer:return {group,0x300,-904,-28};
    case PalHudGroup::Radar:return {group,0x800,0,0};
    default:return {};
    }}();
    if(high){result.x_offset*=2;result.y_offset*=2;}
    if(group==PalHudGroup::Radar || group==PalHudGroup::LeftPlayer || group==PalHudGroup::RightPlayer)
        result.y_offset+=radar_bottom_offset(high);
    return result;
}
PalHudGroup sprite_group(unsigned id){
    switch(id){
    case 1:case 3:case 4:case 7:case 9:case 11:case 12:case 20:case 24:case 25:case 26:
        return PalHudGroup::LeftPlayer;
    case 2:case 5:case 6:case 8:case 10:case 13:case 14:case 21:case 27:case 28:case 29:
        return PalHudGroup::RightPlayer;
    default:
        if(id>=30 && id<=35)return PalHudGroup::Score;
        if(id>=36 && id<=43)return PalHudGroup::Clock;
        return PalHudGroup::None;
    }
}
bool descriptor(unsigned id,uint32_t p){
    const bool match_asset=p>=0x80259918 && p<=0x8025A220 && (p-0x80259918)%12==0;
    switch(id){
    case 1:case 2:return p==0x80076F70;
    case 3:case 4:case 5:case 6:return p==0x80076F88;
    case 7:case 8:return p==0x80076F94;
    case 9:case 10:return p==0x80076F10;
    case 11:case 12:case 13:case 14:case 31:case 32:case 33:case 34:case 35:
    case 40:case 41:case 42:return p==0x80076EF8;
    case 20:case 21:return p==0x80076F04;
    case 24:case 25:case 27:case 28:return p==0x80076F4C;
    case 30:return p==0x80076F7C;
    case 37:return p==0x80076F7C || match_asset;
    case 38:return p==0x80076F1C || p==0x80076F7C;
    case 39:return p==0x80076F28 || p==0x80076EF8;
    case 43:return p==0x80076F28 || match_asset;
    case 26:case 29:case 36:
        return match_asset;
    default:return false;
    }
}
}
PalHudPlacement pal_hud_placement(std::span<const uint8_t> r,bool wide,PalHudDraw draw,uint64_t object) noexcept {
    if(!match_scene(r,wide))return {};
    if(draw==PalHudDraw::ScoreFlags){
        // The separate original flag compositor belongs to this score panel.
        return pal_hud_placement(r,wide,PalHudDraw::Sprite,0x8013CB84);
    }
    if(!canonical(object))return {};
    const auto a=uint32_t(object);
    if(draw==PalHudDraw::Text){
        if(a!=0x801650DC && a!=0x80165104)return {};
        const auto source=word(r,a+0x14);
        if(byte(r,a+4)!=2 || byte(r,a+6)!=11 || !canonical(source))return {};
        return placement(a==0x801650DC?PalHudGroup::LeftPlayer:PalHudGroup::RightPlayer,byte(r,0x8013B42A)==1);
    }
    if(draw!=PalHudDraw::Sprite || a<0x8013C47C || (a-0x8013C47C)%0x3c)return {};
    const unsigned id=(a-0x8013C47C)/0x3c;
    const auto group=id==0?PalHudGroup::Radar:sprite_group(id);
    if(group==PalHudGroup::None)return {};
    if(group==PalHudGroup::Radar){
        if(byte(r,a+4)!=1 || byte(r,a+5)!=11 || word(r,a+0x14)!=0x80259918 ||
           word(r,a+0x34)!=0x8006D718 || word(r,a+0x28)!=0x3f800000 ||
           word(r,a+0x2c)!=0x3f800000 || word(r,a+0x30)!=0x80261B44 ||
           word(r,0x80259918)!=0x00400040 || word(r,0x8025991c)!=0x010c0000 ||
           word(r,0x80259920)!=0x80201280)return {};
        std::array<uint8_t,168> body{};
        for(unsigned i=0;i<body.size();++i)body[i]=byte(r,0x80261B44+i);
        try{if(rom_detail::sha256_hex(body)!="e4d87004cd8e844afe34e517e232d7dde65ac9f00563ca691067bd52750d1186")return {};}catch(...){return {};}
        return placement(group,byte(r,0x8013B42A)==1);
    }
    if(byte(r,a+4)!=1 || byte(r,a+5)!=11 || !descriptor(id,word(r,a+0x14)) ||
       word(r,a+0x28)!=0x3f800000 || word(r,a+0x2c)!=0x3f800000)return {};
    const auto segments=word(r,a+0x30);
    const auto image=word(r,a+0x14);
    // Original801DBD88 changes these same clock objects in numeric mode.
    // ResourcesBA/BB use native panels, andBD/BE supply the period label.
    // Keep the exact variant/segment pairing; a nearby UI object is unrelated.
    const bool numeric_period=id==43 && image==0x80076F28;
    if((id==37 && image==0x80076F7C && segments!=0x80261C70) ||
       (id==38 && image==0x80076F7C && segments!=0x80261C7C) ||
       (id==39 && image==0x80076EF8 && segments!=0x80261C88) ||
       (numeric_period && segments!=0x80261D30 && segments!=0x80261D3C))return {};
    const uint32_t last_segment=numeric_period?0x80261D3C:0x80261D24;
    if(segments<0x8026182C || segments>last_segment || (segments-0x8026182C)%12)return {};
    // Original sign-bit terminator and 12-byte records; bound original work
    // before reserving the original emitter's output plus our balanced scope.
    bool terminated=false;
    for(unsigned n=0;n<16;++n){
        const auto p=segments+12*n;
        if(p>last_segment)return {};
        const auto tag=byte(r,p);
        if(tag!=0 && tag!=0x10 && tag!=0x80 && tag!=0x90)return {};
        if(tag&0x80){terminated=true;break;}
    }
    if(!terminated)return {};
    return placement(group,byte(r,0x8013B42A)==1);
}
bool repair_pal_radar_background(std::span<uint8_t> r,bool wide,uint32_t begin,uint32_t end) noexcept {
    if(!pal_hud_placement(r,wide,PalHudDraw::Sprite,0x8013C47C) || byte(r,0x8013B42A)!=1 ||
       begin%8 || end%8 || end<begin || end-begin>0x3000 ||
       begin<0x800D0320 || end>0x800F03E0)return false;
    constexpr std::array<std::array<int,6>,14> pieces{{
        {240,340,320,452,0,0},{320,340,336,452,40,0},
        {336,372,352,420,48,16},{336,340,352,372,32,0},
        {336,420,352,452,32,40},{368,372,384,388,0,56},
        {384,372,400,388,8,56},{368,388,384,404,16,56},
        {384,388,400,404,24,56},{368,404,384,420,32,56},
        {384,404,400,420,40,56},{352,372,368,420,56,16},
        {352,340,400,372,1000,0},{352,420,400,452,1000,40}}};
    std::array<uint32_t,42> commands{};unsigned count=0;bool texture=false;
    for(auto pc=begin;pc<end;pc+=8){const auto a=word(r,pc),b=word(r,pc+4);
        if(a>>24==0xFD && b==0x80201280)texture=true;
        if(a>>24!=0xE4)continue;
        if(!texture || count==commands.size() || end-pc<24 ||
           word(r,pc+8)!=0xE1000000 || word(r,pc+16)!=0xF1000000)return false;
        commands[count++]=pc;pc+=16;
    }
    if(count!=commands.size())return false;
    for(unsigned i=0;i<pieces.size();++i){const auto& p=pieces[i];
        const std::array<std::array<int,7>,3> expected{{
            {p[0]*4,p[1]*4,p[2]*4-1,p[3]*4,p[4]*32,p[5]*32,0x02000200},
            {p[2]*4,p[1]*4,p[2]*4+4,p[3]*4,(p[4]+(p[2]-p[0])/2)*32-40,p[5]*32,0x04000200},
            {p[0]*4,p[3]*4,p[2]*4,p[3]*4+4,p[4]*32,(p[5]+(p[3]-p[1])/2)*32-40,0x02000400}}};
        for(unsigned j=0;j<3;++j){const auto pc=commands[3*i+j];const auto& e=expected[j];
            if(word(r,pc)!=(0xE4000000u|uint32_t(e[2]<<12)|uint32_t(e[3])) ||
               word(r,pc+4)!=(uint32_t(e[0]<<12)|uint32_t(e[1])) ||
               word(r,pc+12)!=(uint32_t(e[4])<<16|uint32_t(e[5])) ||
               word(r,pc+20)!=uint32_t(e[6]))return false;
        }
    }
    // One-cycle primary bounds round up to the exact next piece boundary.
    // Appended strips therefore double-blend a neighbor; preserve every other
    // command and neutralize only those proven28 redundant rectangles.
    for(unsigned i=0;i<commands.size();++i)if(i%3){const auto pc=commands[i];
        put(r,pc,0xE4000000u|(word(r,pc+4)&0x00FFFFFFu));}
    return true;
}
bool align_pal_radar_marker(std::span<uint8_t> r,bool wide,uint32_t begin) noexcept {
    const auto placement=pal_hud_placement(r,wide,PalHudDraw::Sprite,0x8013C47C);
    if(!placement || byte(r,0x8012E6A3)>1)return false;
    const bool high=byte(r,0x8013B42A)==1;
    const unsigned buffer=(unsigned(byte(r,0x8013B418))<<8)|byte(r,0x8013B419);
    if(buffer>1)return false;
    const uint32_t first=0x802B4408+buffer*0x960,last=first+0x960;
    const auto owner=word(r,0x802B2950);
    if(owner<0x80145624 || (owner-0x80145624)%0x98 || (owner-0x80145624)/0x98>=285 ||
       !(word(r,owner+0x28)&0x80000000u) || word(r,owner+0x7C)!=0x802A5290 ||
       word(r,owner+0x24)!=first || begin%8 || begin<first || begin>last-24 ||
       word(r,0x802B4400)!=begin+24)return false;
    const auto a=word(r,begin),b=word(r,begin+4);
    if(a>>24!=0xE4 || word(r,begin+8)!=0xE1000000 ||
       word(r,begin+16)!=0xF1000000 || word(r,begin+20)!=(high?0x02000200u:0x04000400u))return false;
    const int top=b&0xfff,bottom=a&0xfff,shift=placement.y_offset;
    // Both original flat/projected producers emit8x8logical markers. Preserve
    // their distinct world projection, UVs, derivatives and every other word.
    if(bottom!=top+(high?64:32) || (a>>12&0xfff)!=(b>>12&0xfff)+(high?64:32) ||
       top+shift<0 || bottom+shift>=(high?524:232)*4)return false;
    const auto uv=word(r,begin+12);const unsigned u=uv>>16,v=uv&0xffffu;
    if((u|v)&255u || u>24*32u || v>24*32u)return false;
    // HLE source endpoints are quantized to1/32texel; shader POINT rounds to
    //1/128. Keep the complete8x8 cell, but put the endpoint1/32inside it.
    // At native integer and half-texel sample positions all8 texels survive.
    put(r,begin+12,((u+7)<<16)|(v+7));
    put(r,begin+20,high?0x01F001F0u:0x03E003E0u);
    put(r,begin,(a&~0xfffu)|uint32_t(bottom+shift));
    put(r,begin+4,(b&~0xfffu)|uint32_t(top+shift));
    return true;
}
bool align_pal_training_radar_marker(std::span<uint8_t> r,bool wide,uint32_t begin) noexcept {
    return align_pal_radar_marker(r,wide,begin);
}

PalHudScope::PalHudScope(std::span<uint8_t> r,bool wide,PalHudDraw draw,uint64_t object) noexcept {
    if(hud_scope_active)return;
    const auto p=pal_hud_placement(r,wide,draw,object);
    if(!p)return;
    const auto bounds=pal_gfx_bounds(r);
    // Reserve ample original-output headroom as well as48 prefix/24 suffix
    // bytes; never invent a Gfx array or extend its original64KiB boundary.
    if(!bounds || bounds.end-bounds.cursor<0x3000)return;
    ram=r;end=bounds.end;begin=bounds.cursor;radar=p.group==PalHudGroup::Radar;
    const auto packed=(uint32_t(uint16_t(p.x_offset))<<16)|uint16_t(p.y_offset);
    const uint32_t prefix[]={0xE0525464,0x10000064,0x64000017,0,
        0x64000005,0x01000000,0,byte(r,0x8013B42A)==1?2176u:960u,
        0x64000006,uint32_t(p.origin)|(uint32_t(p.origin)<<12),packed,packed};
    for(unsigned n=0;n<12;++n)put(r,begin+4*n,prefix[n]);
    put(r,0x8009E0C8,begin+48);hud_scope_active=true;active=true;
}
PalHudScope::~PalHudScope(){
    if(!active)return;
    const auto b=pal_gfx_bounds(ram);
    if(!hud_scope_active || !b || b.end!=end || b.cursor<begin+48 || end-b.cursor<24)std::abort();
    if(radar)repair_pal_radar_background(ram,true,begin+48,b.cursor);
    const uint32_t suffix[]={0x64000006,0x00800800,0,0,0x64000018,0};
    for(unsigned n=0;n<6;++n)put(ram,b.cursor+4*n,suffix[n]);
    put(ram,0x8009E0C8,b.cursor+24);hud_scope_active=false;
}
}
