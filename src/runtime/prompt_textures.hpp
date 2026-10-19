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
struct PromptGlyphRequest {PromptGlyphFamily family{};std::string_view label;unsigned port{};};
struct PromptAssetHashes {std::string texture,palette;};
struct PromptDirectionStripLayout {
    uint32_t descriptor_index{},descriptor_attributes{};
    PromptAssetHashes expected;
    std::string fallback_segments_sha256;
};
struct PromptPairStripLayout {
    uint32_t bank_pointer{},descriptor_index{},descriptor_attributes{};
    PromptAssetHashes expected;
};
struct PromptStartImageLayout {
    uint32_t descriptor_index{},descriptor_attributes{};
    PromptAssetHashes expected;
    std::array<std::string,3> consumer_sha256;
};
struct PromptPackedHintLayout {
    uint32_t bank_pointer{},descriptor_index{},dimensions{},descriptor_attributes{};
    PromptAssetHashes expected;
    std::string consumer_sha256;
};
// The exact team-region consumer advances through an offscreen descriptor and
// a second common atlas descriptor. Both original images remain read-only.
struct PromptRegionHintLayout {
    uint32_t bank_pointer{},descriptor_index{},consumer_address{};
    std::array<std::string,2> texture_sha256;
    std::string palette_sha256,consumer_sha256;
    uint32_t owner_mode_address{};
    uint8_t owner_mode_value{};
    uint32_t font_tint_address{};
    std::string font_tint_sha256;
    uint8_t font_tint_selector{};
    uint32_t single_consumer_address{};std::string single_consumer_sha256;
};
struct PromptTeamDirectionLayout {uint32_t consumer_address{},segments{};std::string consumer_sha256;};
// Exact original I4 instruction atlas and its complete fixed consumer.
struct PromptFontImageLayout {
    uint32_t bank_pointer{},descriptor_index{},dimensions{},descriptor_attributes{};
    uint32_t texture_bytes{},consumer_address{},consumer_bytes{};
    std::string texture_sha256,consumer_sha256;
    uint32_t owner_port_address{};
};
struct PromptTextFallbackLayout {
    uint32_t viewport_table{},font_address{},font_bytes{},frame_pointer{};
    std::string font_sha256;
};
enum class PromptSpriteStatus : uint8_t { Unrelated,Applied,TextFallback,RejectedKnown };
enum class PromptSpriteAction : uint8_t { Unknown,A,B,CDirections,StartRandom,Shoulders,StartControls,SetplayControls };
struct PromptSpriteText { int16_t x{},y{};std::string text;uint8_t height{12};uint8_t palette{}; };
struct PromptSpriteIcon {
    int16_t x{},y{};PromptGlyphFamily family{};std::string label;unsigned port{};
    uint8_t width{16},height{16};
};
struct PromptSpriteResult {
    PromptSpriteStatus status{PromptSpriteStatus::Unrelated};
    PromptSpriteAction action{PromptSpriteAction::Unknown};
    std::array<PromptSpriteText,8> lines{};
    uint8_t line_count{};
    // Owned physical labels survive the input snapshot. Original sprite/font
    // transactions draw these together, using an independent authentic palette.
    std::array<PromptSpriteIcon,8> icons{};uint8_t icon_count{};
};
struct PromptTextureLayout {
    uint32_t bank_pointer{}; // Physical offset of the selected bank pointer.
    std::array<uint32_t,2> descriptor_indices{};
    std::array<uint32_t,2> descriptor_attributes{};
    std::array<PromptAssetHashes,2> expected{};
    std::optional<PromptDirectionStripLayout> c_directions;
    std::optional<PromptTextFallbackLayout> text_fallback;
    std::optional<PromptStartImageLayout> start_random;
    std::optional<PromptPairStripLayout> ab_pair;
    std::optional<PromptPackedHintLayout> country_shoulders{};
    std::optional<PromptPackedHintLayout> name_directions{};
    std::array<std::optional<PromptPackedHintLayout>,2> name_ab{};
    std::optional<PromptRegionHintLayout> team_regions{};
    std::array<std::optional<PromptTeamDirectionLayout>,2> team_directions{};
    std::optional<PromptFontImageLayout> field_start{};
    std::optional<PromptFontImageLayout> field_setplay{};
};
PromptTextureLayout us_prompt_texture_layout();
PromptTextureLayout pal_en_prompt_texture_layout();
namespace prompt_detail {
using PixelBytes=std::array<uint8_t,128>;
using AssetHashes=PromptAssetHashes;
using ExpectedHashes=std::array<AssetHashes,2>;
std::optional<PixelBytes> glyph_pixels(PromptGlyphRequest,std::span<const uint8_t,32> palette);
// Fit source artwork into the opaque bounds of one already validated original
// cell. Storage remains16x16; palettes, sprite geometry and UVs stay unchanged.
std::optional<PixelBytes> glyph_pixels(PromptGlyphRequest,std::span<const uint8_t,32> palette,
    std::span<const uint8_t,128> original_cell);
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
    Cache pair_cache_{};
    Cache name_cache_{};
    std::array<Cache,2> name_ab_cache_{};
    uint8_t* memory_{};
    bool warned_{};
    void warn();
    bool font_image_ready(const uint8_t*,uint64_t,const PromptFontImageLayout&) const;
    std::optional<PromptSpriteResult> prepare_field_pause(uint8_t*,uint64_t,const std::array<PromptGlyphRequest,3>*);
    std::optional<PromptSpriteResult> prepare_field_start(uint8_t*,uint64_t,const PromptGlyphRequest*);
    std::optional<PromptSpriteResult> prepare_regions(uint8_t*,uint64_t,const std::array<PromptGlyphRequest,3>*);
    std::optional<PromptSpriteResult> prepare_pair(uint8_t*,uint64_t,
        const std::array<PromptGlyphRequest,2>&);
    void restore_pair(uint8_t*);
    void restore_name(uint8_t*);
    std::optional<PromptSpriteResult> prepare_packed(uint8_t*,uint64_t,
        const std::array<PromptGlyphRequest,2>&,const std::array<PromptGlyphRequest,4>*,const std::array<PromptGlyphRequest,3>*);
    PromptSpriteResult prepare_impl(uint8_t*,uint64_t,
        const std::array<PromptGlyphRequest,2>&,
        const std::array<PromptGlyphRequest,4>*,const PromptGlyphRequest*,const std::array<PromptGlyphRequest,3>*);
public:
    explicit TextureGuard(PromptTextureLayout layout);
    std::optional<unsigned> sprite_port(const uint8_t*,uint64_t,std::optional<unsigned> active_port={}) const;
    bool prepare(uint8_t* rdram,uint64_t sprite,const std::array<PromptGlyphRequest,2>& labels);
    PromptSpriteResult prepare_sprite(uint8_t* rdram,uint64_t sprite,
        const std::array<PromptGlyphRequest,2>& labels,
        const std::array<PromptGlyphRequest,4>& directions,
        std::optional<PromptGlyphRequest> start=std::nullopt,
        std::optional<std::array<PromptGlyphRequest,3>> shoulders=std::nullopt);
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
// Optional shoulder requests are explicit Left shoulder,Z,Right shoulder actions.
// TextFallback is a proposal: preflight and draw ALL lines through the original
// font, then suppress the exact original sprite only after successful drawing.
// Caller must also verify the active original resident font-function identity;
// the original-font helper preflights the complete gfx/stack/context transaction.
PromptSpriteResult prepare_physical_prompt_sprite(uint8_t* rdram,uint64_t sprite,
    const std::array<PromptGlyphRequest,2>& labels,
    const std::array<PromptGlyphRequest,4>& directions,
        std::optional<PromptGlyphRequest> start=std::nullopt,
        std::optional<std::array<PromptGlyphRequest,3>> shoulders=std::nullopt);
// Exact pause prefix uses original selected port1..4 mapped to0..3.
// Exact global field Start uses the supplied last active host port; other sprites
// stay unrelated. Resolve before snapshots and carry the port in every request.
std::optional<unsigned> physical_prompt_sprite_port(const uint8_t* rdram,uint64_t sprite,
    std::optional<unsigned> active_port={});
void restore_prompt_textures(uint8_t* rdram);
}
