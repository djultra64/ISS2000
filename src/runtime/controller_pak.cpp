// Original project work: djultra64.
#include "controller_pak.hpp"
#include <algorithm>
#include <atomic>
#include <fstream>
#include <mutex>
#include <thread>
#include <random>
#include <stdexcept>
#include <system_error>
#ifdef _WIN32
#define NOMINMAX
#include <windows.h>
#else
#include <cerrno>
#include <fcntl.h>
#include <sys/file.h>
#include <unistd.h>
#endif
namespace iss2000 {
namespace {
void put16(PakImage& image,unsigned offset,uint16_t value){image[offset]=uint8_t(value>>8);image[offset+1]=uint8_t(value);}
void regular_or_absent(const std::filesystem::path& path){
    auto type=std::filesystem::symlink_status(path).type();
    if(type!=std::filesystem::file_type::not_found && type!=std::filesystem::file_type::regular)
        throw std::runtime_error("Controller Pak storage target is not a regular file");
}
PakImage read_image(const std::filesystem::path& path){
    regular_or_absent(path);
    if(std::filesystem::file_size(path)!=32768)throw std::runtime_error("Controller Pak image must be exactly 32768 bytes; original preserved: "+path.string());
    PakImage image{};std::ifstream file(path,std::ios::binary);file.read(reinterpret_cast<char*>(image.data()),image.size());
    if(!file)throw std::runtime_error("Cannot read Controller Pak image");
    return image;
}
class DirectoryLock {
#ifdef _WIN32
    HANDLE handle_=INVALID_HANDLE_VALUE;
#else
    int handle_=-1;
#endif
public:
    explicit DirectoryLock(const std::filesystem::path& path){
        regular_or_absent(path);
#ifdef _WIN32
        handle_=CreateFileW(path.c_str(),GENERIC_READ|GENERIC_WRITE,0,nullptr,OPEN_ALWAYS,FILE_ATTRIBUTE_NORMAL,nullptr);
        if(handle_==INVALID_HANDLE_VALUE)throw std::runtime_error("Controller Pak storage is locked by another process");
#else
        handle_=open(path.c_str(),O_RDWR|O_CREAT|O_CLOEXEC|O_NOFOLLOW,0600);
        if(handle_<0)throw std::runtime_error("Cannot open Controller Pak process lock");
        if(flock(handle_,LOCK_EX|LOCK_NB)){close(handle_);handle_=-1;throw std::runtime_error("Controller Pak storage is locked by another process");}
#endif
    }
    ~DirectoryLock(){
#ifdef _WIN32
        if(handle_!=INVALID_HANDLE_VALUE)CloseHandle(handle_);
#else
        if(handle_>=0){flock(handle_,LOCK_UN);close(handle_);}
#endif
    }
};
std::atomic_uint64_t sequence{};
void publish(const std::filesystem::path& destination,const PakImage& image,bool replace){
    regular_or_absent(destination);
    std::random_device entropy;
    auto temp=destination;temp+=".tmp-"+std::to_string(entropy())+"-"+std::to_string(sequence++);
#ifdef _WIN32
    HANDLE file=CreateFileW(temp.c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
    if(file==INVALID_HANDLE_VALUE)throw std::runtime_error("Cannot create temporary Controller Pak image");
    DWORD written{};bool okay=WriteFile(file,image.data(),DWORD(image.size()),&written,nullptr)&&written==image.size()&&FlushFileBuffers(file);
    CloseHandle(file);
    if(!okay){DeleteFileW(temp.c_str());throw std::runtime_error("Cannot synchronize Controller Pak image");}
    if(!MoveFileExW(temp.c_str(),destination.c_str(),MOVEFILE_WRITE_THROUGH|(replace?MOVEFILE_REPLACE_EXISTING:0))){DeleteFileW(temp.c_str());throw std::runtime_error("Cannot atomically publish Controller Pak image");}
#else
    int file=open(temp.c_str(),O_WRONLY|O_CREAT|O_EXCL|O_CLOEXEC|O_NOFOLLOW,0600);
    if(file<0)throw std::runtime_error("Cannot create temporary Controller Pak image");
    size_t offset=0;bool okay=true;
    while(offset<image.size()){
        auto n=write(file,image.data()+offset,image.size()-offset);
        if(n<0&&errno==EINTR)continue;
        if(n<=0){okay=false;break;}offset+=size_t(n);
    }
    if(okay&&fsync(file))okay=false;
    if(close(file))okay=false;
    if(!okay){unlink(temp.c_str());throw std::runtime_error("Cannot synchronize Controller Pak image");}
    int result=replace?rename(temp.c_str(),destination.c_str()):link(temp.c_str(),destination.c_str());
    if(!replace || result)unlink(temp.c_str());
    if(result)throw std::runtime_error("Cannot atomically publish Controller Pak image");
    int directory=open(destination.parent_path().c_str(),O_RDONLY|O_DIRECTORY|O_CLOEXEC);
    if(directory<0)throw std::runtime_error("Cannot open Controller Pak directory for synchronization");
    int synced=fsync(directory);close(directory);
    if(synced)throw std::runtime_error("Cannot synchronize Controller Pak directory");
#endif
}
}
PakImage formatted_controller_pak(const std::array<uint8_t,24>& identity){
    PakImage image{};
    std::copy(identity.begin(),identity.end(),image.begin()+0x20);
    // __osIdCheckSum80060B34 sums the first 14 big-endian halfwords and their
    // complements. Device ID bit 0 and bank count derive from InitPak60550.
    put16(image,0x38,1);image[0x3A]=1;image[0x3B]=0;
    uint16_t sum=0,inverse=0;
    for(unsigned i=0x20;i<0x3C;i+=2){auto value=uint16_t((image[i]<<8)|image[i+1]);sum=uint16_t(sum+value);inverse=uint16_t(inverse+uint16_t(~value));}
    put16(image,0x3C,sum);put16(image,0x3E,inverse);
    for(unsigned offset:{0x60u,0x80u,0xC0u})std::copy_n(image.begin()+0x20,32,image.begin()+offset);
    // One bank: 128 pages, first five reserved. __osPfsRWInode6124C checksum is the
    // low byte of the sum of bytes covering entries 5..127; free marker is 0003.
    for(unsigned offset:{0x100u,0x200u}){
        for(unsigned page=5;page<128;++page)put16(image,offset+page*2,3);
        image[offset+1]=uint8_t(123*3);
    }
    // Empty 16-note directory spans pages 3 and 4. User data starts page 5.
    return image;
}
struct ControllerPakStore::State {
    std::filesystem::path directory;
    DirectoryLock lock;
    mutable std::mutex mutex;
    std::array<PakImage,4> images{};
    struct Transaction {PakImage original;std::thread::id thread;};
    std::array<std::unique_ptr<Transaction>,4> transactions{};
    std::array<PakAccessory,4> accessories{};
    std::array<bool,4> configured{},changed{};
    std::string error;
    explicit State(const std::filesystem::path& path):directory(path),lock(path/"controller-pak.lock"){}
    std::filesystem::path path(unsigned port)const{return directory/("controller-pak-"+std::to_string(port+1)+".mpk");}
    int check(unsigned port)const{
        if(port>=4)return 5;
        if(accessories[port]==PakAccessory::None)return 1;
        if(accessories[port]!=PakAccessory::Controller)return 11;
        return 0;
    }
};
ControllerPakStore::ControllerPakStore(const std::filesystem::path& directory){
    std::filesystem::create_directories(directory);
    state_=std::make_unique<State>(directory);
    // Check all preexisting inputs before creating or backing up any other image.
    for(unsigned n=0;n<4;++n){regular_or_absent(state_->path(n));if(std::filesystem::exists(state_->path(n)))state_->images[n]=read_image(state_->path(n));}
    for(unsigned n=0;n<4;++n){
        auto path=state_->path(n);
        if(std::filesystem::exists(path)){
            // Immutable startup snapshot preserves even corrupt 32768-byte imports
            // before the original SDK performs any repair writes.
            unsigned count=0;std::filesystem::path snapshot;
            do{snapshot=path;snapshot+=".preserved-"+std::to_string(count++);}while(std::filesystem::exists(snapshot));
            publish(snapshot,state_->images[n],false);
        }else{
            std::random_device random;std::array<uint8_t,24> identity{};for(auto& byte:identity)byte=uint8_t(random());
            state_->images[n]=formatted_controller_pak(identity);publish(path,state_->images[n],false);
        }
    }
}
ControllerPakStore::~ControllerPakStore()=default;
void ControllerPakStore::set_accessory(unsigned port,PakAccessory accessory){
    if(port>=4)throw std::out_of_range("Controller Pak port");
    std::lock_guard guard(state_->mutex);
    if(state_->configured[port]&&state_->accessories[port]!=accessory)state_->changed[port]=true;
    state_->accessories[port]=accessory;state_->configured[port]=true;
}
PakAccessory ControllerPakStore::accessory(unsigned port)const{
    if(port>=4)throw std::out_of_range("Controller Pak port");
    std::lock_guard guard(state_->mutex);return state_->accessories[port];
}
int ControllerPakStore::status(unsigned port){
    std::lock_guard guard(state_->mutex);int result=state_->check(port);
    // __osPfsGetStatus tests accessory presence, not its filesystem type.
    if(result&&result!=11)return result;
    if(state_->changed[port]){state_->changed[port]=false;return 2;}return 0;
}
uint8_t ControllerPakStore::plugged_mask()const{
    std::lock_guard guard(state_->mutex);uint8_t mask=0;
    for(unsigned n=0;n<4;++n)if(state_->accessories[n]!=PakAccessory::None)mask|=uint8_t(1u<<n);
    return mask;
}
int ControllerPakStore::read_block(unsigned port,uint16_t block,PakBlock& output){
    std::lock_guard guard(state_->mutex);int result=state_->check(port);if(result)return result;
    if(block>=1024)return 5;
    if(state_->transactions[port]&&state_->transactions[port]->thread!=std::this_thread::get_id())return 4;
    std::copy_n(state_->images[port].begin()+unsigned(block)*32,32,output.begin());return 0;
}
int ControllerPakStore::write_block(unsigned port,uint16_t block,const PakBlock& input,bool force){
    std::lock_guard guard(state_->mutex);int result=state_->check(port);if(result)return result;
    if(state_->transactions[port]&&state_->transactions[port]->thread!=std::this_thread::get_id())return 4;
    // Original __osPfsSelectBank 80060A90 sends 32 identical bank bytes to block 400.
    // This backend implements a single real 32 KiB bank, never aliases other banks.
    if(block==0x400)return std::all_of(input.begin(),input.end(),[](uint8_t value){return value==0;})?0:11;
    if(block>=1024)return 5;
    // Original __osContRamWrite61780 protects ID blocks 1..6 unless force == 1.
    if(block>0&&block<7&&!force)return 0;
    auto next=state_->images[port];std::copy(input.begin(),input.end(),next.begin()+unsigned(block)*32);
    if(state_->transactions[port]){state_->images[port]=next;return 0;}
    try{
        auto path=state_->path(port);
        if(read_image(path)!=state_->images[port])throw std::runtime_error("Controller Pak image changed outside the locked process; write refused");
        if(next==state_->images[port])return 0;
        auto backup=path;backup+=".bak";
        publish(backup,state_->images[port],true);
        publish(path,next,true);
        state_->images[port]=next;state_->error.clear();return 0;
    }catch(const std::exception& error){state_->error=error.what();return 4;}
}
int ControllerPakStore::begin_file_write(unsigned port){
    std::lock_guard guard(state_->mutex);const auto result=state_->check(port);if(result)return result;
    if(state_->transactions[port])return 4;
    try{
        if(read_image(state_->path(port))!=state_->images[port])throw std::runtime_error("Save image changed outside the locked process; write refused");
        state_->transactions[port]=std::make_unique<State::Transaction>(State::Transaction{state_->images[port],std::this_thread::get_id()});return 0;
    }catch(const std::exception&e){state_->error=e.what();return 4;}
}
int ControllerPakStore::finish_file_write(unsigned port,bool commit){
    std::lock_guard guard(state_->mutex);if(port>=4||!state_->transactions[port])return 5;
    if(state_->transactions[port]->thread!=std::this_thread::get_id())return 4;
    auto transaction=std::move(state_->transactions[port]);
    const auto next=state_->images[port];state_->images[port]=transaction->original;
    if(!commit)return 0;
    if(const auto result=state_->check(port))return result;
    try{
        auto path=state_->path(port);
        if(read_image(path)!=transaction->original)throw std::runtime_error("Save image changed outside the locked process; commit refused");
        if(next!=transaction->original){auto backup=path;backup+=".bak";publish(backup,transaction->original,true);publish(path,next,true);}
        state_->images[port]=next;state_->error.clear();return 0;
    }catch(const std::exception&e){state_->error=e.what();return 4;}
}
std::filesystem::path ControllerPakStore::image_path(unsigned port)const{
    if(port>=4)throw std::out_of_range("Controller Pak port");
    return state_->path(port);
}
std::string ControllerPakStore::last_error()const{std::lock_guard guard(state_->mutex);return state_->error;}
}
