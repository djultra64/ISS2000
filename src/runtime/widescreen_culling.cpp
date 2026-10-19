// Original project work: djultra64.
#include "widescreen_culling.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstring>

namespace iss2000 {
namespace {
constexpr size_t MemorySize=0x800000;
bool valid_layout(const WidescreenGuestLayout& layout) noexcept {
    if(!std::isfinite(layout.horizontal_scale) || layout.horizontal_scale<1.f || layout.horizontal_scale>2.f)return false;
    const std::array<uint32_t,8> starts={layout.aspect,layout.horizontal,
        layout.vertical,layout.far_horizontal,layout.far_vertical,
        layout.corner_axes[0],layout.corner_axes[1],layout.corner_axes[2]};
    for(size_t i=0;i<starts.size();++i){
        const uint64_t start=starts[i],end=start+(i<5?4:16);
        if(start%4 || start<0x80000000 || end>0x80800000)return false;
        for(size_t j=0;j<i;++j){
            const uint64_t other=starts[j],other_end=other+(j<5?4:16);
            if(start<other_end && other<end)return false;
        }
    }
    return true;
}
constexpr float OriginalAspect=4.f/3.f;
float read(std::span<uint8_t> ram,size_t offset) noexcept {
    float value;
    std::memcpy(&value,ram.data()+(offset-0x80000000),sizeof(value));
    return value;
}
void write(std::span<uint8_t> ram,size_t offset,float value) noexcept {
    std::memcpy(ram.data()+(offset-0x80000000),&value,sizeof(value));
}
bool approximately(double a,double b) noexcept {
    return std::abs(a-b)<=1.e-5*std::max({1.e-8,std::abs(a),std::abs(b)});
}
bool original_camera(std::span<uint8_t> ram,const WidescreenGuestLayout& layout) noexcept {
    return ram.size()==MemorySize && valid_layout(layout) && std::isfinite(read(ram,layout.aspect)) &&
        approximately(read(ram,layout.aspect),OriginalAspect);
}
bool original_pair(float horizontal,float vertical) noexcept {
    return std::isfinite(horizontal) && std::isfinite(vertical) &&
        horizontal>0.f && vertical>0.f &&
        approximately(horizontal,double(vertical)*OriginalAspect);
}
}

float pal_widescreen_projection_scale(std::span<const uint8_t> ram) noexcept {
    if(ram.size()!=MemorySize)return 0.f;
    auto word=[&](uint32_t a){uint32_t v;std::memcpy(&v,ram.data()+(a&0x7fffff),4);return v;};
    if(word(0x8009E02C)!=0x8013B418)return 0.f;
    const auto mode=ram[0x13B42A^3];
    if(mode>1 || word(0x8013B42C)!=(mode?0x02800220u:0x014000F0u) ||
       (mode && word(0x8013B430)!=0x80700000))return 0.f;
    constexpr std::array<uint32_t,20> low={0x10000000u,0x0000311Eu,0x00000140u,0x04541E3Au,0x00000271u,0x00170C69u,0x0C6F0C6Du,0x008802F7u,0x00000200u,0x00000000u,0x00000519u,0x00000400u,0x0043024Cu,0x0009026Bu,0x00000002u,0x00000519u,0x00000400u,0x0043024Cu,0x0009026Bu,0x00000002u};
    constexpr std::array<uint32_t,20> high={0x18000000u,0x0000305Eu,0x00000500u,0x04541E3Au,0x00000270u,0x00170C69u,0x0C6F0C6Du,0x008802F7u,0x00000400u,0x00000000u,0x00000519u,0x00000400u,0x0043024Cu,0x0009026Bu,0x00000002u,0x00000519u,0x00000400u,0x0043024Cu,0x000D0269u,0x00000002u};
    // Low retains the pre-existing camera correction. Its live osViSetYScale
    // state is separate from the stored mode table; do not infer it here.
    if(!mode)return 4.f/3.f;
    const auto& expected=mode?high:low;
    const auto base=mode?0x80099040u:0x80098DC0u;
    for(unsigned i=0;i<20;++i)if(word(base+i*4)!=expected[i])return 0.f;
    // Pinned VI::fbSize: interlace stride correction, PAL visible rows,
    // then the same two filter rows and nearest multiple-of-four rounding.
    unsigned width=expected[2];
    const float x_scale=1024.f/(expected[8]&0xfff),y_scale=1024.f/(expected[11]&0xfff);
    const unsigned h_start=expected[7]>>16,h_end=expected[7]&0xffff;
    const unsigned v_start=expected[12]>>16,v_end=expected[12]&0xffff;
    if((expected[1]&0x40) && (h_end-h_start)/x_scale<width/1.875f)width/=2;
    unsigned height=std::lround(float(v_end-v_start)/(2.f*y_scale*(float(width)/expected[2])));
    height=std::lround(float(height+2)/4.f)*4;
    return (16.f/9.f)/(float(width)/height);
}

bool apply_widescreen_culling(std::span<uint8_t> ram,bool wide,const WidescreenGuestLayout& layout) noexcept {
    if(!wide)return true;
    if(!original_camera(ram,layout))return false;
    const float h=read(ram,layout.horizontal),v=read(ram,layout.vertical);
    const float far_h=read(ram,layout.far_horizontal),far_v=read(ram,layout.far_vertical);
    const float scaled_h=h*layout.horizontal_scale,scaled_far_h=far_h*layout.horizontal_scale;
    if(!original_pair(h,v) || !original_pair(far_h,far_v) ||
       !std::isfinite(scaled_h) || !std::isfinite(scaled_far_h))return false;
    write(ram,layout.horizontal,scaled_h);
    write(ram,layout.far_horizontal,scaled_far_h);
    return true;
}

bool apply_widescreen_far_extents(std::span<uint8_t> ram,bool wide,const WidescreenGuestLayout& layout) noexcept {
    if(!wide)return true;
    if(!original_camera(ram,layout))return false;
    const float h=read(ram,layout.far_horizontal),v=read(ram,layout.far_vertical),scaled=h*layout.horizontal_scale;
    if(!original_pair(h,v) || !std::isfinite(scaled))return false;
    write(ram,layout.far_horizontal,scaled);
    return true;
}

bool ensure_widescreen_far_extents(std::span<uint8_t> ram,bool wide,const WidescreenGuestLayout& layout) noexcept {
    if(!wide)return true;
    if(!original_camera(ram,layout))return false;
    const float h=read(ram,layout.far_horizontal),v=read(ram,layout.far_vertical);
    if(!std::isfinite(h) || !std::isfinite(v) || h<=0.f || v<=0.f)return false;
    if(approximately(h,double(v)*OriginalAspect*layout.horizontal_scale))return true;
    return apply_widescreen_far_extents(ram,true,layout);
}

bool apply_widescreen_world_corners(std::span<uint8_t> ram,bool wide,const WidescreenGuestLayout& layout) noexcept {
    if(!wide)return true;
    if(!original_camera(ram,layout))return false;
    std::array<std::array<float,3>,4> rays{},result{};
    double horizontal_length_squared=0.;
    for(size_t axis=0;axis<3;++axis){
        for(size_t corner=0;corner<4;++corner){
            rays[corner][axis]=read(ram,layout.corner_axes[axis]+corner*4);
            if(!std::isfinite(rays[corner][axis]))return false;
        }
        // Both pairs share the same camera-horizontal vector. Compare the
        // parallelogram sums with a magnitude-based rounding tolerance.
        const double left=double(rays[0][axis])+rays[3][axis];
        const double right=double(rays[1][axis])+rays[2][axis];
        const double magnitude=std::max({1.,std::abs(left),std::abs(right)});
        if(std::abs(left-right)>1.e-5*magnitude)return false;
        const double difference=double(rays[0][axis])-rays[1][axis];
        horizontal_length_squared+=difference*difference;
        for(size_t first=0;first<4;first+=2){
            const double a=rays[first][axis],b=rays[first+1][axis];
            const double middle=(a+b)*.5,half=(a-b)*.5*layout.horizontal_scale;
            result[first][axis]=float(middle+half);
            result[first+1][axis]=float(middle-half);
            if(!std::isfinite(result[first][axis]) ||
               !std::isfinite(result[first+1][axis]))return false;
        }
    }
    if(horizontal_length_squared<=1.e-16)return false;
    for(size_t axis=0;axis<3;++axis)
        for(size_t corner=0;corner<4;++corner)
            write(ram,layout.corner_axes[axis]+corner*4,result[corner][axis]);
    return true;
}
bool pal_player_culling_disabled(std::span<const uint8_t> ram,uint64_t object) noexcept {
    if(ram.size()!=MemorySize)return false;
    const auto low=uint32_t(object);
    if(object!=low&&object!=uint64_t(int64_t(int32_t(low))))return false;
    auto word=[&](uint32_t a){uint32_t v;std::memcpy(&v,ram.data()+(a&0x7fffff),4);return v;};
    auto half=[&](uint32_t a){uint16_t v;std::memcpy(&v,ram.data()+((a&0x7fffff)^2),2);return v;};
    auto byte=[&](uint32_t a){return ram[(a&0x7fffff)^3];};
    if(word(0x8009e02c)!=0x8013b418||byte(0x8013b446)!=6||byte(0x8013b44c)!=4)return false;
    const auto mode=byte(0x8013b42a);
    if(mode>1||word(0x8013b42c)!=(mode?0x02800220u:0x014000f0u))return false;
    auto record=[](uint32_t p,bool root){const auto base=root?0x80145624u:0x8014ff5cu,stride=root?0x98u:0x60u,count=root?285u:900u;
        return p>=base&&p<base+stride*count&&(p-base)%stride==0;};
    if(!record(low,true)||(word(low+0x28)&0x80000000u)==0||word(low+0x44)!=0)return false;
    // Original8002DC24 initializes exactly22 football players; goalkeeper slots
    //0/11 retain selector2; outfield detail can be0 (maximum) or1. State allocation
    //8002D894 advances this table by100h; later referee/staff states are excluded.
    const auto state=word(low+0x84);
    if(state<0x801a07cc||state>=0x801a07cc+22*0x100||(state-0x801a07cc)%0x100||word(state)!=low)return false;
    const auto detail=half(state+0xb8);if(detail>2)return false;
    std::array<uint32_t,19> rig{};
    for(unsigned n=0;n<rig.size();++n){const auto p=word(state+n*4);
        if(!record(p,n==0)||(word(p+0x28)&0x80000000u)==0)return false;
        for(unsigned previous=0;previous<n;++previous)if(rig[previous]==p)return false;
        rig[n]=p;
    }
    if(word(low+0x48)!=rig[1])return false;
    // Cursor/name markers can be siblings of a hand (live field rigs9/18).
    // They do not own this player and must not invalidate its reciprocal rig.
    for(unsigned n=1;n<rig.size();++n)for(unsigned field:{0x44u,0x48u}){
        const auto link=word(rig[n]+field);
        if(link&&std::find(rig.begin(),rig.end(),link)==rig.end())return false;
    }
    return true;
}

}
