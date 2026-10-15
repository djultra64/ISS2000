// Original project work: djultra64.
// SDL2 host adapters for the pinned N64ModernRuntime callback interfaces.
#include "platform.hpp"
#ifdef _WIN32
#include <SDL_syswm.h>
#endif
#include "runtime/audio_rsp.hpp"
#include "runtime/test_controller.hpp"
#include "runtime/pak_services.hpp"
#include "runtime/settings_dialog.hpp"
#include "runtime/input_preferences.hpp"
#include <librecomp/game.hpp>
#include "runtime/audio_fifo.hpp"
#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <mutex>
#include <stdexcept>
#include <vector>

RspExitReason iss2000_audio_ucode(uint8_t*, uint32_t);
namespace iss2000::platform {
namespace {
SDL_Window* game_window{};
SDL_AudioDeviceID audio_device{};
SDL_AudioStream* audio_stream{};
uint32_t source_frequency = 48000;
std::mutex audio_mutex;
AudioFifo audio_fifo;
AudioFrameClock audio_clock;
uint64_t output_frames_emitted{};
uint64_t output_frames_consumed{};
std::mutex input_mutex;
std::atomic<uint8_t*> guest_memory{};
struct Port {
    SDL_GameController* controller{};
    Family detected = Family::Xbox;
    Family manual = Family::Automatic;
    bool keyboard{};
    bool connected{};
    bool rumble_capable{};
    bool rumble{};
    uint64_t rumble_refresh{};
    uint16_t buttons{};
    float x{}, y{};
    ButtonBindings bindings=PortPreferences{}.bindings;
};
std::array<Port,4> ports;
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
void update(void*) {
    bool settings_requested=false;
    bool preferences_changed=false;
    Family previous_family=Family::Automatic;
    std::array<PakAccessory,4> accessories;
    for(int port=0;port<4;++port)accessories[size_t(port)]=pak_accessory(port);
    std::unique_lock lock(input_mutex);
    test_controller::pump();
    SDL_Event event;
    while(SDL_PollEvent(&event)) {
        if(event.type==SDL_QUIT) { stop_motors(); ultramodern::quit(); }
        if(event.type==SDL_WINDOWEVENT && event.window.event==SDL_WINDOWEVENT_FOCUS_LOST) stop_motors();
        if(event.type==SDL_KEYDOWN && !event.key.repeat) {
            if(event.key.keysym.scancode==SDL_SCANCODE_ESCAPE) { stop_motors(); ultramodern::quit(); }
            if(event.key.keysym.scancode==SDL_SCANCODE_F7)settings_requested=true;
            if(event.key.keysym.scancode==SDL_SCANCODE_F6) {
                if(!preferences_changed)previous_family=ports[0].manual;
                preferences_changed=true;
                ports[0].manual=static_cast<Family>((static_cast<int>(ports[0].manual)+1)%4);
                std::fprintf(stderr,"Controller prompt family override: %d (F6 cycles automatic/Xbox/PlayStation/Nintendo)\n",int(ports[0].manual));
            }
            for(auto key:keys) if(event.key.keysym.scancode==key) ports[0].keyboard=true;
            if(event.key.keysym.scancode==SDL_SCANCODE_W || event.key.keysym.scancode==SDL_SCANCODE_A || event.key.keysym.scancode==SDL_SCANCODE_S || event.key.keysym.scancode==SDL_SCANCODE_D || event.key.keysym.scancode==SDL_SCANCODE_UP || event.key.keysym.scancode==SDL_SCANCODE_DOWN || event.key.keysym.scancode==SDL_SCANCODE_LEFT || event.key.keysym.scancode==SDL_SCANCODE_RIGHT) ports[0].keyboard=true;
        }
        if(event.type==SDL_CONTROLLERDEVICEADDED) add_controllers();
        if(event.type==SDL_CONTROLLERDEVICEREMOVED) for(auto& p:ports) {
            if(p.controller && SDL_JoystickInstanceID(SDL_GameControllerGetJoystick(p.controller))==event.cdevice.which) {
                SDL_GameControllerRumble(p.controller,0,0,0); SDL_GameControllerClose(p.controller); p.controller=nullptr; p.rumble=false; p.rumble_capable=false;
            }
        }
        if(event.type==SDL_CONTROLLERBUTTONDOWN || (event.type==SDL_CONTROLLERAXISMOTION && std::abs(int(event.caxis.value))>12000)) {
            const auto id=event.type==SDL_CONTROLLERBUTTONDOWN?event.cbutton.which:event.caxis.which;
            for(auto& p:ports) if(p.controller && SDL_JoystickInstanceID(SDL_GameControllerGetJoystick(p.controller))==id) p.keyboard=false;
        }
    }
    const auto* keyboard=SDL_GetKeyboardState(nullptr);
    const bool focused=(SDL_GetWindowFlags(game_window)&SDL_WINDOW_INPUT_FOCUS)!=0;
    for(size_t i=0;i<ports.size();++i) {
        auto& p=ports[i]; p.buttons=0; p.x=0; p.y=0; p.connected=p.controller || i==0;
        if(!focused) {p.rumble=false; continue;}
        if(i==0 && (p.keyboard || !p.controller)) {
            for(size_t a=0;a<keys.size();++a) if(keyboard[keys[a]]) p.buttons|=masks[a];
            p.x=float(keyboard[SDL_SCANCODE_D]||keyboard[SDL_SCANCODE_RIGHT])-float(keyboard[SDL_SCANCODE_A]||keyboard[SDL_SCANCODE_LEFT]);
            p.y=float(keyboard[SDL_SCANCODE_W]||keyboard[SDL_SCANCODE_UP])-float(keyboard[SDL_SCANCODE_S]||keyboard[SDL_SCANCODE_DOWN]);
        } else if(p.controller) {
            for(size_t a=0;a<p.bindings.size();++a) if(p.bindings[a]!=SDL_CONTROLLER_BUTTON_INVALID && SDL_GameControllerGetButton(p.controller,p.bindings[a])) p.buttons|=masks[a];
            auto axis=[&](SDL_GameControllerAxis a){float v=SDL_GameControllerGetAxis(p.controller,a)/32767.f; return std::abs(v)<0.15f?0.f:std::clamp(v,-1.f,1.f);};
            p.x=axis(SDL_CONTROLLER_AXIS_LEFTX); p.y=-axis(SDL_CONTROLLER_AXIS_LEFTY);
            if(axis_fallback(Action::Z,p.bindings[size_t(Action::Z)])&&SDL_GameControllerGetAxis(p.controller,SDL_CONTROLLER_AXIS_TRIGGERLEFT)>10000) p.buttons|=0x2000;
            auto cx=axis(SDL_CONTROLLER_AXIS_RIGHTX), cy=axis(SDL_CONTROLLER_AXIS_RIGHTY);
            if(axis_fallback(Action::CLeft,p.bindings[size_t(Action::CLeft)])&&cx<-.4f)p.buttons|=2;
            if(axis_fallback(Action::CRight,p.bindings[size_t(Action::CRight)])&&cx>.4f)p.buttons|=1;
            if(axis_fallback(Action::CUp,p.bindings[size_t(Action::CUp)])&&cy<-.4f)p.buttons|=8;
            if(axis_fallback(Action::CDown,p.bindings[size_t(Action::CDown)])&&cy>.4f)p.buttons|=4;
        }
        if(accessories[i]!=PakAccessory::Rumble)p.rumble=false;
        if(p.controller && p.rumble_capable && SDL_GetTicks64()>=p.rumble_refresh) {
            SDL_GameControllerRumble(p.controller,p.rumble?0xA000:0,p.rumble?0xA000:0,p.rumble?150:0);p.rumble_refresh=SDL_GetTicks64()+50;
        }
    }
    std::array<bool,4> connected{};
    for(size_t i=0;i<ports.size();++i)connected[i]=ports[i].connected;
    if(settings_requested){for(auto& p:ports){p.buttons=0;p.x=0;p.y=0;}stop_motors();}
    lock.unlock();
    for(unsigned i=0;i<connected.size();++i)set_pak_port_connected(i,connected[i]);
    if(preferences_changed){
        try{save_input_preferences(recomp::get_config_path(),capture_input_preferences());}
        catch(const std::exception& error){set_family(0,previous_family);SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_ERROR,"Controller preferences",error.what(),game_window);}
    }
    if(settings_requested)show_settings_dialog(game_window,recomp::get_config_path());
}
void poll() {} // Main-thread SDL event loop maintains snapshots for the guest threads.
bool get_input(int n,uint16_t* buttons,float* x,float* y) {
    std::lock_guard lock(input_mutex); if(n<0||n>=4||!ports[n].connected)return false;
    *buttons=ports[n].buttons; *x=ports[n].x; *y=ports[n].y; return true;
}
void rumble(int n,bool enabled) { std::lock_guard lock(input_mutex); if(n>=0&&n<4)ports[n].rumble=enabled; }
ultramodern::input::connected_device_info_t device(int n) {
    bool connected=false,capable=false;
    {std::lock_guard lock(input_mutex);
    if(n>=0&&n<4){connected=ports[n].connected;capable=ports[n].rumble_capable;}}
    if(!connected)return {ultramodern::input::Device::None,ultramodern::input::Pak::None};
    const auto choice=pak_accessory(n);
    return {ultramodern::input::Device::Controller,capable && choice==PakAccessory::Rumble?ultramodern::input::Pak::RumblePak:ultramodern::input::Pak::None};
}
void sync_audio_locked() {
    uint64_t queued=SDL_GetQueuedAudioSize(audio_device)/4;
    uint64_t consumed=output_frames_emitted>=queued?output_frames_emitted-queued:0;
    if(consumed>output_frames_consumed) {
        audio_fifo.consume(audio_clock.consume(consumed-output_frames_consumed,source_frequency));
        output_frames_consumed=consumed;
    }
}
void frequency(uint32_t hz) {
    if(hz<4000||hz>192000) throw std::runtime_error("Guest requested unsupported audio frequency");
    std::lock_guard lock(audio_mutex);
    if(source_frequency==hz && audio_stream) return;
    sync_audio_locked();
    if(audio_fifo.status())throw std::runtime_error("Audio frequency change while a DMA is active requires a converter transition");
    if(audio_stream) SDL_FreeAudioStream(audio_stream);
    audio_clock=AudioFrameClock{};
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
        output_frames_emitted+=uint64_t(got)/4;
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
    SDL_AudioSpec desired{}; desired.freq=48000;desired.format=AUDIO_S16SYS;desired.channels=2;desired.samples=1024;
    audio_device=SDL_OpenAudioDevice(nullptr,0,&desired,nullptr,0);
    if(!audio_device)fail("Open audio output");
    frequency(48000); SDL_PauseAudioDevice(audio_device,0);
    ports[0].connected=true;ports[0].keyboard=true;test_controller::initialize();add_controllers();
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
    {std::lock_guard lock(input_mutex);stop_motors();for(auto& p:ports)if(p.controller){SDL_GameControllerClose(p.controller);p.controller=nullptr;}}
    {std::lock_guard lock(audio_mutex);if(audio_stream)SDL_FreeAudioStream(audio_stream);audio_stream=nullptr;if(audio_device)SDL_CloseAudioDevice(audio_device);audio_device=0;audio_fifo=AudioFifo{};audio_clock=AudioFrameClock{};output_frames_emitted=0;output_frames_consumed=0;source_frequency=48000;}
    test_controller::shutdown();
    if(game_window)SDL_DestroyWindow(game_window);game_window=nullptr;SDL_Quit();
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
    for(unsigned i=0;i<4;++i){result[i].manual_family=ports[i].manual;result[i].bindings=ports[i].bindings;}
    return result;
}
void apply_port_preferences(const std::array<PortPreferences,4>& preferences){
    for(const auto& preference:preferences){
        if(unsigned(preference.manual_family)>unsigned(Family::Nintendo))throw std::invalid_argument("Invalid controller family");
        for(auto button:preference.bindings)if(int(button)<-1||button>=SDL_CONTROLLER_BUTTON_MAX)throw std::invalid_argument("Invalid controller button");
    }
    std::lock_guard lock(input_mutex);
    for(unsigned i=0;i<4;++i){ports[i].manual=preferences[i].manual_family;ports[i].bindings=preferences[i].bindings;}
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
Prompt prompt(int n,Action action){
    if(n<0||n>=4||unsigned(action)>=unsigned(Action::Count))throw std::out_of_range("Controller prompt");
    std::lock_guard lock(input_mutex);
    return prompt_locked(ports[n],action);
}
ControlsHelp controls_help(int n){
    if(n<0||n>=4)throw std::out_of_range("Controller port");
    std::lock_guard lock(input_mutex);
    const auto& p=ports[n];
    return {{{prompt_locked(p,Action::A),prompt_locked(p,Action::B),prompt_locked(p,Action::Start)}},p.manual};
}
}
