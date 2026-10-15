// Original project work: djultra64.
#pragma once
namespace iss2000 {
struct GameRevision {
    const char* id;
    const char* sha256;
    const char* storage_name;
    const char* description;
    unsigned tv_type,vi_hz,audio_clock,audio_ucode;
};
inline constexpr GameRevision us_revision{
    "iss2000-us-rev0","e18e87c062a66002c0cbd7e2dd793ef755609e70675d5679df0396d4b6c67850",
    "iss2000-us.z64","USA revision 0 (English/Spanish)",1,60,48681812,0x6B770};
inline constexpr GameRevision pal_revision{
    "iss2000-pal-en-de-rev0","6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf",
    "iss2000-pal-en-de.z64","Europe revision 0 (English/German); English release",0,50,49656530,0x6BFF0};
inline constexpr const GameRevision& active_revision(){
#ifdef ISS2000_PAL_ENGLISH
    return pal_revision;
#else
    return us_revision;
#endif
}
}
