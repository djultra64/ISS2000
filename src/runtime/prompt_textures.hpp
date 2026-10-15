// Original project work: djultra64.
#pragma once
#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace iss2000 {
struct PromptAssetHashes {std::string texture,palette;};
struct PromptTextureLayout {
    uint32_t bank_pointer{}; // Physical offset of the selected bank pointer.
    std::array<uint32_t,2> descriptor_indices{};
    std::array<uint32_t,2> descriptor_attributes{};
    std::array<PromptAssetHashes,2> expected{};
};
PromptTextureLayout us_prompt_texture_layout();
PromptTextureLayout pal_en_prompt_texture_layout();
namespace prompt_detail {
using PixelBytes=std::array<uint8_t,128>;
using AssetHashes=PromptAssetHashes;
using ExpectedHashes=std::array<AssetHashes,2>;
std::optional<PixelBytes> glyph_pixels(std::string_view label);
// Independent storage for synthetic tests. Production uses the reviewed hashes.
// Call on the guest sprite generation thread, before original 800414C0 executes.
class TextureGuard {
    struct Cache {
        uint32_t descriptor{},texture{},palette{};
        PixelBytes original{},applied{};
        bool valid{};
    };
    const PromptTextureLayout layout_;
    std::array<Cache,2> cache_{};
    uint8_t* memory_{};
    bool warned_{};
    void warn();
public:
    explicit TextureGuard(PromptTextureLayout layout);
    bool prepare(uint8_t* rdram,uint64_t sprite,const std::array<std::string_view,2>& labels);
    void restore(uint8_t* rdram);
};
}
// Configure once before guest threads; disabled until a revision is selected.
void configure_prompt_textures(const PromptTextureLayout&);
// Labels come from one platform::controls_help snapshot (A/B glyph fields).
// Serializes adapter state; does not hold the input mutex or call SDL.
bool prepare_prompt_textures(uint8_t* rdram,uint64_t sprite,
                             const std::array<std::string_view,2>& labels);
void restore_prompt_textures(uint8_t* rdram);
}
