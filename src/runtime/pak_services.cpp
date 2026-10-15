// Original project work: djultra64.
#include "pak_services.hpp"
#include "guest_addresses.hpp"
#include "json/json.hpp"
#include <atomic>
#include <fstream>
#include <mutex>
#include <random>
#include <set>
#include <stdexcept>
#ifdef _WIN32
#define NOMINMAX
#include <windows.h>
#else
#include <cerrno>
#include <fcntl.h>
#include <unistd.h>
#endif
namespace iss2000 {
namespace {
std::mutex store_mutex;
std::unique_ptr<ControllerPakStore> store;
std::filesystem::path settings_path;
std::array<bool,4> connected{true,false,false,false};
std::array<bool,4> reconnected{};
std::array<bool,4> connection_observed{};
using Choices=std::array<PakAccessory,4>;
const char* name(PakAccessory accessory){
    switch(accessory){case PakAccessory::None:return "none";case PakAccessory::Rumble:return "rumble";case PakAccessory::Controller:return "controller";}
    throw std::invalid_argument("Invalid Controller Pak accessory selection");
}
void regular(const std::filesystem::path& path){
    auto type=std::filesystem::symlink_status(path).type();
    if(type!=std::filesystem::file_type::not_found&&type!=std::filesystem::file_type::regular)
        throw std::runtime_error("Controller Pak settings must be a regular file");
}
Choices load_choices(const std::filesystem::path& path){
    regular(path);
    if(!std::filesystem::exists(path))return {PakAccessory::Controller,PakAccessory::None,PakAccessory::None,PakAccessory::None};
    if(std::filesystem::file_size(path)>4096)throw std::runtime_error("Controller Pak settings exceed size limit; original preserved");
    std::ifstream input(path,std::ios::binary);std::string text(4097,'\0');input.read(text.data(),text.size());
    if(input.bad())throw std::runtime_error("Cannot read Controller Pak settings");
    text.resize(size_t(input.gcount()));std::set<std::string> keys;
    auto json=nlohmann::json::parse(text,[&](int,nlohmann::json::parse_event_t event,nlohmann::json& value){
        if(event==nlohmann::json::parse_event_t::key&&!keys.insert(value.get<std::string>()).second)throw std::runtime_error("Duplicate Controller Pak setting");
        return true;
    });
    if(!json.is_object()||json.size()!=2||!json.contains("schemaVersion")||!json["schemaVersion"].is_number_integer()||json["schemaVersion"]!=1||!json.contains("ports")||!json["ports"].is_array()||json["ports"].size()!=4)
        throw std::runtime_error("Invalid Controller Pak settings schema; original preserved");
    Choices choices{};
    for(unsigned n=0;n<4;++n){
        if(!json["ports"][n].is_string())throw std::runtime_error("Controller Pak choices must be strings");
        auto option=json["ports"][n].get<std::string>();
        if(option=="none")choices[n]=PakAccessory::None;
        else if(option=="rumble")choices[n]=PakAccessory::Rumble;
        else if(option=="controller")choices[n]=PakAccessory::Controller;
        else throw std::runtime_error("Unknown Controller Pak accessory choice; original preserved");
    }
    return choices;
}
void save_choices(const std::filesystem::path& path,const Choices& choices){
    nlohmann::json json{{"schemaVersion",1},{"ports",nlohmann::json::array()}};
    for(auto option:choices)json["ports"].push_back(name(option));
    std::string text=json.dump(2)+"\n";regular(path);
    static std::atomic_uint64_t serial{};
    auto temporary=path;temporary+=".tmp-"+std::to_string(std::random_device{}())+"-"+std::to_string(serial++);
#ifdef _WIN32
    HANDLE file=CreateFileW(temporary.c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
    if(file==INVALID_HANDLE_VALUE)throw std::runtime_error("Cannot create Controller Pak settings temporary file");
    DWORD count{};bool okay=WriteFile(file,text.data(),DWORD(text.size()),&count,nullptr)&&count==text.size()&&FlushFileBuffers(file);CloseHandle(file);
    if(!okay){DeleteFileW(temporary.c_str());throw std::runtime_error("Cannot synchronize Controller Pak settings");}
    if(!MoveFileExW(temporary.c_str(),path.c_str(),MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH)){DeleteFileW(temporary.c_str());throw std::runtime_error("Cannot publish Controller Pak settings");}
#else
    int file=open(temporary.c_str(),O_WRONLY|O_CREAT|O_EXCL|O_CLOEXEC|O_NOFOLLOW,0600);
    if(file<0)throw std::runtime_error("Cannot create Controller Pak settings temporary file");
    size_t offset=0;bool okay=true;
    while(offset<text.size()){
        auto count=write(file,text.data()+offset,text.size()-offset);
        if(count<0&&errno==EINTR)continue;
        if(count<=0){okay=false;break;}offset+=size_t(count);
    }
    if(okay&&fsync(file))okay=false;
    if(close(file))okay=false;
    if(!okay){unlink(temporary.c_str());throw std::runtime_error("Cannot synchronize Controller Pak settings");}
    if(rename(temporary.c_str(),path.c_str())){unlink(temporary.c_str());throw std::runtime_error("Cannot publish Controller Pak settings");}
    int directory=open(path.parent_path().c_str(),O_RDONLY|O_DIRECTORY|O_CLOEXEC);
    if(directory<0)throw std::runtime_error("Cannot open Controller Pak settings directory for synchronization");
    bool synchronized=fsync(directory)==0;
    int closed=close(directory);
    if(!synchronized||closed)throw std::runtime_error("Cannot synchronize Controller Pak settings directory");
#endif
}
// Guest pointers are zero-extended or genuine sign-extended 32-bit KSEG aliases.
// Canonicalize before using the recompiler macros; no 64-bit upper-bit truncation.
bool region(uint64_t address,uint32_t bytes,uint32_t alignment,gpr& canonical){
    uint32_t low=uint32_t(address),high=uint32_t(address>>32);
    if(high!=0&&!(high==0xFFFFFFFFu&&(low&0x80000000u)))return false;
    if((low&0xE0000000u)!=0x80000000u&&(low&0xE0000000u)!=0xA0000000u)return false;
    uint32_t offset=low&0x1FFFFFFFu;
    if((low&(alignment-1))||offset>0x800000u||bytes>0x800000u-offset)return false;
    canonical=gpr(S32(offset|0x80000000u));return true;
}
bool queue_pointer(recomp_context* ctx){gpr ignored{};return region(ctx->r4,24,4,ignored);}
void read_service(uint8_t* rdram,recomp_context* ctx){
    gpr pointer{};
    if(!rdram||uint32_t(ctx->r5)>=4||!queue_pointer(ctx)||!region(ctx->r7,32,1,pointer)){ctx->r2=5;return;}
    std::lock_guard guard(store_mutex);
    if(!store){ctx->r2=1;return;}
    if(!connected[uint32_t(ctx->r5)]){ctx->r2=4;return;}
    PakBlock block{};int result=store->read_block(uint32_t(ctx->r5),uint16_t(ctx->r6),block);
    if(!result)for(unsigned n=0;n<32;++n)MEM_B(n,pointer)=block[n];
    ctx->r2=gpr(S32(result));
}
void write_service(uint8_t* rdram,recomp_context* ctx){
    gpr pointer{},stack{};
    if(!rdram||uint32_t(ctx->r5)>=4||!queue_pointer(ctx)||!region(ctx->r7,32,1,pointer)||!region(ctx->r29,20,4,stack)){ctx->r2=5;return;}
    std::lock_guard guard(store_mutex);
    if(!store){ctx->r2=1;return;}
    if(!connected[uint32_t(ctx->r5)]){ctx->r2=4;return;}
    PakBlock block{};for(unsigned n=0;n<32;++n)block[n]=MEM_BU(n,pointer);
    ctx->r2=gpr(S32(store->write_block(uint32_t(ctx->r5),uint16_t(ctx->r6),block,MEM_W(16,stack)==1)));
}
void status_service(uint8_t* rdram,recomp_context* ctx){
    if(!rdram){ctx->r2=5;return;}
    // Original 800608AC invalidates __osPfsRWInode's cache on every status request.
    MEM_B(0,gpr(S32(active_guest_addresses().pak_inode_cache)))=0xFA;
    if(uint32_t(ctx->r5)>=4||!queue_pointer(ctx)){ctx->r2=5;return;}
    std::lock_guard guard(store_mutex);
    if(!store){ctx->r2=1;return;}
    unsigned port=uint32_t(ctx->r5);
    connection_observed[port]=true;
    if(!connected[port]){ctx->r2=4;return;}
    int result=store->status(port);
    if(result==2)reconnected[port]=false;
    else if(!result&&reconnected[port]){reconnected[port]=false;result=2;}
    ctx->r2=gpr(S32(result));
}
void plug_service(uint8_t* rdram,recomp_context* ctx){
    gpr pointer{};
    if(!rdram||!queue_pointer(ctx)||!region(ctx->r5,1,1,pointer)){ctx->r2=5;return;}
    std::lock_guard guard(store_mutex);
    uint8_t connection_mask=0;
    for(unsigned port=0;port<4;++port)if(connected[port])connection_mask|=uint8_t(1u<<port);
    MEM_B(0,pointer)=store?(store->plugged_mask()&connection_mask):0;ctx->r2=0;
}
}
void configure_paks(const std::filesystem::path& directory){
    std::lock_guard guard(store_mutex);
    if(store)throw std::runtime_error("Controller Pak storage is already initialized");
    auto path=directory/"controller-paks.json";auto choices=load_choices(path);
    auto candidate=std::make_unique<ControllerPakStore>(directory);
    for(unsigned n=0;n<4;++n)candidate->set_accessory(n,choices[n]);
    if(!std::filesystem::exists(path))save_choices(path,choices);
    settings_path=path;connected={true,false,false,false};reconnected={};connection_observed={};store=std::move(candidate);
}
void shutdown_paks(){std::lock_guard guard(store_mutex);store.reset();settings_path.clear();}
PakAccessory pak_accessory(int port){
    std::lock_guard guard(store_mutex);if(!store||port<0||port>=4)return PakAccessory::None;
    return store->accessory(unsigned(port));
}
void set_pak_port_connected(unsigned port,bool is_connected){
    if(port>=4)throw std::out_of_range("Controller Pak port");
    std::lock_guard guard(store_mutex);
    // The first startup snapshot is stable; subsequent reconnections are changes.
    if(connection_observed[port]&&is_connected&&!connected[port])reconnected[port]=true;
    connected[port]=is_connected;connection_observed[port]=true;
}
void set_pak_accessory(unsigned port,PakAccessory accessory){
    if(port>=4)throw std::out_of_range("Controller Pak port");
    name(accessory);
    std::lock_guard guard(store_mutex);if(!store)throw std::runtime_error("Controller Pak storage is not initialized");
    Choices choices{};for(unsigned n=0;n<4;++n)choices[n]=store->accessory(n);choices[port]=accessory;
    save_choices(settings_path,choices);store->set_accessory(port,accessory);
}
recomp_func_t* pak_service_lookup(uint32_t address){
    const auto& guest=active_guest_addresses();
    if(address==guest.pak_read)return &read_service;
    if(address==guest.pak_write)return &write_service;
    if(address==guest.pak_status)return &status_service;
    if(address==guest.pak_plug)return &plug_service;
    return nullptr;
}
std::string pak_storage_error(){std::lock_guard guard(store_mutex);return store?store->last_error():std::string{};}
}
