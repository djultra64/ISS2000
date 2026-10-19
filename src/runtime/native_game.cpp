#include "runtime/pal_real_names.hpp"
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
#include "runtime/prompt_sprite_draw.hpp"
#include "runtime/pal_team_saved_data.hpp"
#include "runtime/prompt_text.hpp"
#include "runtime/prompt_encoded.hpp"
#include "runtime/prompt_title_model.hpp"
#include "runtime/widescreen_culling.hpp"
#include "runtime/marker_aspect.hpp"
#include "runtime/transform_runtime.hpp"
#include "runtime/menu_sprite_runtime.hpp"
#include "runtime/pal_menu_audio.hpp"
#include "runtime/pal_load_trace.hpp"
#include "runtime/pal_shadow_vertices.hpp"
#include "runtime/pal_projected_shadow.hpp"
#include "runtime/pal_game_layout.hpp"
#include "runtime/game_controls_menu.hpp"
#include "runtime/game_settings_menu.hpp"
#include "runtime/football_controller_editor.hpp"
#include "runtime/pal_controller_screen.hpp"
#include "runtime/pal_main_select.hpp"
#include "runtime/pal_football_input.hpp"
#include "runtime/input_preferences.hpp"
#include "runtime/pal_options_entry.hpp"
#include "runtime/pal_sky_widescreen.hpp"
#include "runtime/pal_hud_widescreen.hpp"
#include "runtime/pal_background_widescreen.hpp"
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
extern "C" void func_802A4DC0_overlay_376010_802a4380(uint8_t*,recomp_context*);
extern "C" void func_802A472C_overlay_376010_802a4380(uint8_t*,recomp_context*);
extern "C" void func_802A5290_overlay_376010_802a4380(uint8_t*,recomp_context*);
extern "C" void iss2000_pal_radar_callback(uint8_t*,recomp_context*);
extern "C" void func_802A4F78_overlay_376010_802a4380(uint8_t*,recomp_context*);
extern "C" void func_8023A510_overlay_4a6820_80230590(uint8_t*,recomp_context*);
extern "C" void func_802BE3E4_overlay_401910_802b8500(uint8_t*,recomp_context*);
extern "C" void func_802C53A4_overlay_40c7a0_802c3490(uint8_t*,recomp_context*);
extern "C" void func_802C49B8_overlay_40c7a0_802c3490(uint8_t*,recomp_context*);
extern "C" void func_802C48F4_overlay_40c7a0_802c3490(uint8_t*,recomp_context*);
extern "C" void func_802C4C40_overlay_40c7a0_802c3490(uint8_t*,recomp_context*);
extern "C" void func_802C4D88_overlay_40c7a0_802c3490(uint8_t*,recomp_context*);
extern "C" void func_801D4880_overlay_25aaf0_801ad820(uint8_t*,recomp_context*);
extern "C" void func_801D5A74_overlay_25aaf0_801ad820(uint8_t*,recomp_context*);
extern "C" void func_801D5E1C_overlay_25aaf0_801ad820(uint8_t*,recomp_context*);
extern "C" void func_801D4CC0_overlay_25aaf0_801ad820(uint8_t*,recomp_context*);

extern "C" void iss2000_pal_wide_sky(uint8_t*,recomp_context*);
extern "C" void func_80060140_resident(uint8_t*,recomp_context*);
extern "C" void func_801B3960_overlay_2dee70_801ad820(uint8_t*,recomp_context*);
extern "C" void iss2000_pal_storage_schedule(uint8_t*,recomp_context*,recomp_func_t*);
extern "C" void iss2000_pal_max_detail_models(uint8_t*,recomp_context*);
extern "C" void iss2000_pal_max_detail_shadows(uint8_t*,recomp_context*);
extern "C" void func_8004C59C_resident(uint8_t*,recomp_context*);
extern "C" void func_80048660_resident(uint8_t*,recomp_context*);
extern "C" void func_80008A54_resident(uint8_t*,recomp_context*);
extern "C" void func_80007C2C_resident(uint8_t*,recomp_context*);
extern "C" void func_80041B50_resident(uint8_t*,recomp_context*);
extern "C" void func_80023344_resident(uint8_t*,recomp_context*);
extern "C" void func_80048528_resident(uint8_t*,recomp_context*);
extern "C" void func_8029F2D8_overlay_3b47e0_8029eea0(uint8_t*,recomp_context*);
extern "C" void func_80008C30_resident(uint8_t*,recomp_context*);
extern "C" void iss2000_pal_fixed_high_initializer(uint8_t*,recomp_context*);
extern "C" void func_8001D480_resident(uint8_t*,recomp_context*);
extern "C" void iss2000_pal_framebuffer_allocator(uint8_t*,recomp_context*);
extern "C" void func_802A3464_overlay_3e83d0_8029eea0(uint8_t*,recomp_context*);
extern "C" void iss2000_pal_formation_save(uint8_t*,recomp_context*);
extern "C" void func_80000C30_resident(uint8_t*,recomp_context*);
extern "C" void iss2000_pal_native_frame_pace(uint8_t*,recomp_context*);
extern "C" void func_807AA008_overlay_515890_807aa000(uint8_t*,recomp_context*);
extern "C" void iss2000_pal_high_sprite_edges(uint8_t*,recomp_context*);
extern "C" void func_800019FC_resident(uint8_t*,recomp_context*);
extern "C" void func_801ADD44_overlay_2c99e0_801ad820(uint8_t*,recomp_context*);
extern "C" void func_8005CD50_resident(uint8_t*,recomp_context*);
extern "C" void func_802B5574_overlay_3fc9f0_802b35b0(uint8_t*,recomp_context*);
extern "C" void iss2000_pal_skip_rumble_802B5574(uint8_t*,recomp_context*);
extern "C" void func_802BA770_overlay_401910_802b8500(uint8_t*,recomp_context*);
extern "C" void iss2000_pal_skip_rumble_802BA770(uint8_t*,recomp_context*);
extern "C" void func_802BE1B8_overlay_401910_802b8500(uint8_t*,recomp_context*);
extern "C" void iss2000_pal_skip_rumble_802BE1B8(uint8_t*,recomp_context*);
extern "C" void func_802C6D34_overlay_40c7a0_802c3490(uint8_t*,recomp_context*);
extern "C" void iss2000_pal_skip_rumble_802C6D34(uint8_t*,recomp_context*);
extern "C" void func_803D2F34_overlay_57f870_803d1a30(uint8_t*,recomp_context*);
extern "C" void iss2000_pal_skip_rumble_803D2F34(uint8_t*,recomp_context*);
extern "C" void func_802B1FDC_overlay_481680_802b1070(uint8_t*,recomp_context*);
extern "C" void iss2000_pal_skip_expansion_notice(uint8_t*,recomp_context*);
extern "C" void func_802B1CC8_overlay_481680_802b1070(uint8_t*,recomp_context*);
extern "C" void iss2000_pal_automatic_storage_ui(uint8_t*,recomp_context*);
extern "C" bool iss2000_pal_storage_text(uint8_t*,uint64_t);
extern "C" bool iss2000_pal_storage_loading(uint8_t*);
extern "C" void func_802B1D84_overlay_481680_802b1070(uint8_t*,recomp_context*);
extern "C" void iss2000_pal_automatic_storage_update(uint8_t*,recomp_context*);
extern "C" void func_80041A44_resident(uint8_t*,recomp_context*);
extern "C" void iss2000_pal_automatic_storage_render(uint8_t*,recomp_context*);
#else
extern "C" void iss2000_original_80060550(uint8_t*,recomp_context*);
#endif

