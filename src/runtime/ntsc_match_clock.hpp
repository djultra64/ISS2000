// Original project work: djultra64.
#pragma once
#include <array>
#include <cstdint>
#include <span>

namespace iss2000 {
// Only for the verified PAL clock leaf and its active original overlay. The
// caller verifies ROM/section/function identity and invokes the original once.
// Presentation, physics, audio and the original clock's gates remain separate.
class NtscMatchClock {
public:
    struct Snapshot {
        std::array<uint16_t,2> remaining{},subcounter{};
        uint64_t sequence=0;
        bool valid=false;
    };
    // Call after the original PAL clock initializer. A scheduled first interval
    // counts toward each counter's independent six-interval phase.
    bool reset_after_init(std::span<const uint8_t> rdram) noexcept;
    Snapshot before_tick(std::span<const uint8_t> rdram) const noexcept;
    // Correct only observed original 0->25 reloads that decrement remaining time.
    // Writes only PAL halfword subcounters 8012DDD8 and 8012DDDC. False is an
    // invalid/stale observation, with no guest memory mutation.
    bool after_tick(std::span<uint8_t> rdram,const Snapshot& before) noexcept;
private:
    std::array<uint8_t,2> phase_{1,1};
    uint64_t sequence_=0;
    bool ready_=false;
};
}
