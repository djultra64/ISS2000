// Original project work: djultra64.
#pragma once
#include <filesystem>
#include <cstdint>
#include <string>
#include <string_view>
namespace iss2000 {
enum class AspectRatio { Original4x3, Wide16x9 };
enum class RenderResolution { Original, P720, P900, P1080, P1440, P1800, P2160 };
enum class RenderRefresh { Original, Hz60, Hz120 };
struct GraphicsSettings {
    AspectRatio aspect_ratio = AspectRatio::Wide16x9;
    RenderResolution resolution = RenderResolution::Original;
    RenderRefresh refresh_rate = RenderRefresh::Original;
    bool operator==(const GraphicsSettings&) const = default;
};
// Strict version-1 JSON. Unknown, missing, duplicate and invalid options throw.
GraphicsSettings parse_graphics_settings(std::string_view json);
std::string serialize_graphics_settings(const GraphicsSettings& settings);
// Fixed graphics.json in an existing folder; missing files return new-user defaults (16:9, native resolution/refresh).
// Malformed files throw and remain unchanged. Symlink paths are rejected.
GraphicsSettings load_graphics_settings(const std::filesystem::path& data_folder);
// Flush an exclusively created sibling temporary, then atomically replace graphics.json.
void save_graphics_settings(const std::filesystem::path& data_folder,const GraphicsSettings& settings);
// UI label uses explicit dimensions for the selected aspect, or Original.
std::string resolution_label(const GraphicsSettings& settings);
// Requested height; Original returns 0 because the native height can vary.
std::uint32_t target_height(const GraphicsSettings& settings);
// Convenience scale before the first valid VI: assumes a 240-line native image.
double resolution_multiplier(const GraphicsSettings& settings);
// Scale against RT64 VI::fbSize().y; zero falls back to 240 before a valid VI.
// Original always returns 1. These helpers do not verify actual rendering.
double resolution_multiplier(const GraphicsSettings& settings,std::uint32_t native_height);
}
