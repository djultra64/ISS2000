// Original project work: djultra64.
#pragma once
#include <filesystem>
#include <SDL.h>
namespace iss2000 {
// Main-thread modal settings; caller must release input/render locks first.
// The pinned runtime has no global pause API; this preserves the game's state.
void show_settings_dialog(SDL_Window* window,const std::filesystem::path& data);
}
