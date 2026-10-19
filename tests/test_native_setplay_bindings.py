"""Original work: djultra64. Set-play labels must use the applied football map."""
from pathlib import Path
import re,subprocess,tempfile,unittest
import test_native_prompt_lifetime as fixture
ROOT=fixture.ROOT
class NativeSetplayBindingsTests(unittest.TestCase):
 def test_setplay_curve_cursor_follow_every_scheme_family_and_free_port(self):
  code=fixture.program(fixture.production_prefix())
  begin=code.index('unsigned calls{};');finish=code.index('void draw_physical_prompt(',begin)
  adapter=r'''unsigned calls{};std::array<std::string,2>expected;
PromptSpriteResult prepare_physical_prompt_sprite(uint8_t*,uint64_t,
 const std::array<PromptGlyphRequest,2>&,const std::array<PromptGlyphRequest,4>&,
 std::optional<PromptGlyphRequest> start,std::optional<std::array<PromptGlyphRequest,3>> shoulders){
 assert(start&&shoulders);++calls;
 if(calls==1){PromptSpriteResult r;r.status=PromptSpriteStatus::TextFallback;r.action=PromptSpriteAction::SetplayControls;return r;}
 assert(calls==2&&(*shoulders)[1].label==expected[0]&&(*shoulders)[2].label==expected[1]);
 for(unsigned n=1;n<3;++n)assert((*shoulders)[n].port==selected_port.value_or(0));
 return {};
}
'''
  code=code[:begin]+adapter+code[finish:]
  main=code.index('int main(){')
  code=code[:main]+r'''int main(){using namespace iss2000;
 for(unsigned port=0;port<4;++port)for(auto family:{platform::Family::Xbox,platform::Family::PlayStation,platform::Family::Nintendo,platform::Family::Keyboard})for(unsigned scheme=0;scheme<6;++scheme){
  selected_port=port;auto& pref=platform::preferences[port];pref.football_scheme=ControllerScheme(scheme);pref.free_football_bindings=default_football_bindings;
  std::swap(pref.free_football_bindings[unsigned(FootballAction::Curve)],pref.free_football_bindings[unsigned(FootballAction::Pass)]);
  const auto bindings=scheme==5?pref.free_football_bindings:*scheme_bindings(pref.football_scheme);
  expected={football_control_label(family,bindings[unsigned(FootballAction::Curve)]),football_control_label(family,bindings[unsigned(FootballAction::Cursor)])};
  for(auto& p:platform::configured)p={"original","Original",family};
  calls=0;uint8_t ram{};recomp_context c{0x8013c878};draw_physical_prompt(&ram,&c);
  assert(calls==(family==platform::Family::Keyboard?1:2)&&ram==0&&c.r4==0x8013c878);
 }
}
'''
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);(p/'test.cpp').write_text(code)
   built=subprocess.run(['c++','-std=c++20','-O1','-DISS2000_PAL_ENGLISH','-I'+str(ROOT/'src'),str(p/'test.cpp'),str(ROOT/'src/runtime/controller_schemes.cpp'),'-o',str(p/'test')],capture_output=True,text=True);self.assertEqual(built.returncode,0,built.stderr)
   run=subprocess.run([str(p/'test')],capture_output=True,text=True);self.assertEqual(run.returncode,0,run.stderr)
if __name__=='__main__':unittest.main()
