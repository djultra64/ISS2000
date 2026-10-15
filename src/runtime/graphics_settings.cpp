// Original project work: djultra64.
#include "graphics_settings.hpp"
#include <atomic>
#include <cerrno>
#include <fstream>
#include <set>
#include <stdexcept>
#include "json/json.hpp"
#ifdef _WIN32
#define NOMINMAX
#include <windows.h>
#else
#include <fcntl.h>
#include <unistd.h>
#endif
namespace iss2000 {
namespace {
using Json=nlohmann::json;
constexpr std::size_t max_size=65536;
[[noreturn]] void fail(const char* message){throw std::runtime_error(message);}
const char* aspect_name(AspectRatio a){switch(a){case AspectRatio::Original4x3:return "4:3";case AspectRatio::Wide16x9:return "16:9";}fail("Invalid aspect ratio");}
const char* resolution_name(RenderResolution a){switch(a){case RenderResolution::Original:return "Original";case RenderResolution::P720:return "720";case RenderResolution::P900:return "900";case RenderResolution::P1080:return "1080";case RenderResolution::P1440:return "1440";case RenderResolution::P1800:return "1800";case RenderResolution::P2160:return "2160";}fail("Invalid resolution");}
const char* refresh_name(RenderRefresh a){switch(a){case RenderRefresh::Original:return "Original";case RenderRefresh::Hz60:return "60";case RenderRefresh::Hz120:return "120";}fail("Invalid refresh rate");}
std::filesystem::path checked_folder(const std::filesystem::path& input){
 auto folder=std::filesystem::absolute(input).lexically_normal();
 std::filesystem::path part;
 for(const auto& component:folder){part/=component;auto status=std::filesystem::symlink_status(part);
  if(std::filesystem::is_symlink(status))fail("Graphics data folder must not contain symlinks");
  if(!std::filesystem::is_directory(status))fail("Graphics data folder must exist");
 }
 return folder;
}
bool checked_target(const std::filesystem::path& target){
 std::error_code error;auto status=std::filesystem::symlink_status(target,error);
 if(error && error!=std::errc::no_such_file_or_directory)throw std::filesystem::filesystem_error("Inspect graphics settings",target,error);
 if(status.type()==std::filesystem::file_type::not_found)return false;
 if(!std::filesystem::is_regular_file(status))fail("Graphics settings must be a regular file, not a symlink or directory");
 return true;
}
void atomic_save(const std::filesystem::path& folder,std::string_view text){
 auto destination=folder/"graphics.json";checked_target(destination);
 static std::atomic<unsigned long long> sequence{0};
 std::filesystem::path temporary;
#ifdef _WIN32
 HANDLE file=INVALID_HANDLE_VALUE;
 for(int attempt=0;attempt<128;++attempt){
  temporary=folder/(".graphics.json.tmp."+std::to_string(GetCurrentProcessId())+"."+std::to_string(sequence++));
  file=CreateFileW(temporary.c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
  if(file!=INVALID_HANDLE_VALUE)break;
  if(GetLastError()!=ERROR_FILE_EXISTS && GetLastError()!=ERROR_ALREADY_EXISTS)fail("Create graphics settings temporary file failed");
 }
 if(file==INVALID_HANDLE_VALUE)fail("No free graphics settings temporary filename");
 try{
  DWORD written=0;
  if(!WriteFile(file,text.data(),static_cast<DWORD>(text.size()),&written,nullptr)||written!=text.size()||!FlushFileBuffers(file))fail("Write graphics settings failed");
  CloseHandle(file);file=INVALID_HANDLE_VALUE;
  checked_target(destination);
  if(!MoveFileExW(temporary.c_str(),destination.c_str(),MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH))fail("Publish graphics settings failed");
 }catch(...){if(file!=INVALID_HANDLE_VALUE)CloseHandle(file);DeleteFileW(temporary.c_str());throw;}
#else
 int file=-1;
 for(int attempt=0;attempt<128;++attempt){
  temporary=folder/(".graphics.json.tmp."+std::to_string(getpid())+"."+std::to_string(sequence++));
  file=open(temporary.c_str(),O_CREAT|O_EXCL|O_WRONLY|O_CLOEXEC|O_NOFOLLOW,0600);
  if(file>=0)break;
  if(errno!=EEXIST)fail("Create graphics settings temporary file failed");
 }
 if(file<0)fail("No free graphics settings temporary filename");
 try{
  std::size_t offset=0;
  while(offset<text.size()){
   auto count=write(file,text.data()+offset,text.size()-offset);
   if(count<0 && errno==EINTR)continue;
   if(count<=0)fail("Write graphics settings failed");
   offset+=static_cast<std::size_t>(count);
  }
  if(fsync(file)!=0)fail("Flush graphics settings failed");
  if(close(file)!=0){file=-1;fail("Close graphics settings failed");}file=-1;
  checked_target(destination);
  std::filesystem::rename(temporary,destination);
 }catch(...){if(file>=0)close(file);std::error_code ignored;std::filesystem::remove(temporary,ignored);throw;}
#endif
}
}
GraphicsSettings parse_graphics_settings(std::string_view text){
 if(text.size()>max_size)fail("Graphics settings exceed size limit");
 std::set<std::string> keys;
 auto parsed=Json::parse(text.begin(),text.end(),[&](int,Json::parse_event_t event,Json& value){
  if(event==Json::parse_event_t::key && !keys.insert(value.get<std::string>()).second)fail("Duplicate graphics settings key");
  return true;
 });
 if(!parsed.is_object()||parsed.size()!=4||!parsed.contains("schemaVersion")||!parsed.contains("aspectRatio")||!parsed.contains("resolution")||!parsed.contains("refreshRate"))fail("Invalid graphics settings schema");
 if(!parsed["schemaVersion"].is_number_integer()||parsed["schemaVersion"]!=1)fail("Unsupported graphics settings schema version");
 for(const char* key:{"aspectRatio","resolution","refreshRate"})if(!parsed[key].is_string())fail("Graphics settings options must be strings");
 GraphicsSettings result;
 auto a=parsed["aspectRatio"].get<std::string>();
 if(a=="4:3")result.aspect_ratio=AspectRatio::Original4x3;else if(a=="16:9")result.aspect_ratio=AspectRatio::Wide16x9;else fail("Unsupported aspect ratio");
 auto r=parsed["resolution"].get<std::string>();
 if(r=="Original")result.resolution=RenderResolution::Original;else if(r=="720")result.resolution=RenderResolution::P720;else if(r=="900")result.resolution=RenderResolution::P900;else if(r=="1080")result.resolution=RenderResolution::P1080;else if(r=="1440")result.resolution=RenderResolution::P1440;else if(r=="1800")result.resolution=RenderResolution::P1800;else if(r=="2160")result.resolution=RenderResolution::P2160;else fail("Unsupported resolution");
 auto f=parsed["refreshRate"].get<std::string>();
 if(f=="Original")result.refresh_rate=RenderRefresh::Original;else if(f=="60")result.refresh_rate=RenderRefresh::Hz60;else if(f=="120")result.refresh_rate=RenderRefresh::Hz120;else fail("Unsupported refresh rate");
 return result;
}
std::string serialize_graphics_settings(const GraphicsSettings& s){
 return Json{{"schemaVersion",1},{"aspectRatio",aspect_name(s.aspect_ratio)},{"resolution",resolution_name(s.resolution)},{"refreshRate",refresh_name(s.refresh_rate)}}.dump(2)+"\n";
}
GraphicsSettings load_graphics_settings(const std::filesystem::path& data_folder){
 auto path=checked_folder(data_folder)/"graphics.json";
 if(!checked_target(path))return {};
 if(std::filesystem::file_size(path)>max_size)fail("Graphics settings exceed size limit");
 std::ifstream input(path,std::ios::binary);if(!input)fail("Read graphics settings failed");
 std::string text(max_size+1,'\0');input.read(text.data(),text.size());auto count=input.gcount();
 if(input.bad())fail("Read graphics settings failed");
 text.resize(static_cast<std::size_t>(count));
 return parse_graphics_settings(text);
}
void save_graphics_settings(const std::filesystem::path& folder,const GraphicsSettings& s){
 auto text=serialize_graphics_settings(s);atomic_save(checked_folder(folder),text);
}
std::uint32_t target_height(const GraphicsSettings& s){
 switch(s.resolution){
 case RenderResolution::Original:return 0;
 case RenderResolution::P720:return 720;
 case RenderResolution::P900:return 900;
 case RenderResolution::P1080:return 1080;
 case RenderResolution::P1440:return 1440;
 case RenderResolution::P1800:return 1800;
 case RenderResolution::P2160:return 2160;
 }
 fail("Invalid resolution");
}
std::string resolution_label(const GraphicsSettings& s){
 const auto height=target_height(s);
 // Validate the aspect even for Original, as serialization does.
 aspect_name(s.aspect_ratio);
 if(!height)return "Original";
 const auto width=s.aspect_ratio==AspectRatio::Wide16x9?height*16/9:height*4/3;
 return std::to_string(height)+"p ("+std::to_string(width)+" x "+std::to_string(height)+")";
}
double resolution_multiplier(const GraphicsSettings& s){return resolution_multiplier(s,240);}
double resolution_multiplier(const GraphicsSettings& s,std::uint32_t native_height){
 const auto target=target_height(s);
 return target?static_cast<double>(target)/(native_height?native_height:240):1.;
}
}
