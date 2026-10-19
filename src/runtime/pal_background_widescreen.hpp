// Original project work: djultra64.
#pragma once
#include <cstdint>
#include <span>
namespace iss2000 {
enum class PalBackgroundKind { None, CommonMenu, Career, ScriptedImage, ScreenCover, SceneImage, GlobeImage, GradientCover, ResultCover, MenuHorizontalWatermark, MenuVerticalWatermark };
PalBackgroundKind pal_background_kind(std::span<const uint8_t>,bool wide,uint64_t object) noexcept;
// Scoped around only the reviewed original80041B50 sprite emitter. Original
// geometry/UV/color commands remain unchanged; foreground draws receive none.
class PalBackgroundScope {
    std::span<uint8_t> ram;
    uint32_t begin{},end{},palette{};
    PalBackgroundKind kind{PalBackgroundKind::None};
    bool active{};
public:
    PalBackgroundScope(std::span<uint8_t>,bool wide,uint64_t object) noexcept;
    ~PalBackgroundScope();
    explicit operator bool()const noexcept{return active;}
    PalBackgroundScope(const PalBackgroundScope&)=delete;
    PalBackgroundScope& operator=(const PalBackgroundScope&)=delete;
};
// Only around the exact original800019FC full-frame color clear. Its optional
// FF patch registration runs after the prefix, preserving original pointers.
class PalScreenFillScope {
    std::span<uint8_t> ram;
    uint32_t begin{},end{};
    bool active{};
public:
    PalScreenFillScope(std::span<uint8_t>,bool wide) noexcept;
    ~PalScreenFillScope();
    explicit operator bool()const noexcept{return active;}
    PalScreenFillScope(const PalScreenFillScope&)=delete;
    PalScreenFillScope& operator=(const PalScreenFillScope&)=delete;
};

// Post-adapter for the exact original2C99E0:801ADD44 direct CI8 emitter.
// Capture private cursor801B77C0 before original; append only after original.
// Its parent801ADC7C returns the updated private cursor to its caller.
bool extend_pal_intro_canvas(std::span<uint8_t>,bool wide,uint64_t descriptor,
    uint64_t palette,uint64_t segments,uint64_t alpha,uint64_t original_begin) noexcept;
}
