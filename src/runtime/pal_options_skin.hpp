// Original project work: djultra64.
#pragma once
#include "recomp.h"
#include "prompt_textures.hpp"
#include <cstdint>
#include <span>
#include <string>
#include <string_view>
#include <vector>
namespace iss2000 {
struct PalOptionsSkinRow { std::string label,value; };
struct PalOptionsShortcut {PromptGlyphFamily family{};std::string button,label;};
struct PalOptionsSkinView {
 std::string title;
 std::vector<PalOptionsSkinRow> rows;
 unsigned selected=0;
 std::vector<std::string> help;
 std::vector<PalOptionsShortcut> shortcuts;
};
enum class PalOptionsSkinOwner { Options,Controller };
struct PalOptionsSkinFunctions {
 recomp_func_t* initialize_sprite=nullptr; // exact original80008A54
 recomp_func_t* construct_resource=nullptr; // exact original80007C2C
 recomp_func_t* draw_sprite=nullptr; // exact original80041B50
 recomp_func_t* draw_text=nullptr; // exact original80048660: small values/help only
};
// Call with the user's already validated canonical ROM. No original pixels are
// shipped: original streams are decoded and checked in memory after SHA validation.
// The original common-menu alphabet remains resident for headings. Exact CI4
// row crops and grid/frame art use temporary task-owned pixel storage.
// PC Settings/Graphics body labels fail closed when no exact row recipe exists;
// the frozen experimental controls pages retain their prior rendering path.
bool configure_pal_options_skin(std::span<const uint8_t> canonical_rom);
bool pal_options_skin_text_supported(std::string_view);
// Call only after the complete original frame, guarded by the active original
// registry owner. Redraws the original backdrop then emits original sprite art.
// Texture payload lives in this task arena until its original task is consumed.
// A real original G_DL branch skips the inline asset block; subsequent original
// commands allocate after it, so neither textures nor later draws can overlap.
bool draw_pal_options_skin(std::span<uint8_t>,const recomp_context&,
 const PalOptionsSkinView&,PalOptionsSkinOwner,bool wide,const PalOptionsSkinFunctions&);
// Substitute only the already-verified original Resolution word object. This
// emits the same authentic italic glyphs without clearing other original UI.
bool draw_pal_options_skin_label(std::span<uint8_t>,const recomp_context&,
 std::string_view,int x,int y,bool selected,const PalOptionsSkinFunctions&);
}
