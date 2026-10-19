// Original project work: djultra64.
#include "test_controller.hpp"
#if defined(ISS2000_ENABLE_INPUT_TESTING) && ISS2000_ENABLE_INPUT_TESTING
#include <SDL.h>
#include <array>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>
namespace iss2000::test_controller {
namespace {
std::filesystem::path snapshot_path;
SDL_Joystick* joystick{};
SDL_JoystickID instance=-1;
std::string previous_error;
struct Snapshot {bool start{},a{},b{},x{},y{},l1{},r1{},l2{},r2{},up{},down{},left{},right{};bool dpad_up{},dpad_down{},dpad_left{},dpad_right{};};
void report(const char* error){
 if(previous_error!=error){SDL_LogWarn(SDL_LOG_CATEGORY_APPLICATION,"ISS2000 input test fixture: %s",error);previous_error=error;}
}
bool read_snapshot(Snapshot& snapshot){
 std::error_code error;auto status=std::filesystem::symlink_status(snapshot_path,error);
 if(error || !std::filesystem::is_regular_file(status)){report("snapshot missing or not a regular file; controls released");return false;}
 std::ifstream input(snapshot_path,std::ios::binary);if(!input){report("snapshot cannot be read; controls released");return false;}
 std::array<char,256> bytes{};input.read(bytes.data(),bytes.size());
 if(input.bad() || input.gcount()>=static_cast<std::streamsize>(bytes.size())){report("snapshot exceeds 255 bytes or read failed; controls released");return false;}
 std::istringstream tokens(std::string(bytes.data(),static_cast<std::size_t>(input.gcount())));
 std::string token;
 while(tokens>>token){
  if(token=="start")snapshot.start=true;
  else if(token=="a")snapshot.a=true;
  else if(token=="b")snapshot.b=true;
  else if(token=="x")snapshot.x=true;
  else if(token=="y")snapshot.y=true;
  else if(token=="l1")snapshot.l1=true;
  else if(token=="r1")snapshot.r1=true;
  else if(token=="l2")snapshot.l2=true;
  else if(token=="r2")snapshot.r2=true;
  else if(token=="up")snapshot.up=true;
  else if(token=="down")snapshot.down=true;
  else if(token=="left")snapshot.left=true;
  else if(token=="right")snapshot.right=true;
  else if(token=="dpad_up")snapshot.dpad_up=true;
  else if(token=="dpad_down")snapshot.dpad_down=true;
  else if(token=="dpad_left")snapshot.dpad_left=true;
  else if(token=="dpad_right")snapshot.dpad_right=true;
  else {report("invalid snapshot token; controls released");return false;}
 }
 previous_error.clear();return true;
}
}
std::int32_t device_instance(){return joystick?instance:-1;}
void initialize(){
 if(joystick)return;
 const char* path=SDL_getenv("ISS2000_TEST_CONTROLLER");if(!path || !*path)return;
 try{
  snapshot_path=std::filesystem::path(std::u8string(reinterpret_cast<const char8_t*>(path)));
  if(!snapshot_path.is_absolute()){report("snapshot path must be absolute; fixture disabled");snapshot_path.clear();return;}
  SDL_VirtualJoystickDesc desc{};
  desc.version=SDL_VIRTUAL_JOYSTICK_DESC_VERSION;desc.type=SDL_JOYSTICK_TYPE_GAMECONTROLLER;
  desc.naxes=SDL_CONTROLLER_AXIS_MAX;desc.nbuttons=SDL_CONTROLLER_BUTTON_MAX;
  desc.axis_mask=(1u<<SDL_CONTROLLER_AXIS_MAX)-1;
  desc.button_mask=(1u<<SDL_CONTROLLER_BUTTON_MAX)-1;
  desc.name="ISS2000 app-only test controller";
  int device=SDL_JoystickAttachVirtualEx(&desc);
  if(device<0){report("SDL virtual controller attach failed; fixture disabled");return;}
  joystick=SDL_JoystickOpen(device);
  if(!joystick){SDL_JoystickDetachVirtual(device);report("SDL virtual controller open failed; fixture disabled");return;}
  // Virtual triggers use the full signed raw axis; -32768 maps to SDL rest 0.
  // Establish neutral before the platform opens its GameController handle.
  SDL_JoystickSetVirtualAxis(joystick,SDL_CONTROLLER_AXIS_TRIGGERLEFT,-32768);
  SDL_JoystickSetVirtualAxis(joystick,SDL_CONTROLLER_AXIS_TRIGGERRIGHT,-32768);
  SDL_JoystickUpdate();
  instance=SDL_JoystickInstanceID(joystick);
  SDL_Log("ISS2000 app-only virtual controller enabled; this is not physical input verification");
 }catch(...){report("snapshot path is invalid; fixture disabled");}
}
void pump(){
 if(!joystick)return;
 Snapshot snapshot;
 try{if(!read_snapshot(snapshot))snapshot={};}catch(...){snapshot={};report("snapshot read failed; controls released");}
 SDL_JoystickSetVirtualButton(joystick,SDL_CONTROLLER_BUTTON_A,snapshot.a);
 SDL_JoystickSetVirtualButton(joystick,SDL_CONTROLLER_BUTTON_B,snapshot.b);
 SDL_JoystickSetVirtualButton(joystick,SDL_CONTROLLER_BUTTON_X,snapshot.x);
 SDL_JoystickSetVirtualButton(joystick,SDL_CONTROLLER_BUTTON_Y,snapshot.y);
 SDL_JoystickSetVirtualButton(joystick,SDL_CONTROLLER_BUTTON_LEFTSHOULDER,snapshot.l1);
 SDL_JoystickSetVirtualButton(joystick,SDL_CONTROLLER_BUTTON_RIGHTSHOULDER,snapshot.r1);
 SDL_JoystickSetVirtualButton(joystick,SDL_CONTROLLER_BUTTON_START,snapshot.start);
 SDL_JoystickSetVirtualButton(joystick,SDL_CONTROLLER_BUTTON_DPAD_UP,snapshot.dpad_up);
 SDL_JoystickSetVirtualButton(joystick,SDL_CONTROLLER_BUTTON_DPAD_DOWN,snapshot.dpad_down);
 SDL_JoystickSetVirtualButton(joystick,SDL_CONTROLLER_BUTTON_DPAD_LEFT,snapshot.dpad_left);
 SDL_JoystickSetVirtualButton(joystick,SDL_CONTROLLER_BUTTON_DPAD_RIGHT,snapshot.dpad_right);
 SDL_JoystickSetVirtualAxis(joystick,SDL_CONTROLLER_AXIS_LEFTX,(int(snapshot.right)-int(snapshot.left))*32767);
 SDL_JoystickSetVirtualAxis(joystick,SDL_CONTROLLER_AXIS_LEFTY,(int(snapshot.down)-int(snapshot.up))*32767);
 SDL_JoystickSetVirtualAxis(joystick,SDL_CONTROLLER_AXIS_RIGHTX,0);
 SDL_JoystickSetVirtualAxis(joystick,SDL_CONTROLLER_AXIS_RIGHTY,0);
 SDL_JoystickSetVirtualAxis(joystick,SDL_CONTROLLER_AXIS_TRIGGERLEFT,snapshot.l2?32767:-32768);
 SDL_JoystickSetVirtualAxis(joystick,SDL_CONTROLLER_AXIS_TRIGGERRIGHT,snapshot.r2?32767:-32768);
}
void shutdown(){
 if(!joystick)return;
 SDL_JoystickClose(joystick);joystick=nullptr;
 for(int device=0;device<SDL_NumJoysticks();++device){
  if(SDL_JoystickGetDeviceInstanceID(device)==instance){SDL_JoystickDetachVirtual(device);break;}
 }
 instance=-1;snapshot_path.clear();previous_error.clear();
}
}
#else
namespace iss2000::test_controller {
std::int32_t device_instance(){return -1;}
void initialize(){}
void pump(){}
void shutdown(){}
}
#endif
