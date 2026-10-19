// Original project work: djultra64.
#pragma once
#include "main_exit_menu.hpp"
#include "prompt_sprite_draw.hpp"
namespace iss2000 {
bool pal_main_select_active(std::span<const uint8_t>,bool include_exit=false);
bool draw_pal_main_ball(std::span<uint8_t>,recomp_context&,bool wide,recomp_func_t*);
bool lift_pal_main_select(std::span<uint8_t>,bool wide=false);
bool draw_pal_main_exit(std::span<uint8_t>,const recomp_context&,const MainExitView&,
 const std::array<PromptGlyphRequest,3>&,const PalPromptSpriteFunctions&);
}
