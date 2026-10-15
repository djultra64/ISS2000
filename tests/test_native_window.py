"""Compile real platform entry/handle code against synthetic host interfaces."""
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]

def function(text, signature):
    start=text.index(signature);brace=text.index('{',start);depth=1;end=brace+1
    while depth:
        depth+=(text[end]=='{')-(text[end]=='}');end+=1
    return text[start:end]

class NativeWindowTests(unittest.TestCase):
    def compile_run(self,source):
        with tempfile.TemporaryDirectory(prefix='iss2000-window-contract-') as t:
            p=Path(t);(p/'probe.cpp').write_text(source)
            build=subprocess.run(['c++','-std=c++20','-Wall','-Wextra','-Werror',str(p/'probe.cpp'),'-o',str(p/'probe')],capture_output=True,text=True)
            self.assertEqual(build.returncode,0,build.stderr)
            run=subprocess.run([str(p/'probe')],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
    def test_windows_handle_is_actual_hwnd_with_owning_thread_and_rejects_invalid_native_data(self):
        body=function((ROOT/'src/platform.cpp').read_text(),'ultramodern::renderer::WindowHandle render_window()')
        self.compile_run(r'''#include <stdexcept>
#include <cstdint>
#define _WIN32 1
struct SDL_Window{};using HWND=void*;using DWORD=unsigned long;
namespace ultramodern::renderer {struct WindowHandle {HWND window;DWORD thread_id;};}
struct SDL_SysWMinfo {unsigned version;int subsystem;struct {struct {HWND window;} win;} info;};
constexpr int SDL_SYSWM_WINDOWS=1,SDL_TRUE=1;
SDL_Window storage;SDL_Window* game_window=&storage;bool version_set=false;int subsystem=1;bool succeeds=true;HWND hwnd=reinterpret_cast<void*>(0x1234);DWORD owner=777;
#define SDL_VERSION(version) (version_set=true,*(version)=2)
int SDL_GetWindowWMInfo(SDL_Window*,SDL_SysWMinfo* info){if(!version_set)throw std::runtime_error("missing SDL version");info->subsystem=subsystem;info->info.win.window=hwnd;return succeeds;}
DWORD GetWindowThreadProcessId(HWND value,void*){if(value!=hwnd)throw std::runtime_error("wrong HWND");return owner;}
[[noreturn]] void fail(const char* message){throw std::runtime_error(message);}
''' +body+r'''
int main(){auto value=render_window();if(value.window!=hwnd||value.thread_id!=777)return 1;
for(int mode=0;mode<5;++mode){game_window=&storage;succeeds=true;subsystem=1;hwnd=reinterpret_cast<void*>(0x1234);owner=777;
if(mode==0){game_window=nullptr;} if(mode==1){succeeds=false;} if(mode==2){subsystem=99;} if(mode==3){hwnd=nullptr;} if(mode==4){owner=0;}
try{render_window();return 2;}catch(const std::runtime_error&){} } }
''')
    def test_linux_keeps_sdl_window_and_rejects_missing_window(self):
        body=function((ROOT/'src/platform.cpp').read_text(),'ultramodern::renderer::WindowHandle render_window()')
        self.compile_run('#include <stdexcept>\nstruct SDL_Window{};namespace ultramodern::renderer {using WindowHandle=SDL_Window*;}\nSDL_Window storage;SDL_Window* game_window=&storage;\n'+body+'\nint main(){if(render_window()!=&storage)return 1;game_window=nullptr;try{render_window();return 2;}catch(const std::runtime_error&){} }')
    def test_sdl_main_ready_precedes_initialize_and_main_is_owned_by_application(self):
        code=(ROOT/'src/platform.cpp').read_text();start=code.index('void initialize()');stop=code.index('    game_window=SDL_CreateWindow',start)
        prefix=code[start:stop]+'}\n'
        self.compile_run(r'''#include <stdexcept>
bool ready=false;constexpr int SDL_HINT_GAMECONTROLLER_USE_BUTTON_LABELS=0,SDL_INIT_VIDEO=1,SDL_INIT_AUDIO=2,SDL_INIT_GAMECONTROLLER=4,SDL_INIT_HAPTIC=8;
void SDL_SetHint(int,const char*){}
void SDL_SetMainReady(){ready=true;}
int SDL_Init(int){return ready?0:1;}
[[noreturn]] void fail(const char* x){throw std::runtime_error(x);}
'''+prefix+'int main(){initialize();return ready?0:1;}')
        header=(ROOT/'src/platform.hpp').read_text()
        self.assertLess(header.index('#define SDL_MAIN_HANDLED'),header.index('#include <SDL.h>'))
        main=(ROOT/'src/game_main.cpp').read_text();self.assertIn('config.window_handle=iss2000::platform::render_window()',main)
