// Original project work: djultra64.
#pragma once
#include "recomp.h"
#include <span>
namespace iss2000 {
enum class PalMenuSound { Navigate,Accept,Back,Error };
enum class PalMenuAudioResult { Queued,AlreadyPending,Full,Rejected };
// Call only on the original guest thread with the identity-checked active
// original8004C59C. Genuine resident queue608 retains its eight-slot limit and
// deduplication; no host audio or second audio queue is created. Full may be
// retried by the caller. Rejected invokes nothing and leaves RAM unchanged.
// Original queue writes survive; caller context and borrowed stack always restore.
PalMenuAudioResult play_pal_menu_sound(std::span<uint8_t> ram,const recomp_context& caller,
    PalMenuSound sound,recomp_func_t* original_8004C59C);
}
