// Original project work: djultra64.
#pragma once
#include "recomp.h"
#include "runtime/section_registry.hpp"
namespace iss2000 {
using Registry=SectionRegistry<recomp_func_t*>;
void register_generated_sections(Registry&);
recomp_func_t* reviewed_service(uint32_t);
recomp_func_t* generated_entrypoint();
void call_service(uint32_t,const char*,recomp_func_t*,uint8_t*,recomp_context*);
void initialize_native_game();
void on_game_init(uint8_t*,recomp_context*);
void enter_game(uint8_t*,recomp_context*);
void runtime_message(const char*);
}
