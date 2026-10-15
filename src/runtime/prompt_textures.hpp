// Original project work: djultra64.
#pragma once
#include <array>
#include <cstdint>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <vector>

namespace iss2000 {
enum class PromptGlyphFamily : uint8_t { Automatic, Xbox, PlayStation, Nintendo, Keyboard };
struct PromptGlyphRequest {PromptGlyphFamily family{};std::string_view label;};
struct PromptAssetHashes {std::string texture,palette;};
struct PromptDirectionStripLayout {
    uint32_t descriptor_index{},descriptor_attributes{};
    PromptAssetHashes expected;
    std::string fallback_segments_sha256;
};
struct PromptStartImageLayout {
    uint32_t descriptor_index{},descriptor_attributes{};
    PromptAssetHashes expected;
    std::array<std::string,3> consumer_sha256;
};
struct PromptTextFallbackLayout {
    uint32_t viewport_table{},font_address{},font_bytes{},frame_pointer{};
    std::string font_sha256;
};
enum class PromptSpriteStatus : uint8_t { Unrelated,Applied,TextFallback,RejectedKnown };
enum class PromptSpriteAction : uint8_t { Unknown,A,B,CDirections,StartRandom };
struct PromptSpriteText { int16_t x{},y{};std::string text; };
struct PromptSpriteResult {
    PromptSpriteStatus status{PromptSpriteStatus::Unrelated};
    PromptSpriteAction action{PromptSpriteAction::Unknown};
    std::array<PromptSpriteText,4> lines{};
    uint8_t line_count{};
};
struct PromptTextureLayout {
    uint32_t bank_pointer{}; // Physical offset of the selected bank pointer.
    std::array<uint32_t,2> descriptor_indices{};
    std::array<uint32_t,2> descriptor_attributes{};
    std::array<PromptAssetHashes,2> expected{};
    std::optional<PromptDirectionStripLayout> c_directions;
    std::optional<PromptTextFallbackLayout> text_fallback;
    std::optional<PromptStartImageLayout> start_random;
};
PromptTextureLayout us_prompt_texture_layout();
PromptTextureLayout pal_en_prompt_texture_layout();
namespace prompt_detail {
using PixelBytes=std::array<uint8_t,128>;
using AssetHashes=PromptAssetHashes;
using ExpectedHashes=std::array<AssetHashes,2>;
std::optional<PixelBytes> glyph_pixels(PromptGlyphRequest,std::span<const uint8_t,32> palette);
// Independent storage for synthetic tests. Production uses the reviewed hashes.
// Call on the guest sprite generation thread, before the selected revision's original sprite builder executes.
class TextureGuard {
    struct Cache {
        uint32_t descriptor{},texture{},palette{};
        std::vector<uint8_t> original,applied;
        bool valid{};
    };
    const PromptTextureLayout layout_;
    std::array<Cache,3> cache_{};
    uint8_t* memory_{};
    bool warned_{};
    void warn();
    PromptSpriteResult prepare_impl(uint8_t*,uint64_t,
        const std::array<PromptGlyphRequest,2>&,
        const std::array<PromptGlyphRequest,4>*,const PromptGlyphRequest*);
public:
    explicit TextureGuard(PromptTextureLayout layout);
    bool prepare(uint8_t* rdram,uint64_t sprite,const std::array<PromptGlyphRequest,2>& labels);
    PromptSpriteResult prepare_sprite(uint8_t* rdram,uint64_t sprite,
        const std::array<PromptGlyphRequest,2>& labels,
        const std::array<PromptGlyphRequest,4>& directions,
        std::optional<PromptGlyphRequest> start=std::nullopt);
    void restore(uint8_t* rdram);
};
}
// Configure once before guest threads; disabled until a revision is selected.
void configure_prompt_textures(const PromptTextureLayout&);
// Family and physical glyph label come from one controls_help snapshot.
// Authentic artist tiles are quantized to the guarded, unchanged game palette.
// Serializes adapter state; does not hold the input mutex or call SDL.
bool prepare_prompt_textures(uint8_t* rdram,uint64_t sprite,
                             const std::array<PromptGlyphRequest,2>& labels);
// Directions are explicit physical requests in Left,Right,Up,Down order.
// TextFallback is a proposal: preflight and draw ALL lines through the original
// font, then suppress the exact original sprite only after successful drawing.
// Caller must also verify the active original resident font-function identity;
// the original-font helper preflights the complete gfx/stack/context transaction.
PromptSpriteResult prepare_physical_prompt_sprite(uint8_t* rdram,uint64_t sprite,
    const std::array<PromptGlyphRequest,2>& labels,
    const std::array<PromptGlyphRequest,4>& directions,
        std::optional<PromptGlyphRequest> start=std::nullopt);
void restore_prompt_textures(uint8_t* rdram);
}
