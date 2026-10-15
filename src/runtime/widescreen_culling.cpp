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
constexpr float OriginalAspect=4.f/3.f, WideScale=4.f/3.f;
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

bool apply_widescreen_culling(std::span<uint8_t> ram,bool wide,const WidescreenGuestLayout& layout) noexcept {
    if(!wide)return true;
    if(!original_camera(ram,layout))return false;
    const float h=read(ram,layout.horizontal),v=read(ram,layout.vertical);
    const float far_h=read(ram,layout.far_horizontal),far_v=read(ram,layout.far_vertical);
    const float scaled_h=h*WideScale,scaled_far_h=far_h*WideScale;
    if(!original_pair(h,v) || !original_pair(far_h,far_v) ||
       !std::isfinite(scaled_h) || !std::isfinite(scaled_far_h))return false;
    write(ram,layout.horizontal,scaled_h);
    write(ram,layout.far_horizontal,scaled_far_h);
    return true;
}

bool apply_widescreen_far_extents(std::span<uint8_t> ram,bool wide,const WidescreenGuestLayout& layout) noexcept {
    if(!wide)return true;
    if(!original_camera(ram,layout))return false;
    const float h=read(ram,layout.far_horizontal),v=read(ram,layout.far_vertical),scaled=h*WideScale;
    if(!original_pair(h,v) || !std::isfinite(scaled))return false;
    write(ram,layout.far_horizontal,scaled);
    return true;
}

bool ensure_widescreen_far_extents(std::span<uint8_t> ram,bool wide,const WidescreenGuestLayout& layout) noexcept {
    if(!wide)return true;
    if(!original_camera(ram,layout))return false;
    const float h=read(ram,layout.far_horizontal),v=read(ram,layout.far_vertical);
    if(!std::isfinite(h) || !std::isfinite(v) || h<=0.f || v<=0.f)return false;
    if(approximately(h,double(v)*OriginalAspect*WideScale))return true;
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
            const double middle=(a+b)*.5,half=(a-b)*.5*WideScale;
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
}
