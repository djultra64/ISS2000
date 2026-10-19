"""Execute native Options wrappers and the real device-preference input dispatch.

Original project work: djultra64. CPU-only; no SDL/game execution. Original-ROM
owner/label validation lives in test_pal_options_entry; this test controls those
adapter boundaries and extracts the actual production callers rather than a copy.
"""
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


def function(source,name,returns="void"):
    match=re.search(r'\b'+re.escape(returns)+r'\s+'+re.escape(name)+r'\([^;{}]*\)\s*\{',source)
    if not match:raise ValueError('Missing production definition: '+name)
    start=match.start()
    opening=match.end()-1
    depth=1
    end=opening+1
    while depth:
        depth+=(source[end]=='{')-(source[end]=='}')
        end+=1
    return source[start:end]


def production_fragments():
    native=(ROOT/'src/runtime/native_game.cpp').read_text()
    platform=(ROOT/'src/platform.cpp').read_text()
    select=function(native,'select_original_pc_settings')
    # Preserve the complete real label gate. Only replace the unrelated physical
    # prompt tail with a sentinel representing its eventual original-word draw.
    label=function(native,'draw_physical_prompt').split('    const unsigned port=physical_prompt_sprite_port',1)[0]
    label+='\n#endif\n    ++original_word_draws;\n}\n'
    label=function(native,'native_options_skin_functions','PalOptionsSkinFunctions')+'\n'+label
    hook=native.split('    if(uint32_t(address)==0x8001D480u',1)[1].split('    if(uint32_t(address)==0x801ADD44u',1)[0]
    hook='    if(uint32_t(address)==0x8001D480u'+hook
    snapshot=platform.split('    auto& controls_menu=game_controls_menu();',1)[1].split('    Family menu_family=',1)[0]
    snapshot='    auto& controls_menu=game_controls_menu();'+snapshot
    dispatch=platform.split('    if(menu_frame.active&&menu_result.deliver&&controls_active)',1)[1].split('\n}\nvoid poll()',1)[0]
    dispatch='    if(menu_frame.active&&menu_result.deliver&&controls_active)'+dispatch
    return select,label,hook,snapshot,dispatch


