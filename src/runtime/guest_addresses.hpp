// Original project work: djultra64. Exact original-body evidence: pal-runtime.md.
#pragma once
#include <cstdint>
namespace iss2000 {
struct GuestAddresses {
    uint32_t debug_output,pfs_init;
    uint32_t arena,model,child,allocate_model,allocate_child,release_model;
    uint32_t far_visibility,visibility,world_corners,title_prompt,button_prompt;
    uint32_t pak_read,pak_write,pak_status,pak_plug,pak_inode_cache;
};
inline constexpr GuestAddresses us_guest_addresses{
    0x800036C8,0x80060550,0x800252B0,0x800252F8,0x80025710,
    0x8002A5A8,0x8002A820,0x8002A6C8,0x80022760,0x80022E58,0x800243E0,
    0x800039F4,0x800414C0,0x80061590,0x80061780,0x80060880,0x80060060,0x8009C434};
inline constexpr GuestAddresses pal_guest_addresses{
    0x80003B88,0x80060DD0,0x80025910,0x80025958,0x80025D70,
    0x8002AC08,0x8002AE80,0x8002AD28,0x80022D90,0x80023488,0x80024A10,
    0x80003EB4,0x80041B50,0x80061E10,0x80062000,0x80061100,0x800608E0,0x80099A44};
inline constexpr const GuestAddresses& active_guest_addresses(){
#ifdef ISS2000_PAL_ENGLISH
    return pal_guest_addresses;
#else
    return us_guest_addresses;
#endif
}
}
