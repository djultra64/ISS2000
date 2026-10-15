#include "runtime/motor_result.hpp"
// Original project work: djultra64.
#include "runtime/native_game.hpp"
#include "runtime/game_revision.hpp"
#include "runtime/boot_environment.hpp"
#include "runtime/guest_addresses.hpp"
#include "runtime/video_timing.hpp"
#include "runtime/ntsc_match_clock.hpp"
#include <ultramodern/ultramodern.hpp>
#include "runtime/debug_console.hpp"
#include "runtime/pi_transfer.hpp"
#include "runtime/pak_services.hpp"
#include "runtime/prompt_textures.hpp"
#include "runtime/prompt_text.hpp"
#include "runtime/prompt_encoded.hpp"
#include "runtime/widescreen_culling.hpp"
#include "runtime/marker_aspect.hpp"
#include "runtime/transform_runtime.hpp"
#include "runtime/pal_game_layout.hpp"
#include "renderer_settings.hpp"
#include "platform.hpp"
#include <librecomp/game.hpp>
#include <ultramodern/ultra64.h>
#include <SDL.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <mutex>
#include <sstream>
#include <unordered_set>

// Pinned runtime PI implementation; bounds and canonical addresses are checked below.
void do_dma(uint8_t*,int32_t,gpr,uint32_t,uint32_t,uint32_t);

#ifdef ISS2000_PAL_ENGLISH
extern "C" void iss2000_original_80060DD0(uint8_t*,recomp_context*);
extern "C" void func_801DB94C_overlay_287ab0_801db100(uint8_t*,recomp_context*);
extern "C" void func_801DC14C_overlay_287ab0_801db100(uint8_t*,recomp_context*);
extern "C" void func_801E68F0_overlay_287ab0_801db100(uint8_t*,recomp_context*);
extern "C" void func_801E78F4_overlay_287ab0_801db100(uint8_t*,recomp_context*);
extern "C" void func_802B718C_overlay_386080_802b57e0(uint8_t*,recomp_context*);
extern "C" void func_802388C8_overlay_4a6820_80230590(uint8_t*,recomp_context*);
#else
extern "C" void iss2000_original_80060550(uint8_t*,recomp_context*);
#endif