HARNESS=r'''
#include "runtime/game_settings_menu.hpp"
#include "runtime/game_controls_input.hpp"
#include "runtime/input_preferences.hpp"
#include "runtime/pal_options_entry.hpp"
#include "runtime/pal_team_saved_data.hpp"
#include "runtime/pak_services.hpp"
#include "renderer_settings.hpp"
#include <cassert>
#include <map>
#include <vector>
#include <cstring>
#include <filesystem>
void func_80008C30_resident(uint8_t*,recomp_context*){}
void func_8001D480_resident(uint8_t*,recomp_context*){}
void iss2000_pal_framebuffer_allocator(uint8_t*,recomp_context*){}
void func_802A3464_overlay_3e83d0_8029eea0(uint8_t*,recomp_context*){}
void iss2000_pal_formation_save(uint8_t*,recomp_context*){}
void func_80041B50_resident(uint8_t*,recomp_context*){assert(false);}
void iss2000_pal_fixed_high_initializer(uint8_t*,recomp_context*){}
unsigned original_calls=0;
void func_8029F2D8_overlay_3b47e0_8029eea0(uint8_t*,recomp_context* c){++original_calls;++c->r2;}
void foreign(uint8_t*,recomp_context*){}
void font(uint8_t*,recomp_context*){}
namespace recomp {std::filesystem::path get_config_path(){return "test-config";}}
namespace iss2000 {
// The unrelated Select Teams caption path must stay unreachable in Options.
bool draw_pal_team_saved_data(std::span<uint8_t>,const recomp_context&,recomp_func_t*){assert(false);return false;}
struct TestRegistry {std::map<uint32_t,recomp_func_t*> entries;recomp_func_t* find(uint32_t a){return entries[a];}}registry;
std::optional<unsigned> row;
std::optional<PalOptionsLabel> label;
unsigned label_probes=0,font_draws=0,original_word_draws=0;
// These observer-aware entrypoints are passed as identities to the controlled
// original-skin boundary. This fixture never executes a sprite draw.
void track_initialize_sprite(uint8_t*,recomp_context*){assert(false);}
void track_menu_sprite(uint8_t*,recomp_context*){assert(false);}
void track_menu_text(uint8_t*,recomp_context*){assert(false);}
bool draw_success=false;
std::optional<PalOptionsEntry> pal_options_entry(std::span<const uint8_t> r)noexcept{assert(r.size()==0x800000);if(!row)return {};return PalOptionsEntry{*row,*row==6};}
std::optional<PalOptionsLabel> pal_options_pc_label(std::span<const uint8_t> r,uint64_t object)noexcept{assert(r.size()==0x800000&&object==0x8013c47c);++label_probes;return label;}
bool draw_pal_options_skin_label(std::span<uint8_t> r,const recomp_context& c,std::string_view text,int x,int y,bool selected,const PalOptionsSkinFunctions& f){
 assert(r.size()==0x800000&&c.r4==0x8013c47c&&f.initialize_sprite==&track_initialize_sprite&&f.draw_sprite==&track_menu_sprite&&f.draw_text==&track_menu_text);
 assert(x==67&&y==167&&text=="PC Settings"&&selected);++font_draws;return draw_success;
}

InputPreferences preferences,saved_preferences;
std::array<PakAccessory,4> accessories{PakAccessory::None,PakAccessory::Rumble,PakAccessory::Controller,PakAccessory::None};
unsigned saves=0,applies=0;
InputPreferences capture_input_preferences(){return preferences;}
void save_input_preferences(const std::filesystem::path& p,const InputPreferences& v){assert(p=="test-config");saved_preferences=v;++saves;}
void apply_input_preferences(const InputPreferences& v){assert(saved_preferences==v&&saves==applies+1);preferences=v;++applies;}
PakAccessory pak_accessory(int p){assert(p>=0&&p<4);return accessories.at(p);}
void set_pak_accessory(unsigned p,PakAccessory a){accessories.at(p)=a;}
void save_graphics_settings(const std::filesystem::path&,const GraphicsSettings&){}
void save_game_preferences(const std::filesystem::path& p,const GraphicsSettings& g,const InputPreferences& v){save_graphics_settings(p,g);save_input_preferences(p,v);}
namespace platform {
unsigned input_port=1;
GraphicsSettings graphics{AspectRatio::Original4x3,RenderResolution::P1440,RenderRefresh::Hz120};
GraphicsSettings render_settings(){return graphics;}
void set_render_settings(const GraphicsSettings& g){graphics=g;}
unsigned active_input_port(){return input_port;}
std::array<PortPreferences,4> port_preferences(){return preferences.ports;}
}
SELECT
LABEL
namespace platform {
struct Snapshot {ControlsMenuInputFrame frame;bool controls_active;};
Snapshot snapshot(){
SNAPSHOT
 return {menu_frame,controls_active};
}
void dispatch(const ControlsMenuInputFrame& menu_frame,const ControlsMenuInputResult& menu_result,bool controls_active){
 auto& controls_menu=game_controls_menu();auto& settings_menu=game_settings_menu();Family menu_family=Family::Xbox;
DISPATCH
}
}
}
recomp_func_t* selected_function(int32_t address){
HOOK
 return iss2000::registry.find(uint32_t(address));
}
using namespace iss2000;using C=ControlsMenuCommand;
int main(int,char**argv){const std::string test=argv[1];
 if(test=="entry"){
  for(unsigned p=0;p<4;++p){preferences.ports[p].vibration=p%2==0;preferences.ports[p].manual_family=platform::Family(p);}
  std::vector<uint8_t> ram(0x800000,0xa5);const auto before=ram;
  auto& settings=game_settings_menu();
  for(unsigned i=0;i<8;++i){row=i;recomp_context ctx{};ctx.r2=99;const unsigned calls=original_calls;
   select_original_pc_settings(ram.data(),&ctx);
   if(i==6){assert(settings.active()&&settings.port()==1&&ctx.r2==99&&original_calls==calls);const auto draft=settings.draft();assert(draft.graphics==platform::graphics);for(unsigned p=0;p<4;++p){assert(draft.vibration[p]==preferences.ports[p].vibration);assert(draft.families[p]==preferences.ports[p].manual_family);}settings.command(C::Cancel);}
   else assert(!settings.active()&&ctx.r2==100&&original_calls==calls+1);
   assert(ram==before);
  }
  row.reset();recomp_context ctx{};select_original_pc_settings(ram.data(),&ctx);assert(original_calls==8&&!settings.active()&&ctx.r2==1);return 0;
 }
 if(test=="lookup"){
  for(auto address:{0x8001d480u,0x802a3464u,0x80008c30u,0x8029f2d8u}){
   registry.entries.clear();assert(selected_function(int32_t(address))==nullptr);
   registry.entries[address]=&foreign;assert(selected_function(int32_t(address))==&foreign);
  }
  registry.entries[0x802a3464]=&func_802A3464_overlay_3e83d0_8029eea0;assert(selected_function(int32_t(0x802a3464u))==&iss2000_pal_formation_save);
  registry.entries[0x8001d480]=&func_8001D480_resident;assert(selected_function(int32_t(0x8001d480u))==&iss2000_pal_framebuffer_allocator);
  registry.entries[0x80008c30]=&func_80008C30_resident;assert(selected_function(int32_t(0x80008c30u))==&iss2000_pal_fixed_high_initializer);
  registry.entries[0x8029f2d8]=&func_8029F2D8_overlay_3b47e0_8029eea0;assert(selected_function(int32_t(0x8029f2d8u))==&select_original_pc_settings);
  registry.entries[0x8001c9a4]=&foreign;assert(selected_function(int32_t(0x8001c9a4u))==&foreign);return 0;
 }
 if(test=="label"){
  std::vector<uint8_t> ram(0x800000,0x5a);auto before=ram;recomp_context ctx{};ctx.r4=0x8013c47c;ctx.r2=999;
  registry.entries[0x80048660]=&font;registry.entries[0x8029f2d8]=&foreign;
  label=PalOptionsLabel{67,167,128,16,false};draw_success=true;draw_physical_prompt(ram.data(),&ctx);assert(original_word_draws==1&&label_probes==0&&font_draws==0);
  registry.entries[0x8029f2d8]=&func_8029F2D8_overlay_3b47e0_8029eea0;
  label.reset();draw_physical_prompt(ram.data(),&ctx);assert(original_word_draws==2&&label_probes==1&&font_draws==0);
  label=PalOptionsLabel{67,167,128,16,true};draw_success=false;draw_physical_prompt(ram.data(),&ctx);assert(original_word_draws==3&&font_draws==1&&ram==before&&ctx.r2==999);
  draw_success=true;draw_physical_prompt(ram.data(),&ctx);assert(original_word_draws==3&&font_draws==2&&ram==before&&ctx.r2==999);return 0;
 }
 if(test=="port-save"){
  auto& settings=game_settings_menu();auto& old_editor=game_controls_menu();GameSettingsDraft draft;
  draft.graphics=platform::graphics;for(unsigned p=0;p<4;++p){draft.vibration[p]=preferences.ports[p].vibration;draft.families[p]=preferences.ports[p].manual_family;}
  assert(settings.open(0,draft));settings.command(C::Down);settings.command(C::Accept);settings.command(C::Down);settings.command(C::Down);settings.command(C::Accept);
  ControlsMenuInputResult accept;accept.deliver=true;accept.command=C::Accept;
  auto dispatch=[&](){auto snap=platform::snapshot();platform::dispatch(snap.frame,accept,snap.controls_active);assert(!old_editor.active());};
  dispatch();assert(settings.draft().families[2]==platform::Family::Xbox);
  settings.command(C::Down);dispatch();assert(!settings.draft().vibration[2]);
  // Independent raw bindings and football schemes change while device settings
  // stay open. The actual Save callback must merge a fresh snapshot.
  preferences.ports[1].bindings[unsigned(platform::Action::A)]=SDL_CONTROLLER_BUTTON_LEFTSTICK;
  preferences.ports[3].football_scheme=ControllerScheme::Type4;const auto fresh=preferences;
  settings.command(C::Cancel);settings.command(C::Cancel);settings.command(C::Down);dispatch();
  assert(!settings.active()&&saves==1&&applies==1&&saved_preferences==preferences);
  auto expected=fresh;expected.ports[2].manual_family=platform::Family::Xbox;expected.ports[2].vibration=false;assert(preferences==expected);return 0;
 }
 if(test=="routing"||test=="same-port"){
  auto& settings=game_settings_menu();auto& old_editor=game_controls_menu();GameSettingsDraft draft;assert(settings.open(0,draft));
  const unsigned target=test=="same-port"?0:2;
  settings.command(C::Down);settings.command(C::Accept);for(unsigned n=0;n<target;++n)settings.command(C::Down);settings.command(C::Accept);
  ControlsMenuInputRouter router;std::array<uint32_t,4> held{};bool escape=false;
  auto tick=[&](){auto sample=platform::snapshot();auto& frame=sample.frame;frame.focused=true;frame.escape=escape;
   for(unsigned p=0;p<4;++p){frame.controllers[p].held=held[p];frame.controllers[p].preferences=preferences.ports[p];frame.any_input|=held[p]!=0;}
   const auto result=router.route(frame);platform::dispatch(frame,result,sample.controls_active);assert(!old_editor.active());return result;
  };
  auto release=[&](){held.fill(0);escape=false;tick();};
  // The press that opened this parent must not change a family before release.
  held[0]=1u<<SDL_CONTROLLER_BUTTON_A;assert(!tick().deliver);assert(settings.draft().families[target]==platform::Family::Automatic);release();
  held[0]=1u<<SDL_CONTROLLER_BUTTON_A;assert(tick().command==C::Accept);assert(settings.draft().families[target]==platform::Family::Xbox);
  assert(platform::snapshot().frame.owner_token==1&&platform::snapshot().frame.port==0);
  assert(tick().command==C::None);assert(settings.draft().families[target]==platform::Family::Xbox);release();
  // Settings input stays with the opening player, even when editing another.
  held[target?target:3]=1u<<SDL_CONTROLLER_BUTTON_A;assert(tick().command==C::None);assert(settings.draft().families[target]==platform::Family::Xbox);release();
  held[0]=1u<<SDL_CONTROLLER_BUTTON_B;assert(tick().command==C::Cancel&&settings.active());assert(settings.lines("A","B")[0].text=="Controls");
  assert(tick().command==C::None&&settings.lines("A","B")[0].text=="Controls");release();
  escape=true;assert(tick().command==C::Cancel&&settings.active());release();escape=true;assert(tick().command==C::Cancel&&!settings.active());
  // Cancel discards family edits and closing buttons stay suppressed until up.
  assert(settings.draft()==draft);escape=false;held[0]=1u<<SDL_CONTROLLER_BUTTON_A;assert(tick().suppress);held.fill(0);assert(!tick().suppress);
  assert(saves==0&&applies==0);return 0;
 }
 assert(false);
}
'''


class NativeSettingsIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.folder=Path(cls.temp.name)
        source=HARNESS
        for token,value in zip(('SELECT','LABEL','HOOK','SNAPSHOT','DISPATCH'),production_fragments()):
            source=source.replace(token,value)
        cls.source=source
        cls.binary=cls.build(source,'production')
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    @classmethod
    def build(cls,source,name,include_override=None):
        cpp=cls.folder/(name+'.cpp');cpp.write_text(source);binary=cls.folder/name
        # Compile the exact menu state implementation, excluding the separate
        # engine font renderer whose success/failure boundary this test controls.
        controls=cls.folder/'controls-state.cpp'
        controls.write_text((ROOT/'src/runtime/game_controls_menu.cpp').read_text().split('\nnamespace {\nuint16_t read_half',1)[0]+'\n}\n')
        includes=['src','.local/deps/N64Recomp/include','.local/deps/N64ModernRuntime/librecomp/include','.local/deps/N64ModernRuntime/ultramodern/include','.local/deps/N64ModernRuntime/thirdparty','.local/deps/N64ModernRuntime/thirdparty/concurrentqueue']
        result=subprocess.run(['c++','-std=c++20','-O1','-DISS2000_PAL_ENGLISH','-Wall','-Wextra','-Werror','-pthread','-ffunction-sections','-fdata-sections','-Wl,--gc-sections',*(['-I'+str(include_override)]if include_override else []),*['-I'+str(ROOT/i)for i in includes],'-I/home/linuxbrew/.linuxbrew/include/SDL2',str(cpp),str(ROOT/'src/runtime/game_settings_menu.cpp'),str(controls),'-o',str(binary)],capture_output=True,text=True)
        if result.returncode:raise RuntimeError(result.stderr)
        return binary
    def run_case(self,name):
        result=subprocess.run([str(self.binary),name],capture_output=True,text=True,timeout=8)
        self.assertEqual(result.returncode,0,result.stderr)
    def test_actual_options_wrapper_replaces_row_six_preserving_other_seven(self):self.run_case('entry')
    def test_actual_lookup_requires_exact_high_initializer_and_options_symbols(self):self.run_case('lookup')
    def test_actual_label_gate_keeps_original_word_on_draw_failure(self):self.run_case('label')
    def test_actual_platform_family_target_keeps_opening_player_input(self):self.run_case('routing')
    def test_actual_platform_family_change_requires_release_and_cancel_is_transactional(self):self.run_case('same-port')
    def test_actual_platform_device_save_preserves_fresh_raw_bindings_and_schemes(self):self.run_case('port-save')
    def test_negative_control_detects_held_button_repeating_family_change(self):
        original=(ROOT/'src/runtime/game_controls_input.hpp').read_text()
        condition='navigation&~previous_navigation_'
        self.assertIn(condition,original)
        override=self.folder/'old-router-include';(override/'runtime').mkdir(parents=True,exist_ok=True)
        (override/'runtime/game_controls_input.hpp').write_text(original.replace(condition,'navigation'))
        binary=self.build(self.source,'old-router',override)
        result=subprocess.run([str(binary),'routing'],capture_output=True,text=True,timeout=8)
        self.assertNotEqual(result.returncode,0,'Regression control failed to detect repeated family changes while Accept stays held')

if __name__=='__main__':unittest.main()
