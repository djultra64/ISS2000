#include "runtime/filter_2d.hpp"
// Original project work: djultra64.
// Integrates the public RT64 Application interface with N64ModernRuntime.
// API usage follows the generic upstream RecompFrontend RT64 adapter; its
// original author notices and licenses remain in the dependency checkouts.
#include "platform.hpp"
#ifdef _WIN32
#include <objidl.h>
#endif
#include "renderer_settings.hpp"
#include "runtime/transform_runtime.hpp"
#include "runtime/rt64_transform_bridge.hpp"
#include "runtime/menu_sprite_bridge.hpp"
#include "runtime/menu_sprite_render.hpp"
#include "runtime/rt64_shadow_bridge.hpp"
#include "runtime/rt64_presentation_policy.hpp"
#include <mutex>
#include <algorithm>
#include <array>
#include <memory>
#include <chrono>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <sstream>
#include "runtime/render_evidence_api.hpp"
#include "runtime/rom_image.hpp"
#include "render/rt64_render_target.h"
#include "contrib/plume/plume_vulkan.h"
#include "hle/rt64_application.h"
#include "hle/rt64_state.h"
#include "hle/rt64_rsp.h"
#include "hle/rt64_rdp.h"
#include "hle/rt64_present_queue.h"

namespace iss2000::render_evidence {
namespace {
struct EvidenceRegion {uint32_t x{},y{},width{},height{};};
EvidenceRegion evidence_region(uint32_t width,uint32_t height,bool small_region,bool radar){
    if(radar){
        // Lower central fifth/quarter includes the actual field radar; scale
        // against the offscreen target, which can be taller than the window.
        const auto w=std::min(width,std::max(1u,width/5));
        const auto h=std::min(height,std::max(1u,height/4));
        return {(width-w)/2,height-h,w,h};
    }
    const auto w=small_region?std::min(width,256u):width;
    const auto h=small_region?std::min(height,256u):height;
    return {(width-w)/2,(height-h)/2,w,h};
}
struct Log {
    std::mutex mutex;
    std::ofstream stream;
    std::chrono::steady_clock::time_point start=std::chrono::steady_clock::now();
    uint64_t frames{},readbacks{};
    std::filesystem::path gate;
    bool gpu{},small_region{},radar_region{};
    Log(){
        const char* path=std::getenv("ISS2000_RENDER_EVIDENCE");
        if(!path || !*path)return;
        stream.open(path,std::ios::out|std::ios::trunc);
        gpu=std::getenv("ISS2000_RENDER_EVIDENCE_GPU") && std::string_view(std::getenv("ISS2000_RENDER_EVIDENCE_GPU"))=="1";
        if(const char* region=std::getenv("ISS2000_RENDER_EVIDENCE_ROI")){small_region=std::string_view(region)=="256";radar_region=std::string_view(region)=="radar";}
        if(const char* value=std::getenv("ISS2000_RENDER_EVIDENCE_GPU_GATE"))gate=value;
        if(stream)stream<<"{\"event\":\"start\",\"schema\":1,\"gpu_readback_requested\":"<<(gpu?"true":"false")
            <<",\"physical_refresh_proven\":false,\"capture_limit\":240,\"capture_affects_performance\":true}\n"<<std::flush;
    }
    bool enabled()const{return stream.is_open();}
    uint64_t microseconds()const{return std::chrono::duration_cast<std::chrono::microseconds>(std::chrono::steady_clock::now()-start).count();}
    bool capture(){
        if(!gpu || readbacks>=240)return false;
        std::error_code error;
        return gate.empty() || std::filesystem::is_regular_file(gate,error);
    }
    void write(std::string_view fields){
        stream<<"{\"time_us\":"<<microseconds()<<","<<fields<<"}\n"<<std::flush;
    }
};
Log& log(){static Log value;return value;}
}
void display(uint32_t rate,uint32_t width,uint32_t height,uint32_t requested){
    auto& out=log();if(!out.enabled())return;std::lock_guard lock(out.mutex);
    std::ostringstream s;s<<"\"event\":\"display\",\"detected_hz\":"<<rate<<",\"width\":"<<width
        <<",\"height\":"<<height<<",\"requested_hz\":"<<requested;out.write(s.str());
}
void display_list(const TransformTaskSnapshot* snapshot,const TransformBridgeStats& stats,bool installed,const MenuSpriteTaskSnapshot* menu){
    auto& out=log();if(!out.enabled())return;std::lock_guard lock(out.mutex);
    size_t radar_commands=0;
    if(menu)for(const auto& ownership:menu->radar)for(const auto& command:ownership.capture.commands())
        if(menu->commands.contains(command.pc&0x7fffffu))++radar_commands;
    std::ostringstream s;s<<"\"event\":\"display_list\",\"snapshot\":"<<(snapshot?"true":"false")
        <<",\"bridge\":"<<(installed?"true":"false")<<",\"sequence\":"<<(snapshot?snapshot->sequence:0)
        <<",\"scene\":"<<(snapshot?snapshot->scene_token:0)<<",\"epoch\":"<<(snapshot?snapshot->scene_epoch:0)
        <<",\"matrix_calls\":"<<stats.matrix_calls<<",\"model_groups\":"<<stats.model_groups
        <<",\"camera_groups\":"<<stats.camera_groups<<",\"inherited_groups\":"<<stats.inherited_groups
        <<",\"ignored_groups\":"<<stats.ignored_groups
        <<",\"menu_snapshot\":"<<(menu?"true":"false")
        <<",\"menu_commands\":"<<(menu?menu->commands.size():0)
        <<",\"radar_captures\":"<<(menu?menu->radar.size():0)
        <<",\"radar_commands\":"<<radar_commands;out.write(s.str());
}
}
extern "C" bool iss2000_render_evidence_enabled(){return iss2000::render_evidence::log().enabled();}
extern "C" void iss2000_render_evidence_frame(RT64::RenderWorker* worker,RT64::RenderTarget* target,
    uint64_t workload,uint64_t present,uint32_t frame,uint32_t planned,float weight,float previous,
    uint32_t target_hz,uint32_t original_hz,bool matched){
    using namespace iss2000;using namespace plume;
    auto& out=render_evidence::log();if(!out.enabled())return;
    std::lock_guard lock(out.mutex);
    std::string digest;const char* capture="not_requested";uint64_t bytes=0;
    const uint32_t width=target?target->width:0,height=target?target->height:0;
    // A fixed center crop reduces diagnostic copy/hash cost. It samples the
    // completed real target; it never changes rendering or interpolation.
    const auto region=render_evidence::evidence_region(width,height,out.small_region,out.radar_region);
    const uint32_t capture_width=region.width,capture_height=region.height;
    const uint32_t capture_x=region.x,capture_y=region.y;
    // The private generator holds RT64's workload and worker mutexes here.
    // This is the completed normal offscreen image; swapchain images do not
    // advertise transfer-source usage and must never be read back this way.
    if(out.capture() && target && target->texture && width && height){
        capture="unsupported_backend_or_target";
        auto* texture=dynamic_cast<VulkanTexture*>(target->texture.get());
        auto* commands=dynamic_cast<VulkanCommandList*>(worker->commandList.get());
        if(texture && commands && target->multisampling.sampleCount==1 &&
           (target->format==RenderFormat::R8G8B8A8_UNORM || target->format==RenderFormat::R16G16B16A16_UNORM)){
            bytes=uint64_t(capture_width)*capture_height*RenderFormatSize(target->format);
            auto buffer=worker->device->createBuffer(RenderBufferDesc::ReadbackBuffer(bytes));
            auto* destination=dynamic_cast<VulkanBuffer*>(buffer.get());
            if(destination && destination->vk!=VK_NULL_HANDLE){
                const auto previous_layout=texture->textureLayout;
                worker->commandList->begin();
                worker->commandList->barriers(RenderBarrierStage::COPY,RenderTextureBarrier(texture,RenderTextureLayout::COPY_SOURCE));
                VkBufferImageCopy copy{};copy.imageSubresource.aspectMask=VK_IMAGE_ASPECT_COLOR_BIT;
                copy.imageSubresource.layerCount=1;
                copy.imageOffset={int32_t(capture_x),int32_t(capture_y),0};
                copy.imageExtent={capture_width,capture_height,1};
                vkCmdCopyImageToBuffer(commands->vk,texture->vk,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,destination->vk,1,&copy);
                VkBufferMemoryBarrier host{};host.sType=VK_STRUCTURE_TYPE_BUFFER_MEMORY_BARRIER;
                host.srcAccessMask=VK_ACCESS_TRANSFER_WRITE_BIT;host.dstAccessMask=VK_ACCESS_HOST_READ_BIT;
                host.srcQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED;host.dstQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED;
                host.buffer=destination->vk;host.size=VK_WHOLE_SIZE;
                vkCmdPipelineBarrier(commands->vk,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_HOST_BIT,0,0,nullptr,1,&host,0,nullptr);
                worker->commandList->barriers(RenderBarrierStage::GRAPHICS,RenderTextureBarrier(texture,previous_layout));
                worker->commandList->end();worker->execute();worker->wait();
                if(auto* data=static_cast<const uint8_t*>(buffer->map())){
                    if(vmaInvalidateAllocation(destination->device->allocator,destination->allocation,0,VK_WHOLE_SIZE)==VK_SUCCESS){
                        digest=rom_detail::sha256_hex({data,size_t(bytes)});capture="gpu_readback";++out.readbacks;
                    }else capture="invalidate_failed";
                    buffer->unmap();
                }else capture="map_failed";
            }else capture="allocation_failed";
        }
    }
    const auto menu=iss2000::menu_rect_render_stats();
    std::ostringstream s;s<<"\"event\":\"render\",\"ordinal\":"<<++out.frames<<",\"workload\":"<<workload
        <<",\"present\":"<<present<<",\"frame\":"<<frame<<",\"planned\":"<<planned
        <<",\"weight\":"<<weight<<",\"previous_weight\":"<<previous<<",\"target_hz\":"<<target_hz
        <<",\"original_hz\":"<<original_hz<<",\"matched\":"<<(matched?"true":"false")
        <<",\"menu_rectangles\":"<<menu.rectangles<<",\"menu_matches\":"<<menu.matches
        <<",\"menu_moved\":"<<menu.moved<<",\"menu_fades\":"<<menu.fades<<",\"menu_fractional\":"<<(menu.fractional?"true":"false")
        <<",\"width\":"<<width<<",\"height\":"<<height<<",\"bytes\":"<<bytes
        <<",\"capture_x\":"<<capture_x<<",\"capture_y\":"<<capture_y
        <<",\"capture_width\":"<<capture_width<<",\"capture_height\":"<<capture_height
        <<",\"capture_format\":"<<(target?uint32_t(target->format):0)
        <<",\"capture\":\""<<capture<<"\",\"pixel_sha256\":\""<<digest<<"\"";
    out.write(s.str());
}
extern "C" void iss2000_render_evidence_present(uint64_t present,uint32_t frame,uint32_t planned,
    uint32_t target_hz,uint32_t original_hz,bool success){
    auto& out=iss2000::render_evidence::log();if(!out.enabled())return;std::lock_guard lock(out.mutex);
    std::ostringstream s;s<<"\"event\":\"present\",\"present\":"<<present<<",\"frame\":"<<frame
        <<",\"planned\":"<<planned<<",\"target_hz\":"<<target_hz<<",\"original_hz\":"<<original_hz
        <<",\"success\":"<<(success?"true":"false");out.write(s.str());
}

