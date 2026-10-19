"""Main-thread SDL fullscreen requests use actual flags, independent of RT64 config. Work by djultra64."""
from pathlib import Path
import re,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
def function(source,marker):
 start=source.index(marker);opening=source.index('{',start);depth=1;end=opening+1
 while depth:
  depth+=(source[end]=='{')-(source[end]=='}');end+=1
 return source[start:end]
class FullscreenSyncTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.temp.cleanup);p=Path(cls.temp.name)
  platform=(ROOT/'src/platform.cpp').read_text();renderer=(ROOT/'src/renderer.cpp').read_text()
  # Execute the actual main-thread prefix before unrelated input/menu sampling.
  prefix=function(platform,'void update(void*)').split('    auto& controls_menu=game_controls_menu();',1)[0]+'}\n'
  sync=function(platform,'void sync_window_mode(')if 'void sync_window_mode('in platform else ''
  state='WindowModeSync window_mode;bool fullscreen_error_reported=false;'if 'void sync_window_mode('in platform else ''
  copied=re.search(r'applied_settings=chosen;',renderer).group()
  code=r'''#include "runtime/graphics_settings.hpp"
#if __has_include("runtime/window_mode_sync.hpp")
#include "runtime/window_mode_sync.hpp"
#endif
#include <cassert>
#include <cstdio>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <thread>
using namespace iss2000;
struct SDL_Window{uint32_t flags=0;};SDL_Window storage;SDL_Window* game_window=&storage;
constexpr uint32_t SDL_WINDOW_FULLSCREEN=1,SDL_WINDOW_FULLSCREEN_DESKTOP=0x1001;
uint64_t now=0;unsigned calls=0;bool fail_request=false,apply_immediately=true;
const auto owner=std::this_thread::get_id();
GraphicsSettings desired,applied_settings;
GraphicsSettings render_settings(){return desired;}
uint32_t SDL_GetWindowFlags(SDL_Window* window){assert(window==game_window);return window->flags;}
uint64_t SDL_GetTicks64(){return now;}
const char* SDL_GetError(){return "injected denied fullscreen request";}
int SDL_SetWindowFullscreen(SDL_Window* window,uint32_t flags){
 assert(std::this_thread::get_id()==owner&&window==game_window);++calls;
 assert(flags==0||flags==SDL_WINDOW_FULLSCREEN_DESKTOP);
 if(fail_request)return -1;
 if(apply_immediately)window->flags=flags;return 0;
}
STATE
SYNC
PREFIX
void renderer_config_copy(){const auto chosen=render_settings();COPIED}
void require(bool v,const char* message){if(!v)throw std::runtime_error(message);}
int main(int,char**argv){try{
 const std::string mode=argv[1];
 if(mode=="config"){
  desired.fullscreen=true;renderer_config_copy();require(applied_settings.fullscreen,"config did not consume snapshot");
  update(nullptr);require(calls==1&&(storage.flags&SDL_WINDOW_FULLSCREEN),"copied renderer config swallowed real SDL fullscreen request");
  update(nullptr);require(calls==1,"satisfied fullscreen repeatedly requested");
 }else if(mode=="failure"){
  desired.fullscreen=true;fail_request=true;update(nullptr);
  require(calls==1&&!(storage.flags&SDL_WINDOW_FULLSCREEN),"failed SDL request marked fullscreen applied");
  for(now=1;now<1000;++now)update(nullptr);require(calls==1,"failed request spammed every frame");
  now=1000;fail_request=false;apply_immediately=false;update(nullptr);
  require(calls==2&&!(storage.flags&SDL_WINDOW_FULLSCREEN),"asynchronous request success was treated as actual fullscreen");
  now=1001;update(nullptr);require(calls==2,"pending request repeatedly issued");
  storage.flags|=SDL_WINDOW_FULLSCREEN;now=1002;update(nullptr);require(calls==2,"confirmed flags not honored");
 }else if(mode=="toggle"){
  desired.fullscreen=true;apply_immediately=false;update(nullptr);require(calls==1,"initial request missing");
  desired.fullscreen=false;now=1;update(nullptr);require(calls==1,"already-windowed cancellation requested mode change");
  desired.fullscreen=true;now=2;apply_immediately=true;update(nullptr);require(calls==2&&(storage.flags&1),"fresh preference suppressed by previous cooldown");
  desired.fullscreen=false;renderer_config_copy();now=3;update(nullptr);require(calls==3&&!(storage.flags&1),"windowed request swallowed");
 }else if(mode=="flags"){
  update(nullptr);require(calls==0,"already-windowed startup changed window");
  storage.flags=SDL_WINDOW_FULLSCREEN_DESKTOP;now=1;update(nullptr);require(calls==1&&storage.flags==0,"actual window state not reconciled with request");
 }else return 2;
 return 0;
}catch(const std::exception&e){std::fprintf(stderr,"%s\n",e.what());return 1;}}
'''.replace('STATE',state).replace('SYNC',sync).replace('PREFIX',prefix).replace('COPIED',copied)
  (p/'test.cpp').write_text(code);cls.binary=p/'test'
  result=subprocess.run(['c++','-std=c++20','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-pthread','-I'+str(ROOT/'src'),str(p/'test.cpp'),'-o',str(cls.binary)],capture_output=True,text=True)
  if result.returncode:raise RuntimeError(result.stderr)
 def run_case(self,name):
  result=subprocess.run([str(self.binary),name],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
 def test_renderer_config_snapshot_cannot_consume_native_fullscreen_change(self):self.run_case('config')
 def test_failure_and_async_request_require_actual_flags_and_bounded_retry(self):self.run_case('failure')
 def test_new_selection_bypasses_previous_pending_request_cooldown(self):self.run_case('toggle')
 def test_actual_sdl_flags_control_reconciliation(self):self.run_case('flags')
if __name__=='__main__':unittest.main()
