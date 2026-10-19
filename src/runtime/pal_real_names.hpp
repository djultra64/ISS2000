// Original project work: djultra64.
#pragma once
#include <array>
#include <cstdint>
#include <optional>
#include <span>
#include <string_view>
namespace iss2000 {
using PalPlayerName=std::array<uint8_t,8>;
std::optional<PalPlayerName> encode_pal_player_name(std::string_view text);
class PalRealNames {
 std::array<PalPlayerName,106*22> names_{};
 bool ready_=false;
public:
 // Exact supported immutable ROM identity, complete bounded names only.
 // Invalid input disables this instance without partially installing names.
 bool configure(std::span<const uint8_t> rom,std::span<const std::string_view> names);
 // Called only immediately after a genuine ROM DMA and before PI completion.
 // Addresses must match the verified factory-table load mapping. Partial DMA
 // fragments affect only their own eight-byte name intersections. Runtime,
 // Career and user-registration records are outside this ownership domain.
 std::size_t apply(std::span<uint8_t> rdram,uint32_t rom_offset,uint32_t guest,uint32_t size)const;
};
std::span<const std::string_view> pal_default_real_names();
PalRealNames& pal_real_names_override();
}
