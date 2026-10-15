// Original project work: djultra64.
#pragma once
#include <cstdint>
namespace iss2000::test_controller {
// Main SDL thread only. Disabled builds expose inert functions with no SDL dependency.
// SDL_JoystickID is a signed 32-bit instance ID. No SDL header is needed by disabled builds.
std::int32_t device_instance();
void initialize();
void pump();
void shutdown();
}
