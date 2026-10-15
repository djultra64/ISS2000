// Original project work: djultra64.
#pragma once
#include "platform.hpp"
#include <filesystem>
namespace iss2000 {
struct InputPreferences {
    std::array<platform::PortPreferences,4> ports{};
    bool operator==(const InputPreferences&)const=default;
};
InputPreferences default_input_preferences();
InputPreferences parse_input_preferences(std::string_view text);
std::string serialize_input_preferences(const InputPreferences& preferences);
InputPreferences load_input_preferences(const std::filesystem::path& data);
void save_input_preferences(const std::filesystem::path& data,const InputPreferences& preferences);
InputPreferences capture_input_preferences();
void apply_input_preferences(const InputPreferences& preferences);
}
