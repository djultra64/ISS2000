// Original project work: djultra64.
#include "input_preferences.hpp"
#include "json/json.hpp"
#include <atomic>
#include <fstream>
#include <random>
#include <set>
#include <stdexcept>
#include <vector>
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
using Json=nlohmann::json;
constexpr size_t limit=16384;
const char* family_name(platform::Family family){
    switch(family){case platform::Family::Automatic:return "auto";case platform::Family::Xbox:return "xbox";case platform::Family::PlayStation:return "playstation";case platform::Family::Nintendo:return "switch";default:throw std::invalid_argument("Invalid manual controller family");}
}
void validate(const InputPreferences& preferences){
    for(const auto& port:preferences.ports){
        family_name(port.manual_family);
        for(auto button:port.bindings)if(int(button)<-1||button>=SDL_CONTROLLER_BUTTON_MAX)throw std::invalid_argument("Invalid controller button mapping");
    }
}
void target(const std::filesystem::path& path){
    auto type=std::filesystem::symlink_status(path).type();
    if(type!=std::filesystem::file_type::not_found&&type!=std::filesystem::file_type::regular)throw std::runtime_error("Input preferences must be a regular file");
}
void publish(const std::filesystem::path& path,std::string_view text){
    static std::atomic_uint64_t sequence{};auto temporary=path;
    temporary+=".tmp-"+std::to_string(std::random_device{}())+"-"+std::to_string(sequence++);
#ifdef _WIN32
    HANDLE file=CreateFileW(temporary.c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
    if(file==INVALID_HANDLE_VALUE)throw std::runtime_error("Cannot create input preferences temporary file");
    DWORD count{};bool okay=WriteFile(file,text.data(),DWORD(text.size()),&count,nullptr)&&count==text.size()&&FlushFileBuffers(file);CloseHandle(file);
    if(!okay){DeleteFileW(temporary.c_str());throw std::runtime_error("Cannot synchronize input preferences");}
    if(!MoveFileExW(temporary.c_str(),path.c_str(),MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH)){DeleteFileW(temporary.c_str());throw std::runtime_error("Cannot publish input preferences");}
#else
    int file=open(temporary.c_str(),O_WRONLY|O_CREAT|O_EXCL|O_CLOEXEC|O_NOFOLLOW,0600);
    if(file<0)throw std::runtime_error("Cannot create input preferences temporary file");
    size_t offset=0;bool okay=true;
    while(offset<text.size()){
        auto count=write(file,text.data()+offset,text.size()-offset);if(count<0&&errno==EINTR)continue;
        if(count<=0){okay=false;break;}offset+=size_t(count);
    }
    if(okay&&fsync(file))okay=false;
    if(close(file))okay=false;
    if(!okay){unlink(temporary.c_str());throw std::runtime_error("Cannot synchronize input preferences");}
    if(rename(temporary.c_str(),path.c_str())){unlink(temporary.c_str());throw std::runtime_error("Cannot publish input preferences");}
    int directory=open(path.parent_path().c_str(),O_RDONLY|O_DIRECTORY|O_CLOEXEC);
    if(directory<0)throw std::runtime_error("Cannot open input preferences directory for synchronization");
    bool synced=fsync(directory)==0;int closed=close(directory);
    if(!synced||closed)throw std::runtime_error("Cannot synchronize input preferences directory");
#endif
}
}
InputPreferences default_input_preferences(){return {};}
InputPreferences parse_input_preferences(std::string_view text){
    if(text.size()>limit)throw std::runtime_error("Input preferences exceed size limit");
    std::vector<std::set<std::string>> keys;
    auto json=Json::parse(text.begin(),text.end(),[&](int,Json::parse_event_t event,Json& value){
        if(event==Json::parse_event_t::object_start)keys.emplace_back();
        if(event==Json::parse_event_t::key&&!keys.back().insert(value.get<std::string>()).second)throw std::runtime_error("Duplicate input preferences key");
        if(event==Json::parse_event_t::object_end)keys.pop_back();
        return true;
    });
    if(!json.is_object()||json.size()!=2||!json.contains("schemaVersion")||!json["schemaVersion"].is_number_integer()||json["schemaVersion"]!=1||!json.contains("ports")||!json["ports"].is_array()||json["ports"].size()!=4)throw std::runtime_error("Invalid input preferences schema");
    InputPreferences preferences;
    for(unsigned i=0;i<4;++i){
        const auto& port=json["ports"][i];
        if(!port.is_object()||port.size()!=2||!port.contains("manualFamily")||!port["manualFamily"].is_string()||!port.contains("buttons")||!port["buttons"].is_array()||port["buttons"].size()!=size_t(platform::Action::Count))throw std::runtime_error("Invalid controller preferences");
        auto family=port["manualFamily"].get<std::string>();
        if(family=="auto")preferences.ports[i].manual_family=platform::Family::Automatic;
        else if(family=="xbox")preferences.ports[i].manual_family=platform::Family::Xbox;
        else if(family=="playstation")preferences.ports[i].manual_family=platform::Family::PlayStation;
        else if(family=="switch")preferences.ports[i].manual_family=platform::Family::Nintendo;
        else throw std::runtime_error("Unknown manual controller family");
        for(unsigned action=0;action<size_t(platform::Action::Count);++action){
            const auto& value=port["buttons"][action];
            if(!value.is_number_integer()||value<-1||value>=SDL_CONTROLLER_BUTTON_MAX)throw std::runtime_error("Invalid controller button mapping");
            preferences.ports[i].bindings[action]=SDL_GameControllerButton(value.get<int>());
        }
    }
    return preferences;
}
std::string serialize_input_preferences(const InputPreferences& preferences){
    validate(preferences);Json json{{"schemaVersion",1},{"ports",Json::array()}};
    for(const auto& port:preferences.ports){Json buttons=Json::array();for(auto button:port.bindings)buttons.push_back(int(button));json["ports"].push_back({{"manualFamily",family_name(port.manual_family)},{"buttons",buttons}});}
    return json.dump(2)+"\n";
}
InputPreferences load_input_preferences(const std::filesystem::path& data){
    auto path=data/"input-preferences.json";target(path);if(!std::filesystem::exists(path))return {};
    if(std::filesystem::file_size(path)>limit)throw std::runtime_error("Input preferences exceed size limit");
    std::ifstream input(path,std::ios::binary);std::string text(limit+1,'\0');input.read(text.data(),text.size());
    if(input.bad())throw std::runtime_error("Cannot read input preferences");
    text.resize(size_t(input.gcount()));return parse_input_preferences(text);
}
void save_input_preferences(const std::filesystem::path& data,const InputPreferences& preferences){
    auto text=serialize_input_preferences(preferences);(void)load_input_preferences(data);
    publish(data/"input-preferences.json",text);
}
InputPreferences capture_input_preferences(){return {platform::port_preferences()};}
void apply_input_preferences(const InputPreferences& preferences){validate(preferences);platform::apply_port_preferences(preferences.ports);}
}
