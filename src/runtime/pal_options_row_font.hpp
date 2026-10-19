// Original project work: djultra64.
#pragma once
#include <cstdint>
#include <optional>
#include <span>
#include <string_view>
#include <vector>
namespace iss2000 {
// Original Options row CI4 pixels, copied at unit scale into a new owned image.
// This is a bounded word/crop composer, not a reconstructed Latin alphabet.
// Render through original 41B50 with the original row palette: ROM35E3E0
// unselected or ROM353890 selected. No header-font I4 tint is appropriate.
struct PalOptionsRowBitmap {
    uint16_t width{128},height{16},advance{};
    std::vector<uint8_t> pixels;
};
// Input is the complete decoded original PAL asset42, verified independently.
// Known noncontrols labels use exact source columns, with natural aliases:
// Graphics -> Picture, Aspect -> Screen ratio, Frame rate -> Rate,
// Save -> Store, Back -> Go back. No full alphabet is claimed.
// Unsupported text/foreign assets fail without modifying the caller's bytes.
std::optional<PalOptionsRowBitmap> pal_options_row_bitmap(
    std::span<const uint8_t> decoded_asset42,std::string_view text);
}
