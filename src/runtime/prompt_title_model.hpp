// Original project work: djultra64.
#pragma once
#include "prompt_textures.hpp"

namespace iss2000 {
// Graphics-only replacement of the exact original PAL commercial-title model.
// After original80000BB8 returns, pass the current task arena begin..cursor.
// Original80002A10 initializes that arena before00BB8 and finalizes/submits it
// afterward. The active original font48660 identity is caller-owned.
class TitlePromptPlan {
public:
    const PromptSpriteText& line()const{return line_;}
private:
    PromptSpriteText line_;
    std::string physical_name_;
    uint32_t begin_{},end_{},base_{},model_{};
    std::array<uint32_t,20> commands_{};
    friend std::optional<TitlePromptPlan> plan_pal_title_prompt(std::span<const uint8_t>,uint32_t,uint32_t,std::string_view);
    friend bool suppress_pal_title_prompt(std::span<uint8_t>,const TitlePromptPlan&);
};
// Pure preflight: exact state, original model228 with all60 relocations checked,
// exact font/frame and one complete20-part original model draw are mandatory.
std::optional<TitlePromptPlan> plan_pal_title_prompt(std::span<const uint8_t> ram,
    uint32_t gfx_begin,uint32_t gfx_end,std::string_view physical_start_name);
// Call ONLY after draw_pal_engine_text successfully appends plan.line(). Entire
// preflight repeats before changing any word. NOPs only the20 original DE calls;
// leaves all original CPU work, model/animation and other task buffers intact.
bool suppress_pal_title_prompt(std::span<uint8_t> ram,const TitlePromptPlan& plan);
}
