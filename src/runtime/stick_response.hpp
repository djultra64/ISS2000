// Original project work: djultra64.
#pragma once
#include <algorithm>
#include <cmath>
namespace iss2000 {
struct StickPosition {float x{},y{};};
// Continuous radial deadzone and a gentler low/mid response. Full deflection
// keeps the original maximum running/aiming range; menu navigation stays raw.
inline StickPosition gameplay_stick_response(float x,float y) noexcept {
    if(!std::isfinite(x)||!std::isfinite(y))return {};
    x=std::clamp(x,-1.f,1.f);y=std::clamp(y,-1.f,1.f);
    const float length=std::sqrt(x*x+y*y);
    constexpr float deadzone=.15f;
    if(length<=deadzone)return {};
    const float magnitude=(std::min(length,1.f)-deadzone)/(1.f-deadzone);
    const float response=magnitude*(.5f+.5f*magnitude);
    return {x/length*response,y/length*response};
}
}
