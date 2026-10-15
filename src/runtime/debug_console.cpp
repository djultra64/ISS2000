// Original project work: djultra64.
// The original guest formatter remains responsible for format/vararg semantics.
#include "runtime/debug_console.hpp"
#include <algorithm>
#include <array>
#include <mutex>

namespace iss2000 {
namespace {
std::mutex console_mutex;
constexpr uint32_t memory_begin=0x80000000u;
constexpr uint64_t memory_end=0x80800000ull;
}

bool debug_console_write_bytes(const uint8_t* rdram, uint32_t address,
                               uint32_t count, std::FILE* output) {
    if (!rdram || !output || address<memory_begin ||
        uint64_t(address)+count>memory_end) return false;
    std::lock_guard lock(console_mutex);
    std::array<unsigned char,1024> bytes{};
    uint32_t offset=address-memory_begin;
    uint32_t remaining=count;
    while (remaining) {
        const auto length=std::min<size_t>(remaining,bytes.size());
        for (size_t i=0;i<length;++i) bytes[i]=rdram[(offset+i)^3u];
        if (std::fwrite(bytes.data(),1,length,output)!=length) return false;
        offset+=static_cast<uint32_t>(length);
        remaining-=static_cast<uint32_t>(length);
    }
    return std::fflush(output)==0 && !std::ferror(output);
}

void debug_console_callback(uint8_t* rdram, recomp_context* ctx) {
    ctx->r2=debug_console_write_bytes(rdram,static_cast<uint32_t>(ctx->r5),
                                    static_cast<uint32_t>(ctx->r6),stderr) ? 1 : 0;
}
}
