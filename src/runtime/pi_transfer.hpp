// Original project work: djultra64.
#pragma once
#include <cstdint>
#include <stdexcept>

namespace iss2000 {
enum class PiRegion { Rom, Sram };
struct PiTransfer {
    PiRegion region;
    std::uint32_t direction; // libultra: 0=device to RDRAM, 1=RDRAM to device.
    std::uint32_t physical;
    std::uint32_t offset;
    std::uint32_t ram;       // Canonical KSEG0 address for the host memory macros.
    std::uint32_t size;
};
namespace pi_detail {
constexpr std::uint32_t guest_size=0x800000;
constexpr std::uint32_t handle_limit=0x801000;
constexpr std::uint32_t rom_base=0x10000000;
constexpr std::uint32_t rom_size=0x1000000;
constexpr std::uint32_t sram_base=0x08000000;
constexpr std::uint32_t sram_size=0x8000;

inline std::uint32_t physical_ram(std::uint32_t address,bool physical_allowed) {
    if(address<0x20000000u) {
        if(physical_allowed)return address;
        throw std::invalid_argument("PI structure pointer must use KSEG0 or KSEG1");
    }
    if(address>=0x80000000u && address<0xC0000000u)return address&0x1FFFFFFFu;
    throw std::invalid_argument("PI pointer is not a physical RDRAM or KSEG address");
}
inline void range(std::uint32_t start,std::uint32_t size,std::uint32_t limit) {
    // Inclusive one-past endpoint is valid only for an empty transfer. No
    // unsigned addition may wrap before this check.
    if(std::uint64_t(start)+size>limit)
        throw std::invalid_argument("PI transfer exceeds verified device or RDRAM bounds");
}
}

// Guest handle/message pointers must be word aligned and represented as either
// a zero-extended 32-bit value or the genuine sign extension of that value.
// Only handles may occupy the runtime's reserved 0x80800000..0x80801000 area.
inline std::uint32_t normalize_pi_pointer(std::uint64_t address,std::uint32_t bytes,
                                         bool runtime_handle=false) {
    const auto low=std::uint32_t(address),high=std::uint32_t(address>>32);
    if(high!=0 && !(high==0xFFFFFFFFu && (low&0x80000000u)))
        throw std::invalid_argument("PI structure pointer has invalid 64-bit extension");
    if(low&3u)throw std::invalid_argument("PI structure pointer must be word aligned");
    const auto physical=pi_detail::physical_ram(low,false);
    pi_detail::range(physical,bytes,runtime_handle?pi_detail::handle_limit:pi_detail::guest_size);
    return 0x80000000u|physical;
}

// Validates the actual OSPiHandle.baseAddress | OSIoMesg.devAddr expression.
// Does not access memory, copy bytes, register code or deliver completion. The
// caller must preserve normal PI completion even when the byte count is zero.
inline PiTransfer validate_pi_transfer(std::uint32_t handle_base,std::uint32_t device_address,
                                       std::uint32_t dram_address,std::uint32_t size,
                                       std::uint32_t direction) {
    if(direction>1)throw std::invalid_argument("Unsupported PI DMA direction");
    const auto physical=(handle_base|device_address)&0x1FFFFFFFu;
    const auto ram_physical=pi_detail::physical_ram(dram_address,true);
    pi_detail::range(ram_physical,size,pi_detail::guest_size);
    const auto ram=ram_physical|0x80000000u;
    if(physical>=pi_detail::rom_base) {
        if(direction!=0)throw std::invalid_argument("Cartridge ROM is read-only");
        const auto offset=physical-pi_detail::rom_base;
        pi_detail::range(offset,size,pi_detail::rom_size);
        // Pinned upstream do_rom_read requires even device and 8-byte RDRAM
        // addresses. SRAM uses byte copies and has no such restriction.
        if((physical&1u)||(ram&7u))
            throw std::invalid_argument("ROM PI DMA violates upstream address alignment");
        return {PiRegion::Rom,direction,physical,offset,ram,size};
    }
    if(physical>=pi_detail::sram_base) {
        const auto offset=physical-pi_detail::sram_base;
        pi_detail::range(offset,size,pi_detail::sram_size);
        return {PiRegion::Sram,direction,physical,offset,ram,size};
    }
    throw std::invalid_argument("PI device address is not supported cartridge ROM or SRAM");
}
}
