// Original project work: djultra64.
#include "pal_hud_widescreen.hpp"
#include "pal_sky_widescreen.hpp"
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
bool match_scene(std::span<const uint8_t> r,bool wide){
    return wide && r.size()==0x800000 && word(r,0x8009E02C)==0x8013B418 &&
        byte(r,0x8013B446)==6 && byte(r,0x8013B44C)==4 &&
        byte(r,0x8013B452)==0 && byte(r,0x8012DE27)<=1 &&
        byte(r,0x8013B42A)==0 && word(r,0x80143D6C)==0x80261E68;
}
PalHudPlacement placement(PalHudGroup group){
    switch(group){
    case PalHudGroup::Score:return {group,0,-24,4};
    case PalHudGroup::Clock:return {group,0x400,-1284,12};
    case PalHudGroup::LeftPlayer:return {group,0,-40,-28};
    case PalHudGroup::RightPlayer:return {group,0x400,-1240,-28};
    default:return {};
    }
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
    case 38:return p==0x80076F1C;
    case 39:return p==0x80076F28;
    case 26:case 29:case 36:case 37:case 43:
        return p>=0x80259918 && p<=0x8025A220 && (p-0x80259918)%12==0;
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
        return placement(a==0x801650DC?PalHudGroup::LeftPlayer:PalHudGroup::RightPlayer);
    }
    if(draw!=PalHudDraw::Sprite || a<0x8013C47C || (a-0x8013C47C)%0x3c)return {};
    const unsigned id=(a-0x8013C47C)/0x3c;
    const auto group=sprite_group(id);
    if(group==PalHudGroup::None)return {};
    if(byte(r,a+4)!=1 || byte(r,a+5)!=11 || !descriptor(id,word(r,a+0x14)) ||
       word(r,a+0x28)!=0x3f800000 || word(r,a+0x2c)!=0x3f800000)return {};
    const auto segments=word(r,a+0x30);
    if(segments<0x8026182C || segments>0x80261D24 || (segments-0x8026182C)%12)return {};
    // Original sign-bit terminator and 12-byte records; bound original work
    // before reserving the original emitter's output plus our balanced scope.
    bool terminated=false;
    for(unsigned n=0;n<16;++n){
        const auto p=segments+12*n;
        if(p>0x80261D24)return {};
        const auto tag=byte(r,p);
        if(tag!=0 && tag!=0x10 && tag!=0x80 && tag!=0x90)return {};
        if(tag&0x80){terminated=true;break;}
    }
    if(!terminated)return {};
    return placement(group);
}
PalHudScope::PalHudScope(std::span<uint8_t> r,bool wide,PalHudDraw draw,uint64_t object) noexcept {
    if(hud_scope_active)return;
    const auto p=pal_hud_placement(r,wide,draw,object);
    if(!p)return;
    const auto bounds=pal_gfx_bounds(r);
    // Reserve ample original-output headroom as well as48 prefix/24 suffix
    // bytes; never invent a Gfx array or extend its original64KiB boundary.
    if(!bounds || bounds.end-bounds.cursor<0x3000)return;
    ram=r;end=bounds.end;begin=bounds.cursor;
    const auto packed=(uint32_t(uint16_t(p.x_offset))<<16)|uint16_t(p.y_offset);
    const uint32_t prefix[]={0xE0525464,0x10000064,0x64000017,0,
        0x64000005,0x01000000,0,960,
        0x64000006,uint32_t(p.origin)|(uint32_t(p.origin)<<12),packed,packed};
    for(unsigned n=0;n<12;++n)put(r,begin+4*n,prefix[n]);
    put(r,0x8009E0C8,begin+48);hud_scope_active=true;active=true;
}
PalHudScope::~PalHudScope(){
    if(!active)return;
    const auto b=pal_gfx_bounds(ram);
    if(!hud_scope_active || !b || b.end!=end || b.cursor<begin+48 || end-b.cursor<24)std::abort();
    const uint32_t suffix[]={0x64000006,0x00800800,0,0,0x64000018,0};
    for(unsigned n=0;n<6;++n)put(ram,b.cursor+4*n,suffix[n]);
    put(ram,0x8009E0C8,b.cursor+24);hud_scope_active=false;
}
}
