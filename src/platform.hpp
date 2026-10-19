// Original project work: djultra64.
#pragma once
#include <array>
#include <cstdint>
#include <string>
#include <string_view>
#include "runtime/controller_schemes.hpp"
#ifndef SDL_MAIN_HANDLED
#define SDL_MAIN_HANDLED
#endif
#include <SDL.h>
#include <librecomp/rsp.hpp>
#include <ultramodern/ultramodern.hpp>

namespace iss2000::platform {
enum class Family { Automatic, Xbox, PlayStation, Nintendo, Keyboard };
enum class Action { A, B, Start, Z, L, R, CUp, CDown, CLeft, CRight, DUp, DDown, DLeft, DRight, Count };
// Positions follow SDL semantic buttons: south, east, west, north.
constexpr std::string_view face_label(Family family, unsigned position) {
    constexpr std::string_view xbox[]{"A","B","X","Y"};
    constexpr std::string_view ps[]{"Cross","Circle","Square","Triangle"};
    constexpr std::string_view nintendo[]{"B","A","Y","X"};
    if(position>=4)return "Unbound";
    return family==Family::Nintendo?nintendo[position]:family==Family::PlayStation?ps[position]:xbox[position];
}
using ButtonBindings=std::array<SDL_GameControllerButton,static_cast<size_t>(Action::Count)>;
constexpr SDL_GameControllerButton default_binding(Action action){
    constexpr ButtonBindings defaults{SDL_CONTROLLER_BUTTON_A,SDL_CONTROLLER_BUTTON_B,SDL_CONTROLLER_BUTTON_START,
        SDL_CONTROLLER_BUTTON_INVALID,SDL_CONTROLLER_BUTTON_LEFTSHOULDER,SDL_CONTROLLER_BUTTON_RIGHTSHOULDER,
        SDL_CONTROLLER_BUTTON_Y,SDL_CONTROLLER_BUTTON_X,SDL_CONTROLLER_BUTTON_INVALID,SDL_CONTROLLER_BUTTON_INVALID,
        SDL_CONTROLLER_BUTTON_DPAD_UP,SDL_CONTROLLER_BUTTON_DPAD_DOWN,SDL_CONTROLLER_BUTTON_DPAD_LEFT,SDL_CONTROLLER_BUTTON_DPAD_RIGHT};
    return unsigned(action)<unsigned(Action::Count)?defaults[size_t(action)]:SDL_CONTROLLER_BUTTON_INVALID;
}
constexpr bool axis_fallback(Action action,SDL_GameControllerButton binding){
    if(action==Action::Z||action==Action::CLeft||action==Action::CRight)return binding==SDL_CONTROLLER_BUTTON_INVALID;
    if(action==Action::CUp||action==Action::CDown)return binding==SDL_CONTROLLER_BUTTON_INVALID||binding==default_binding(action);
    return false;
}
constexpr std::string_view button_label(Family family,SDL_GameControllerButton button){
    if(button>=SDL_CONTROLLER_BUTTON_A&&button<=SDL_CONTROLLER_BUTTON_Y)return face_label(family,unsigned(button));
    switch(button){
        case SDL_CONTROLLER_BUTTON_LEFTSHOULDER:return family==Family::PlayStation?"L1":family==Family::Nintendo?"L":"LB";
        case SDL_CONTROLLER_BUTTON_RIGHTSHOULDER:return family==Family::PlayStation?"R1":family==Family::Nintendo?"R":"RB";
        case SDL_CONTROLLER_BUTTON_LEFTSTICK:return family==Family::PlayStation?"L3":family==Family::Nintendo?"Left stick":"LS";
        case SDL_CONTROLLER_BUTTON_RIGHTSTICK:return family==Family::PlayStation?"R3":family==Family::Nintendo?"Right stick":"RS";
        case SDL_CONTROLLER_BUTTON_BACK:return family==Family::PlayStation?"Share":family==Family::Nintendo?"-":"View";
        case SDL_CONTROLLER_BUTTON_START:return family==Family::PlayStation?"Options":family==Family::Nintendo?"+":"Menu";
        case SDL_CONTROLLER_BUTTON_GUIDE:return family==Family::PlayStation?"PS":family==Family::Nintendo?"Home":"Xbox";
        case SDL_CONTROLLER_BUTTON_DPAD_UP:return "D-pad up";
        case SDL_CONTROLLER_BUTTON_DPAD_DOWN:return "D-pad down";
        case SDL_CONTROLLER_BUTTON_DPAD_LEFT:return "D-pad left";
        case SDL_CONTROLLER_BUTTON_DPAD_RIGHT:return "D-pad right";
        case SDL_CONTROLLER_BUTTON_MISC1:return family==Family::Nintendo?"Capture":family==Family::PlayStation?"Microphone":"Share";
        case SDL_CONTROLLER_BUTTON_PADDLE1:return "Paddle 1";
        case SDL_CONTROLLER_BUTTON_PADDLE2:return family==Family::Xbox?"Paddle 3":"Paddle 2";
        case SDL_CONTROLLER_BUTTON_PADDLE3:return family==Family::Xbox?"Paddle 2":"Paddle 3";
        case SDL_CONTROLLER_BUTTON_PADDLE4:return "Paddle 4";
        case SDL_CONTROLLER_BUTTON_TOUCHPAD:return "Touchpad";
        default:return "Unbound";
    }
}
struct PortPreferences {
    bool vibration=true;
    Family manual_family=Family::Automatic;
    ButtonBindings bindings=[] {ButtonBindings result{};for(unsigned i=0;i<result.size();++i)result[i]=default_binding(Action(i));return result;}();
    // Football controls are independent of raw menu bindings; retain Free while a preset is selected.
    ControllerScheme football_scheme=ControllerScheme::Type1;
    FootballBindings free_football_bindings=default_football_bindings;
    bool operator==(const PortPreferences&)const=default;
};
SDL_GameControllerButton get_binding(int port,Action action);
Family controller_family(int port);
std::string physical_button_label(int port,SDL_GameControllerButton button);
std::array<PortPreferences,4> port_preferences();
void apply_port_preferences(const std::array<PortPreferences,4>& preferences);
// Independent physical positions. Neither getter consumes a sample. The SI
// sequence advances only at the genuine runtime get_input callback.
struct FootballPhysicalInput {
    uint16_t held=0;
    bool start=false,cancel=false,up=false,down=false;
    bool gamepad=false;
    bool operator==(const FootballPhysicalInput&)const=default;
};
struct FootballSiInput {
    uint16_t held=0,pressed=0;
    uint64_t sequence=0;
    bool gamepad=false;
    bool operator==(const FootballSiInput&)const=default;
};
FootballPhysicalInput football_physical_input(unsigned port);
FootballSiInput football_si_input(unsigned port);
struct Prompt { std::string name; std::string glyph; Family family; };
struct MainExitPrompts {std::array<Prompt,3> prompts;unsigned port;};
MainExitPrompts main_exit_prompts();
struct ControlsHelp { std::array<Prompt,3> prompts; Family manual_family; };
int submit_audio(uint8_t* rdram,uint32_t address,uint32_t bytes);
uint32_t audio_length();
uint32_t audio_status();
void initialize();
SDL_Window* window();
ultramodern::renderer::WindowHandle render_window();
void shutdown();
void set_rdram(uint8_t* rdram);
RspUcodeFunc* rsp_microcode(const OSTask* task);
ultramodern::renderer::callbacks_t renderer_callbacks();
ultramodern::audio_callbacks_t audio_callbacks();
ultramodern::input::callbacks_t input_callbacks();
ultramodern::gfx_callbacks_t gfx_callbacks();
void set_family(int port, Family family);
void bind_button(int port, Action action, SDL_GameControllerButton button);
// Last meaningful input event; keyboard and disconnected-controller fallback use P1.
unsigned active_input_port();
Prompt prompt(int port, Action action);
// One input-lock snapshot for physical action prompts and the manual family preference.
ControlsHelp controls_help(int port);
}
