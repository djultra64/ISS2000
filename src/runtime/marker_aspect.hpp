// Original project work: djultra64.
#pragma once
#include <cmath>
namespace iss2000 {
// Local forward/reverse marker coordinates share the target aspect. Guest
// projection, centered 2D layout and all global RAM remain unchanged.
inline float marker_aspect(float original,bool wide) noexcept {
    if(wide && std::isfinite(original) && std::abs(original-4.f/3.f)<1e-5f)
        return 16.f/9.f;
    return original;
}
}
