// Original project work: djultra64.
#pragma once
#include "recomp.h"
#include <atomic>
#include <cstdio>
namespace iss2000 {
enum class PalLoadTracePoint {TrainingBegin,ControllerReady};
// Call only from the original guest thread, after an exact active-function
// identity check. Logs to the existing process stderr; opens no file/device,
// borrows no guest stack, and executes the original with its live context once.
// A null stream disables logging while retaining all original behavior.
inline void trace_pal_load_transition(PalLoadTracePoint point,uint8_t*ram,
        recomp_context*context,recomp_func_t*original,FILE*stream=stderr){
    static std::atomic<unsigned long long> next{};
    const auto sequence=next.fetch_add(1,std::memory_order_relaxed)+1;
    const bool ready=point==PalLoadTracePoint::ControllerReady;
    const char*name=ready?"ControllerReady":"BeginTraining";
    const unsigned pc=ready?0x802C53A4u:0x802BE3E4u;
    auto log=[&](const char*phase){
        if(!stream)return;
        std::fprintf(stream,"[Load] %llu %s %08X %s sp=%08X a0=%08X v0=%08X\n",
            sequence,name,pc,phase,unsigned(context->r29),unsigned(context->r4),unsigned(context->r2));
        std::fflush(stream);
    };
    log("enter");
    try{original(ram,context);}
    catch(...){log("throw");throw;}
    log("return");
}
}