namespace iss2000 {
namespace {
const auto& guest=active_guest_addresses();
#ifdef ISS2000_PAL_ENGLISH
constexpr auto wide_layout=verified_pal_widescreen_layout();
#else
constexpr auto wide_layout=verified_us_widescreen_layout();
#endif
Registry registry;
#ifdef ISS2000_PAL_ENGLISH
NtscMatchClock ntsc_match_clock;
#endif
std::mutex trace_mutex;
std::unordered_set<uint32_t> traced_services;
struct {uint32_t rom{},ram{},size{};} last_dma;
void complete_dma(uint32_t rom,uint32_t ram,uint32_t size) {
    std::lock_guard lock(trace_mutex);
    last_dma={rom,ram,size};
    std::fprintf(stderr,"[DMA] ROM %08X -> RAM %08X size %08X\n",rom,ram,size);
    registry.dma_completed(rom,ram,size);
}
}
void initialize_native_game(){
    register_generated_sections(registry);
#ifdef ISS2000_PAL_ENGLISH
    configure_title_prompt(pal_en_title_prompt_layout());
    configure_prompt_textures(pal_en_prompt_texture_layout());
    configure_encoded_menu_prompts(pal_en_encoded_prompt_layout());
    configure_transform_runtime(verified_pal_transform_layout());
#else
    configure_title_prompt(us_title_prompt_layout());
    configure_prompt_textures(us_prompt_texture_layout());
    configure_transform_runtime(us_transform_layout());
#endif
}
void run_original_guest(uint32_t address,uint8_t* rdram,recomp_context* ctx){
    auto* original=registry.find(address);
    if(!original){runtime_message("Verified original hook body is not active in the selected code map.");std::exit(1);}
    original(rdram,ctx);
}
void runtime_message(const char* message){
    std::fprintf(stderr,"[Runtime] %s\n",message);std::fflush(stderr);
    SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_ERROR,"ISS2000: execution stopped",message,platform::window());
}
void on_game_init(uint8_t* rdram,recomp_context*){
    platform::set_rdram(rdram);
    set_boot_tv_type({rdram,0x800000},active_revision().tv_type);
    std::fprintf(stderr,"[Boot] IPL television identity %u (%u VI/s)\n",active_revision().tv_type,active_revision().vi_hz);
    complete_dma(0x1000,0x80000400,0x100000);
}
void enter_game(uint8_t* rdram,recomp_context* ctx){
    std::fprintf(stderr,"[Boot] Executing original ISS2000 entry at 80000400\n");
    generated_entrypoint()(rdram,ctx);
}
void track_matrix_arena(uint8_t* rdram,recomp_context* ctx){
    run_original_guest(guest.arena,rdram,ctx);
    observe_transform_frame({rdram,0x800000});
}
void track_model_matrix(uint8_t* rdram,recomp_context* ctx){
    const auto before=observe_transform_matrix_before({rdram,0x800000},ctx->r4,TransformMatrixBuilder::Conditional252F8);
    run_original_guest(guest.model,rdram,ctx);
    observe_transform_matrix_after({rdram,0x800000},before);
}
void track_child_matrix(uint8_t* rdram,recomp_context* ctx){
    const auto before=observe_transform_matrix_before({rdram,0x800000},ctx->r4,TransformMatrixBuilder::Unconditional25710);
    run_original_guest(guest.child,rdram,ctx);
    observe_transform_matrix_after({rdram,0x800000},before);
}
void track_model_allocation(uint8_t* rdram,recomp_context* ctx){
    run_original_guest(guest.allocate_model,rdram,ctx);
    observe_transform_allocation(ctx->r2);
}
void track_child_allocation(uint8_t* rdram,recomp_context* ctx){
    run_original_guest(guest.allocate_child,rdram,ctx);
    observe_transform_allocation(ctx->r2);
}
void track_model_release(uint8_t* rdram,recomp_context* ctx){
    observe_transform_release(ctx->r4);
    run_original_guest(guest.release_model,rdram,ctx);
}
void test_wide_far_visibility(uint8_t* rdram,recomp_context* ctx){
    const bool wide=platform::render_settings().aspect_ratio==AspectRatio::Wide16x9;
    if(!ensure_widescreen_far_extents({rdram,0x800000},wide,wide_layout)){
        static std::once_flag warning;
        std::call_once(warning,[]{std::fprintf(stderr,"[Render] Original far-plane extents are outside the reviewed widescreen layout.\n");});
    }
    run_original_guest(guest.far_visibility,rdram,ctx);
}
void update_wide_visibility(uint8_t* rdram,recomp_context* ctx){
    run_original_guest(guest.visibility,rdram,ctx);
    const bool wide=platform::render_settings().aspect_ratio==AspectRatio::Wide16x9;
    if(!apply_widescreen_culling({rdram,0x800000},wide,wide_layout)){
        static std::once_flag warning;
        std::call_once(warning,[]{std::fprintf(stderr,"[Render] Original camera bounds are outside the reviewed widescreen layout.\n");});
    }
}
void update_wide_world_corners(uint8_t* rdram,recomp_context* ctx){
    run_original_guest(guest.world_corners,rdram,ctx);
    const bool wide=platform::render_settings().aspect_ratio==AspectRatio::Wide16x9;
    if(!apply_widescreen_world_corners({rdram,0x800000},wide,wide_layout)){
        static std::once_flag warning;
        std::call_once(warning,[]{std::fprintf(stderr,"[Render] Original camera corner rays are outside the reviewed widescreen layout.\n");});
    }
}
void register_physical_title(uint8_t* rdram,recomp_context* ctx){
    prepare_title_prompt(rdram,ctx->r4,ctx->r5,platform::prompt(0,platform::Action::Start).name);
    run_original_guest(guest.title_prompt,rdram,ctx);
}
void draw_physical_prompt(uint8_t* rdram,recomp_context* ctx){
    const auto help=platform::controls_help(0);
    prepare_prompt_textures(rdram,ctx->r4,{help.prompts[0].glyph,help.prompts[1].glyph});
    run_original_guest(guest.button_prompt,rdram,ctx);
}
#ifdef ISS2000_PAL_ENGLISH
// Each original setter still updates its complete hierarchical stage context.
// Same-value resets invalidate IDs as well as numerical scene changes.
template<uint32_t Address> void transition_stage(uint8_t* rdram,recomp_context* ctx){
    run_original_guest(Address,rdram,ctx);
    notify_transform_discontinuity();
}
void begin_recorded_replay(uint8_t* rdram,recomp_context* ctx){
    notify_transform_discontinuity();
    func_801E68F0_overlay_287ab0_801db100(rdram,ctx);
    notify_transform_discontinuity();
}
void leave_recorded_replay(uint8_t* rdram,recomp_context* ctx){
    notify_transform_discontinuity();
    func_801E78F4_overlay_287ab0_801db100(rdram,ctx);
    notify_transform_discontinuity();
}
void correct_recorded_ball_position(uint8_t* rdram,recomp_context* ctx){
    const auto before=observe_transform_position_before({rdram,0x800000},0x2B57D0);
    func_802B718C_overlay_386080_802b57e0(rdram,ctx);
    observe_transform_position_after({rdram,0x800000},before);
}
void place_original_players(uint8_t* rdram,recomp_context* ctx){
    func_802388C8_overlay_4a6820_80230590(rdram,ctx);
    notify_transform_discontinuity();
}
void draw_encoded_physical_prompt(uint8_t* rdram,recomp_context* ctx){
    const auto help=platform::controls_help(0);
    prepare_encoded_menu_prompt({rdram,0x800000},ctx->r4,
        {help.prompts[0].name,help.prompts[1].name,help.prompts[2].name});
    run_original_guest(0x80048660u,rdram,ctx);
}
void initialize_ntsc_match_clock(uint8_t* rdram,recomp_context* ctx){
    func_801DB94C_overlay_287ab0_801db100(rdram,ctx);
    if(!ntsc_match_clock.reset_after_init({rdram,0x800000}))
        throw std::runtime_error("Original PAL match-clock initialization differs from its verified layout");
}
void tick_ntsc_match_clock(uint8_t* rdram,recomp_context* ctx){
    const auto before=ntsc_match_clock.before_tick({rdram,0x800000});
    func_801DC14C_overlay_287ab0_801db100(rdram,ctx);
    if(!ntsc_match_clock.after_tick({rdram,0x800000},before)){
        static std::once_flag warning;
        std::call_once(warning,[]{std::fprintf(stderr,"[Timing] Match-clock observation unavailable; retaining original clock state.\n");});
    }
}
#endif
void init_controller_pak(uint8_t* rdram,recomp_context* ctx){
    const auto port=uint32_t(ctx->r6);
    if(port>=4){ctx->r2=5;return;}
    if(platform::input_callbacks().get_connected_device_info(int(port)).connected_device==ultramodern::input::Device::None){ctx->r2=4;return;}
    const auto accessory=pak_accessory(int(port));
    if(accessory!=PakAccessory::Controller){ctx->r2=accessory==PakAccessory::Rumble?11:1;return;}
    try{
        ctx->r4=S32(normalize_pi_pointer(ctx->r4,sizeof(OSMesgQueue)));
        ctx->r5=S32(normalize_pi_pointer(ctx->r5,sizeof(OSPfs)));
    }catch(const std::exception&){ctx->r2=5;return;}
#ifdef ISS2000_PAL_ENGLISH
    call_service(guest.pfs_init,"osPfsInitPak",&iss2000_original_80060DD0,rdram,ctx);
#else
    call_service(guest.pfs_init,"osPfsInitPak",&iss2000_original_80060550,rdram,ctx);
#endif
}
void call_service(uint32_t address,const char* name,recomp_func_t* service,uint8_t* rdram,recomp_context* ctx){
    {
        std::lock_guard lock(trace_mutex);
        if(traced_services.insert(address).second)std::fprintf(stderr,"[Service] %08X %s\n",address,name);
    }
    // The pinned upstream's raw DP path is an unimplemented assertion. Keep it
    // fatal even in a Release build, rather than reporting pretend completion.
    if(std::strcmp(name,"osYieldThread")==0){runtime_message("The original game requested osYieldThread, which is not implemented by the pinned runtime.");std::exit(1);}
    if(std::strcmp(name,"osDpSetNextBuffer")==0){runtime_message("The original game requested raw RDP submission, which is not integrated yet.");std::exit(1);}
#ifdef ISS2000_PAL_ENGLISH
    if(std::strcmp(name,"osAiSetFrequency")==0){
        const auto rate=audio_frequency(uint32_t(ctx->r4),active_revision().audio_clock);
        if(!rate){ctx->r2=S32(-1);return;}
        ultramodern::set_audio_frequency(rate->actual_hz);
        ctx->r2=S32(rate->actual_hz);return;
    }
#endif
    // AI_LEN exposes the current DMA, rather than both buffers accumulated by SDL.
    if(std::strcmp(name,"osAiGetLength")==0){ctx->r2=platform::audio_length();return;}
    if(std::strcmp(name,"osAiGetStatus")==0){ctx->r2=platform::audio_status();return;}
    if(std::strcmp(name,"osAiSetNextBuffer")==0){ctx->r2=S32(platform::submit_audio(rdram,uint32_t(ctx->r4),uint32_t(ctx->r5)));return;}
    if(std::strcmp(name,"osSpTaskStartGo")==0){
        try{
            const auto source=normalize_pi_pointer(ctx->r4,sizeof(OSTask));
            const auto task=*TO_PTR(OSTask,S32(source));
            const TransformTaskFingerprint fingerprint{.data_ptr=uint32_t(task.t.data_ptr),
                .ucode=uint32_t(task.t.ucode),.ucode_data=uint32_t(task.t.ucode_data),.data_size=task.t.data_size};
            // The first graphics producer is pinned by the tracker. The pinned
            // upstream queue guarantees FIFO within that producer stream only.
            std::lock_guard lock(transform_submission_mutex());
            submit_transform_metadata({rdram,0x800000},task.t.type,fingerprint);
            service(rdram,ctx);
            return;
        }catch(const std::exception& error){runtime_message(error.what());std::exit(1);}
    }
    if(std::strcmp(name,"osEPiStartDma")==0){
        try {
            const auto handle_address=normalize_pi_pointer(ctx->r4,sizeof(OSPiHandle),true);
            const auto message_address=normalize_pi_pointer(ctx->r5,sizeof(OSIoMesg));
            const auto* handle=TO_PTR(OSPiHandle,S32(handle_address));
            const auto* message=TO_PTR(OSIoMesg,S32(message_address));
            const auto transfer=validate_pi_transfer(handle->baseAddress,message->devAddr,
                message->dramAddr,message->size,uint32_t(ctx->r6));
            const auto queue=normalize_pi_pointer(uint32_t(message->hdr.retQueue),sizeof(OSMesgQueue));
            if(transfer.region==PiRegion::Rom && transfer.size){
                // Register executable aliases before real PI completion reaches the game.
                registry.transfer(transfer.offset,transfer.ram,transfer.size,
                    [&]{recomp::do_rom_read(rdram,S32(transfer.ram),transfer.physical,transfer.size);},
                    [&]{
                        {std::lock_guard lock(trace_mutex);last_dma={transfer.offset,transfer.ram,transfer.size};
                        if(std::getenv("ISS2000_TRACE_DMA"))std::fprintf(stderr,"[DMA] ROM %08X -> RAM %08X size %08X\n",transfer.offset,transfer.ram,transfer.size);}
                        ultramodern::enqueue_external_message_src(int32_t(queue),0,false,ultramodern::EventMessageSource::Pi);
                    });
            }else{
                // Actual upstream ROM/SRAM copy and completion, including zero bytes.
                do_dma(rdram,int32_t(queue),S32(transfer.ram),transfer.physical,transfer.size,transfer.direction);
            }
            ctx->r2=0;
            return;
        }catch(const std::exception& error){
            runtime_message(error.what());std::exit(1);
        }
    }
    if(std::strcmp(name,"osMotorInit")==0){
        try{
            ctx->r4=S32(normalize_pi_pointer(ctx->r4,sizeof(OSMesgQueue)));
            ctx->r5=S32(normalize_pi_pointer(ctx->r5,sizeof(OSPfs)));
            const auto port=uint32_t(ctx->r6);
            if(port>=4){ctx->r2=5;return;}
            service(rdram,ctx); // Keep real OSPfs queue/channel/status initialization.
            ctx->r2=gpr(S32(motor_init_result(int32_t(ctx->r2),pak_accessory(int(port)))));
            return;
        }catch(const std::exception& error){runtime_message(error.what());std::exit(1);}
    }
    if(std::strcmp(name,"osContInit")==0 || std::strcmp(name,"osContGetQuery")==0){
        try{
            const bool initial=std::strcmp(name,"osContInit")==0;
            const auto status=normalize_pi_pointer(initial?ctx->r6:ctx->r4,4*sizeof(OSContStatus));
            if(initial){
                // Validate byte-aligned bitpattern without losing KSEG aliases.
                const auto pattern_offset=uint32_t(ctx->r5)&3u;
                ctx->r5=S32(normalize_pi_pointer(ctx->r5&~uint64_t(3),4)+pattern_offset);
                ctx->r4=S32(normalize_pi_pointer(ctx->r4,sizeof(OSMesgQueue)));
                ctx->r6=S32(status);
            }else ctx->r4=S32(status);
            service(rdram,ctx);
            auto* slots=TO_PTR(OSContStatus,S32(status));
            for(int port=0;port<4;++port)if(slots[port].err_no==0)slots[port].status=pak_accessory(port)!=PakAccessory::None;
            return;
        }catch(const std::exception& error){runtime_message(error.what());std::exit(1);}
    }
    service(rdram,ctx);
}
}
// Called only at three reviewed local marker-aspect loads in private generated
// derivatives. Guest projection/global RAM and physics retain original values.
extern "C" float iss2000_marker_aspect(float original){
    return iss2000::marker_aspect(original,
        iss2000::platform::render_settings().aspect_ratio==iss2000::AspectRatio::Wide16x9);
}
#ifdef ISS2000_LOOKUP_DIRECT
extern "C" recomp_func_t* get_function(int32_t address){
#else
extern "C" recomp_func_t* __wrap_get_function(int32_t address){
#endif
    // Original IS64 output transport; the guest formatter still executes natively.
    // Exact supported ROM digest also binds ROM42C8..4470 to the reviewed callback.
    const auto& guest=iss2000::active_guest_addresses();
#ifdef ISS2000_PAL_ENGLISH
    if(uint32_t(address)==0x80048660u)return &iss2000::draw_encoded_physical_prompt;
    if(uint32_t(address)==0x800036ACu)return &iss2000::transition_stage<0x800036AC>;
    if(uint32_t(address)==0x80003710u)return &iss2000::transition_stage<0x80003710>;
    if(uint32_t(address)==0x800037BCu)return &iss2000::transition_stage<0x800037BC>;
    if(uint32_t(address)==0x80003868u)return &iss2000::transition_stage<0x80003868>;
    if(uint32_t(address)==0x80003914u)return &iss2000::transition_stage<0x80003914>;
    if(uint32_t(address)==0x801E68F0u && iss2000::registry.find(uint32_t(address))==&func_801E68F0_overlay_287ab0_801db100)
        return &iss2000::begin_recorded_replay;
    if(uint32_t(address)==0x801E78F4u && iss2000::registry.find(uint32_t(address))==&func_801E78F4_overlay_287ab0_801db100)
        return &iss2000::leave_recorded_replay;
    if(uint32_t(address)==0x802B718Cu && iss2000::registry.find(uint32_t(address))==&func_802B718C_overlay_386080_802b57e0)
        return &iss2000::correct_recorded_ball_position;
    if(uint32_t(address)==0x802388C8u && iss2000::registry.find(uint32_t(address))==&func_802388C8_overlay_4a6820_80230590)
        return &iss2000::place_original_players;
    // Overlay guest PCs can be reused. Intercept only the exact active original
    // function pointer from the verified match-clock section, never an alias.
    if(uint32_t(address)==0x801DB94Cu && iss2000::registry.find(uint32_t(address))==&func_801DB94C_overlay_287ab0_801db100)
        return &iss2000::initialize_ntsc_match_clock;
    if(uint32_t(address)==0x801DC14Cu && iss2000::registry.find(uint32_t(address))==&func_801DC14C_overlay_287ab0_801db100)
        return &iss2000::tick_ntsc_match_clock;
#endif
    if(uint32_t(address)==guest.debug_output)return &iss2000::debug_console_callback;
    if(uint32_t(address)==guest.arena)return &iss2000::track_matrix_arena;
    if(uint32_t(address)==guest.model)return &iss2000::track_model_matrix;
    if(uint32_t(address)==guest.child)return &iss2000::track_child_matrix;
    if(uint32_t(address)==guest.allocate_model)return &iss2000::track_model_allocation;
    if(uint32_t(address)==guest.allocate_child)return &iss2000::track_child_allocation;
    if(uint32_t(address)==guest.release_model)return &iss2000::track_model_release;
    if(uint32_t(address)==guest.far_visibility)return &iss2000::test_wide_far_visibility;
    if(uint32_t(address)==guest.visibility)return &iss2000::update_wide_visibility;
    if(uint32_t(address)==guest.world_corners)return &iss2000::update_wide_world_corners;
    if(uint32_t(address)==guest.title_prompt)return &iss2000::register_physical_title;
    if(uint32_t(address)==guest.button_prompt)return &iss2000::draw_physical_prompt;
    if(uint32_t(address)==guest.pfs_init)return &iss2000::init_controller_pak;
    if(auto* peripheral=iss2000::pak_service_lookup(uint32_t(address)))return peripheral;
    if(auto* service=iss2000::reviewed_service(uint32_t(address)))return service;
    if(auto* function=iss2000::registry.find(uint32_t(address)))return function;
    std::ostringstream message;
    message<<"Unmapped original guest call at 0x"<<std::hex<<uint32_t(address)<<".\nActive code sections: ";
    for(const auto& name:iss2000::registry.active_names())message<<name<<' ';
    {std::lock_guard lock(iss2000::trace_mutex);
    message<<"\nLast DMA: ROM 0x"<<iss2000::last_dma.rom<<" to RAM 0x"<<iss2000::last_dma.ram<<" size 0x"<<iss2000::last_dma.size;}

    iss2000::runtime_message(message.str().c_str());
    std::exit(1);
}
