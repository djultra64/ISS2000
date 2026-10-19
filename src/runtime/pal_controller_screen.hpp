// Original project work: djultra64.
#pragma once
#include "recomp.h"
#include "prompt_textures.hpp"
#include <array>
#include <span>
#include <string>
namespace iss2000 {
struct PalControllerActionRow {
 PromptGlyphFamily family=PromptGlyphFamily::Xbox;
 std::string physical_label,action;
};
struct PalControllerScreenView {
 std::array<std::string,4> types{"Type 1","Type 1","Type 1","Type 1"};
 unsigned selected_port=0;
 std::array<PalControllerActionRow,8> actions;
 std::string start_footer;
 bool free_capture=false;
 unsigned selected_action=0;
};
struct PalControllerScreenFunctions {
 recomp_func_t* initialize_sprite=nullptr;
 recomp_func_t* construct_resource=nullptr;
 recomp_func_t* draw_sprite=nullptr;
 recomp_func_t* draw_text=nullptr;
};
// Configure before guest execution with the already validated original PAL ROM.
// All strings in the immutable view are owned. Host schemes never enter the
// original three-entry N64 Type table or replace its Cursor/Keeper/Ready state.
bool configure_pal_controller_screen(std::span<const uint8_t> canonical_rom);
// After the complete original frame80000BB8, under exact active function guards.
// Preflight the complete page and original task before changing any RAM. Keep
// the original background, four cards, Cursor/Keeper/Ready and panel border;
// replace only Type value rectangles and the panel's original foreground.
// Genuine CC0 glyph pixels/palette live in this task's original Gfx arena and
// are emitted by original80041B50. Text uses original80048660, never a host HUD.
bool draw_pal_controller_screen(std::span<uint8_t>,const recomp_context&,
 const PalControllerScreenView&,const PalControllerScreenFunctions&);
}
