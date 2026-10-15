// Original project work: djultra64.
// Executes original generated boot code, then explicitly stops before the game.
#include "recomp.h"
#include "funcs.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string_view>
#include <vector>

namespace {
constexpr std::size_t rdram_size = 8 * 1024 * 1024;
constexpr std::size_t bss_begin = 0xA0600;
constexpr std::size_t bss_end = 0x1AFD80;
constexpr std::uint8_t sentinel = 0xA5;
bool allow_continuation = true;
bool continuation_observed = false;

void stop_at_original_continuation(std::uint8_t*, recomp_context* ctx) {
    if (std::uint32_t(ctx->r29) != 0x800CEC50u)
        throw std::runtime_error("Original entry produced an unexpected stack pointer");
    continuation_observed = true;
    // Deliberate diagnostic stop. No OS calls or game initialization are stubbed.
}

std::array<std::uint32_t, 3> original_buffers(std::uint8_t* rdram, bool expanded) {
    // Set only the original game's configuration pointer/flag, then execute
    // its unmodified buffer setup. The diagnostic does not emulate OS detection.
    MEM_W(0, S32(0x800A0914u)) = 0x80100000u;
    MEM_B(0x12, S32(0x80100000u)) = expanded ? 1 : 0;
    recomp_context context{};
    func_80000500(rdram, &context);
    return {std::uint32_t(MEM_W(0, S32(0x801A3048u))),
            std::uint32_t(MEM_W(8, S32(0x801A3048u))),
            std::uint32_t(MEM_W(16, S32(0x801A3048u)))};
}
}

extern "C" recomp_func_t* get_function(std::int32_t address) {
    if (allow_continuation && std::uint32_t(address) == 0x800007B8u)
        return &stop_at_original_continuation;
    throw std::runtime_error("Unimplemented guest continuation");
}

int main(int argc, char** argv) {
    try {
        if (argc > 2 || (argc == 2 && std::string_view(argv[1]) != "--reject-continuation"))
            throw std::runtime_error("Usage: iss2000-diagnostic [--reject-continuation]");
        allow_continuation = argc == 1;
        // Word-backed storage guarantees the alignment required by MEM_W.
        std::vector<std::uint32_t> memory(rdram_size / 4, 0xA5A5A5A5u);
        auto* rdram = reinterpret_cast<std::uint8_t*>(memory.data());
        recomp_context context{};
        func_80000400(rdram, &context);
        const bool cleared = std::all_of(rdram+bss_begin, rdram+bss_end,
                                        [](auto value) { return value == 0; });
        const auto intact = [](auto value) { return value == sentinel; };
        const bool preserved = std::all_of(rdram, rdram+bss_begin, intact) &&
                               std::all_of(rdram+bss_end, rdram+rdram_size, intact);
        if (!cleared || !preserved || !continuation_observed)
            throw std::runtime_error("Original entry diagnostic memory/dispatch verification failed");
        const auto standard = original_buffers(rdram, false);
        const auto expanded = original_buffers(rdram, true);
        if (standard != std::array<std::uint32_t, 3>{0x80307800u, 0x8032D000u, 0x80281D40u} ||
            expanded != std::array<std::uint32_t, 3>{0x80500000u, 0x80596000u, 0x8062C000u})
            throw std::runtime_error("Original buffer profile selection failed");
        std::cout << "{\"mode\":\"original-entry-diagnostic\","
                  << "\"rdram_bytes\":" << rdram_size << ','
                  << "\"bss_cleared\":true,\"outside_bss_preserved\":true,"
                  << "\"stack_pointer\":\"0x800CEC50\","
                  << "\"continuation\":\"0x800007B8\",\"game_booted\":false,"
                  << "\"original_buffer_setup\":{"
                  << "\"standard\":[\"0x80307800\",\"0x8032D000\",\"0x80281D40\"],"
                  << "\"expanded\":[\"0x80500000\",\"0x80596000\",\"0x8062C000\"]}}\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
