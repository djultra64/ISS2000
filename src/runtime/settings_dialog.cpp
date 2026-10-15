// Original project work: djultra64.
#include "settings_dialog.hpp"
#include "graphics_settings.hpp"
#include "pak_services.hpp"
#include "input_preferences.hpp"
#include "platform.hpp"
#include "renderer_settings.hpp"
#include <cstdio>
#include <initializer_list>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>
namespace iss2000 {
namespace {
// Choice zero always means cancel/back/close; closing the native dialog is also
// cancellation. No settings are changed merely by opening a menu.
int choose(SDL_Window* window,const std::string& title,const std::string& message,
           std::initializer_list<std::pair<int,std::string>> options){
    std::vector<SDL_MessageBoxButtonData> buttons;
    buttons.reserve(options.size());
    for(const auto& [id,label]:options){
        Uint32 flags=id==0?(SDL_MESSAGEBOX_BUTTON_ESCAPEKEY_DEFAULT|SDL_MESSAGEBOX_BUTTON_RETURNKEY_DEFAULT):0;
        buttons.push_back({flags,id,label.c_str()});
    }
    SDL_MessageBoxData dialog{};
    dialog.flags=SDL_MESSAGEBOX_INFORMATION|SDL_MESSAGEBOX_BUTTONS_LEFT_TO_RIGHT;
    dialog.window=window;dialog.title=title.c_str();dialog.message=message.c_str();
    dialog.numbuttons=int(buttons.size());dialog.buttons=buttons.data();
    int result=-1;
    if(SDL_ShowMessageBox(&dialog,&result)<0)throw std::runtime_error(std::string("Cannot open settings: ")+SDL_GetError());
    return result<0?0:result;
}
const char* aspect_name(AspectRatio aspect){return aspect==AspectRatio::Wide16x9?"16:9":"4:3";}
std::string resolution_name(RenderResolution resolution,AspectRatio aspect){
    GraphicsSettings settings;
    settings.resolution=resolution;settings.aspect_ratio=aspect;
    return resolution_label(settings);
}
const char* refresh_name(RenderRefresh refresh){
    switch(refresh){case RenderRefresh::Original:return "Original";case RenderRefresh::Hz60:return "60 Hz";case RenderRefresh::Hz120:return "120 Hz";}
    return "Original";
}
void graphics_dialog(SDL_Window* window,const std::filesystem::path& data){
    // Loading validates the persisted file. A malformed file is reported and
    // preserved, rather than overwritten with a guessed default by the dialog.
    GraphicsSettings draft=load_graphics_settings(data);
    while(true){
        std::string message=std::string("Display: ")+aspect_name(draft.aspect_ratio)+
            "\nResolution: "+resolution_name(draft.resolution,draft.aspect_ratio)+"\nRefresh rate: "+refresh_name(draft.refresh_rate)+
            "\n\nSelect Save to apply your changes.";
        switch(choose(window,"Graphics",message,{{1,"Display"},{2,"Resolution"},{3,"Refresh rate"},{4,"Save"},{0,"Cancel"}})){
            case 1:{
                int choice=choose(window,"Display","Choose the shape of the picture.",{{1,"4:3"},{2,"16:9"},{0,"Cancel"}});
                if(choice==1)draft.aspect_ratio=AspectRatio::Original4x3;
                else if(choice==2)draft.aspect_ratio=AspectRatio::Wide16x9;
                break;
            }
            case 2:{
                bool high=draft.resolution==RenderResolution::P1440 || draft.resolution==RenderResolution::P1800 || draft.resolution==RenderResolution::P2160;
                while(true){
                    std::string explanation=std::string("Choose the rendering resolution for ")+aspect_name(draft.aspect_ratio)+".\nOriginal preserves the native rendering resolution.";
                    int choice=high
                        ?choose(window,"Resolution - High",explanation,{{5,resolution_name(RenderResolution::P1440,draft.aspect_ratio)},{6,resolution_name(RenderResolution::P1800,draft.aspect_ratio)},{7,resolution_name(RenderResolution::P2160,draft.aspect_ratio)},{8,"Standard resolutions"},{0,"Cancel"}})
                        :choose(window,"Resolution - Standard",explanation,{{1,"Original"},{2,resolution_name(RenderResolution::P720,draft.aspect_ratio)},{3,resolution_name(RenderResolution::P900,draft.aspect_ratio)},{4,resolution_name(RenderResolution::P1080,draft.aspect_ratio)},{8,"High resolutions"},{0,"Cancel"}});
                    if(choice==8){high=!high;continue;}
                    switch(choice){
                        case 1:draft.resolution=RenderResolution::Original;break;
                        case 2:draft.resolution=RenderResolution::P720;break;
                        case 3:draft.resolution=RenderResolution::P900;break;
                        case 4:draft.resolution=RenderResolution::P1080;break;
                        case 5:draft.resolution=RenderResolution::P1440;break;
                        case 6:draft.resolution=RenderResolution::P1800;break;
                        case 7:draft.resolution=RenderResolution::P2160;break;
                    }
                    break;
                }
                break;
            }
            case 3:{
                int choice=choose(window,"Refresh rate","Choose how smoothly the picture is displayed.",{{1,"Original"},{2,"60 Hz"},{3,"120 Hz"},{0,"Cancel"}});
                if(choice==1)draft.refresh_rate=RenderRefresh::Original;
                else if(choice==2)draft.refresh_rate=RenderRefresh::Hz60;
                else if(choice==3)draft.refresh_rate=RenderRefresh::Hz120;
                break;
            }
            case 4:
                // Persist successfully before changing the running renderer.
                save_graphics_settings(data,draft);platform::set_render_settings(draft);return;
            default:return;
        }
    }
}
const char* accessory_name(PakAccessory accessory){
    switch(accessory){case PakAccessory::Controller:return "Controller Pak (save)";case PakAccessory::Rumble:return "Rumble Pak";case PakAccessory::None:return "None";}
    return "None";
}
const char* family_name(platform::Family family){
    switch(family){
        case platform::Family::Automatic:return "Automatic";
        case platform::Family::Xbox:return "Xbox";
        case platform::Family::PlayStation:return "PlayStation";
        case platform::Family::Nintendo:return "Nintendo Switch";
        case platform::Family::Keyboard:return "Keyboard";
    }
    return "Automatic";
}
void save_family(const std::filesystem::path& data,unsigned port,platform::Family family){
    auto preferences=capture_input_preferences();preferences.ports[port].manual_family=family;
    save_input_preferences(data,preferences);apply_input_preferences(preferences);
}
void save_mapping(const std::filesystem::path& data,unsigned port,platform::Action action,SDL_GameControllerButton button){
    auto preferences=capture_input_preferences();preferences.ports[port].bindings[size_t(action)]=button;
    save_input_preferences(data,preferences);apply_input_preferences(preferences);
}
int physical_button_dialog(SDL_Window* window,unsigned port){
    using namespace platform;
    auto label=[&](SDL_GameControllerButton button){return physical_button_label(int(port),button);};
    while(true){
        int category=choose(window,"Button mapping","Choose the kind of physical button.",{{1,"Face buttons"},{2,"Shoulders"},{3,"Stick buttons"},{4,"D-pad"},{5,"More buttons"},{0,"Cancel"}});
        int choice=0;
        switch(category){
            case 1:choice=choose(window,"Face buttons","Choose the physical button.",{{1,label(SDL_CONTROLLER_BUTTON_A)},{2,label(SDL_CONTROLLER_BUTTON_B)},{3,label(SDL_CONTROLLER_BUTTON_X)},{4,label(SDL_CONTROLLER_BUTTON_Y)},{0,"Back"}});break;
            case 2:choice=choose(window,"Shoulders","Choose the physical button.",{{10,label(SDL_CONTROLLER_BUTTON_LEFTSHOULDER)},{11,label(SDL_CONTROLLER_BUTTON_RIGHTSHOULDER)},{0,"Back"}});break;
            case 3:choice=choose(window,"Stick buttons","Choose which stick to press.",{{8,label(SDL_CONTROLLER_BUTTON_LEFTSTICK)},{9,label(SDL_CONTROLLER_BUTTON_RIGHTSTICK)},{0,"Back"}});break;
            case 4:choice=choose(window,"D-pad","Choose a direction.",{{12,"Up"},{13,"Down"},{14,"Left"},{15,"Right"},{0,"Back"}});break;
            case 5:{
                int group=choose(window,"More buttons","Choose a group.",{{1,"Menu buttons"},{2,"Extra buttons"},{0,"Back"}});
                if(group==1)choice=choose(window,"Menu buttons","Choose the physical button.",{{5,label(SDL_CONTROLLER_BUTTON_BACK)},{6,label(SDL_CONTROLLER_BUTTON_GUIDE)},{7,label(SDL_CONTROLLER_BUTTON_START)},{0,"Back"}});
                if(group==2){
                    int extra=choose(window,"Extra buttons","Choose an extra control if your controller has it.",{{16,label(SDL_CONTROLLER_BUTTON_MISC1)},{21,"Touchpad"},{22,"Paddles"},{0,"Back"}});
                    if(extra==22)choice=choose(window,"Paddles","Choose a paddle.",{{17,label(SDL_CONTROLLER_BUTTON_PADDLE1)},{18,label(SDL_CONTROLLER_BUTTON_PADDLE2)},{19,label(SDL_CONTROLLER_BUTTON_PADDLE3)},{20,label(SDL_CONTROLLER_BUTTON_PADDLE4)},{0,"Back"}});
                    else choice=extra;
                }
                break;
            }
            default:return -1;
        }
        if(choice>0)return choice-1;
    }
}
const char* action_name(platform::Action action){
    constexpr const char* names[]{"N64 A action","N64 B action","Pause / Start","Z action","L action","R action","C up","C down","C left","C right","D-pad up","D-pad down","D-pad left","D-pad right"};
    return names[size_t(action)];
}
void action_mapping_dialog(SDL_Window* window,const std::filesystem::path& data,unsigned port,platform::Action action){
    using namespace platform;
    while(true){
        auto binding=get_binding(int(port),action);
        std::string current=physical_button_label(int(port),binding);
        if(binding==SDL_CONTROLLER_BUTTON_INVALID&&axis_fallback(action,binding))current=action==Action::Z?"Left trigger":"Right stick";
        std::string message=std::string("Game action: ")+action_name(action)+"\nCurrent control: "+current;
        if((action==Action::CUp||action==Action::CDown)&&binding==default_binding(action))message+="\nThe default also accepts the right stick.";
        const char* fallback=action==Action::Z?"Use left trigger":axis_fallback(action,SDL_CONTROLLER_BUTTON_INVALID)?"Use right stick":"Unbind";
        int choice=choose(window,"Button mapping",message,{{1,"Choose button"},{2,fallback},{3,"Restore default"},{0,"Back"}});
        if(choice==0)return;
        if(choice==1){int button=physical_button_dialog(window,port);if(button>=0)save_mapping(data,port,action,SDL_GameControllerButton(button));}
        else if(choice==2)save_mapping(data,port,action,SDL_CONTROLLER_BUTTON_INVALID);
        else if(choice==3)save_mapping(data,port,action,default_binding(action));
    }
}
void mapping_dialog(SDL_Window* window,const std::filesystem::path& data,unsigned port){
    while(true){
        int group=choose(window,"Button mapping","Choose a group of game actions.",{{1,"Main actions"},{2,"Shoulders"},{3,"C directions"},{4,"D-pad"},{0,"Back"}});
        int action=0;
        if(group==1)action=choose(window,"Main actions","Choose the game action to change.",{{1,"N64 A action"},{2,"N64 B action"},{3,"Pause / Start"},{4,"Z action"},{0,"Back"}});
        else if(group==2)action=choose(window,"Shoulder actions","Choose the game action to change.",{{5,"L action"},{6,"R action"},{0,"Back"}});
        else if(group==3)action=choose(window,"C directions","Choose the game action to change.",{{7,"C up"},{8,"C down"},{9,"C left"},{10,"C right"},{0,"Back"}});
        else if(group==4)action=choose(window,"D-pad actions","Choose the game action to change.",{{11,"Up"},{12,"Down"},{13,"Left"},{14,"Right"},{0,"Back"}});
        else return;
        if(action>0)action_mapping_dialog(window,data,port,platform::Action(action-1));
    }
}
void port_dialog(SDL_Window* window,unsigned port,const std::filesystem::path& data){
    std::string title="Controller "+std::to_string(port+1);
    while(true){
        auto help=platform::controls_help(int(port));
        std::string message=std::string("Accessory: ")+accessory_name(pak_accessory(int(port)))+
            "\nPrompt style: "+family_name(help.manual_family)+
            "\n\nAccessory choices, prompt style and button mappings are saved.";
        switch(choose(window,title,message,{{1,"Accessory"},{2,"Prompt style"},{3,"Button mapping"},{0,"Back"}})){
            case 1:{
                int choice=choose(window,title+": accessory","Choose one accessory for this controller.\nController Pak stores saves; Rumble Pak provides vibration.",
                    {{1,"Controller Pak (save)"},{2,"Rumble Pak"},{3,"None"},{0,"Cancel"}});
                if(choice==1)set_pak_accessory(port,PakAccessory::Controller);
                else if(choice==2)set_pak_accessory(port,PakAccessory::Rumble);
                else if(choice==3)set_pak_accessory(port,PakAccessory::None);
                break;
            }
            case 2:{
                int choice=choose(window,title+": prompt style","Automatic follows the active controller.\nChoose a style if detection is incorrect.",
                    {{1,"Automatic"},{2,"Xbox"},{3,"PlayStation"},{4,"Nintendo Switch"},{0,"Cancel"}});
                if(choice==1)save_family(data,port,platform::Family::Automatic);
                else if(choice==2)save_family(data,port,platform::Family::Xbox);
                else if(choice==3)save_family(data,port,platform::Family::PlayStation);
                else if(choice==4)save_family(data,port,platform::Family::Nintendo);
                break;
            }
            case 3:mapping_dialog(window,data,port);break;
            default:return;
        }
    }
}
void controllers_dialog(SDL_Window* window,const std::filesystem::path& data){
    while(true){
        int choice=choose(window,"Controllers","Choose a controller port.",{{1,"Controller 1"},{2,"Controller 2"},{3,"Controller 3"},{4,"Controller 4"},{0,"Back"}});
        if(choice<1||choice>4)return;
        port_dialog(window,unsigned(choice-1),data);
    }
}
}
void show_settings_dialog(SDL_Window* window,const std::filesystem::path& data){
    try{
        // No global pause API exists in the pinned runtime. Use the current
        // device's actual Start-action label and preserve the game's own state.
        auto help=platform::controls_help(0);
        std::string pause_label=help.prompts[2].name;
        if(pause_label.empty()||pause_label=="Unbound")pause_label="your pause control";
        std::string message="If you are in a match, pause with "+pause_label+" before changing settings.";
        while(true){
            switch(choose(window,"Settings",message,{{1,"Graphics"},{2,"Controllers"},{0,"Close"}})){
                case 1:graphics_dialog(window,data);break;
                case 2:controllers_dialog(window,data);break;
                default:return;
            }
        }
    }catch(const std::exception& error){
        if(SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_ERROR,"Settings could not be changed",error.what(),window)<0)
            std::fprintf(stderr,"Settings: %s\n",error.what());
    }catch(...){
        SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_ERROR,"Settings","The settings could not be changed. Please try again.",window);
    }
}
}
