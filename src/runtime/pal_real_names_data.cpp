// Original project work: djultra64.
#include "pal_real_names.hpp"
namespace iss2000 {
std::span<const std::string_view> pal_default_real_names(){
 static constexpr std::array<std::string_view,106*22> names{
#include "pal_real_names_data.inc"
 };
 return names;
}
PalRealNames& pal_real_names_override(){static PalRealNames value;return value;}
}
