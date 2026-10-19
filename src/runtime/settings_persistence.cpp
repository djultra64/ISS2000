// Original project work: djultra64.
#include "runtime/settings_persistence.hpp"
#include <array>
#include <atomic>
#include <exception>
#include <random>
#include <stdexcept>
#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#else
#include <cerrno>
#include <cstdio>
#include <fcntl.h>
#include <unistd.h>
#endif
namespace iss2000 { namespace {
void publish(const std::filesystem::path& from,const std::filesystem::path& to){
#ifdef _WIN32
 if(!MoveFileExW(from.c_str(),to.c_str(),MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH))
  throw std::runtime_error("Cannot publish PC Settings file");
#else
 if(::rename(from.c_str(),to.c_str()))
  throw std::runtime_error("Cannot publish PC Settings file");
#endif
}
void sync_folder(const std::filesystem::path& folder){
#ifndef _WIN32
 int fd=open(folder.c_str(),O_RDONLY|O_DIRECTORY|O_CLOEXEC);
 if(fd<0)throw std::runtime_error("Cannot open PC Settings directory for synchronization");
 const bool synced=fsync(fd)==0;const int closed=close(fd);
 if(!synced||closed)throw std::runtime_error("Cannot synchronize PC Settings directory");
#else
 (void)folder; // Each MoveFileExW above requests WRITE_THROUGH.
#endif
}
}
void save_game_preferences(const std::filesystem::path& folder,
                           const GraphicsSettings& graphics,
                           const InputPreferences& preferences){
 // Keep existing validation, including malformed data and symlink rejection,
 // before staging or changing either target.
 (void)load_graphics_settings(folder);
 (void)load_input_preferences(folder);
 static std::atomic_uint64_t sequence{};
 std::filesystem::path stage;
 for(unsigned n=0;n<128;++n){
  stage=folder/(".pc-settings.transaction."+std::to_string(std::random_device{}())+"."+std::to_string(sequence++));
  if(std::filesystem::create_directory(stage))break;
  if(n==127)throw std::runtime_error("Cannot create PC Settings staging directory");
 }
 const std::array<const char*,2> names{"graphics.json","input-preferences.json"};
 std::array<bool,2> backed_up{},published{};
 try{
  save_graphics_settings(stage,graphics);
  save_input_preferences(stage,preferences);
  for(unsigned n=0;n<names.size();++n){
   const auto target=folder/names[n],backup=stage/(std::string("previous-")+names[n]);
   if(std::filesystem::exists(target)){publish(target,backup);backed_up[n]=true;}
   publish(stage/names[n],target);published[n]=true;
  }
  sync_folder(folder);
 }catch(...){
  const auto failure=std::current_exception();
  try{
   for(unsigned n=names.size();n-->0;){
    const auto target=folder/names[n];
    if(backed_up[n])publish(stage/(std::string("previous-")+names[n]),target);
    else if(published[n])std::filesystem::remove(target);
   }
   sync_folder(folder);
  }catch(...){
   // Do not erase old files when recovery itself fails. The next manual repair
   // can recover the original bytes from the retained private directory.
   throw std::runtime_error("PC Settings rollback failed; previous files preserved in "+stage.string());
  }
  std::error_code ignored;std::filesystem::remove_all(stage,ignored);
  std::rethrow_exception(failure);
 }
 std::error_code ignored;std::filesystem::remove_all(stage,ignored);
}
}
