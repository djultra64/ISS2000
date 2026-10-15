// Original project work: djultra64.
#include "pal_sky_widescreen.hpp"
#include <algorithm>
#include <cstring>
#include <cstdlib>
namespace iss2000 {
namespace {
thread_local uint32_t scope_end{};
thread_local uint8_t* scope_ram{};
uint32_t word(std::span<const uint8_t> r,uint32_t address){uint32_t v{};std::memcpy(&v,r.data()+(address&0x7fffff),4);return v;}
void put(std::span<uint8_t> r,uint32_t address,uint32_t v){std::memcpy(r.data()+(address&0x7fffff),&v,4);}
bool range(std::span<const uint8_t> r,uint32_t cursor,uint32_t end,uint32_t bytes){
    return (cursor&0xFF800007u)==0x80000000u && (end&0xFF800007u)==0x80000000u &&
        end>=cursor && end-cursor>=bytes && (end&0x7fffff)<=r.size();
}
}
PalGfxBounds pal_gfx_bounds(std::span<const uint8_t> r) noexcept {
    if(r.size()!=0x800000)return {};
    const auto base=word(r,0x800A4AA4),cursor=word(r,0x8009E0C8);
    if(base!=0x800D0320 && base!=0x800E0380)return {};
    const auto begin=base+8,end=base+0x10008;
    if(cursor<begin || !range(r,cursor,end,0))return {};
    return {begin,end,cursor};
}
PalSkyRectangle pal_sky_rectangle(int32_t x,int32_t y,uint32_t flags,bool high) noexcept {
    PalSkyRectangle out;
    if(x < -128 || x>448 || y < -32 || y>512)return out;
    const int scale=high?2:1;
    const int raw_left=(3*x+160)*scale,raw_right=raw_left+192*scale;
    const int left=std::max(raw_left,0),right=std::min(raw_right,1280*scale);
    const int top=std::max(y,0),bottom=std::min(y+32,239);
    if(left>=right || top>=bottom)return out;
    const int s=((left-raw_left)*32+3*scale/2)/(3*scale)+((flags&0x80)?64*32:0);
    const int t=(32+top-y)*32;
    const uint32_t dsdx=high?2731:5461,dtdy=high?512:1024;
    out.visible=true;
    out.words={0xE4000000u|(uint32_t(right)<<12)|uint32_t(bottom*4*scale),
        (uint32_t(left)<<12)|uint32_t(top*4*scale),0xE1000000u,
        (uint32_t(s)<<16)|uint32_t(t),0xF1000000u,(dsdx<<16)|dtdy};
    return out;
}
bool pal_sky_preflight(std::span<const uint8_t> r,bool wide) noexcept {
    if(!wide)return false;
    const auto b=pal_gfx_bounds(r);
    if(!b || b.end-b.cursor<0xA20)return false;
    // Exact original 24x14 table relevant to normalized row0..16+7. Every
    // row alternates two different texture IDs: at most 8*4=32 records per
    // texture, below its 39 usable entries plus the original terminator.
    for(unsigned row=0;row<24;++row)for(unsigned col=0;col<14;++col){
        const unsigned even=row<10?0:row<17?(row-9)*2:14;
        if(r[(0x8384c+row*14+col)^3]!=(even+(col&1)))return false;
    }
    return true;
}
uint32_t append_pal_sky_rectangle(std::span<uint8_t> r,uint32_t cursor,uint32_t end,
    int32_t x,int32_t y,uint32_t flags,bool high) noexcept {
    const auto q=pal_sky_rectangle(x,y,flags,high);
    if(!q.visible)return cursor;
    if(!range(r,cursor,end,24))return 0;
    for(unsigned i=0;i<6;++i)put(r,cursor+i*4,q.words[i]);
    return cursor+24;
}
PalSkyWriteScope::PalSkyWriteScope(std::span<uint8_t> r,bool wide) noexcept {
    if(!pal_sky_preflight(r,wide))return;
    previous_end=scope_end;previous_ram=scope_ram;
    scope_end=pal_gfx_bounds(r).end;scope_ram=r.data();active=true;
}
PalSkyWriteScope::~PalSkyWriteScope(){if(active){scope_end=previous_end;scope_ram=previous_ram;}}
}
extern "C" uint32_t iss2000_pal_sky_emit(uint8_t* ram,uint32_t cursor,int32_t x,int32_t y,uint32_t flags,int high){
    using namespace iss2000;
    if(ram!=scope_ram || !scope_end)std::abort();
    const auto next=append_pal_sky_rectangle({ram,0x800000},cursor,scope_end,x,y,flags,high!=0);
    if(!next)std::abort();
    return next;
}
extern "C" void iss2000_pal_sky_aspect(uint8_t* ram,int wide){
    using namespace iss2000;
    if(ram!=scope_ram || !scope_end)std::abort();
    std::span<uint8_t> r{ram,0x800000};auto cursor=word(r,0x8009E0C8);
    const uint32_t bytes=wide?16:8;
    if(!range(r,cursor,scope_end,bytes))std::abort();
    if(wide){ // F3DEX2's native no-op enables the pinned RT64 extended opcode.
        put(r,cursor,0xE0525464);put(r,cursor+4,0x10000064);cursor+=8;
    }
    put(r,cursor,0x64000033);put(r,cursor+4,wide?1:0);cursor+=8;
    put(r,0x8009E0C8,cursor);
}
