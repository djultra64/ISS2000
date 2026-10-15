// Original project work: djultra64.
#pragma once
#include <cstdint>
namespace RT64 {struct RenderWorker;struct RenderTarget;}
// Called only by privately generated, hash-pinned RT64 observers. A callback
// observes completed GPU work; it never supplies game frames or changes cadence.
extern "C" bool iss2000_render_evidence_enabled();
extern "C" void iss2000_render_evidence_frame(RT64::RenderWorker*,RT64::RenderTarget*,
    uint64_t workload,uint64_t present,uint32_t frame,uint32_t planned,float weight,float previous,
    uint32_t target_hz,uint32_t original_hz,bool matched);
extern "C" void iss2000_render_evidence_present(uint64_t present,uint32_t frame,uint32_t planned,
    uint32_t target_hz,uint32_t original_hz,bool success);
