"""Execute production prompt construction with owning platform strings.

Original project work: djultra64. CPU-only; no SDL/game execution.
"""
from pathlib import Path
import os
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


def production_prefix():
    source=(ROOT/'src/runtime/native_game.cpp').read_text()
    # Match a definition, never its observer forward declaration. Keep the
    # complete production request construction through the real adapter call.
    definition=re.search(r'\bvoid\s+draw_physical_prompt\([^;{}]*\)\s*\{',source)
    if not definition:raise ValueError('Missing production prompt definition')
    return source[definition.start():].split(
        '    if(result.status==PromptSpriteStatus::TextFallback)',1)[0]+'\n#endif\n    (void)result;\n}\n'


def program(prefix):
    header=(ROOT/'src/platform.hpp').read_text()
    declarations='\n'.join(re.search(pattern,header).group() for pattern in (
        r'enum class Family \{[^}]+\};',r'enum class Action \{[^}]+\};',
        r'struct Prompt \{[^}]+\};',r'struct ControlsHelp \{[^}]+\};'))
    face=header[header.index('constexpr std::string_view face_label('):header.index('\nusing ButtonBindings')]
    native=(ROOT/'src/runtime/native_game.cpp').read_text()
    begin=native.index('std::string football_control_label(');finish=native.index('void draw_native_football_controller',begin)
    football_label=native[begin:finish]
    return r'''#include "runtime/prompt_textures.hpp"
#include "runtime/controller_schemes.hpp"
#include "runtime/pal_options_entry.hpp"
#include <span>
#include <array>
#include <cassert>
#include <cstdint>
#include <string>
#include <vector>
namespace iss2000 {
std::optional<unsigned> selected_port;
std::optional<unsigned> physical_prompt_sprite_port(const uint8_t*,uint64_t,std::optional<unsigned> active){assert(active==selected_port.value_or(0));return selected_port;}
namespace platform {
unsigned active_input_port(){return selected_port.value_or(0);}
DECLARATIONS
FACE_LABEL
struct Preference {ControllerScheme football_scheme{ControllerScheme::Type1};FootballBindings free_football_bindings=default_football_bindings;};
std::array<Preference,4> preferences;
auto port_preferences(){return preferences;}
std::array<Prompt,static_cast<unsigned>(Action::Count)> configured;
std::vector<Action> requested;
Prompt prompt(int port,Action action){assert(unsigned(port)==selected_port.value_or(0));requested.push_back(action);return configured[unsigned(action)];}
ControlsHelp controls_help(int port){assert(unsigned(port)==selected_port.value_or(0));return {{{configured[unsigned(Action::A)],configured[unsigned(Action::B)],configured[unsigned(Action::Start)]}},Family::Automatic};}
}
struct recomp_context {uint64_t r4;};
using recomp_func_t=void(uint8_t*,recomp_context*);
void func_8029F2D8_overlay_3b47e0_8029eea0(uint8_t*,recomp_context*){assert(false);}
void func_80041B50_resident(uint8_t*,recomp_context*){assert(false);}
bool storage_owner;unsigned storage_probes;
// This string-lifetime fixture supplies no guest texture atlas. Its foreign
// field tooltip must decline the new SavedData prehook before construction.
// The actual original SavedData sprite CPU transaction has its own fixture.
bool draw_pal_team_saved_data(std::span<uint8_t> ram,const recomp_context& ctx,recomp_func_t* draw){assert(ram.size()==0x800000&&ctx.r4==0x8013C878&&draw==&func_80041B50_resident);++storage_probes;return false;}
// This fixture owns a field prompt, not an Options-screen sprite. Keep the
// production Options gate and prove its foreign registry owner declines it.
struct PromptRegistry {recomp_func_t* find(uint32_t address){if(address==0x80041B50)return storage_owner?&func_80041B50_resident:nullptr;assert(address==0x8029F2D8);return nullptr;}} registry;
std::optional<PalOptionsLabel> pal_options_pc_label(std::span<const uint8_t>,uint64_t) noexcept {assert(false);return std::nullopt;}
struct MenuBoundary {bool active(){assert(false);return false;}};
MenuBoundary& game_settings_menu(){static MenuBoundary m;return m;}
MenuBoundary& game_controls_menu(){static MenuBoundary m;return m;}
struct PalOptionsSkinFunctions {};
PalOptionsSkinFunctions native_options_skin_functions(){assert(false);return {};}
bool draw_pal_options_skin_label(std::span<uint8_t>,const recomp_context&,std::string_view,int,int,bool,const PalOptionsSkinFunctions&){assert(false);return false;}
struct EngineTextLine {int16_t x=24,y=24;std::string text;uint8_t height=12,palette=0;};
bool draw_pal_engine_text(std::span<uint8_t>,const recomp_context&,std::span<const EngineTextLine>,recomp_func_t*){assert(false);return false;}
FOOTBALL_LABEL
unsigned calls{};
PromptSpriteResult prepare_physical_prompt_sprite(uint8_t* ram,uint64_t sprite,
 const std::array<PromptGlyphRequest,2>& ab,const std::array<PromptGlyphRequest,4>& c,
 std::optional<PromptGlyphRequest> start,std::optional<std::array<PromptGlyphRequest,3>> shoulders){
 assert(ram&&sprite==0x8013C878&&start&&shoulders);
 auto same=[](const PromptGlyphRequest& actual,platform::Action action){
  const auto& expected=platform::configured[unsigned(action)];
  assert(actual.family==static_cast<PromptGlyphFamily>(expected.family));
  assert(actual.port==selected_port.value_or(0));
  // This dereference is the actual adapter call boundary. ASan catches the old
  // destroyed SSO buffer or freed heap buffer before any glyph conversion.
  assert(actual.label==expected.glyph);
 };
 same(ab[0],platform::Action::A);same(ab[1],platform::Action::B);same(*start,platform::Action::Start);
 constexpr platform::Action directions[]={platform::Action::CLeft,platform::Action::CRight,platform::Action::CUp,platform::Action::CDown};
 constexpr platform::Action buttons[]={platform::Action::L,platform::Action::Z,platform::Action::R};
 for(unsigned i=0;i<4;++i)same(c[i],directions[i]);
 for(unsigned i=0;i<3;++i)same((*shoulders)[i],buttons[i]);
 assert(platform::requested==std::vector<platform::Action>({directions[0],directions[1],directions[2],directions[3],buttons[0],buttons[1],buttons[2]}));
 ++calls;return {};
}
PREFIX
}
int main(){
 using namespace iss2000;using platform::Action;using platform::Family;
 constexpr Family families[]={Family::Xbox,Family::PlayStation,Family::Nintendo};
 const std::array<std::array<std::string,3>,3> labels{{{{"LB","LT","RB"}},{{"L1","L2","R1"}},{{"L","ZL","R"}}}};
 for(unsigned selected=0;selected<5;++selected)for(bool long_strings:{false,true})for(unsigned scenario=0;scenario<4;++scenario){
  selected_port=selected?std::optional<unsigned>(selected-1):std::nullopt;
  for(unsigned n=0;n<platform::configured.size();++n)
   platform::configured[n]={"Logical action",std::string(1,char('A'+n)),families[n%3]};
  constexpr Action buttons[]={Action::L,Action::Z,Action::R};
  for(unsigned n=0;n<3;++n){unsigned family=scenario<3?scenario:n;
   auto label=labels[family][n];if(long_strings)label+=" extended physical binding with separately owned long text "+std::to_string(n);
   platform::configured[unsigned(buttons[n])]={"Logical shoulder",label,families[family]};
  }
  storage_owner=scenario%2==0;platform::requested.clear();uint8_t ram{};recomp_context ctx{0x8013C878};draw_physical_prompt(&ram,&ctx);assert(ram==0&&ctx.r4==0x8013C878);
 }
 assert(calls==40&&storage_probes==20);
}
'''.replace('DECLARATIONS',declarations).replace('FACE_LABEL',face).replace('FOOTBALL_LABEL',football_label).replace('PREFIX',prefix)


