// Original project work: djultra64.
#pragma once
#include "prompt_textures.hpp"
#include "recomp.h"
#include <span>
namespace iss2000 {
struct PalPromptSpriteFunctions {
 recomp_func_t* initialize_sprite{};
 recomp_func_t* construct_resource{};
 recomp_func_t* draw_sprite{};
 recomp_func_t* draw_text{};
};
bool pal_prompt_icon_available(const PromptSpriteIcon&);
// Draw an already guarded physical-prompt proposal through original PAL sprite
// and font functions. Preflight the entire transaction before changing RAM.
// Authentic glyph pixels and their TLUT remain in this original task's arena;
// the stack objects and temporary resource-bank pointer are restored on return.
bool draw_pal_prompt_sprite(std::span<uint8_t>,const recomp_context&,
 const PromptSpriteResult&,const PalPromptSpriteFunctions&);
}
