// Original project work: djultra64.
#pragma once
#include <algorithm>
#include <cstdint>
#include <mutex>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace iss2000 {
// Resolve a guest PC only while its exact original ROM section is loaded.
// Coverage accumulates across chunked DMA; stale aliases never survive a write.
template<class Function> class SectionRegistry {
public:
    struct Entry { std::uint32_t offset; Function function; };
    struct Section {
        std::string name;
        std::uint32_t rom, ram, size, text_size;
        std::vector<Entry> entries;
    };
    void add(Section section) {
        std::lock_guard lock(mutex_);
        if (!section.size || !section.text_size || section.text_size > section.size ||
            section.ram < 0x80000000u || std::uint64_t(section.ram)+section.size > 0x80800000ull ||
            std::uint64_t(section.rom)+section.size > 0x1000000ull)
            throw std::invalid_argument("Executable section exceeds verified guest/ROM memory");
        for (const auto& e : section.entries)
            if (e.offset >= section.text_size || e.offset % 4 || !e.function)
                throw std::invalid_argument("Executable target is outside section text");
        for (const auto& s : sections_)
            if (s.section.name == section.name)
                throw std::invalid_argument("Duplicate section identity");
        sections_.push_back({std::move(section), {}, false});
    }
    void dma_completed(std::uint32_t rom, std::uint32_t ram, std::uint32_t size) {
        validate_dma(rom, ram, size);
        std::lock_guard lock(mutex_);
        apply_dma(rom, ram, size);
    }
    template<class Copy, class Notify>
    void transfer(std::uint32_t rom, std::uint32_t ram, std::uint32_t size, Copy copy, Notify notify) {
        validate_dma(rom, ram, size);
        {
            std::lock_guard lock(mutex_);
            copy();
            apply_dma(rom, ram, size);
        }
        // Completion may wake a guest thread; its native mapping is ready now.
        notify();
    }
    Function find(std::uint32_t pc) const {
        std::lock_guard lock(mutex_);
        for (const auto& state : sections_) {
            if (!state.active || pc < state.section.ram || pc >= std::uint64_t(state.section.ram)+state.section.text_size) continue;
            for (const auto& e : state.section.entries)
                if (std::uint64_t(state.section.ram)+e.offset == pc) return e.function;
        }
        return nullptr;
    }
    std::vector<std::string> active_names() const {
        std::lock_guard lock(mutex_);
        std::vector<std::string> names;
        for (const auto& state : sections_) if (state.active) names.push_back(state.section.name);
        return names;
    }
private:
    static void validate_dma(std::uint32_t rom, std::uint32_t ram, std::uint32_t size) {
        if (!size || ram < 0x80000000u || std::uint64_t(ram)+size > 0x80800000ull ||
            std::uint64_t(rom)+size > 0x1000000ull)
            throw std::invalid_argument("DMA exceeds verified guest/ROM memory");
    }
    void apply_dma(std::uint32_t rom, std::uint32_t ram, std::uint32_t size) {
        for (auto& state : sections_) {
            const auto& s = state.section;
            const bool overlaps = ram < std::uint64_t(s.ram)+s.size && s.ram < std::uint64_t(ram)+size;
            if (!overlaps) continue;
            const bool same_bytes = std::int64_t(rom)-s.rom == std::int64_t(ram)-s.ram;
            if (!same_bytes) {
                state.coverage.clear();
                if (ram < std::uint64_t(s.ram)+s.text_size && s.ram < std::uint64_t(ram)+size)
                    state.active = false;
                continue;
            }
            const auto begin = std::max(ram, s.ram)-s.ram;
            const auto end = std::uint32_t(std::min(std::uint64_t(ram)+size, std::uint64_t(s.ram)+s.size)-s.ram);
            state.coverage.emplace_back(begin, end);
            std::sort(state.coverage.begin(), state.coverage.end());
            std::uint32_t through=0;
            for (const auto& span : state.coverage) {
                if (span.first > through) break;
                through=std::max(through,span.second);
            }
            if (through == s.size) {
                state.active=true;
                state.coverage={{0,s.size}};
            }
        }
    }
    struct State {
        Section section;
        std::vector<std::pair<std::uint32_t,std::uint32_t>> coverage;
        bool active;
    };
    mutable std::mutex mutex_;
    std::vector<State> sections_;
};
}
