// Original project work: djultra64.
#pragma once
#include <array>
#include <cstdint>
#include <span>
#include <string>
#include <string_view>
#include <vector>
namespace iss2000 {
struct EncodedPromptEdit {
    uint32_t offset{},capacity{};
    unsigned prompt_index{}; // One controls_help snapshot: A, B, Start.
    std::string prefix,suffix;
};
struct EncodedPromptMessage {
    uint32_t source_offset{},byte_count{};
    std::string original_sha256;
    std::vector<EncodedPromptEdit> edits;
};
struct EncodedPromptLayout {std::vector<EncodedPromptMessage> messages;};
EncodedPromptLayout pal_en_encoded_prompt_layout();
// Guarded byte edits only. Original PAL48660/48D30 still measure, parse and draw
// the original message, including all existing color/newline/end controls.
class EncodedPromptGuard {
    struct Cache {std::vector<uint8_t> original,applied;bool valid{};};
    const EncodedPromptLayout layout_;
    std::vector<Cache> cache_;
    const uint8_t* memory_{};
public:
    explicit EncodedPromptGuard(EncodedPromptLayout);
    bool prepare(std::span<uint8_t> rdram,uint64_t text_object,
                 const std::array<std::string_view,3>& physical_names);
};
// Configure once before guest threads. No implicit revision or address fallback.
void configure_encoded_menu_prompts(const EncodedPromptLayout&);
// Invoke BEFORE original PAL80048660, with its original a0 text-object pointer.
bool prepare_encoded_menu_prompt(std::span<uint8_t> rdram,uint64_t text_object,
                                 const std::array<std::string_view,3>& physical_names);
}
