#include "runtime/stick_response.hpp"
// Original project work: djultra64.
// SDL2 host adapters for the pinned N64ModernRuntime callback interfaces.
#include "platform.hpp"
#ifdef _WIN32
#include <SDL_syswm.h>
#endif
#include "runtime/audio_rsp.hpp"
#include "runtime/test_controller.hpp"
#include "runtime/pak_services.hpp"
#include "runtime/game_settings_menu.hpp"
#include "renderer_settings.hpp"
#include "runtime/input_preferences.hpp"
#include "runtime/settings_persistence.hpp"
#include "runtime/window_mode_sync.hpp"
#include "runtime/fullscreen_shortcut.hpp"
#include "runtime/game_controls_input.hpp"
#include "runtime/main_exit_menu.hpp"
#include "runtime/football_controller_editor.hpp"
#include <librecomp/game.hpp>
#include "runtime/audio_fifo.hpp"
#include <algorithm>
#include <atomic>
#include <cmath>
#include <chrono>
#include <cstdio>
#include <cstring>
#include <mutex>
#include <stdexcept>
#include <vector>

RspExitReason iss2000_audio_ucode(uint8_t*, uint32_t);
namespace iss2000::platform {
namespace {
SDL_Window* game_window{};
WindowModeSync window_mode;
FullscreenShortcut fullscreen_shortcut;
bool fullscreen_error_reported=false;
SDL_AudioDeviceID audio_device{};
bool audio_output_started{};
constexpr uint32_t audio_output_prefill_bytes=4096*2*sizeof(int16_t);
SDL_AudioStream* audio_stream{};
uint32_t source_frequency = 48000;
std::mutex audio_mutex;
AudioFifo audio_fifo;
AudioDmaClock audio_clock;
std::mutex input_mutex;
ControlsMenuInputRouter controls_menu_router;
std::atomic<bool> controls_menu_release{false};
std::atomic<uint8_t*> guest_memory{};
struct Port {
    SDL_GameController* controller{};
    Family detected = Family::Xbox;
    Family manual = Family::Automatic;
    bool keyboard{};
    bool connected{};
    bool rumble_capable{};
    bool rumble{};
    bool vibration=true;
    uint64_t rumble_refresh{};
    uint16_t buttons{};
    float x{}, y{};
    ButtonBindings bindings=PortPreferences{}.bindings;
    ControllerScheme football_scheme=ControllerScheme::Type1;
    FootballBindings free_football_bindings=default_football_bindings;
    FootballPhysicalInput football_physical{};
    FootballSiInput football_si{};
};
std::array<Port,4> ports;
unsigned active_prompt_port{};
constexpr std::array<uint16_t,static_cast<size_t>(Action::Count)> masks {
    0x8000,0x4000,0x1000,0x2000,0x20,0x10,0x8,0x4,0x2,0x1,0x800,0x400,0x200,0x100
};
constexpr std::array<SDL_Scancode,static_cast<size_t>(Action::Count)> keys {
    SDL_SCANCODE_Z,SDL_SCANCODE_X,SDL_SCANCODE_RETURN,SDL_SCANCODE_LSHIFT,SDL_SCANCODE_Q,SDL_SCANCODE_E,
    SDL_SCANCODE_I,SDL_SCANCODE_K,SDL_SCANCODE_J,SDL_SCANCODE_L,SDL_SCANCODE_T,SDL_SCANCODE_G,SDL_SCANCODE_F,SDL_SCANCODE_H
};
void fail(const char* action) { throw std::runtime_error(std::string(action)+": "+SDL_GetError()); }
Family detect(SDL_GameController* controller) {
    switch(SDL_GameControllerGetType(controller)) {
    case SDL_CONTROLLER_TYPE_PS3: case SDL_CONTROLLER_TYPE_PS4: case SDL_CONTROLLER_TYPE_PS5: return Family::PlayStation;
    case SDL_CONTROLLER_TYPE_NINTENDO_SWITCH_PRO: case SDL_CONTROLLER_TYPE_NINTENDO_SWITCH_JOYCON_LEFT:
    case SDL_CONTROLLER_TYPE_NINTENDO_SWITCH_JOYCON_RIGHT: case SDL_CONTROLLER_TYPE_NINTENDO_SWITCH_JOYCON_PAIR: return Family::Nintendo;
    default: return Family::Xbox;
    }
}
void stop_motors() {
    for(auto& p:ports) { p.rumble=false; if(p.controller && p.rumble_capable) SDL_GameControllerRumble(p.controller,0,0,0); }
}
void add_controllers() {
    // The opt-in app-only fixture occupies P1 for deterministic visible tests.
    // Physical-device ordering is unchanged when the fixture is disabled.
    std::vector<int> devices;
    for(int device=0;device<SDL_NumJoysticks();++device)devices.push_back(device);
    const auto fixture=test_controller::device_instance();
    if(fixture>=0)std::stable_sort(devices.begin(),devices.end(),[&](int a,int b){
        return SDL_JoystickGetDeviceInstanceID(a)==fixture && SDL_JoystickGetDeviceInstanceID(b)!=fixture;
    });
    for(int device:devices) {
        if(!SDL_IsGameController(device)) continue;
        auto id=SDL_JoystickGetDeviceInstanceID(device);
        bool known=false;
        for(auto& p:ports) if(p.controller && SDL_JoystickInstanceID(SDL_GameControllerGetJoystick(p.controller))==id) known=true;
        if(known) continue;
        for(auto& p:ports) if(!p.controller) {
            p.controller=SDL_GameControllerOpen(device);
            if(p.controller) { p.detected=detect(p.controller); p.rumble_capable=SDL_GameControllerHasRumble(p.controller); p.keyboard=false; p.connected=true; }
            break;
        }
    }
}
void observe_prompt_input(const SDL_Event& event) {
    if(event.type==SDL_KEYDOWN && !event.key.repeat){
        const auto key=event.key.keysym.scancode;
        const bool action=std::find(keys.begin(),keys.end(),key)!=keys.end()||key==SDL_SCANCODE_Y||key==SDL_SCANCODE_ESCAPE;
        const bool movement=key==SDL_SCANCODE_W || key==SDL_SCANCODE_A || key==SDL_SCANCODE_S || key==SDL_SCANCODE_D ||
            key==SDL_SCANCODE_UP || key==SDL_SCANCODE_DOWN || key==SDL_SCANCODE_LEFT || key==SDL_SCANCODE_RIGHT;
        if(action||movement){ports[0].keyboard=true;active_prompt_port=0;}
    }
    const bool button=event.type==SDL_CONTROLLERBUTTONDOWN && event.cbutton.button<SDL_CONTROLLER_BUTTON_MAX;
    const bool axis=event.type==SDL_CONTROLLERAXISMOTION && event.caxis.axis<SDL_CONTROLLER_AXIS_MAX &&
        (event.caxis.axis>=SDL_CONTROLLER_AXIS_TRIGGERLEFT?event.caxis.value>12000:std::abs(int(event.caxis.value))>12000);
    if(button||axis||event.type==SDL_CONTROLLERDEVICEREMOVED){
        const auto id=button?event.cbutton.which:axis?event.caxis.which:event.cdevice.which;
        for(unsigned port=0;port<ports.size();++port){
            auto& p=ports[port];
            if(!p.controller||SDL_JoystickInstanceID(SDL_GameControllerGetJoystick(p.controller))!=id)continue;
            if(event.type==SDL_CONTROLLERDEVICEREMOVED){if(active_prompt_port==port)active_prompt_port=0;}
            else {p.keyboard=false;active_prompt_port=port;}
        }
    }
}
void sync_window_mode() {
    const bool requested=render_settings().fullscreen;
    const bool actual=(SDL_GetWindowFlags(game_window)&SDL_WINDOW_FULLSCREEN)!=0;
    const auto result=window_mode.update(requested,actual,SDL_GetTicks64(),[](bool fullscreen){
        return SDL_SetWindowFullscreen(game_window,fullscreen?SDL_WINDOW_FULLSCREEN_DESKTOP:0)==0;
    });
    if(result==WindowModeSync::Result::Failed&&!fullscreen_error_reported){
        std::fprintf(stderr,"[Window] Fullscreen request failed: %s\n",SDL_GetError());
        fullscreen_error_reported=true;
    }else if(result==WindowModeSync::Result::Satisfied)fullscreen_error_reported=false;
}
void toggle_fullscreen() {
    auto settings=render_settings();settings.fullscreen=!settings.fullscreen;
    set_render_settings(settings);
    // Preserve other unsaved fields, and keep Cancel from undoing the shortcut.
    // Saving remains an explicit PC Settings action.
    game_settings_menu().sync_fullscreen(settings.fullscreen);
}
FootballPhysicalInput sample_football_physical(const Port& port,const Uint8* keyboard,bool focused) {
    FootballPhysicalInput result;
    if(!focused)return result;
    // Escape is the only Cancel control: East remains an assignable position.
    if(keyboard){
        result.start=keyboard[SDL_SCANCODE_RETURN]!=0;
        result.cancel=keyboard[SDL_SCANCODE_ESCAPE]!=0;
        result.up=keyboard[SDL_SCANCODE_UP]!=0;
        result.down=keyboard[SDL_SCANCODE_DOWN]!=0;
    }
    if(!port.connected||port.keyboard||!port.controller||!SDL_GameControllerGetAttached(port.controller))return result;
    result.gamepad=true;
    constexpr std::array<SDL_GameControllerButton,6> positional_buttons{
        SDL_CONTROLLER_BUTTON_A,SDL_CONTROLLER_BUTTON_B,SDL_CONTROLLER_BUTTON_X,SDL_CONTROLLER_BUTTON_Y,
        SDL_CONTROLLER_BUTTON_LEFTSHOULDER,SDL_CONTROLLER_BUTTON_RIGHTSHOULDER};
    for(unsigned position=0;position<positional_buttons.size();++position)
        if(SDL_GameControllerGetButton(port.controller,positional_buttons[position]))result.held|=uint16_t(1u<<position);
    if(SDL_GameControllerGetAxis(port.controller,SDL_CONTROLLER_AXIS_TRIGGERLEFT)>10000)result.held|=physical_control_mask(PhysicalControl::L2);
    if(SDL_GameControllerGetAxis(port.controller,SDL_CONTROLLER_AXIS_TRIGGERRIGHT)>10000)result.held|=physical_control_mask(PhysicalControl::R2);
    result.start|=SDL_GameControllerGetButton(port.controller,SDL_CONTROLLER_BUTTON_START)!=0;
    result.up|=SDL_GameControllerGetButton(port.controller,SDL_CONTROLLER_BUTTON_DPAD_UP)!=0;
    result.down|=SDL_GameControllerGetButton(port.controller,SDL_CONTROLLER_BUTTON_DPAD_DOWN)!=0;
    return result;
}
void update(void*) {
    // librecomp invokes this on the same main thread that created the SDL window.
    sync_window_mode();
    // Menu snapshots precede input_mutex. Persistence/remap callbacks run after
    // unlocking input and outside the menu mutex.
    auto& controls_menu=game_controls_menu();
    ControlsMenuInputFrame menu_frame;
    auto& settings_menu=game_settings_menu();
    const bool controls_active=controls_menu.active();
    menu_frame.owner_token=controls_active?2:1;
    menu_frame.active=controls_active||settings_menu.active();
    if(controls_active){menu_frame.port=controls_menu.port();menu_frame.capturing=controls_menu.capturing();}
    else if(menu_frame.active)menu_frame.port=settings_menu.port();
    menu_frame.apply_save_enabled=!controls_active&&settings_menu.can_apply_shortcut();
    Family menu_family=Family::Xbox;
    const bool football_free=football_controller_editor().snapshot().editing_free;
    std::unique_lock lock(input_mutex);
    test_controller::pump();
    unsigned fullscreen_toggles=0;
    bool exit_escape=false;
    SDL_Event event;
    while(SDL_PollEvent(&event)) {
        const auto shortcut=fullscreen_shortcut.handle(event);
        if(shortcut.toggle)++fullscreen_toggles;
        if(shortcut.consumed)continue;
        observe_prompt_input(event);
        if(event.type==SDL_QUIT) { stop_motors(); ultramodern::quit(); }
        if(event.type==SDL_WINDOWEVENT && event.window.event==SDL_WINDOWEVENT_FOCUS_LOST) stop_motors();
        if(event.type==SDL_KEYDOWN && !event.key.repeat) {
            const auto key=event.key.keysym.scancode;
            const bool menu_visible=menu_frame.active||controls_menu.active()||settings_menu.active();
            if(key==SDL_SCANCODE_ESCAPE){
                // The original Free screen receives Escape through its physical
                // snapshot; do not also close the game or the old host menu.
                if(main_exit_menu().view().available||main_exit_menu().view().open){exit_escape=true;}
                else if(!football_free){
                    if(menu_visible){menu_frame.escape=true;menu_frame.keyboard_command=ControlsMenuCommand::Cancel;}
                    else if(!controls_menu_release.load()){stop_motors();ultramodern::quit();}
                }
            }
            if(menu_visible){
                switch(key){
                case SDL_SCANCODE_Z:menu_frame.keyboard_command=ControlsMenuCommand::Accept;break;
                case SDL_SCANCODE_X:menu_frame.keyboard_command=menu_frame.apply_save_enabled?ControlsMenuCommand::ApplySave:ControlsMenuCommand::Cancel;break;
                case SDL_SCANCODE_UP:menu_frame.keyboard_command=ControlsMenuCommand::Up;break;
                case SDL_SCANCODE_DOWN:menu_frame.keyboard_command=ControlsMenuCommand::Down;break;
                case SDL_SCANCODE_LEFT:case SDL_SCANCODE_PAGEUP:menu_frame.keyboard_command=ControlsMenuCommand::PreviousPage;break;
                case SDL_SCANCODE_RIGHT:case SDL_SCANCODE_PAGEDOWN:menu_frame.keyboard_command=ControlsMenuCommand::NextPage;break;
                case SDL_SCANCODE_BACKSPACE:case SDL_SCANCODE_DELETE:menu_frame.keyboard_command=ControlsMenuCommand::RestoreDefault;break;
                default:break;
                }
            }

        }
        if(event.type==SDL_CONTROLLERDEVICEADDED) add_controllers();
        if(event.type==SDL_CONTROLLERDEVICEREMOVED) for(auto& p:ports) {
            if(p.controller && SDL_JoystickInstanceID(SDL_GameControllerGetJoystick(p.controller))==event.cdevice.which) {
                SDL_GameControllerRumble(p.controller,0,0,0); SDL_GameControllerClose(p.controller); p.controller=nullptr; p.rumble=false; p.rumble_capable=false;
            }
        }
    }
    int keyboard_count=0;
    const auto* raw_keyboard=SDL_GetKeyboardState(&keyboard_count);
    std::array<Uint8,SDL_NUM_SCANCODES> keyboard_snapshot{};
    keyboard_count=std::clamp(keyboard_count,0,int(keyboard_snapshot.size()));
    std::copy_n(raw_keyboard,keyboard_count,keyboard_snapshot.begin());
    fullscreen_shortcut.filter(keyboard_snapshot.data(),keyboard_count);
    const auto* keyboard=keyboard_snapshot.data();
    for(int k=0;k<keyboard_count;++k)menu_frame.any_input|=keyboard[k]!=0;
    const bool focused=(SDL_GetWindowFlags(game_window)&SDL_WINDOW_INPUT_FOCUS)!=0;
    menu_frame.focused=focused;
    menu_frame.keyboard_active=menu_frame.port==0&&(ports[0].keyboard||!ports[0].controller);
    for(size_t i=0;i<ports.size();++i) {
        auto& p=ports[i]; p.buttons=0; p.x=0; p.y=0; p.connected=p.controller || i==0;
        p.football_physical=sample_football_physical(p,keyboard,focused);
        auto& sample=menu_frame.controllers[i];
        sample.preferences.manual_family=p.manual;sample.preferences.bindings=p.bindings;
        if(p.controller){
            for(unsigned b=0;b<unsigned(SDL_CONTROLLER_BUTTON_MAX);++b)
                if(SDL_GameControllerGetButton(p.controller,SDL_GameControllerButton(b)))sample.held|=uint32_t(1)<<b;
            sample.x=SDL_GameControllerGetAxis(p.controller,SDL_CONTROLLER_AXIS_LEFTX)/32767.f;
            sample.y=-SDL_GameControllerGetAxis(p.controller,SDL_CONTROLLER_AXIS_LEFTY)/32767.f;
            for(int a=0;a<SDL_CONTROLLER_AXIS_MAX;++a){
                const auto v=int(SDL_GameControllerGetAxis(p.controller,SDL_GameControllerAxis(a)));
                menu_frame.any_input|=a>=SDL_CONTROLLER_AXIS_TRIGGERLEFT?v>10000:std::abs(v)>4915;
            }
        }
        menu_frame.any_input|=sample.held!=0;
        if(i==menu_frame.port)menu_family=p.manual==Family::Automatic?p.detected:p.manual;
        if(!focused) {p.rumble=false; continue;}
        if(i==0 && (p.keyboard || !p.controller)) {
            for(size_t a=0;a<keys.size();++a) if(keyboard[keys[a]]) p.buttons|=masks[a];
            p.x=float(keyboard[SDL_SCANCODE_D]||keyboard[SDL_SCANCODE_RIGHT])-float(keyboard[SDL_SCANCODE_A]||keyboard[SDL_SCANCODE_LEFT]);
            p.y=float(keyboard[SDL_SCANCODE_W]||keyboard[SDL_SCANCODE_UP])-float(keyboard[SDL_SCANCODE_S]||keyboard[SDL_SCANCODE_DOWN]);
        } else if(p.controller) {
            for(size_t a=0;a<p.bindings.size();++a) if(p.bindings[a]!=SDL_CONTROLLER_BUTTON_INVALID && SDL_GameControllerGetButton(p.controller,p.bindings[a])) p.buttons|=masks[a];
            auto axis=[&](SDL_GameControllerAxis a){float v=SDL_GameControllerGetAxis(p.controller,a)/32767.f; return std::abs(v)<0.15f?0.f:std::clamp(v,-1.f,1.f);};
            const auto stick=gameplay_stick_response(
                SDL_GameControllerGetAxis(p.controller,SDL_CONTROLLER_AXIS_LEFTX)/32767.f,
                -SDL_GameControllerGetAxis(p.controller,SDL_CONTROLLER_AXIS_LEFTY)/32767.f);
            p.x=stick.x;p.y=stick.y;
            if(axis_fallback(Action::Z,p.bindings[size_t(Action::Z)])&&SDL_GameControllerGetAxis(p.controller,SDL_CONTROLLER_AXIS_TRIGGERLEFT)>10000) p.buttons|=0x2000;
            auto cx=axis(SDL_CONTROLLER_AXIS_RIGHTX), cy=axis(SDL_CONTROLLER_AXIS_RIGHTY);
            if(axis_fallback(Action::CLeft,p.bindings[size_t(Action::CLeft)])&&cx<-.4f)p.buttons|=2;
            if(axis_fallback(Action::CRight,p.bindings[size_t(Action::CRight)])&&cx>.4f)p.buttons|=1;
            if(axis_fallback(Action::CUp,p.bindings[size_t(Action::CUp)])&&cy<-.4f)p.buttons|=8;
            if(axis_fallback(Action::CDown,p.bindings[size_t(Action::CDown)])&&cy>.4f)p.buttons|=4;
        }
        if(!p.vibration||menu_frame.active||controls_menu_release.load())p.rumble=false;
        if(p.controller && p.rumble_capable && SDL_GetTicks64()>=p.rumble_refresh) {
            SDL_GameControllerRumble(p.controller,p.rumble?0xA000:0,p.rumble?0xA000:0,p.rumble?150:0);p.rumble_refresh=SDL_GetTicks64()+50;
        }
    }
    const unsigned exit_port=std::min(active_prompt_port,3u);
    const auto& exit_device=ports[exit_port];
    const bool exit_keyboard=exit_port==0&&(exit_device.keyboard||!exit_device.controller);
    const auto& exit_sample=menu_frame.controllers[exit_port];
    MainExitInput exit_input;
    exit_input.focused=focused;exit_input.any=menu_frame.any_input;
    const uint64_t controller_id=exit_device.controller?uint32_t(SDL_JoystickInstanceID(SDL_GameControllerGetJoystick(exit_device.controller))):0;
    exit_input.device=(controller_id<<8)|(exit_port<<1)|unsigned(exit_keyboard);
    const bool exit_open=main_exit_menu().view().open;
    exit_input.north=exit_keyboard?keyboard[SDL_SCANCODE_Y]!=0:(exit_sample.held&(uint32_t(1)<<SDL_CONTROLLER_BUTTON_Y))!=0;
    exit_input.north|=exit_escape&&!exit_open;
    exit_input.accept=(exit_device.buttons&0x8000)!=0;
    exit_input.cancel=(exit_device.buttons&0x4000)!=0||(exit_escape&&exit_open);
    exit_input.left=exit_device.x<-.5f||(exit_device.buttons&0x200)!=0;
    exit_input.right=exit_device.x>.5f||(exit_device.buttons&0x100)!=0;
    const auto exit_result=main_exit_menu().input(exit_input);
    const auto menu_result=controls_menu_router.route(menu_frame);
    const bool suppress=exit_result.suppress||menu_result.suppress||controls_menu.active()||settings_menu.active();
    controls_menu_release.store(suppress,std::memory_order_release);
    if(suppress){for(auto& p:ports){p.buttons=0;p.x=0;p.y=0;}stop_motors();}
    std::array<bool,4> connected{};
    for(size_t i=0;i<ports.size();++i)connected[i]=ports[i].connected;
    if(exit_result.quit){stop_motors();ultramodern::quit();}
    lock.unlock();
    if(fullscreen_toggles&1u)toggle_fullscreen();
    for(unsigned i=0;i<connected.size();++i)set_pak_port_connected(i,connected[i]);
    if(menu_frame.active&&menu_result.deliver&&controls_active){
        controls_menu.update(menu_result.command,menu_result.held,menu_result.keyboard_navigation?Family::Keyboard:menu_family,
            [](unsigned selected,const PortPreferences& draft){
                // Fresh snapshot preserves edits to every other port. Persist before apply.
                auto preferences=capture_input_preferences();preferences.ports.at(selected)=draft;
                save_input_preferences(recomp::get_config_path(),preferences);apply_input_preferences(preferences);return true;
            });
    }
    if(menu_frame.active&&menu_result.deliver&&!controls_active){
        settings_menu.command(menu_result.command,
            [](const GameSettingsDraft& draft){
                auto preferences=capture_input_preferences();
                for(unsigned port=0;port<4;++port){
                    preferences.ports[port].vibration=draft.vibration[port];
                    preferences.ports[port].manual_family=draft.families[port];
                }
                save_game_preferences(recomp::get_config_path(),draft.graphics,preferences);
                apply_input_preferences(preferences);
                set_render_settings(draft.graphics);return true;
            },
            [](unsigned selected){const auto preferences=port_preferences();return game_controls_menu().open(selected,preferences.at(selected));});
    }
}
void poll() {} // Main-thread SDL event loop maintains snapshots for the guest threads.
bool get_input(int n,uint16_t* buttons,float* x,float* y) {
    const bool menu_active=game_controls_menu().active()||game_settings_menu().active()||main_exit_menu().view().open;
    if(menu_active)controls_menu_release.store(true,std::memory_order_release);
    std::lock_guard lock(input_mutex);if(n<0||n>=4)return false;
    auto& port=ports[n];
    // Recheck the atomic flag: the guest may open the menu after our first read.
    const bool suppressed=menu_active||game_controls_menu().active()||game_settings_menu().active()||main_exit_menu().view().open||controls_menu_release.load(std::memory_order_acquire);
    const bool gamepad=port.connected&&!port.keyboard&&port.football_physical.gamepad&&!suppressed;
    const uint16_t held=gamepad?port.football_physical.held:0;
    const uint16_t pressed=uint16_t(held&~port.football_si.held);
    port.football_si={held,pressed,port.football_si.sequence+1,gamepad};
    // Bounded route diagnostics for the user-owned manual controller check.
    // Record mode changes, never individual button presses or keyboard contents.
    static std::array<unsigned,4> previous_route{~0u,~0u,~0u,~0u},route_lines{};
    const auto scheme=unsigned(port.football_scheme);
    const unsigned route=unsigned(port.connected)|unsigned(port.keyboard)<<1|
        unsigned(port.football_physical.gamepad)<<2|unsigned(suppressed)<<3|scheme<<4;
    if(previous_route[n]!=route&&route_lines[n]<12){
        previous_route[n]=route;++route_lines[n];
        constexpr const char* names[]{"Type1","Type2","Type3","Type4","Type5","Free"};
        const auto* device_name=port.controller?SDL_GameControllerName(port.controller):"Keyboard";
        std::fprintf(stderr,"[Controls] SI port=%d scheme=%s device=%s connected=%u keyboard=%u physical_gamepad=%u suppressed=%u gamepad=%u sequence=%llu\n",
            n+1,scheme<std::size(names)?names[scheme]:"Invalid",device_name?device_name:"Unknown",
            unsigned(port.connected),unsigned(port.keyboard),unsigned(port.football_physical.gamepad),
            unsigned(suppressed),unsigned(gamepad),static_cast<unsigned long long>(port.football_si.sequence));
        std::fflush(stderr);
    }
    if(!port.connected)return false;
    if(suppressed){*buttons=0;*x=0;*y=0;return true;}
    *buttons=port.buttons;*x=port.x;*y=port.y;return true;
}
void rumble(int n,bool enabled) {
    const bool suppress=game_controls_menu().active()||game_settings_menu().active()||controls_menu_release.load();
    std::lock_guard lock(input_mutex);if(n>=0&&n<4)ports[n].rumble=enabled&&ports[n].vibration&&!suppress;
}
ultramodern::input::connected_device_info_t device(int n) {
    bool connected=false,capable=false;
    {std::lock_guard lock(input_mutex);
    if(n>=0&&n<4){connected=ports[n].connected;capable=ports[n].rumble_capable;}}
    if(!connected)return {ultramodern::input::Device::None,ultramodern::input::Pak::None};
    return {ultramodern::input::Device::Controller,capable?ultramodern::input::Pak::RumblePak:ultramodern::input::Pak::None};
}
uint64_t audio_now_ns() {
    return uint64_t(std::chrono::duration_cast<std::chrono::nanoseconds>(
        std::chrono::steady_clock::now().time_since_epoch()).count());
}
void sync_audio_locked() {
    audio_clock.advance(audio_now_ns(),source_frequency,audio_fifo);
}
void frequency(uint32_t hz) {
    if(hz<4000||hz>192000) throw std::runtime_error("Guest requested unsupported audio frequency");
    std::lock_guard lock(audio_mutex);
    if(source_frequency==hz && audio_stream) return;
    sync_audio_locked();
    if(audio_fifo.status())throw std::runtime_error("Audio frequency change while a DMA is active requires a converter transition");
    if(audio_stream) SDL_FreeAudioStream(audio_stream);
    audio_clock=AudioDmaClock{};
    audio_stream=SDL_NewAudioStream(AUDIO_S16SYS,2,hz,AUDIO_S16SYS,2,48000);
    if(!audio_stream) fail("Create audio converter"); source_frequency=hz;
}
void queue_samples_locked(int16_t* data,size_t count) {
    std::vector<int16_t> samples(count);
    // RDRAM is stored in swapped 32-bit words; restore left/right 16-bit sample order.
    for(size_t i=0;i<count;i+=2) {samples[i]=data[i+1]; samples[i+1]=data[i];}
    if(SDL_AudioStreamPut(audio_stream,samples.data(),int(samples.size()*2))<0) fail("Convert guest audio");
    int available=SDL_AudioStreamAvailable(audio_stream);
    if(available<0)fail("Measure converted audio");
    if(available>0) {
        std::vector<uint8_t> output(available);
        int got=SDL_AudioStreamGet(audio_stream,output.data(),available);
        if(got<0)fail("Read converted audio");
        if(SDL_QueueAudio(audio_device,output.data(),got)<0)fail("Queue audio");
        // Prime with real PCM once per device lifetime. Four 1024-frame pulls
        // absorb PAL producer jitter without changing the independent AI clock.
        if(!audio_output_started && SDL_GetQueuedAudioSize(audio_device)>=audio_output_prefill_bytes) {
            SDL_PauseAudioDevice(audio_device,0);
            audio_output_started=true;
        }
    }
}
void queue_samples(int16_t* data,size_t count) {
    if(count%4 || count>131072)throw std::runtime_error("Invalid guest AI DMA sample count");
    std::lock_guard lock(audio_mutex);
    sync_audio_locked();
    if(!audio_fifo.submit(uint32_t(count*2)))throw std::runtime_error("AI callback bypassed DMA FIFO backpressure");
    if(count)queue_samples_locked(data,count);
}
size_t remaining() {
    std::lock_guard lock(audio_mutex);
    sync_audio_locked();
    return audio_fifo.length()/4;
}
}
FootballPhysicalInput football_physical_input(unsigned port) {
    std::lock_guard lock(input_mutex);
    return port<ports.size()?ports[port].football_physical:FootballPhysicalInput{};
}
FootballSiInput football_si_input(unsigned port) {
    std::lock_guard lock(input_mutex);
    return port<ports.size()?ports[port].football_si:FootballSiInput{};
}
int submit_audio(uint8_t* rdram,uint32_t address,uint32_t bytes) {
    // Reject malformed submissions before touching guest memory or allocating PCM.
    if(!rdram || !valid_audio_buffer(address,bytes))return -1;
    std::lock_guard lock(audio_mutex);
    sync_audio_locked();
    if(!audio_fifo.submit(bytes))return -1;
    if(bytes)queue_samples_locked(reinterpret_cast<int16_t*>(rdram+(address&0x1FFFFFFFu)),bytes/2);
    return 0;
}
uint32_t audio_length() {
    std::lock_guard lock(audio_mutex);sync_audio_locked();return audio_fifo.length();
}
uint32_t audio_status() {
    std::lock_guard lock(audio_mutex);sync_audio_locked();return audio_fifo.status();
}
void initialize() {
    SDL_SetMainReady();
    SDL_SetHint(SDL_HINT_GAMECONTROLLER_USE_BUTTON_LABELS,"0");
    if(SDL_Init(SDL_INIT_VIDEO|SDL_INIT_AUDIO|SDL_INIT_GAMECONTROLLER|SDL_INIT_HAPTIC))fail("Initialize SDL");
    game_window=SDL_CreateWindow("ISS2000 | djultra64",SDL_WINDOWPOS_CENTERED,SDL_WINDOWPOS_CENTERED,1280,720,SDL_WINDOW_VULKAN|SDL_WINDOW_RESIZABLE|SDL_WINDOW_ALLOW_HIGHDPI);
    if(!game_window)fail("Create game window");
    window_mode=WindowModeSync{};fullscreen_shortcut=FullscreenShortcut{};fullscreen_error_reported=false;
    SDL_AudioSpec desired{}; desired.freq=48000;desired.format=AUDIO_S16SYS;desired.channels=2;desired.samples=1024;
    audio_device=SDL_OpenAudioDevice(nullptr,0,&desired,nullptr,0);
    if(!audio_device)fail("Open audio output");
    audio_output_started=false;
    frequency(48000); // SDL opens paused; queue_samples_locked starts after priming.
    for(auto& port:ports){port.football_physical={};port.football_si={};}
    active_prompt_port=0;ports[0].connected=true;ports[0].keyboard=true;test_controller::initialize();add_controllers();
    SDL_ShowWindow(game_window); SDL_RaiseWindow(game_window);
}
SDL_Window* window(){return game_window;}
ultramodern::renderer::WindowHandle render_window(){
    if(!game_window)throw std::runtime_error("Game window is not initialized");
#ifdef _WIN32
    SDL_SysWMinfo native{};
    SDL_VERSION(&native.version);
    if(SDL_GetWindowWMInfo(game_window,&native)!=SDL_TRUE)fail("Get native game window");
    if(native.subsystem!=SDL_SYSWM_WINDOWS || !native.info.win.window)
        throw std::runtime_error("SDL did not provide a native Windows game window");
    const DWORD owner=GetWindowThreadProcessId(native.info.win.window,nullptr);
    if(!owner)throw std::runtime_error("Native game window has no owning thread");
    return {native.info.win.window,owner};
#else
    return game_window;
#endif
}
void shutdown(){
    {std::lock_guard lock(input_mutex);active_prompt_port=0;stop_motors();for(auto& p:ports){p.football_physical={};p.football_si={};if(p.controller){SDL_GameControllerClose(p.controller);p.controller=nullptr;}}}
    {std::lock_guard lock(audio_mutex);if(audio_stream)SDL_FreeAudioStream(audio_stream);audio_stream=nullptr;if(audio_device)SDL_CloseAudioDevice(audio_device);audio_device=0;audio_output_started=false;audio_fifo=AudioFifo{};audio_clock=AudioDmaClock{};source_frequency=48000;}
    test_controller::shutdown();
    if(game_window)SDL_DestroyWindow(game_window);game_window=nullptr;window_mode=WindowModeSync{};fullscreen_shortcut=FullscreenShortcut{};fullscreen_error_reported=false;SDL_Quit();
}
void set_rdram(uint8_t* rdram){guest_memory.store(rdram);}
RspUcodeFunc* rsp_microcode(const OSTask* task){
    auto* rdram=guest_memory.load();
    if(rdram && matches_audio_rsp({rdram,0x800000},task->t.type,uint32_t(task->t.ucode)))
        return &iss2000_audio_ucode;
    std::fprintf(stderr,"Unknown RSP task: type=%u ucode=0x%08X data=0x%08X code_size=0x%X data_size=0x%X\n",task->t.type,task->t.ucode,task->t.ucode_data,task->t.ucode_size,task->t.ucode_data_size);
    return nullptr;
}
ultramodern::audio_callbacks_t audio_callbacks(){return {queue_samples,remaining,frequency};}
ultramodern::input::callbacks_t input_callbacks(){return {poll,get_input,rumble,device};}
ultramodern::gfx_callbacks_t gfx_callbacks(){return {nullptr,nullptr,update};}
void set_family(int n,Family family){
    if(n<0||n>=4||unsigned(family)>unsigned(Family::Nintendo))throw std::out_of_range("Controller family");
    std::lock_guard lock(input_mutex);ports[n].manual=family;
}
void bind_button(int n,Action action,SDL_GameControllerButton button){
    if(n<0||n>=4||unsigned(action)>=unsigned(Action::Count)||int(button)<-1||button>=SDL_CONTROLLER_BUTTON_MAX)throw std::out_of_range("Controller action");
    std::lock_guard lock(input_mutex);ports[n].bindings[size_t(action)]=button;
}
SDL_GameControllerButton get_binding(int n,Action action){
    if(n<0||n>=4||unsigned(action)>=unsigned(Action::Count))throw std::out_of_range("Controller action");
    std::lock_guard lock(input_mutex);return ports[n].bindings[size_t(action)];
}
Family controller_family(int n){
    if(n<0||n>=4)throw std::out_of_range("Controller port");
    std::lock_guard lock(input_mutex);return ports[n].manual==Family::Automatic?ports[n].detected:ports[n].manual;
}
std::string physical_button_label(int n,SDL_GameControllerButton button){
    if(n<0||n>=4||int(button)<-1||button>=SDL_CONTROLLER_BUTTON_MAX)throw std::out_of_range("Controller button");
    std::lock_guard lock(input_mutex);const auto& port=ports[n];
    auto family=port.manual==Family::Automatic?port.detected:port.manual;
    if(button==SDL_CONTROLLER_BUTTON_START&&family==Family::PlayStation&&port.controller&&SDL_GameControllerGetType(port.controller)==SDL_CONTROLLER_TYPE_PS3)return "Start";
    return std::string(button_label(family,button));
}
std::array<PortPreferences,4> port_preferences(){
    std::lock_guard lock(input_mutex);std::array<PortPreferences,4> result;
    for(unsigned i=0;i<4;++i){result[i].manual_family=ports[i].manual;result[i].bindings=ports[i].bindings;result[i].vibration=ports[i].vibration;result[i].football_scheme=ports[i].football_scheme;result[i].free_football_bindings=ports[i].free_football_bindings;}
    return result;
}
void apply_port_preferences(const std::array<PortPreferences,4>& preferences){
    for(const auto& preference:preferences){
        if(unsigned(preference.manual_family)>unsigned(Family::Nintendo))throw std::invalid_argument("Invalid controller family");
        if(unsigned(preference.football_scheme)>unsigned(ControllerScheme::Free)||!valid_football_bindings(preference.free_football_bindings))
            throw std::invalid_argument("Invalid football controller preferences");
        for(auto button:preference.bindings)if(int(button)<-1||button>=SDL_CONTROLLER_BUTTON_MAX)throw std::invalid_argument("Invalid controller button");
    }
    std::lock_guard lock(input_mutex);
    for(unsigned i=0;i<4;++i){ports[i].manual=preferences[i].manual_family;ports[i].bindings=preferences[i].bindings;ports[i].vibration=preferences[i].vibration;ports[i].football_scheme=preferences[i].football_scheme;ports[i].free_football_bindings=preferences[i].free_football_bindings;if(!ports[i].vibration&&ports[i].controller&&ports[i].rumble_capable){ports[i].rumble=false;SDL_GameControllerRumble(ports[i].controller,0,0,0);}}
}
namespace {
Prompt prompt_locked(const Port& p,Action action){
    auto family=(p.keyboard||!p.controller)?Family::Keyboard:(p.manual==Family::Automatic?p.detected:p.manual);
    if(family==Family::Keyboard){auto name=SDL_GetScancodeName(keys[size_t(action)]);return {name,name,family};}
    auto b=p.bindings[size_t(action)];
    if(b>=SDL_CONTROLLER_BUTTON_A&&b<=SDL_CONTROLLER_BUTTON_Y){
        const char* glyph[]={"×","○","□","△"};
        auto name=std::string(face_label(family,unsigned(b)));
        return {name,family==Family::PlayStation?glyph[b]:name,family};
    }
    if(b==SDL_CONTROLLER_BUTTON_START){
        auto name=family==Family::Nintendo?"+":family==Family::PlayStation?"Options":"Menu";
        if(family==Family::PlayStation && p.controller && SDL_GameControllerGetType(p.controller)==SDL_CONTROLLER_TYPE_PS3)name="Start";
        return {name,name,family};
    }
    if(b==SDL_CONTROLLER_BUTTON_INVALID){
        if(action==Action::Z)return {family==Family::PlayStation?"L2":family==Family::Nintendo?"ZL":"Left trigger",family==Family::PlayStation?"L2":family==Family::Nintendo?"ZL":"LT",family};
        if(action==Action::CLeft)return {"Right stick left","R←",family};
        if(action==Action::CRight)return {"Right stick right","R→",family};
        if(action==Action::CUp)return {"Right stick up","R↑",family};
        if(action==Action::CDown)return {"Right stick down","R↓",family};
    }
    auto label=std::string(button_label(family,b));
    const char* glyph=b==SDL_CONTROLLER_BUTTON_DPAD_UP?"D↑":b==SDL_CONTROLLER_BUTTON_DPAD_DOWN?"D↓":b==SDL_CONTROLLER_BUTTON_DPAD_LEFT?"D←":b==SDL_CONTROLLER_BUTTON_DPAD_RIGHT?"D→":nullptr;
    return {label,glyph?glyph:label,family};
}
}
unsigned active_input_port(){
    std::lock_guard lock(input_mutex);
    if(active_prompt_port>=ports.size())return 0;
    const auto controller=ports[active_prompt_port].controller;
    if(active_prompt_port&&(!controller||!SDL_GameControllerGetAttached(controller)))return 0;
    return active_prompt_port;
}
Prompt prompt(int n,Action action){
    if(n<0||n>=4||unsigned(action)>=unsigned(Action::Count))throw std::out_of_range("Controller prompt");
    std::lock_guard lock(input_mutex);
    return prompt_locked(ports[n],action);
}
MainExitPrompts main_exit_prompts(){
    std::lock_guard lock(input_mutex);const auto port=std::min(active_prompt_port,3u);const auto& p=ports[port];
    auto accept=prompt_locked(p,Action::A),cancel=prompt_locked(p,Action::B);
    const auto north=accept.family==Family::Keyboard?std::string("Y"):std::string(button_label(accept.family,SDL_CONTROLLER_BUTTON_Y));
    return {{{{north,north,accept.family},std::move(accept),std::move(cancel)}},port};
}
ControlsHelp controls_help(int n){
    if(n<0||n>=4)throw std::out_of_range("Controller port");
    std::lock_guard lock(input_mutex);
    const auto& p=ports[n];
    return {{{prompt_locked(p,Action::A),prompt_locked(p,Action::B),prompt_locked(p,Action::Start)}},p.manual};
}
}
