// Original project work: djultra64.
#pragma once
#include "controller_schemes.hpp"
#include "recomp.h"
#include <span>
namespace iss2000 {
// Diagnostic outcomes only; they never select or alter the input mapping.
enum class PalFootballInputResult {
 Entry,Applied,NoGamepad,NoSiSample,InvalidMemory,MissingOriginal,
 NoncanonicalContext,InvalidPhysicalSample,InvalidObject,InvalidStack,
 ForeignPacket,UnknownProfile,UnknownNormalizationTable,InvalidBindings
};
// Thread-local result of the last projection attempt on this guest thread.
PalFootballInputResult pal_football_input_result() noexcept;
// First entry and unique outcome/stage/device/scheme signatures, capped at8 lines per
// port for the process. Rejections include source/SP/profile, never button data.
void trace_pal_football_stage(std::span<const uint8_t> ram,const recomp_context& context,
 unsigned port,uint32_t stage,uint32_t object,uint64_t sequence,bool gamepad,
 ControllerScheme scheme,PalFootballInputResult result);
// Only call with an active, identity-checked original PAL controller processor
// (801D5A74/801D5E1C/801D4CC0 or initializer fallback801D4880) and a current
// physical gamepad SI snapshot. False leaves RAM/context untouched and does not
// invoke original; the wrapper must then run its ordinary original path.
// On success original runs exactly once with the live context. Its ABI outputs
// survive; the temporary packet pointer,32B stack frame and incoming SP restore
// even if original throws. Raw SI input, including navigation/sticks, is retained.
bool apply_pal_football_input(std::span<uint8_t> ram,recomp_context& context,
    uint16_t held_physical,uint16_t pressed_physical,const FootballBindings& bindings,
    recomp_func_t* original);
}
