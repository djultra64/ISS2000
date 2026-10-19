"""Original-engine PC settings drafts and callback ownership. Work by djultra64."""
from pathlib import Path
import subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
HARNESS=r'''
#include "runtime/game_settings_menu.hpp"
#include <cassert>
#include <future>
#include <stdexcept>
using namespace iss2000;
using C=ControlsMenuCommand;
int main(int,char** argv){
 GameSettingsMenu m;GameSettingsDraft original;original.graphics.resolution=RenderResolution::Original;original.graphics.refresh_rate=RenderRefresh::Original;original.vibration={true,false,true,false};original.families[1]=platform::Family::Xbox;
 auto cmd=[&](C c){m.command(c);};
 auto down=[&](unsigned n){while(n--)cmd(C::Down);};
 auto selected=[&](){for(const auto& l:m.lines("Return","X"))if(l.text.starts_with("SELECT "))return l.text;return std::string{};};
 const std::string test=argv[1];
 assert(!m.open(4,original));auto bad=original;bad.graphics.resolution=RenderResolution(99);assert(!m.open(0,bad));
 bad=original;bad.families[2]=platform::Family::Keyboard;assert(!m.open(0,bad));bad.families[2]=platform::Family(255);assert(!m.open(0,bad));
 assert(m.open(1,original));assert(!m.open(0,original));assert(m.active()&&m.port()==1);
 if(test=="sounds"){
  auto take=[&](PalMenuSound expected){auto e=m.pending_sound();assert(e&&e->sound==expected);m.acknowledge_sound(e->sequence+1);assert(m.pending_sound());m.acknowledge_sound(e->sequence);};
  take(PalMenuSound::Accept);cmd(C::None);assert(!m.pending_sound());cmd(C::Down);take(PalMenuSound::Navigate);cmd(C::Up);take(PalMenuSound::Navigate);
  cmd(C::Accept);take(PalMenuSound::Accept);cmd(C::NextPage);take(PalMenuSound::Navigate);
  m.command(C::ApplySave,[](const auto&){return false;});take(PalMenuSound::Error);
  m.command(C::ApplySave,[](const auto&){return true;});take(PalMenuSound::Accept);
  for(unsigned n=0;n<5;++n){cmd(C::Down);take(PalMenuSound::Navigate);}
  m.command(C::ApplySave,[](const auto&){return true;});take(PalMenuSound::Accept);
  cmd(C::PreviousPage);cmd(C::NextPage);assert(!m.pending_sound());bool saved=false;for(auto l:m.lines("Z","X"))saved|=l.text=="Options saved";assert(saved);
  cmd(C::Cancel);take(PalMenuSound::Back);cmd(C::Cancel);assert(!m.active());take(PalMenuSound::Back);assert(!m.pending_sound());return 0;
 }
 if(test=="apply"){
  unsigned calls=0;m.command(C::ApplySave,[&](const auto&){++calls;return true;});assert(!calls);
  cmd(C::Accept);assert(m.can_apply_shortcut());down(1);cmd(C::NextPage);
  auto edited=m.draft();m.command(C::ApplySave,[&](const auto& d){++calls;assert(d==edited);auto f=std::async(std::launch::async,[&]{return m.draft();});assert(f.wait_for(std::chrono::seconds(1))==std::future_status::ready);m.command(C::Cancel);return false;});
  assert(calls==1&&m.active()&&m.can_apply_shortcut()&&m.draft()==edited);
  m.command(C::ApplySave,[&](const auto& d){++calls;assert(d==edited);return true;});assert(calls==2&&m.active());
  cmd(C::NextPage);assert(m.draft()!=edited);cmd(C::Cancel);assert(!m.can_apply_shortcut());cmd(C::Cancel);assert(!m.active()&&m.draft()==edited);return 0;
 }
 if(test=="consumer_labels"){
  bool found=false;for(auto l:m.lines("Z","X"))found|=l.text=="       Save options";assert(found);
  cmd(C::Accept);found=false;for(auto l:m.lines("Z","X"))found|=l.text.starts_with("       Framerate limit ");assert(found);return 0;
 }
 if(test=="transparent"){
  auto check=[&](){for(const auto& line:m.lines("A","B")){assert(line.text.find("Pak")==std::string::npos);assert(line.text.find("Accessory")==std::string::npos);assert(line.text.find("glyph")==std::string::npos);assert(line.text.find("Remap")==std::string::npos);assert(line.text.find("Button mapping")==std::string::npos);}};
  check();down(1);cmd(C::Accept);check();cmd(C::Accept);check();return 0;
 }
 if(test=="graphics"){
  cmd(C::Accept);assert(selected().find("Aspect")!=std::string::npos);
  cmd(C::Accept);assert(m.draft().graphics.aspect_ratio==AspectRatio::Original4x3);cmd(C::PreviousPage);assert(m.draft().graphics.aspect_ratio==AspectRatio::Wide16x9);
  down(1);for(unsigned n=1;n<=7;++n){cmd(C::NextPage);assert(unsigned(m.draft().graphics.resolution)==n%7);}
  cmd(C::PreviousPage);assert(m.draft().graphics.resolution==RenderResolution::P2160);
  down(1);for(unsigned n=1;n<=3;++n){cmd(C::Accept);assert(unsigned(m.draft().graphics.refresh_rate)==n%3);}
  cmd(C::PreviousPage);assert(m.draft().graphics.refresh_rate==RenderRefresh::Hz120);
  down(1);cmd(C::Accept);assert(m.draft().graphics.fullscreen);cmd(C::PreviousPage);assert(!m.draft().graphics.fullscreen);down(1);assert(selected()=="SELECT Filtering 2D Original");
  auto view=m.view("A","B");assert(view.rows.size()==6&&view.selected==4&&view.rows[4].label=="Filtering"&&view.rows[4].value=="2D Original"&&view.rows[5].label=="Back");
  cmd(C::NextPage);assert(m.draft().graphics.filter_2d==Filter2D::Bilinear);view=m.view("A","B");assert(view.rows[4].value=="2D Bilinear");cmd(C::PreviousPage);assert(m.draft().graphics.filter_2d==Filter2D::Original);down(1);cmd(C::Accept);assert(selected()=="SELECT Graphics");cmd(C::Cancel);assert(!m.active()&&m.draft()==original);return 0;
 }
 if(test=="ports"){
  down(1);cmd(C::Accept);down(2);cmd(C::Accept);assert(m.port()==1);assert(m.lines("A","B")[0].text=="Player 3");
  unsigned calls=0;auto obsolete=[&](unsigned){++calls;return true;};
  m.command(C::Accept,{},obsolete);assert(calls==0&&m.draft().families[2]==platform::Family::Xbox);
  m.command(C::NextPage,{},obsolete);assert(calls==0&&m.draft().families[2]==platform::Family::PlayStation);
  m.command(C::NextPage,{},obsolete);assert(m.draft().families[2]==platform::Family::Nintendo);
  m.command(C::NextPage,{},obsolete);assert(m.draft().families[2]==platform::Family::Automatic);
  m.command(C::PreviousPage,{},obsolete);assert(m.draft().families[2]==platform::Family::Nintendo);
  for(unsigned p=0;p<4;++p)if(p!=2)assert(m.draft().families[p]==original.families[p]);
  auto view=m.view("A","B");assert(view.rows[0].label=="Controller type"&&view.rows[0].value=="Nintendo");
  down(1);cmd(C::Accept);assert(!m.draft().vibration[2]);cmd(C::PreviousPage);assert(m.draft().vibration[2]);cmd(C::NextPage);assert(!m.draft().vibration[2]);
  cmd(C::Cancel);assert(selected()=="SELECT Player 3");cmd(C::Cancel);assert(selected()=="SELECT Controls");cmd(C::Cancel);assert(!m.active()&&m.draft()==original);return 0;
 }
 if(test=="save"){
  cmd(C::Accept);cmd(C::Accept);cmd(C::Cancel);down(1);cmd(C::Accept);down(2);cmd(C::Accept);cmd(C::Accept);cmd(C::Down);cmd(C::Accept);cmd(C::Cancel);cmd(C::Cancel);cmd(C::Down);bool called=false;
  m.command(C::Accept,[&](const GameSettingsDraft& d){called=true;assert(d.graphics.aspect_ratio!=original.graphics.aspect_ratio&&m.active());assert(d.families[2]==platform::Family::Xbox&&!d.vibration[2]);auto f=std::async(std::launch::async,[&]{return m.draft();});assert(f.wait_for(std::chrono::seconds(1))==std::future_status::ready);m.command(C::Cancel);assert(m.active());return false;});assert(called&&m.active());bool error=false;for(auto l:m.lines("Cross","Circle"))error|=l.text=="Save failed. Try again";assert(error);
  m.command(C::Accept,[](const auto&)->bool{throw std::runtime_error("disk");});assert(m.active());
  m.command(C::Accept,[&](const auto& d){assert(d.graphics.aspect_ratio==AspectRatio::Original4x3);assert(d.families[2]==platform::Family::Xbox&&!d.vibration[2]);return true;});assert(!m.active()&&m.lines("A","B").empty());return 0;
 }
 if(test=="bounds"){
  auto check=[&](){auto v=m.lines("Left Shift","Options");assert(!v.empty());bool accept=false,back=false;for(auto l:v){assert(l.text.size()<=40&&l.x>=0&&l.y>=0&&l.x+6*l.text.size()<=320&&l.y+l.height<=240);for(char c:l.text)assert((c>='A'&&c<='Z')||(c>='a'&&c<='z')||(c>='0'&&c<='9')||c==' '||c=='.');accept|=l.text=="Left Shift select";back|=l.text=="Options back";}assert(accept&&back);};
  check();cmd(C::Accept);for(unsigned i=0;i<5;++i){check();cmd(C::Down);}cmd(C::Cancel);down(1);cmd(C::Accept);for(unsigned p=0;p<4;++p){cmd(C::Accept);check();cmd(C::Cancel);cmd(C::Down);}check();
  auto plus=m.lines("+","D-pad left");assert(plus[plus.size()-2].text=="Plus select"&&plus.back().text=="D pad left back");assert(m.lines("unsupported?","B").empty());assert(m.lines(std::string(35,'X'),"B").empty());return 0;
 }
 if(test=="navigation"){
  cmd(C::Up);assert(selected()=="SELECT Cancel");cmd(C::Down);assert(selected()=="SELECT Graphics");cmd(C::Accept);cmd(C::Up);assert(selected()=="SELECT Back");cmd(C::Accept);down(1);cmd(C::Accept);cmd(C::Up);assert(selected()=="SELECT Back");cmd(C::Accept);cmd(C::Accept);cmd(C::Accept);
  unsigned called=0;m.command(C::Accept,{},[&](unsigned){++called;return false;});assert(!called);
  for(auto l:m.lines("A","B"))assert(l.text.find("Remap")==std::string::npos);
  cmd(C::Cancel);cmd(C::Cancel);down(2);cmd(C::Accept);assert(!m.active());return 0;
 }
 assert(false);
}
'''
class GameSettingsMenuTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();d=Path(cls.tmp.name);(d/'test.cpp').write_text(HARNESS);cls.binary=d/'test'
  includes=['src','.local/deps/N64Recomp/include','.local/deps/N64ModernRuntime/librecomp/include','.local/deps/N64ModernRuntime/ultramodern/include','.local/deps/N64ModernRuntime/thirdparty','.local/deps/N64ModernRuntime/thirdparty/concurrentqueue']
  r=subprocess.run(['c++','-std=c++20','-Wall','-Wextra','-Werror','-pthread',*['-I'+str(ROOT/i) for i in includes],'-I/home/linuxbrew/.linuxbrew/include/SDL2',str(d/'test.cpp'),str(ROOT/'src/runtime/game_settings_menu.cpp'),'-o',str(cls.binary)],capture_output=True,text=True)
  if r.returncode:raise RuntimeError(r.stderr)
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def run_case(self,name):subprocess.run([str(self.binary),name],check=True,timeout=8)
 def test_consumer_controls_hide_console_accessories_and_technical_glyph_labels(self):self.run_case('transparent')
 def test_all_graphics_cycles_and_draft_cancel(self):self.run_case('graphics')
 def test_four_player_family_cycle_vibration_and_cancel_without_raw_editor(self):self.run_case('ports')
 def test_unlocked_save_failure_exception_retry_and_success(self):self.run_case('save')
 def test_original_font_bounds_and_physical_footer(self):self.run_case('bounds')
 def test_navigation_wrap_back_and_obsolete_callback_never_invoked(self):self.run_case('navigation')

 def test_apply_saves_without_closing_and_cancel_retains_saved_baseline(self):self.run_case("apply")
 def test_user_requested_save_and_framerate_labels(self):self.run_case("consumer_labels")

 def test_semantic_sounds_follow_accepted_navigation_changes_and_save_result(self):self.run_case("sounds")
