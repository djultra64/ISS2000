// Original project work: djultra64.
#pragma once
#include <array>
#include <cstdint>
#include <string_view>
namespace iss2000 {
struct TitlePromptLayout {
    uint32_t text_offset{};
    uint64_t registration_slot{};
    std::array<uint8_t,12> original{};
};
// Preserved US layout; callers must explicitly select a verified ROM profile.
inline constexpr TitlePromptLayout us_title_prompt_layout(){
    return {0x9D490,1,{'P','R','E','S','S',' ','S','T','A','R','T',0}};
}
inline constexpr TitlePromptLayout pal_en_title_prompt_layout(){
    return {0x9AB98,1,{'P','R','E','S','S',' ','S','T','A','R','T',0}};
}
namespace prompt_detail {
// Only the exact twelve-byte resident title string is owned; no guest allocation.
class TitleTextGuard {
    const TitlePromptLayout layout_;
    uint8_t* memory_{};
    std::array<uint8_t,12> applied_{};
    bool owned_{};
public:
    explicit TitleTextGuard(const TitlePromptLayout&);
    bool prepare(uint8_t* rdram,uint64_t slot,uint64_t source,std::string_view physical_name);
};
}
// Configure once before guest threads; disabled until a revision is selected.
void configure_title_prompt(const TitlePromptLayout&);
// Invoke before the verified revision's original title registration.
bool prepare_title_prompt(uint8_t*,uint64_t slot,uint64_t source,std::string_view physical_name);
}
