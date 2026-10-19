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
// A section must have been fully loaded once. Thereafter each native target
// requires its complete original instruction span and any folded jump-table bytes
// to retain exact ROM coverage.
template<class Function> class SectionRegistry {
public:
    struct Entry {
        std::uint32_t offset; Function function; std::uint32_t size;
        // Half-open section-relative ranges read by the static translator.
        std::vector<std::pair<std::uint32_t,std::uint32_t>> dependencies{};
    };
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
        for (const auto& e : section.entries) {
            if (!e.size || e.offset % 4 || e.size % 4 ||
                std::uint64_t(e.offset)+e.size > section.text_size || !e.function)
                throw std::invalid_argument("Executable target is outside section text");
            for (const auto& span : e.dependencies)
                if (span.first % 4 || span.second % 4 || span.first >= span.second || span.second > section.size)
                    throw std::invalid_argument("Native dependency is outside loaded section");
        }
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
    // Original guest stores have no ROM identity. Byte alignment is intentional:
    // the original zero-fill handles both unaligned edges and word interiors.
    void invalidate_ram_range(std::uint32_t ram, std::uint32_t size) {
        if (!size) return;
        if (ram < 0x80000000u || std::uint64_t(ram)+size > 0x80800000ull)
            throw std::invalid_argument("Guest write exceeds verified memory");
        std::lock_guard lock(mutex_);
        for (auto& state : sections_) {
            const auto& s=state.section;
            if (ram >= std::uint64_t(s.ram)+s.size || s.ram >= std::uint64_t(ram)+size) continue;
            const auto begin=std::max(ram,s.ram)-s.ram;
            const auto end=std::uint32_t(std::min(std::uint64_t(ram)+size,std::uint64_t(s.ram)+s.size)-s.ram);
            subtract(state.coverage,begin,end);
        }
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
            if (!state.ever_loaded || pc < state.section.ram || pc >= std::uint64_t(state.section.ram)+state.section.text_size) continue;
            for (const auto& e : state.section.entries)
                if (std::uint64_t(state.section.ram)+e.offset == pc && entry_covered(state.coverage,e)) return e.function;
        }
        return nullptr;
    }
    std::vector<std::string> active_names() const {
        std::lock_guard lock(mutex_);
        std::vector<std::string> names;
        for (const auto& state : sections_) {
            if (state.ever_loaded && std::any_of(state.section.entries.begin(),state.section.entries.end(),[&](const auto& entry){
                return entry_covered(state.coverage,entry);
            })) names.push_back(state.section.name);
        }
        return names;
    }
private:
    static void validate_dma(std::uint32_t rom, std::uint32_t ram, std::uint32_t size) {
        if (!size || ram < 0x80000000u || std::uint64_t(ram)+size > 0x80800000ull ||
            std::uint64_t(rom)+size > 0x1000000ull)
            throw std::invalid_argument("DMA exceeds verified guest/ROM memory");
    }
    using Range = std::pair<std::uint32_t,std::uint32_t>;
    static bool covered(const std::vector<Range>& ranges,std::uint32_t begin,std::uint32_t end) {
        // Ranges are merged, sorted and disjoint, including adjacent spans.
        return std::any_of(ranges.begin(),ranges.end(),[&](const auto& span){return span.first<=begin && span.second>=end;});
    }
    static bool entry_covered(const std::vector<Range>& ranges,const Entry& entry) {
        return covered(ranges,entry.offset,entry.offset+entry.size) &&
            std::all_of(entry.dependencies.begin(),entry.dependencies.end(),[&](const auto& span){
                return covered(ranges,span.first,span.second);
            });
    }
    static void subtract(std::vector<Range>& ranges,std::uint32_t begin,std::uint32_t end) {
        std::vector<Range> retained;
        for (const auto& span : ranges) {
            if (span.second<=begin || span.first>=end) retained.push_back(span);
            else {
                if (span.first<begin) retained.emplace_back(span.first,begin);
                if (span.second>end) retained.emplace_back(end,span.second);
            }
        }
        ranges=std::move(retained);
    }
    static void include(std::vector<Range>& ranges,std::uint32_t begin,std::uint32_t end) {
        ranges.emplace_back(begin,end);
        std::sort(ranges.begin(),ranges.end());
        std::vector<Range> merged;
        for (const auto& span : ranges) {
            if (!merged.empty() && span.first<=merged.back().second)
                merged.back().second=std::max(merged.back().second,span.second);
            else merged.push_back(span);
        }
        ranges=std::move(merged);
    }
    void apply_dma(std::uint32_t rom, std::uint32_t ram, std::uint32_t size) {
        for (auto& state : sections_) {
            const auto& s = state.section;
            const bool overlaps = ram < std::uint64_t(s.ram)+s.size && s.ram < std::uint64_t(ram)+size;
            if (!overlaps) continue;
            const auto begin = std::max(ram, s.ram)-s.ram;
            const auto end = std::uint32_t(std::min(std::uint64_t(ram)+size, std::uint64_t(s.ram)+s.size)-s.ram);
            const bool same_bytes = std::int64_t(rom)-s.rom == std::int64_t(ram)-s.ram;
            if (!same_bytes) {
                // A different overlay owns only the bytes actually written.
                // Unchanged tails remain original code; partial bodies do not.
                subtract(state.coverage,begin,end);
            } else {
                include(state.coverage,begin,end);
                if (!state.ever_loaded && covered(state.coverage,0,s.size)) state.ever_loaded=true;
            }
        }
    }
    struct State {
        Section section;
        std::vector<Range> coverage;
        bool ever_loaded;
    };
    mutable std::mutex mutex_;
    std::vector<State> sections_;
};
}
