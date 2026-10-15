// Original project work: djultra64.
#pragma once
#include <chrono>
#include <cmath>
#include <cstdint>
#include <limits>
#include <optional>
#include <stdexcept>
namespace iss2000 {
struct VideoTiming {
    uint32_t vi_hz;
    uint32_t audio_clock;
    std::chrono::microseconds deadline(uint64_t total_vis,uint32_t speed) const {
        if(!vi_hz || !speed)throw std::invalid_argument("VI cadence and speed must be positive");
        return std::chrono::microseconds(total_vis*1000000ull)/(uint64_t(vi_hz)*speed);
    }
    template<class Rep,class Period>
    uint64_t elapsed_vis(std::chrono::duration<Rep,Period> elapsed,uint32_t speed) const {
        if(!vi_hz || !speed)throw std::invalid_argument("VI cadence and speed must be positive");
        return (elapsed*(uint64_t(vi_hz)*speed)/std::chrono::seconds(1))+1;
    }
};
inline constexpr VideoTiming pal_video_timing{50,49656530};
inline constexpr VideoTiming ntsc_video_timing{60,48681812};
struct AudioFrequency {uint32_t divider,bitrate,actual_hz;};
// Original PAL osAiSetFrequency uses single-precision division and rounding,
// minimum divider 132, then returns the integer hardware clock/divider.
inline std::optional<AudioFrequency> audio_frequency(uint32_t requested,uint32_t clock) {
    if(!requested || !clock)return std::nullopt;
    const float quotient=float(clock)/float(requested);
    const float rounded=quotient+0.5f;
    if(!std::isfinite(rounded) || double(rounded)>double(std::numeric_limits<uint32_t>::max()))return std::nullopt;
    const uint32_t divider=uint32_t(rounded);
    if(divider<132)return std::nullopt;
    const uint32_t bits=(divider/66)&0xFFu;
    return AudioFrequency{divider,bits<16?bits:16,clock/divider};
}
}
