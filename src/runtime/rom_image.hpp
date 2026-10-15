#pragma once

#include <cstdint>
#include <filesystem>
#include <span>
#include <string>
#include <vector>

namespace iss2000 {
// Reads only the exact ROM revision selected at build time (raw or a ZIP with exactly one ROM).
// Returns canonical big-endian bytes; all failures throw std::runtime_error.
std::vector<std::uint8_t> read_rom_image(const std::filesystem::path& source);

// Validates canonical bytes before touching the destination tree. Publishing
// is atomic and fails if any destination entry already exists.
void write_rom_exclusive(const std::filesystem::path& destination,
                         std::span<const std::uint8_t> canonical);

// Called after the user selects a verified ROM. Exact canonical storage stays
// untouched; corrupt or noncanonical storage is preserved in a unique .invalid-backup file
// before the complete canonical replacement is published without overwriting.
void ensure_rom_storage(const std::filesystem::path& destination,
                        std::span<const std::uint8_t> canonical);

namespace rom_detail {
// Implementation primitives shared by the reader/writer and synthetic tests.
std::vector<std::uint8_t> normalize_byte_order(std::span<const std::uint8_t> bytes);
std::string sha256_hex(std::span<const std::uint8_t> bytes);
void write_bytes_exclusive(const std::filesystem::path& destination,
                           std::span<const std::uint8_t> bytes);
void ensure_bytes_storage(const std::filesystem::path& destination,
                          std::span<const std::uint8_t> bytes);

}
}
