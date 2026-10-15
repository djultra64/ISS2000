// Original project work: djultra64.
#pragma once
#include <array>
#include <cstdint>
#include <mutex>
#include <optional>
namespace iss2000 {
// A copied VI keeps its origin. Retain authoritative identities across queued
// presents instead of inferring a framebuffer base from a one-row assumption.
class ViFramebufferRegistry {
    struct Entry {uint32_t origin{},width{},base{};uint8_t size{};bool used{},conflict{};};
    std::array<Entry,256> entries_{};
    unsigned next_{};
    mutable std::mutex mutex_;
public:
    void record(uint32_t origin,uint32_t width,uint32_t status,uint32_t base);
    std::optional<uint32_t> resolve(uint32_t origin,uint32_t width,uint8_t size)const;
};
}
extern "C" void iss2000_record_vi_framebuffer(uint32_t origin,uint32_t width,uint32_t status,uint32_t framebuffer);
// UINT32_MAX is an unknown/conflicting key; caller retains its original policy.
extern "C" uint32_t iss2000_resolve_vi_framebuffer(uint32_t origin,uint32_t width,uint8_t size);
extern "C" uint32_t iss2000_vi_original_rate(uint32_t vertical_sync);