namespace iss2000 {
namespace {
const auto& guest=active_guest_addresses();
#ifdef ISS2000_PAL_ENGLISH
WidescreenGuestLayout current_wide_layout(uint8_t* ram){return verified_pal_widescreen_layout(pal_widescreen_projection_scale({ram,0x800000}));}
#else
WidescreenGuestLayout current_wide_layout(uint8_t*){return verified_us_widescreen_layout();}
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
    configure_pal_shadow_vertices(true);
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
#ifdef ISS2000_PAL_ENGLISH
void draw_physical_prompt(uint8_t*,recomp_context*);
void track_initialize_text(uint8_t* ram,recomp_context* ctx){
    const auto object=ctx->r4;
    run_original_guest(0x80048528,ram,ctx);
    observe_menu_text_initialization(object);
}
void track_initialize_sprite(uint8_t* ram,recomp_context* ctx){
    run_original_guest(0x80008A54,ram,ctx);
    observe_menu_sprite_initialization(ctx->r4);
}
void track_menu_sprite(uint8_t* ram,recomp_context* ctx){
    const auto observation=observe_menu_sprite_before({ram,0x800000},ctx->r4);
    struct Completed {uint8_t* ram;MenuSpriteObservation observation;
        ~Completed(){observe_menu_sprite_after({ram,0x800000},observation);}
    } completed{ram,observation};
    draw_physical_prompt(ram,ctx);
}
void draw_encoded_physical_prompt(uint8_t*,recomp_context*);
void track_menu_text(uint8_t* ram,recomp_context* ctx){
    const auto observation=observe_menu_text_before({ram,0x800000},ctx->r4);
    struct Completed {uint8_t* ram;MenuSpriteObservation observation;
        ~Completed(){observe_menu_sprite_after({ram,0x800000},observation);}
    } completed{ram,observation};
    draw_encoded_physical_prompt(ram,ctx);
}
void draw_widescreen_intro_canvas(uint8_t* ram,recomp_context* ctx){
    const auto descriptor=ctx->r4,palette=ctx->r5,segments=ctx->r6,alpha=ctx->r7;
    uint32_t begin;std::memcpy(&begin,ram+0x1B77C0,sizeof(begin));
    run_original_guest(0x801ADD44,ram,ctx);
    extend_pal_intro_canvas({ram,0x800000},platform::render_settings().aspect_ratio==AspectRatio::Wide16x9,
        descriptor,palette,segments,alpha,begin);
    uint32_t end;std::memcpy(&end,ram+0x1B77C0,sizeof(end));
    observe_menu_canvas({ram,0x800000},descriptor,begin,end);
}
void draw_widescreen_screen_fill(uint8_t* ram,recomp_context* ctx){
    PalScreenFillScope fill({ram,0x800000},
        platform::render_settings().aspect_ratio==AspectRatio::Wide16x9);
    func_800019FC_resident(ram,ctx);
}
void clear_original_guest_memory(uint8_t* ram,recomp_context* ctx){
    // Observe the genuine signed-length zero fill, including unaligned bytes.
    // Loader BSS clears must retire overwritten code and folded table bytes.
    const auto length=int32_t(ctx->r5);
    uint32_t start=0;
    if(length>0){
        try{
            const auto offset=uint32_t(ctx->r4)&3u;
            start=normalize_pi_pointer(ctx->r4&~uint64_t(3),uint32_t(length)+offset)+offset;
        }catch(const std::exception& error){runtime_message(error.what());std::exit(1);}
    }
    run_original_guest(0x8005CD50,ram,ctx);
    if(length>0)registry.invalidate_ram_range(start,uint32_t(length));
}
bool original_controller_screen(uint8_t* ram,bool include_exit=false){
    if(registry.find(0x802C49B8)!=&func_802C49B8_overlay_40c7a0_802c3490 ||
       registry.find(0x802C48F4)!=&func_802C48F4_overlay_40c7a0_802c3490)return false;
    auto word=[&](uint32_t offset){uint32_t value;std::memcpy(&value,ram+offset,4);return value;};
    // Original scheduler 801B3750 initializes 220 nodes of 0x74 bytes;
    // 801B36E0 walks this list and clears the transient current-node pointer.
    uint32_t node=word(0x77390);
    std::array<bool,220> seen{};
    bool found=false;
    while(node){
        if(node<0x801E7070 || node>=0x801ED420 || (node-0x801E7070)%0x74)return false;
        const auto index=(node-0x801E7070)/0x74;
        if(index>=seen.size() || seen[index])return false;
        seen[index]=true;
        const auto callback=word((node&0x7FFFFF)+0xC);
        const auto pending=word((node&0x7FFFFF)+0x10);
        if(callback==0x802C48F4||callback==0x802C48C0||
           (callback==0x8000CDD0&&pending==0x802C48C0)||
           (include_exit&&callback==0x8000C96C&&pending==0x802C48C0))found=true;
        node=word(node&0x7FFFFF);
    }
    return found;
}
void run_football_controller_stage(uint8_t* ram,recomp_context* ctx,recomp_func_t* original){
    // Diagnostic nesting only: the original packet-pointer guard still owns
    // projection. Nested normalizer/special calls must not flood the trace.
    static thread_local unsigned trace_depth=0;
    struct TraceDepth {unsigned& value;TraceDepth(unsigned& v):value(v){++value;}~TraceDepth(){--value;}} depth(trace_depth);
    const auto stage=original==&func_801D5A74_overlay_25aaf0_801ad820?0x801D5A74u:
        original==&func_801D5E1C_overlay_25aaf0_801ad820?0x801D5E1Cu:
        original==&func_801D4CC0_overlay_25aaf0_801ad820?0x801D4CC0u:0x801D4880u;
    const auto object=uint32_t(ctx->r4);
    if(object>=0x80127468&&object<=0x80127468+3*0xA8&&(object-0x80127468)%0xA8==0){
        const unsigned port=(object-0x80127468)/0xA8;
        uint32_t packet;std::memcpy(&packet,ram+(object&0x7FFFFF)+0x24,4);
        // An outer original processor already owns a projected packet. Keep
        // its complete original closure inside that scope without converting
        // or consuming the physical sample a second time.
        if(packet==0x8013B454+port*10){
            const auto input=platform::football_si_input(port);
            const auto preferences=platform::port_preferences();
            const auto& config=preferences[port];
            auto trace=[&](PalFootballInputResult result){if(trace_depth==1)
                trace_pal_football_stage({ram,0x800000},*ctx,port,stage,object,input.sequence,input.gamepad,config.football_scheme,result);};
            trace(PalFootballInputResult::Entry);
            if(input.gamepad&&input.sequence){
                const auto bindings=config.football_scheme==ControllerScheme::Free?config.free_football_bindings:
                    *scheme_bindings(config.football_scheme);
                if(apply_pal_football_input({ram,0x800000},*ctx,input.held,input.pressed,bindings,original)){
                    trace(PalFootballInputResult::Applied);return;
                }
                trace(pal_football_input_result());
            }else trace(input.gamepad?PalFootballInputResult::NoSiSample:PalFootballInputResult::NoGamepad);
        }else if(trace_depth==1){
            const auto preferences=platform::port_preferences();
            trace_pal_football_stage({ram,0x800000},*ctx,port,stage,object,0,false,preferences[port].football_scheme,PalFootballInputResult::Entry);
            trace_pal_football_stage({ram,0x800000},*ctx,port,stage,object,0,false,preferences[port].football_scheme,PalFootballInputResult::ForeignPacket);
        }
    }
    original(ram,ctx);
}
void normalize_football_controller(uint8_t* ram,recomp_context* ctx){
    run_football_controller_stage(ram,ctx,&func_801D4880_overlay_25aaf0_801ad820);
}
void process_football_controller(uint8_t* ram,recomp_context* ctx){
    run_football_controller_stage(ram,ctx,&func_801D5A74_overlay_25aaf0_801ad820);
}
void process_auxiliary_football_controller(uint8_t* ram,recomp_context* ctx){
    run_football_controller_stage(ram,ctx,&func_801D5E1C_overlay_25aaf0_801ad820);
}
void process_special_football_controller(uint8_t* ram,recomp_context* ctx){
    run_football_controller_stage(ram,ctx,&func_801D4CC0_overlay_25aaf0_801ad820);
}

bool controller_save_failed=false;
void ensure_controller_editor(){
    auto& editor=football_controller_editor();
    if(editor.snapshot().active)return;
    const auto preferences=platform::port_preferences();
    std::array<FootballPortConfig,4> initial;
    for(unsigned port=0;port<4;++port)
        initial[port]={preferences[port].football_scheme,preferences[port].free_football_bindings};
    editor.begin(initial,platform::active_input_port());
    controller_save_failed=false;
}
bool save_original_controller_port(unsigned port){
    const auto state=football_controller_editor().snapshot();
    if(!state.active||state.editing_free||port>=4)return false;
    try{
        auto preferences=capture_input_preferences();
        preferences.ports[port].football_scheme=state.draft[port].scheme;
        preferences.ports[port].free_football_bindings=state.draft[port].free_bindings;
        save_input_preferences(recomp::get_config_path(),preferences);
        apply_input_preferences(preferences);
        controller_save_failed=false;
        return true;
    }catch(const std::exception& error){
        std::fprintf(stderr,"[Controls] Save failed: %s\n",error.what());
        controller_save_failed=true;
        return false;
    }
}
void select_original_controller_action(uint8_t* ram,recomp_context* ctx){
    if(!original_controller_screen(ram)){
        func_802C49B8_overlay_40c7a0_802c3490(ram,ctx);
        return;
    }
    ensure_controller_editor();
    const unsigned port=ram[0x2D21EF^3];
    const bool editable=port<4&&ram[(0x2D21F0+port)^3]==0;
    const unsigned row=editable?ram[(0x2D21E0+port)^3]:255;
    if(row==0&&!save_original_controller_port(port))return;
    // Preserve the original Type-row no-op and genuine OK/Ready continuation.
    func_802C49B8_overlay_40c7a0_802c3490(ram,ctx);
    if(row==1){
        auto& editor=football_controller_editor();
        editor.select_port(port);
        if(editor.snapshot().draft[port].scheme==ControllerScheme::Free)editor.open_free();
    }
}
bool cycle_original_controller_type(uint8_t* ram,int direction){
    if(!original_controller_screen(ram))return false;
    const unsigned port=ram[0x2D21EF^3];
    if(port>=4||ram[(0x2D21F0+port)^3]||ram[(0x2D21E0+port)^3]!=1)return false;
    ensure_controller_editor();
    auto& editor=football_controller_editor();
    editor.select_port(port);
    editor.cycle_scheme(direction);
    controller_save_failed=false;
    return true;
}
void previous_original_controller_type(uint8_t* ram,recomp_context* ctx){
    const bool host=cycle_original_controller_type(ram,-1);
    const unsigned port=ram[0x2D21EF^3];
    const auto type=host?ram[(0x2D21E4+port)^3]:uint8_t(0);
    func_802C4C40_overlay_40c7a0_802c3490(ram,ctx);
    if(host)ram[(0x2D21E4+port)^3]=type;
}
void next_original_controller_type(uint8_t* ram,recomp_context* ctx){
    const bool host=cycle_original_controller_type(ram,1);
    const unsigned port=ram[0x2D21EF^3];
    const auto type=host?ram[(0x2D21E4+port)^3]:uint8_t(0);
    func_802C4D88_overlay_40c7a0_802c3490(ram,ctx);
    if(host)ram[(0x2D21E4+port)^3]=type;
}
void update_original_controller(uint8_t* ram,recomp_context* ctx){
    if(original_controller_screen(ram)){
        ensure_controller_editor();
        auto& editor=football_controller_editor();
        const auto state=editor.snapshot();
        if(state.editing_free){
            const auto input=platform::football_physical_input(state.selected_port);
            editor.input({input.held,input.start,input.cancel,input.up,input.down});
            return; // Only this original screen waits while its Free draft is edited.
        }
    }
    func_802C48F4_overlay_40c7a0_802c3490(ram,ctx);
}
std::string football_control_label(platform::Family family,PhysicalControl control){
    if(unsigned(control)<4)return std::string(platform::face_label(family,unsigned(control)));
    const bool left=control==PhysicalControl::L1||control==PhysicalControl::L2;
    const bool trigger=control==PhysicalControl::L2||control==PhysicalControl::R2;
    if(family==platform::Family::PlayStation)return trigger?(left?"L2":"R2"):(left?"L1":"R1");
    if(family==platform::Family::Nintendo)return trigger?(left?"ZL":"ZR"):(left?"L":"R");
    return trigger?(left?"LT":"RT"):(left?"LB":"RB");
}
void draw_native_football_controller(uint8_t* ram,recomp_context* ctx){
    ensure_controller_editor();
    auto& editor=football_controller_editor();
    auto state=editor.snapshot();
    if(!state.editing_free){editor.select_port(platform::active_input_port());state=editor.snapshot();}
    PalControllerScreenView view;
    view.selected_port=state.selected_port;
    view.free_capture=state.editing_free;
    view.selected_action=state.selected_action;
    for(unsigned port=0;port<4;++port){
        const auto scheme=state.draft[port].scheme;
        view.types[port]=scheme==ControllerScheme::Free?"Free":"Type "+std::to_string(unsigned(scheme)+1);
    }
    const auto& config=state.draft[state.selected_port];
    const auto bindings=config.scheme==ControllerScheme::Free?config.free_bindings:*scheme_bindings(config.scheme);
    constexpr const char* actions[]{"Pass","Shoot","Dash","Lob","Through","One Two","Curve","Cursor"};
    const auto family=platform::prompt(int(state.selected_port),platform::Action::Start).family;
    // Keyboard gameplay retains its existing keys; presets describe gamepads.
    constexpr const char* keyboard_actions[3][8]{
        {"Z","X","L","K","I","J","Left Shift","E"},
        {"Z","J","L","X","I","K","Left Shift","E"},
        {"K","I","Z","J","X","L","Left Shift","E"}};
    const unsigned keyboard_profile=ram[(0x2D21E4+state.selected_port)^3];
    if(keyboard_profile>=3)return;
    for(unsigned action=0;action<8;++action){
        const auto physical=family==platform::Family::Keyboard?std::string(keyboard_actions[keyboard_profile][action]):
            football_control_label(family,bindings[action]);
        view.actions[action]={static_cast<PromptGlyphFamily>(family),physical,actions[action]};
    }
    auto start=family==platform::Family::Keyboard?std::string("Enter"):
        platform::physical_button_label(int(state.selected_port),SDL_CONTROLLER_BUTTON_START);
    if(start=="+")start="Plus";
    const auto accept=platform::prompt(int(state.selected_port),platform::Action::A).name;
    view.start_footer=state.editing_free?"Press "+start+" to confirm":"Left Right select. "+accept+" edits Free";
    if(controller_save_failed)view.start_footer="Save failed. Try again";
    const PalControllerScreenFunctions functions{&track_initialize_sprite,registry.find(0x80007C2C),
        &track_menu_sprite,&track_menu_text};
    draw_pal_controller_screen({ram,0x800000},*ctx,view,functions);
}
void trace_training_begin(uint8_t* ram,recomp_context* ctx){
    trace_pal_load_transition(PalLoadTracePoint::TrainingBegin,ram,ctx,&func_802BE3E4_overlay_401910_802b8500);
}
void trace_controller_ready(uint8_t* ram,recomp_context* ctx){
    trace_pal_load_transition(PalLoadTracePoint::ControllerReady,ram,ctx,&func_802C53A4_overlay_40c7a0_802c3490);
}
void select_original_pc_settings(uint8_t* ram,recomp_context* ctx){
    const auto entry=pal_options_entry({ram,0x800000});
    if(entry&&entry->pc_settings){
        GameSettingsDraft draft;draft.graphics=platform::render_settings();
        const auto preferences=platform::port_preferences();
        for(unsigned port=0;port<4;++port){draft.vibration[port]=preferences[port].vibration;draft.families[port]=preferences[port].manual_family;}
        game_settings_menu().open(platform::active_input_port(),draft);
        return; // Explicitly replace only the retired original Resolution action.
    }
    func_8029F2D8_overlay_3b47e0_8029eea0(ram,ctx);
}
void adapt_physical_title_model(uint8_t* rdram,recomp_context* ctx){
    // The completed original frame is still in its current arena and has not
    // been submitted. Append the original font after every original UI pass.
    const auto bounds=pal_gfx_bounds({rdram,0x800000});
    if(!bounds || registry.find(0x80048660)!=&func_80048660_resident)return;
    const auto physical_start=platform::prompt(0,platform::Action::Start);
    const auto plan=plan_pal_title_prompt({rdram,0x800000},bounds.begin,bounds.cursor,physical_start.name);
    if(!plan)return;
    const auto& prompt=plan->line();
    const std::array<EngineTextLine,1> lines{{{prompt.x,prompt.y,prompt.text}}};
    if(!draw_pal_engine_text({rdram,0x800000},*ctx,lines,registry.find(0x80048660)))return;
    if(!suppress_pal_title_prompt({rdram,0x800000},*plan)){
        runtime_message("The original title control prompt changed during its native font draw.");std::exit(1);
    }
}
PalOptionsSkinFunctions native_options_skin_functions(){
    return {&track_initialize_sprite,registry.find(0x80007C2C),&track_menu_sprite,&track_menu_text};
}
void draw_startup_loading(uint8_t* ram,recomp_context* ctx){
    if(registry.find(0x80048660)!=&func_80048660_resident||!iss2000_pal_storage_loading(ram))return;
    const std::array<EngineTextLine,1> lines{{{124,112,"Loading game",8}}};
    draw_pal_engine_text({ram,0x800000},*ctx,lines,&func_80048660_resident);
}
void draw_main_select_exit(uint8_t* ram,recomp_context* ctx){
    const bool main_select=pal_main_select_active({ram,0x800000});
    const bool main_lifted=lift_pal_main_select({ram,0x800000},platform::render_settings().aspect_ratio==AspectRatio::Wide16x9);
    bool exit_shown=false;
    if(main_select&&main_lifted){
        auto view=main_exit_menu().view();view.available=true;
        const auto physical=platform::main_exit_prompts();
        const auto port=physical.port;
        std::array<PromptGlyphRequest,3> prompts;
        for(unsigned n=0;n<3;++n)prompts[n]={static_cast<PromptGlyphFamily>(physical.prompts[n].family),physical.prompts[n].glyph,port};
        const PalPromptSpriteFunctions functions{&track_initialize_sprite,registry.find(0x80007C2C),&track_menu_sprite,&track_menu_text};
        MenuSpriteSemanticScope semantic(0x4d41494e45584954ull);
        exit_shown=draw_pal_main_exit({ram,0x800000},*ctx,view,prompts,functions);
    }
    main_exit_menu().publish(exit_shown);

}
void draw_original_controller_menu(uint8_t* ram,recomp_context* ctx){
    // 80000BB8 encloses the complete original frame render. All twelve queued
    // UI lists and the intervening direct sprite passes must finish first.
    begin_menu_sprite_frame({ram,0x800000});
    run_original_guest(0x80000BB8,ram,ctx);
    adapt_physical_title_model(ram,ctx);
    draw_startup_loading(ram,ctx);
    draw_main_select_exit(ram,ctx);
    auto& menu=game_controls_menu();
    auto& settings=game_settings_menu();
    const bool original_options=pal_options_entry({ram,0x800000}).has_value();
    const bool controller=original_controller_screen(ram,true);
    if(original_options&&registry.find(0x8004C59C)==&func_8004C59C_resident){
        for(unsigned n=0;n<4;++n){const auto event=settings.pending_sound();if(!event)break;
            const auto result=play_pal_menu_sound({ram,0x800000},*ctx,event->sound,&func_8004C59C_resident);
            if(result==PalMenuAudioResult::Full)break;
            settings.acknowledge_sound(event->sequence);
            if(result==PalMenuAudioResult::Rejected)break;
        }
    }
    if(!controller&&!original_options){football_controller_editor().end();return;}
    if(controller){MenuSpriteSemanticScope semantic(0x50434F4E54524F4Cull);draw_native_football_controller(ram,ctx);return;}
    if(settings.active()&&!menu.active()){
        const auto help=platform::controls_help(settings.port());
        auto view=settings.view(help.prompts[0].name,help.prompts[1].name);
        uint64_t page_id=1469598103934665603ull;for(const unsigned char c:view.title){page_id^=c;page_id*=1099511628211ull;}
        MenuSpriteSemanticScope semantic(page_id);
        // One input snapshot owns both the action and its physical glyph.
        const auto family=static_cast<PromptGlyphFamily>(help.prompts[0].family);
        const bool keyboard=help.prompts[0].family==platform::Family::Keyboard;
        const bool apply=settings.can_apply_shortcut();
        view.shortcuts.push_back({family,apply&&!keyboard?std::string(platform::button_label(help.prompts[0].family,SDL_CONTROLLER_BUTTON_A)):help.prompts[0].glyph,apply?"Change":"Select"});
        if(apply)view.shortcuts.push_back({family,keyboard?"X":std::string(platform::button_label(help.prompts[0].family,SDL_CONTROLLER_BUTTON_X)),"Apply and save"});
        view.shortcuts.push_back({family,apply?(keyboard?"Escape":std::string(platform::button_label(help.prompts[0].family,SDL_CONTROLLER_BUTTON_B))):help.prompts[1].glyph,"Back"});
        std::erase_if(view.help,[](const auto& line){return line!="Save failed. Try again"&&line!="Saving"&&line!="Options saved";});
        draw_pal_options_skin({ram,0x800000},*ctx,view,original_options?PalOptionsSkinOwner::Options:PalOptionsSkinOwner::Controller,
            platform::render_settings().aspect_ratio==AspectRatio::Wide16x9,native_options_skin_functions());
        return;
    }
    if(menu.active()){
        MenuSpriteSemanticScope semantic(0x50434C4547414359ull);
        const auto view=menu.view(platform::controller_family(int(menu.port())));
        draw_pal_options_skin({ram,0x800000},*ctx,view,original_options?PalOptionsSkinOwner::Options:PalOptionsSkinOwner::Controller,
            platform::render_settings().aspect_ratio==AspectRatio::Wide16x9,native_options_skin_functions());
        return;
    }

}
void write_original_save_file(uint8_t* ram,recomp_context* ctx){
    run_pak_file_write(ram,ctx,&func_80060140_resident);
}
void schedule_automatic_storage(uint8_t* ram,recomp_context* ctx){
    iss2000_pal_storage_schedule(ram,ctx,&func_801B3960_overlay_2dee70_801ad820);
}
void draw_ball_with_projected_shadow(uint8_t*ram,recomp_context*ctx){
    const auto root=ctx->r4;
    restore_pal_ball_shadow({ram,0x800000},root);
    func_802A472C_overlay_376010_802a4380(ram,ctx);
    project_pal_shadow({ram,0x800000},root);
    observe_pal_shadow_vertices({ram,0x800000},root);
}
void draw_max_detail_shadows(uint8_t* ram,recomp_context* ctx){
    const auto object=ctx->r4;
    iss2000_pal_max_detail_shadows(ram,ctx);
    project_pal_shadow({ram,0x800000},object);
    observe_pal_shadow_vertices({ram,0x800000},object);
}
void draw_widescreen_sky(uint8_t* ram,recomp_context* ctx){
    PalSkyWriteScope scope({ram,0x800000},platform::render_settings().aspect_ratio==AspectRatio::Wide16x9);
    if(scope)iss2000_pal_wide_sky(ram,ctx);
    else run_original_guest(0x80035CC0,ram,ctx);
}
#endif
void track_matrix_arena(uint8_t* rdram,recomp_context* ctx){
    run_original_guest(guest.arena,rdram,ctx);
#ifdef ISS2000_PAL_ENGLISH
    extend_pal_field_matrix_arena({rdram,0x800000});
#endif
    observe_transform_frame({rdram,0x800000});
    observe_pal_shadow_frame({rdram,0x800000});
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
    observe_pal_shadow_allocation(ctx->r2);
}
void track_child_allocation(uint8_t* rdram,recomp_context* ctx){
    run_original_guest(guest.allocate_child,rdram,ctx);
    observe_transform_allocation(ctx->r2);
    observe_pal_shadow_allocation(ctx->r2);
}
void track_model_release(uint8_t* rdram,recomp_context* ctx){
    observe_transform_release(ctx->r4);
    observe_pal_shadow_release(ctx->r4);
    run_original_guest(guest.release_model,rdram,ctx);
}
void test_wide_far_visibility(uint8_t* rdram,recomp_context* ctx){
    const bool wide=platform::render_settings().aspect_ratio==AspectRatio::Wide16x9;
    if(!ensure_widescreen_far_extents({rdram,0x800000},wide,current_wide_layout(rdram))){
        static std::once_flag warning;
        std::call_once(warning,[]{std::fprintf(stderr,"[Render] Original far-plane extents are outside the reviewed widescreen layout.\n");});
    }
    run_original_guest(guest.far_visibility,rdram,ctx);
}
#ifdef ISS2000_PAL_ENGLISH
void retain_football_player(uint8_t* rdram,recomp_context* ctx){
    const auto object=ctx->r4;
    run_original_guest(0x80023344,rdram,ctx);
    if(ctx->r2!=0 && pal_player_culling_disabled({rdram,0x800000},object))ctx->r2=0;
}
#endif
void update_wide_visibility(uint8_t* rdram,recomp_context* ctx){
    run_original_guest(guest.visibility,rdram,ctx);
    const bool wide=platform::render_settings().aspect_ratio==AspectRatio::Wide16x9;
    if(!apply_widescreen_culling({rdram,0x800000},wide,current_wide_layout(rdram))){
        static std::once_flag warning;
        std::call_once(warning,[]{std::fprintf(stderr,"[Render] Original camera bounds are outside the reviewed widescreen layout.\n");});
    }
}
void update_wide_world_corners(uint8_t* rdram,recomp_context* ctx){
    run_original_guest(guest.world_corners,rdram,ctx);
    const bool wide=platform::render_settings().aspect_ratio==AspectRatio::Wide16x9;
    if(!apply_widescreen_world_corners({rdram,0x800000},wide,current_wide_layout(rdram))){
        static std::once_flag warning;
        std::call_once(warning,[]{std::fprintf(stderr,"[Render] Original camera corner rays are outside the reviewed widescreen layout.\n");});
    }
}
void register_physical_title(uint8_t* rdram,recomp_context* ctx){
    prepare_title_prompt(rdram,ctx->r4,ctx->r5,platform::prompt(0,platform::Action::Start).name);
    run_original_guest(guest.title_prompt,rdram,ctx);
}
void draw_physical_prompt(uint8_t* rdram,recomp_context* ctx){
#ifdef ISS2000_PAL_ENGLISH
    if(registry.find(0x80041B50)==&func_80041B50_resident &&
       draw_pal_team_saved_data({rdram,0x800000},*ctx,&func_80041B50_resident))return;
    if(registry.find(0x8029F2D8)==&func_8029F2D8_overlay_3b47e0_8029eea0 &&
       !game_settings_menu().active()&&!game_controls_menu().active()){
        if(const auto label=pal_options_pc_label({rdram,0x800000},ctx->r4)){
            if(draw_pal_options_skin_label({rdram,0x800000},*ctx,"PC Settings",label->x,label->y,
                label->selected,native_options_skin_functions()))return;
        }
    }
    const unsigned port=physical_prompt_sprite_port(rdram,ctx->r4,platform::active_input_port()).value_or(0);
#else
    const unsigned port=0;
#endif
    const auto help=platform::controls_help(port);
    const std::array<PromptGlyphRequest,2> glyphs{{
        {static_cast<PromptGlyphFamily>(help.prompts[0].family),help.prompts[0].glyph,port},
        {static_cast<PromptGlyphFamily>(help.prompts[1].family),help.prompts[1].glyph,port}}};
#ifdef ISS2000_PAL_ENGLISH
    const std::array<platform::Action,4> actions{platform::Action::CLeft,platform::Action::CRight,
        platform::Action::CUp,platform::Action::CDown};
    std::array<platform::Prompt,4> physical;
    std::array<PromptGlyphRequest,4> directions;
    for(unsigned i=0;i<4;++i){
        physical[i]=platform::prompt(port,actions[i]);
        directions[i]={static_cast<PromptGlyphFamily>(physical[i].family),physical[i].glyph,port};
    }
    const std::array<platform::Action,3> shoulder_actions{
        platform::Action::L,platform::Action::Z,platform::Action::R};
    std::array<platform::Prompt,3> physical_shoulders;
    std::array<PromptGlyphRequest,3> shoulder_glyphs;
    for(unsigned i=0;i<shoulder_glyphs.size();++i){
        physical_shoulders[i]=platform::prompt(port,shoulder_actions[i]);
        shoulder_glyphs[i]={static_cast<PromptGlyphFamily>(physical_shoulders[i].family),physical_shoulders[i].glyph,port};
    }
    auto result=prepare_physical_prompt_sprite(rdram,ctx->r4,glyphs,directions,
        PromptGlyphRequest{static_cast<PromptGlyphFamily>(help.prompts[2].family),help.prompts[2].glyph,port},
        shoulder_glyphs);
    if(result.action==PromptSpriteAction::SetplayControls&&result.status==PromptSpriteStatus::TextFallback&&
       help.prompts[2].family!=platform::Family::Keyboard){
        const auto preferences=platform::port_preferences();const auto& config=preferences[port];
        const auto bindings=config.football_scheme==ControllerScheme::Free?config.free_football_bindings:
            *scheme_bindings(config.football_scheme);
        // Original Z and R are projected as Curve and Cursor by the football
        // normalizer. Set-play help must describe the same applied preset/Free
        // map, while replay and menu prompts retain their raw logical actions.
        const std::array<FootballAction,2> actions{FootballAction::Curve,FootballAction::Cursor};
        for(unsigned n=0;n<actions.size();++n){
            const auto label=football_control_label(help.prompts[2].family,bindings[unsigned(actions[n])]);
            physical_shoulders[n+1]={label,label,help.prompts[2].family};
            shoulder_glyphs[n+1]={static_cast<PromptGlyphFamily>(help.prompts[2].family),physical_shoulders[n+1].glyph,port};
        }
        result=prepare_physical_prompt_sprite(rdram,ctx->r4,glyphs,directions,
            PromptGlyphRequest{static_cast<PromptGlyphFamily>(help.prompts[2].family),help.prompts[2].glyph,port},shoulder_glyphs);
    }
    if(result.status==PromptSpriteStatus::TextFallback){
        if(result.icon_count){
            const PalPromptSpriteFunctions functions{registry.find(0x80008A54),registry.find(0x80007C2C),
                registry.find(0x80041B50),registry.find(0x80048660)};
            if(functions.initialize_sprite!=&func_80008A54_resident ||
               functions.construct_resource!=&func_80007C2C_resident ||
               functions.draw_sprite!=&func_80041B50_resident ||
               functions.draw_text!=&func_80048660_resident ||
               !draw_pal_prompt_sprite({rdram,0x800000},*ctx,result,functions)){
                runtime_message("The original game could not safely draw the physical control glyphs.");std::exit(1);
            }
            return;
        }
        std::array<EngineTextLine,8> lines;
        if(result.line_count==0 || result.line_count>lines.size() ||
           registry.find(0x80048660)!=&func_80048660_resident){
            runtime_message("The original font is unavailable for this remapped control prompt.");std::exit(1);
        }
        for(unsigned i=0;i<result.line_count;++i)
            lines[i]={result.lines[i].x,result.lines[i].y,result.lines[i].text,result.lines[i].height,result.lines[i].palette};
        if(!draw_pal_engine_text({rdram,0x800000},*ctx,{lines.data(),result.line_count},registry.find(0x80048660))){
            runtime_message("The original game could not safely draw the remapped control prompt.");std::exit(1);
        }
        return;
    }
    if(registry.find(0x80041B50)==&func_80041B50_resident&&
       draw_pal_main_ball({rdram,0x800000},*ctx,
           platform::render_settings().aspect_ratio==AspectRatio::Wide16x9,&func_80041B50_resident))return;
    PalHudScope hud({rdram,0x800000},platform::render_settings().aspect_ratio==AspectRatio::Wide16x9,
        PalHudDraw::Sprite,ctx->r4);
    PalBackgroundScope background({rdram,0x800000},
        platform::render_settings().aspect_ratio==AspectRatio::Wide16x9,ctx->r4);
#else
    prepare_prompt_textures(rdram,ctx->r4,glyphs);
#endif
    run_original_guest(guest.button_prompt,rdram,ctx);
}
#ifdef ISS2000_PAL_ENGLISH
void align_training_radar_marker(uint8_t* rdram,recomp_context* ctx){
    uint32_t begin;std::memcpy(&begin,rdram+0x2B4400,sizeof(begin));
    func_802A4DC0_overlay_376010_802a4380(rdram,ctx);
    align_pal_radar_marker({rdram,0x800000},platform::render_settings().aspect_ratio==AspectRatio::Wide16x9,begin);
}
void align_projected_radar_marker(uint8_t* rdram,recomp_context* ctx){
    uint32_t begin;std::memcpy(&begin,rdram+0x2B4400,sizeof(begin));
    func_802A4F78_overlay_376010_802a4380(rdram,ctx);
    align_pal_radar_marker({rdram,0x800000},platform::render_settings().aspect_ratio==AspectRatio::Wide16x9,begin);
}
void draw_widescreen_score_flags(uint8_t* rdram,recomp_context* ctx){
    // The original compositor supplies two stable logical sides. Capture the
    // complete inner output after its balanced HUD scope has finished.
    const uint32_t side=uint32_t(ctx->r5);
    const bool flag_call=uint32_t(ctx->r4)==0x8009E0C8u && side<2;
    uint32_t begin;std::memcpy(&begin,rdram+0x9E0C8,sizeof(begin));
    {
        PalHudScope hud({rdram,0x800000},flag_call && platform::render_settings().aspect_ratio==AspectRatio::Wide16x9,
            PalHudDraw::ScoreFlags);
        run_original_guest(0x8023A510,rdram,ctx);
    }
    if(flag_call){
        uint32_t end;std::memcpy(&end,rdram+0x9E0C8,sizeof(end));
        observe_menu_canvas({rdram,0x800000},0x53434F5245464C00ULL|side,begin,end);
    }
}
// Each original setter still updates its complete hierarchical stage context.
// Same-value resets invalidate IDs as well as numerical scene changes.
template<uint32_t Address> void transition_stage(uint8_t* rdram,recomp_context* ctx){
    run_original_guest(Address,rdram,ctx);
    notify_transform_discontinuity();
    notify_menu_sprite_discontinuity();
    invalidate_pal_shadow_vertices();
}
void begin_recorded_replay(uint8_t* rdram,recomp_context* ctx){
    notify_transform_discontinuity();
    notify_menu_sprite_discontinuity();
    invalidate_pal_shadow_vertices();
    func_801E68F0_overlay_287ab0_801db100(rdram,ctx);
    notify_transform_discontinuity();
    notify_menu_sprite_discontinuity();
    invalidate_pal_shadow_vertices();
}
void leave_recorded_replay(uint8_t* rdram,recomp_context* ctx){
    notify_transform_discontinuity();
    notify_menu_sprite_discontinuity();
    invalidate_pal_shadow_vertices();
    func_801E78F4_overlay_287ab0_801db100(rdram,ctx);
    notify_transform_discontinuity();
    notify_menu_sprite_discontinuity();
    invalidate_pal_shadow_vertices();
}
void correct_recorded_ball_position(uint8_t* rdram,recomp_context* ctx){
    const auto before=observe_transform_position_before({rdram,0x800000},0x2B57D0);
    func_802B718C_overlay_386080_802b57e0(rdram,ctx);
    observe_transform_position_after({rdram,0x800000},before);
}
void place_original_players(uint8_t* rdram,recomp_context* ctx){
    func_802388C8_overlay_4a6820_80230590(rdram,ctx);
    notify_transform_discontinuity();
    notify_menu_sprite_discontinuity();
    invalidate_pal_shadow_vertices();
}
void draw_encoded_physical_prompt(uint8_t* rdram,recomp_context* ctx){
    iss2000_pal_storage_text(rdram,ctx->r4);
    const auto help=platform::controls_help(0);
    prepare_encoded_menu_prompt({rdram,0x800000},ctx->r4,
        {help.prompts[0].name,help.prompts[1].name,help.prompts[2].name});
    PalHudScope hud({rdram,0x800000},platform::render_settings().aspect_ratio==AspectRatio::Wide16x9,
        PalHudDraw::Text,ctx->r4);
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
            submit_menu_sprite_metadata(task.t.type,fingerprint,{rdram,0x800000});
            submit_pal_shadow_metadata({rdram,0x800000},task.t.type,fingerprint);
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
                    [&]{
                        recomp::do_rom_read(rdram,S32(transfer.ram),transfer.physical,transfer.size);
#ifdef ISS2000_PAL_ENGLISH
                        pal_real_names_override().apply({rdram,0x800000},transfer.offset,transfer.ram,transfer.size);
#endif
                    },
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
    if(uint32_t(address)==0x802A472Cu && iss2000::registry.find(uint32_t(address))==&func_802A472C_overlay_376010_802a4380)
        return &iss2000::draw_ball_with_projected_shadow;
    if(uint32_t(address)==0x802A5290u && iss2000::registry.find(uint32_t(address))==&func_802A5290_overlay_376010_802a4380)
        return &iss2000_pal_radar_callback;
    if(uint32_t(address)==0x807AA008u && iss2000::registry.find(uint32_t(address))==&func_807AA008_overlay_515890_807aa000)
        return &iss2000_pal_high_sprite_edges;
    if(uint32_t(address)==0x80000C30u && iss2000::registry.find(uint32_t(address))==&func_80000C30_resident)
        return &iss2000_pal_native_frame_pace;
    if(uint32_t(address)==0x8001D480u && iss2000::registry.find(uint32_t(address))==&func_8001D480_resident)
        return &iss2000_pal_framebuffer_allocator;
    if(uint32_t(address)==0x802A3464u && iss2000::registry.find(uint32_t(address))==&func_802A3464_overlay_3e83d0_8029eea0)
        return &iss2000_pal_formation_save;
    if(uint32_t(address)==0x80008C30u && iss2000::registry.find(uint32_t(address))==&func_80008C30_resident)
        return &iss2000_pal_fixed_high_initializer;
    if(uint32_t(address)==0x8029F2D8u && iss2000::registry.find(uint32_t(address))==&func_8029F2D8_overlay_3b47e0_8029eea0)
        return &iss2000::select_original_pc_settings;
    if(uint32_t(address)==0x801ADD44u && iss2000::registry.find(uint32_t(address))==&func_801ADD44_overlay_2c99e0_801ad820)
        return &iss2000::draw_widescreen_intro_canvas;
    if(uint32_t(address)==0x800019FCu && iss2000::registry.find(uint32_t(address))==&func_800019FC_resident)
        return &iss2000::draw_widescreen_screen_fill;
    if(uint32_t(address)==0x8005CD50u && iss2000::registry.find(uint32_t(address))==&func_8005CD50_resident)
        return &iss2000::clear_original_guest_memory;
    if(uint32_t(address)==0x80060140u && iss2000::registry.find(uint32_t(address))==&func_80060140_resident)
        return &iss2000::write_original_save_file;
    if(uint32_t(address)==0x801B3960u && iss2000::registry.find(uint32_t(address))==&func_801B3960_overlay_2dee70_801ad820)
        return &iss2000::schedule_automatic_storage;
    if(uint32_t(address)==0x802B1CC8u && iss2000::registry.find(uint32_t(address))==&func_802B1CC8_overlay_481680_802b1070)
        return &iss2000_pal_automatic_storage_ui;
    if(uint32_t(address)==0x802B1D84u && iss2000::registry.find(uint32_t(address))==&func_802B1D84_overlay_481680_802b1070)
        return &iss2000_pal_automatic_storage_update;
    if(uint32_t(address)==0x80041A44u && iss2000::registry.find(uint32_t(address))==&func_80041A44_resident)
        return &iss2000_pal_automatic_storage_render;
    if(uint32_t(address)==0x802B1FDCu && iss2000::registry.find(uint32_t(address))==&func_802B1FDC_overlay_481680_802b1070)
        return &iss2000_pal_skip_expansion_notice;
    if(uint32_t(address)==0x802B5574u && iss2000::registry.find(uint32_t(address))==&func_802B5574_overlay_3fc9f0_802b35b0)
        return &iss2000_pal_skip_rumble_802B5574;
    if(uint32_t(address)==0x802BA770u && iss2000::registry.find(uint32_t(address))==&func_802BA770_overlay_401910_802b8500)
        return &iss2000_pal_skip_rumble_802BA770;
    if(uint32_t(address)==0x802BE1B8u && iss2000::registry.find(uint32_t(address))==&func_802BE1B8_overlay_401910_802b8500)
        return &iss2000_pal_skip_rumble_802BE1B8;
    if(uint32_t(address)==0x802C6D34u && iss2000::registry.find(uint32_t(address))==&func_802C6D34_overlay_40c7a0_802c3490)
        return &iss2000_pal_skip_rumble_802C6D34;
    if(uint32_t(address)==0x803D2F34u && iss2000::registry.find(uint32_t(address))==&func_803D2F34_overlay_57f870_803d1a30)
        return &iss2000_pal_skip_rumble_803D2F34;
    if(uint32_t(address)==0x80023344u && iss2000::registry.find(uint32_t(address))==&func_80023344_resident)
        return &iss2000::retain_football_player;
    if(uint32_t(address)==0x800300D0u)return &iss2000_pal_max_detail_models;
    if(uint32_t(address)==0x80037498u)return &iss2000::draw_max_detail_shadows;
    if(uint32_t(address)==0x80035CC0u)return &iss2000::draw_widescreen_sky;
    if(uint32_t(address)==0x80048528u && iss2000::registry.find(uint32_t(address))==&func_80048528_resident)
        return &iss2000::track_initialize_text;
    if(uint32_t(address)==0x80008A54u)return &iss2000::track_initialize_sprite;
    if(uint32_t(address)==0x80000BB8u)return &iss2000::draw_original_controller_menu;
    if(uint32_t(address)==0x802BE3E4u && iss2000::registry.find(uint32_t(address))==&func_802BE3E4_overlay_401910_802b8500)
        return &iss2000::trace_training_begin;
    if(uint32_t(address)==0x802C53A4u && iss2000::registry.find(uint32_t(address))==&func_802C53A4_overlay_40c7a0_802c3490)
        return &iss2000::trace_controller_ready;
    if(uint32_t(address)==0x802C49B8u && iss2000::registry.find(uint32_t(address))==&func_802C49B8_overlay_40c7a0_802c3490)
        return &iss2000::select_original_controller_action;
    if(uint32_t(address)==0x801D5A74u && iss2000::registry.find(uint32_t(address))==&func_801D5A74_overlay_25aaf0_801ad820)
        return &iss2000::process_football_controller;
    if(uint32_t(address)==0x801D5E1Cu && iss2000::registry.find(uint32_t(address))==&func_801D5E1C_overlay_25aaf0_801ad820)
        return &iss2000::process_auxiliary_football_controller;
    if(uint32_t(address)==0x801D4CC0u && iss2000::registry.find(uint32_t(address))==&func_801D4CC0_overlay_25aaf0_801ad820)
        return &iss2000::process_special_football_controller;
    if(uint32_t(address)==0x801D4880u && iss2000::registry.find(uint32_t(address))==&func_801D4880_overlay_25aaf0_801ad820)
        return &iss2000::normalize_football_controller;
    if(uint32_t(address)==0x802C48F4u && iss2000::registry.find(uint32_t(address))==&func_802C48F4_overlay_40c7a0_802c3490)
        return &iss2000::update_original_controller;
    if(uint32_t(address)==0x802C4C40u && iss2000::registry.find(uint32_t(address))==&func_802C4C40_overlay_40c7a0_802c3490)
        return &iss2000::previous_original_controller_type;
    if(uint32_t(address)==0x802C4D88u && iss2000::registry.find(uint32_t(address))==&func_802C4D88_overlay_40c7a0_802c3490)
        return &iss2000::next_original_controller_type;
    if(uint32_t(address)==0x80048660u)return &iss2000::track_menu_text;
    if(uint32_t(address)==0x802A4DC0u && iss2000::registry.find(uint32_t(address))==&func_802A4DC0_overlay_376010_802a4380)
        return &iss2000::align_training_radar_marker;
    if(uint32_t(address)==0x802A4F78u && iss2000::registry.find(uint32_t(address))==&func_802A4F78_overlay_376010_802a4380)
        return &iss2000::align_projected_radar_marker;
    if(uint32_t(address)==0x8023A510u && iss2000::registry.find(uint32_t(address))==&func_8023A510_overlay_4a6820_80230590)
        return &iss2000::draw_widescreen_score_flags;
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
    if(uint32_t(address)==guest.button_prompt){
#ifdef ISS2000_PAL_ENGLISH
        return &iss2000::track_menu_sprite;
#else
        return &iss2000::draw_physical_prompt;
#endif
    }
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
