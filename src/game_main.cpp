// Original project work: djultra64.
#include "platform.hpp"
#include "renderer_settings.hpp"
#include "runtime/native_game.hpp"
#include "runtime/game_revision.hpp"
#include "runtime/rom_image.hpp"
#include "runtime/pak_services.hpp"
#include "runtime/input_preferences.hpp"
#include <librecomp/game.hpp>
#include <librecomp/overlays.hpp>
#include <ultramodern/config.hpp>
#include <nfd.h>
#define XXH_INLINE_ALL
#include <xxHash/xxhash.h>
#include <filesystem>
#include <cstdio>
#include <iostream>
#include <string>

int main(int argc,char** argv){
    bool initialized=false;
    try{
        std::filesystem::path input,data;
        bool validate_only=false;
        for(int i=1;i<argc;++i){
            std::string option=argv[i];
            if((option=="--rom"||option=="--validate-rom"||option=="--data-dir")&&i+1<argc){
                if(option=="--data-dir")data=argv[++i];
                else{validate_only=option=="--validate-rom";input=argv[++i];}
            }else throw std::runtime_error("Unknown option or missing argument: "+option);
        }
        if(validate_only){
            const auto image=iss2000::read_rom_image(input);
            std::cout<<"{\"rom_valid\":true,\"bytes\":"<<image.size()<<"}\n";return 0;
        }
        iss2000::platform::initialize();initialized=true;
        if(data.empty()){
            char* base=SDL_GetBasePath();if(!base)throw std::runtime_error("Cannot locate portable program folder");
            data=std::filesystem::u8path(base)/"data";SDL_free(base);
        }
        data=std::filesystem::absolute(data);
        auto stored=data/iss2000::active_revision().storage_name;
        if(input.empty() && std::filesystem::exists(stored))input=stored;
        std::vector<uint8_t> image;
        while(true){
            if(input.empty()){
                const std::string prompt=std::string("Select your own International Superstar Soccer 2000 ")+iss2000::active_revision().description+" ROM. ZIP, Z64, N64 and V64 are supported. It will be imported into this portable folder.";
                SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_INFORMATION,"ISS2000: select your ROM",prompt.c_str(),iss2000::platform::window());
                if(NFD_Init()!=NFD_OKAY)throw std::runtime_error("Cannot open ROM file selector");
                nfdu8char_t* selection=nullptr;nfdu8filteritem_t filters[]={{"ISS2000 ROM","zip,z64,n64,v64"}};
                auto selected=NFD_OpenDialogU8(&selection,filters,1,nullptr);
                if(selected==NFD_CANCEL){NFD_Quit();iss2000::platform::shutdown();return 0;}
                if(selected!=NFD_OKAY){NFD_Quit();throw std::runtime_error("ROM selection failed");}
                input=std::filesystem::u8path(selection);NFD_FreePathU8(selection);NFD_Quit();
            }
            try{image=iss2000::read_rom_image(input);break;}
            catch(const std::exception& error){
                SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_ERROR,"ISS2000: ROM not supported",error.what(),iss2000::platform::window());
                input.clear();
            }
        }
        std::filesystem::create_directories(data);
        iss2000::ensure_rom_storage(stored,image);
        iss2000::apply_input_preferences(iss2000::load_input_preferences(data));
        const auto selected_graphics=iss2000::load_graphics_settings(data);
        iss2000::platform::set_render_settings(selected_graphics);
        if(!std::filesystem::exists(data/"graphics.json"))iss2000::save_graphics_settings(data,selected_graphics);
        #ifdef ISS2000_PAL_ENGLISH
        iss2000::configure_paks(data/"saves"/iss2000::active_revision().id);
#else
        iss2000::configure_paks(data/"saves");
#endif
        for(unsigned port=0;port<4;++port)iss2000::set_pak_port_connected(port,
            iss2000::platform::input_callbacks().get_connected_device_info(int(port)).connected_device!=ultramodern::input::Device::None);
        recomp::register_config_path(data);
        iss2000::initialize_native_game();
        recomp::GameEntry game{};
        game.rom_hash=XXH3_64bits(image.data(),image.size());game.internal_name="I.S.S.2000";
        game.display_name="International Superstar Soccer 2000";
#ifdef ISS2000_PAL_ENGLISH
        game.game_id=u8"iss2000-pal-en-de";
#else
        game.game_id=u8"iss2000-us";
#endif
        game.mod_game_id="iss2000";
        game.is_enabled=true;game.save_type=recomp::SaveType::None;
        game.entrypoint_address=S32(0x80000400);game.entrypoint=iss2000::enter_game;game.on_init_callback=iss2000::on_game_init;
        recomp::register_game(game);
        ultramodern::renderer::GraphicsConfig graphics{};
        graphics.developer_mode=false;graphics.res_option=ultramodern::renderer::Resolution::Original;
        graphics.wm_option=ultramodern::renderer::WindowMode::Windowed;graphics.hr_option=ultramodern::renderer::HUDRatioMode::Original;
        graphics.api_option=ultramodern::renderer::GraphicsApi::Vulkan;graphics.ar_option=ultramodern::renderer::AspectRatio::Original;
        graphics.msaa_option=ultramodern::renderer::Antialiasing::None;graphics.rr_option=ultramodern::renderer::RefreshRate::Original;
        graphics.hpfb_option=ultramodern::renderer::HighPrecisionFramebuffer::Off;graphics.ds_option=1;graphics.rr_manual_value=60;
        ultramodern::renderer::set_graphics_config(graphics);
        char app[]="iss2000";char flag[]="--game";char id[]="iss2000";char* runtime_args[]={app,flag,id};
        recomp::Configuration config{};config.argc=3;config.argv=runtime_args;config.project_version={0,0,1,"native-development"};
        config.window_handle=iss2000::platform::render_window();config.rsp_callbacks={iss2000::platform::rsp_microcode};
        config.renderer_callbacks=iss2000::platform::renderer_callbacks();config.audio_callbacks=iss2000::platform::audio_callbacks();
        config.input_callbacks=iss2000::platform::input_callbacks();config.gfx_callbacks=iss2000::platform::gfx_callbacks();
        config.error_handling_callbacks={iss2000::runtime_message};
        std::fprintf(stderr,"[Launch] ISS2000 native development build; match verification in progress. Portable data: %s\n",data.string().c_str());
        recomp::start(config);
        iss2000::shutdown_paks();iss2000::platform::shutdown();return 0;
    }catch(const std::exception& error){
        std::cerr<<"ISS2000 ROM/runtime error: "<<error.what()<<'\n';
        if(initialized){SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_ERROR,"ISS2000",error.what(),iss2000::platform::window());iss2000::platform::shutdown();}
        iss2000::shutdown_paks();
        return 1;
    }
}
