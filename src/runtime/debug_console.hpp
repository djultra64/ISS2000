// Original project work: djultra64.
#pragma once
#include "recomp.h"
#include <cstdint>
#include <cstdio>

namespace iss2000 {
// Transport already-formatted original _Printf chunks. No host printf parsing.
// Guest memory uses swapped 32-bit words; only the 8 MiB RDRAM range is readable.
bool debug_console_write_bytes(const uint8_t* rdram, uint32_t address,
                               uint32_t count, std::FILE* output);
// Original 800036C8 callback ABI: a0 opaque, a1 buffer, a2 byte count;
// non-null v0=1 means accepted output, v0=0 reports a transport failure.
void debug_console_callback(uint8_t* rdram, recomp_context* ctx);
}
