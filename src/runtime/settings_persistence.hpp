// Original project work: djultra64.
#pragma once
#include "runtime/graphics_settings.hpp"
#include "runtime/input_preferences.hpp"
namespace iss2000 {
// Stage both settings files before publishing either. On a publication failure,
// restore the exact previous files before reporting failure; live state is the
// caller's responsibility after success. This is not a power-loss transaction.
void save_game_preferences(const std::filesystem::path& folder,
                           const GraphicsSettings& graphics,
                           const InputPreferences& preferences);
}