namespace iss2000::platform {
namespace {
std::mutex settings_mutex;
GraphicsSettings active_settings;
class RT64Context final:public ultramodern::renderer::RendererContext {
    std::unique_ptr<RT64::Application> app;
    std::array<uint8_t,0x1000> dmem{},imem{};
    std::array<uint8_t,0x40> header{};
    uint32_t native_height=240;
    GraphicsSettings applied_settings;
    uint32_t evidence_display_rate=UINT32_MAX,evidence_requested_rate=UINT32_MAX;
    uint32_t mi{},dpc_start{},dpc_end{},dpc_current{},dpc_status{},dpc_clock{},dpc_bufbusy{},dpc_pipebusy{},dpc_tmem{};
    static void check_interrupts() {} // Runtime schedules SP/DP completion after task submission.
    void config(const ultramodern::renderer::GraphicsConfig& c){
        auto& u=app->userConfig;
        // RT64 owns the sole perspective correction. Guest projection matrices
        // remain 4:3; native visibility hooks widen only horizontal bounds.
        // Untagged rectangles retain their centered coordinate system. Only
        // reviewed HUD scopes opt into explicit left/right screen origins.
        u.extAspectRatio=RT64::UserConfiguration::AspectRatio::Expand;
        u.antialiasing=static_cast<RT64::UserConfiguration::Antialiasing>(c.msaa_option);
        u.internalColorFormat=c.hpfb_option==ultramodern::renderer::HighPrecisionFramebuffer::On?RT64::UserConfiguration::InternalColorFormat::High:c.hpfb_option==ultramodern::renderer::HighPrecisionFramebuffer::Off?RT64::UserConfiguration::InternalColorFormat::Standard:RT64::UserConfiguration::InternalColorFormat::Automatic;
        const auto chosen=render_settings();
        u.resolution=chosen.resolution==RenderResolution::Original?RT64::UserConfiguration::Resolution::Original:RT64::UserConfiguration::Resolution::Manual;
        u.resolutionMultiplier=resolution_multiplier(chosen,native_height);
        applied_settings=chosen;
        u.downsampleMultiplier=1;
        // Sprite strips must share their original texel origins at fractional
        // PAL output scales. The default low-resolution screen-grid snapping
        // shifts separate identity-scale tiles by different source fractions.
        u.upscale2D=RT64::UserConfiguration::Upscale2D::All;
        u.aspectRatio=chosen.aspect_ratio==AspectRatio::Wide16x9?RT64::UserConfiguration::AspectRatio::Manual:RT64::UserConfiguration::AspectRatio::Original;
        u.aspectTarget=chosen.aspect_ratio==AspectRatio::Wide16x9?16.0/9.0:4.0/3.0;
        u.refreshRate=chosen.refresh_rate==RenderRefresh::Original?RT64::UserConfiguration::RefreshRate::Original:RT64::UserConfiguration::RefreshRate::Manual;
        u.refreshRateTarget=chosen.refresh_rate==RenderRefresh::Hz120?120:60;
        u.displayBuffering=RT64::UserConfiguration::DisplayBuffering::Triple;
        app->enhancementConfig.presentation.mode=rt64_presentation_mode(chosen.refresh_rate);
    }
    void refresh_settings(){
        const auto& vi=app->state->viHistory.top().vi;
        if(vi.visible() && vi.fbSize().y)native_height=vi.fbSize().y;
        const auto chosen=render_settings();
        if(chosen!=applied_settings || resolution_multiplier(chosen,native_height)!=app->userConfig.resolutionMultiplier){
            config(ultramodern::renderer::get_graphics_config());
            app->updateUserConfig(true);
            app->updateEnhancementConfig();
        }
        if(iss2000_render_evidence_enabled()){
            std::lock_guard lock(app->sharedQueueResources->configurationMutex);
            const auto& resources=*app->sharedQueueResources;
            if(evidence_display_rate!=resources.swapChainRate || evidence_requested_rate!=app->userConfig.refreshRateTarget){
                evidence_display_rate=resources.swapChainRate;evidence_requested_rate=app->userConfig.refreshRateTarget;
                render_evidence::display(resources.swapChainRate,resources.swapChainWidth,resources.swapChainHeight,
                    app->userConfig.refreshRateTarget);
            }
        }
    }
public:
    RT64Context(uint8_t* rdram,ultramodern::renderer::WindowHandle handle,bool developer){
        set_rdram(rdram);
        RT64::Application::Core core{};
#if defined(_WIN32)
        core.window=handle.window;
#else
        core.window=handle;
#endif
        core.HEADER=header.data();core.RDRAM=rdram;core.DMEM=dmem.data();core.IMEM=imem.data();core.checkInterrupts=check_interrupts;
        core.MI_INTR_REG=&mi;core.DPC_START_REG=&dpc_start;core.DPC_END_REG=&dpc_end;core.DPC_CURRENT_REG=&dpc_current;core.DPC_STATUS_REG=&dpc_status;
        core.DPC_CLOCK_REG=&dpc_clock;core.DPC_BUFBUSY_REG=&dpc_bufbusy;core.DPC_PIPEBUSY_REG=&dpc_pipebusy;core.DPC_TMEM_REG=&dpc_tmem;
        auto* vi=ultramodern::renderer::get_vi_regs();
#define ISS_VI(name) core.name=&vi->name
        ISS_VI(VI_STATUS_REG);ISS_VI(VI_ORIGIN_REG);ISS_VI(VI_WIDTH_REG);ISS_VI(VI_INTR_REG);ISS_VI(VI_V_CURRENT_LINE_REG);ISS_VI(VI_TIMING_REG);
        ISS_VI(VI_V_SYNC_REG);ISS_VI(VI_H_SYNC_REG);ISS_VI(VI_LEAP_REG);ISS_VI(VI_H_START_REG);ISS_VI(VI_V_START_REG);ISS_VI(VI_V_BURST_REG);ISS_VI(VI_X_SCALE_REG);ISS_VI(VI_Y_SCALE_REG);
#undef ISS_VI
        RT64::ApplicationConfiguration settings;settings.useConfigurationFile=false;settings.detectDataPath=false;settings.appId="iss2000";
        app=std::make_unique<RT64::Application>(core,settings);
        const auto& c=ultramodern::renderer::get_graphics_config();config(c);
        app->userConfig.developerMode=developer;app->userConfig.graphicsAPI=RT64::UserConfiguration::GraphicsAPI::Vulkan;
        auto result=app->setup(0);
        switch(result){
        case RT64::Application::SetupResult::Success:setup_result=ultramodern::renderer::SetupResult::Success;break;
        case RT64::Application::SetupResult::DynamicLibrariesNotFound:setup_result=ultramodern::renderer::SetupResult::DynamicLibrariesNotFound;break;
        case RT64::Application::SetupResult::InvalidGraphicsAPI:setup_result=ultramodern::renderer::SetupResult::InvalidGraphicsAPI;break;
        case RT64::Application::SetupResult::GraphicsAPINotFound:setup_result=ultramodern::renderer::SetupResult::GraphicsAPINotFound;break;
        case RT64::Application::SetupResult::GraphicsDeviceNotFound:setup_result=ultramodern::renderer::SetupResult::GraphicsDeviceNotFound;break;
        }
        chosen_api=ultramodern::renderer::GraphicsApi::Vulkan;
        if(setup_result!=ultramodern::renderer::SetupResult::Success){app.reset();return;}
        {
            const auto& resources=*app->sharedQueueResources;
            std::lock_guard lock(app->sharedQueueResources->configurationMutex);
            render_evidence::display(resources.swapChainRate,resources.swapChainWidth,resources.swapChainHeight,
                app->userConfig.refreshRateTarget);
        }
    }
    bool valid()override{return bool(app);}
    void send_dl(const OSTask* task)override{
        refresh_settings();
        app->state->rsp->reset();
        app->interpreter->loadUCodeGBI(task->t.ucode&0x3FFFFFF,task->t.ucode_data&0x3FFFFFF,true);
        const TransformTaskFingerprint fingerprint{.data_ptr=uint32_t(task->t.data_ptr),
            .ucode=uint32_t(task->t.ucode),.ucode_data=uint32_t(task->t.ucode_data),.data_size=task->t.data_size};
        const auto snapshot=consume_transform_metadata(fingerprint);
        const auto menu_snapshot=consume_menu_sprite_metadata(fingerprint,{app->core.RDRAM,0x800000});
        const auto shadow_snapshot=consume_pal_shadow_metadata(fingerprint);
        const bool interpolate=applied_settings.refresh_rate!=RenderRefresh::Original;
        RT64TransformBridge tracking(app->state.get(),app->interpreter->hleGBI,snapshot,interpolate);
        RT64ShadowBridge shadow_tracking(app->state.get(),app->interpreter->hleGBI,shadow_snapshot,interpolate);
        MenuSpriteBridge menu_tracking(app->state.get(),app->interpreter->hleGBI,menu_snapshot,interpolate);
        app->processDisplayLists(app->core.RDRAM,task->t.data_ptr&0x3FFFFFF,0,true);
        render_evidence::display_list(snapshot.get(),tracking.stats(),tracking.installed(),menu_snapshot.get());
    }
    void send_dummy_workload(uint32_t address)override{
        app->state->listProcessBegin();
        app->state->rdp->setColorImage(G_IM_FMT_RGBA,G_IM_SIZ_16b,320,address);
        app->state->rdp->setOtherMode(0x382C30,0);
        app->state->rdp->fillRect(0,0,320<<2,240<<2);
        app->state->fullSync();app->state->listProcessEnd();
    }
    void update_screen()override{app->updateScreen();refresh_settings();}
    void shutdown()override{if(app)app->end();}
    bool update_config(const ultramodern::renderer::GraphicsConfig& old,const ultramodern::renderer::GraphicsConfig& next)override{
        if(old==next)return false;config(next);
        app->updateUserConfig(true);app->updateEnhancementConfig();if(old.msaa_option!=next.msaa_option)app->updateMultisampling();return true;
    }
    void enable_instant_present()override{
        app->enhancementConfig.presentation.mode=RT64::EnhancementConfiguration::Presentation::Mode::PresentEarly;app->updateEnhancementConfig();
    }
    uint32_t get_display_framerate()const override{return app?app->presentQueue->ext.sharedResources->swapChainRate:0;}
    float get_resolution_scale()const override{
        if(!app)return 1.f;
        if(app->userConfig.resolution==RT64::UserConfiguration::Resolution::WindowIntegerScale)return std::max(1.f,float((app->sharedQueueResources->swapChainHeight+239)/240));
        return float(app->userConfig.resolutionMultiplier);
    }
};
std::unique_ptr<ultramodern::renderer::RendererContext> create(uint8_t* rdram,ultramodern::renderer::WindowHandle handle,bool developer){return std::make_unique<RT64Context>(rdram,handle,developer);}
}
void set_render_settings(const GraphicsSettings& settings){std::lock_guard lock(settings_mutex);active_settings=settings;}
GraphicsSettings render_settings(){std::lock_guard lock(settings_mutex);return active_settings;}
ultramodern::renderer::callbacks_t renderer_callbacks(){return {create,nullptr};}
}

extern "C" bool iss2000_filter_2d_enabled(){return iss2000::platform::render_settings().filter_2d==iss2000::Filter2D::Bilinear;}
