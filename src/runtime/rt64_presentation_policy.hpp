// Original project work: djultra64.
#pragma once
#include "graphics_settings.hpp"
#include "common/rt64_enhancement_configuration.h"
namespace iss2000 {
inline RT64::EnhancementConfiguration::Presentation::Mode rt64_presentation_mode(RenderRefresh refresh){
    using Mode=RT64::EnhancementConfiguration::Presentation::Mode;
    // PAL rotates rendering and VI buffers. RT64's SkipBuffering mode accepts
    // only buffers matching compatible VI history (address/width/pixel size),
    // allowing intermediate frames without bypassing normal VI presentation.
    return refresh==RenderRefresh::Hz60 || refresh==RenderRefresh::Hz120
        ?Mode::SkipBuffering:Mode::Console;
}
}