@unittest.skipUnless(shutil.which('c++'),'C++ compiler required')
class NativePromptLifetimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.folder=Path(cls.temp.name)
        probe=cls.folder/'asan.cpp';probe.write_text('int main(){}\n')
        check=subprocess.run(['c++','-fsanitize=address',str(probe),'-o',str(cls.folder/'asan')],capture_output=True,text=True)
        cls.sanitizer=check.returncode==0
        cls.options=['-fsanitize=address','-fsanitize-address-use-after-scope','-fno-omit-frame-pointer','-g'] if cls.sanitizer else []
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def execute(self,prefix,name):
        source=self.folder/(name+'.cpp');source.write_text(program(prefix));binary=self.folder/name
        result=subprocess.run(['c++','-std=c++20','-O1','-DISS2000_PAL_ENGLISH','-Wall','-Wextra','-Werror',*self.options,'-I'+str(ROOT/'src'),str(source),str(ROOT/'src/runtime/controller_schemes.cpp'),'-o',str(binary)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        env=os.environ.copy();env['ASAN_OPTIONS']='detect_stack_use_after_return=1:detect_leaks=0:halt_on_error=1'
        return subprocess.run([str(binary)],env=env,capture_output=True,text=True)
    def test_production_native_requests_own_sso_and_heap_labels_through_adapter_call(self):
        result=self.execute(production_prefix(),'production')
        self.assertEqual(result.returncode,0,result.stderr)
    def test_original_temporary_owner_regression_is_detected_at_real_adapter_boundary(self):
        # Negative control recreates only the old bug in extracted production
        # construction; the repository's native source remains untouched.
        prefix=production_prefix()
        prefix=prefix.replace('physical_shoulders[i]=platform::prompt(port,shoulder_actions[i]);','const auto physical_shoulder=platform::prompt(port,shoulder_actions[i]);')
        prefix=prefix.replace('physical_shoulders[i].family','physical_shoulder.family').replace('physical_shoulders[i].glyph','physical_shoulder.glyph')
        result=self.execute(prefix,'old-temporary-owner')
        self.assertNotEqual(result.returncode,0,'Negative control failed to detect the original dangling views')
        if self.sanitizer:self.assertRegex(result.stderr,r'AddressSanitizer: (stack-use-after-scope|stack-use-after-return|heap-use-after-free)',result.stderr)

if __name__=='__main__':unittest.main()
