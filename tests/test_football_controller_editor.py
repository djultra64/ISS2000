"""Pure original-screen football editor state and held-control safety. Work by djultra64."""
from pathlib import Path
import subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
CODE=r'''#include "runtime/football_controller_editor.hpp"
#include <algorithm>
#include <iostream>
#include <stdexcept>
#include <future>
using namespace iss2000;
void require(bool b,const char*msg){if(!b)throw std::runtime_error(msg);}
std::array<FootballPortConfig,4> configs(){std::array<FootballPortConfig,4> a{};for(unsigned p=0;p<4;++p)std::rotate(a[p].free_bindings.begin(),a[p].free_bindings.begin()+p,a[p].free_bindings.end());a[2].scheme=ControllerScheme::Free;return a;}
FootballEditorInput held(PhysicalControl p){return {physical_control_mask(p)};}
void neutral(FootballControllerEditor&e){require(e.input({}),"neutral input rejected");}
void open(FootballControllerEditor&e){require(e.begin(configs(),2)&&e.open_free(),"validFree entry failed");}
int main(int,char**argv){try{
 std::string name=argv[1];FootballControllerEditor e;auto initial=configs();
 if(name=="begin"){
  const auto before=e.snapshot();auto bad=initial;bad[3].scheme=ControllerScheme(255);
  require(!e.begin(bad)&&e.snapshot()==before,"badlaterport partially initialized session");bad=initial;bad[3].free_bindings[0]=bad[3].free_bindings[1];require(!e.begin(bad)&&e.snapshot()==before,"duplicateFree map initialized session");
  require(!e.begin(initial,4)&&e.snapshot()==before,"invalidselectedport mutated session");require(e.begin(initial,1),"validsession rejected");auto saved=e.snapshot();require(saved.active&&saved.draft==initial&&saved.selected_port==1,"beginlostconfiguredports");require(!e.begin(configs())&&e.snapshot()==saved,"activebeginreplacedunsaveddraft");
 }else if(name=="cycle"){
  require(e.begin(initial),"begin");for(unsigned n=1;n<=6;++n){require(e.cycle_scheme(1),"cycle");auto s=e.snapshot();require(unsigned(s.draft[0].scheme)==n%6,"sixchoiceforwardcyclewrong");require(s.draft[0].free_bindings==initial[0].free_bindings&&s.draft[3]==initial[3],"presetcyclechangedstoredFreeorotherport");}
  require(e.cycle_scheme(-1)&&e.snapshot().draft[0].scheme==ControllerScheme::Free,"reversewrapwrong");auto saved=e.snapshot();require(!e.cycle_scheme(0)&&!e.cycle_scheme(2)&&!e.select_port(4)&&e.snapshot()==saved,"invalidnavigationmutateddraft");
 }else if(name=="entry"){
  require(e.begin(initial)&&!e.open_free(),"presetopenedFree");require(e.select_port(2)&&e.open_free(),"storedFree entry");auto s=e.snapshot();require(s.active&&s.editing_free&&!s.armed&&s.selected_action==0&&s.draft==initial&&s.status==FootballEditorStatus::ReleaseControls,"Freeentrydidnotretaincustommap");require(!e.select_port(1)&&!e.cycle_scheme(1)&&e.snapshot()==s,"editingchangedportorpreset");
 }else if(name=="gate"){
  open(e);const auto before=e.snapshot().draft;auto input=held(PhysicalControl::South);input.start=true;e.input(input);e.input(input);require(e.snapshot().editing_free&&e.snapshot().draft==before,"openingheldbuttonconfirmedoreditedFree");neutral(e);require(e.snapshot().armed,"neutraldidnotarm");
  input={};input.down=true;input.held=physical_control_mask(PhysicalControl::East);e.input(input);require(e.snapshot().selected_action==1&&e.snapshot().draft==before,"Dpadchangedbinding");e.input(input);require(e.snapshot().selected_action==1,"heldDownrepeatedrow");neutral(e);input={};input.up=true;e.input(input);require(e.snapshot().selected_action==0,"Updidnotselectrow");neutral(e);e.input(input);require(e.snapshot().selected_action==7,"Upwrapwrong");
 }else if(name=="swap"){
  open(e);neutral(e);auto expected=initial[2].free_bindings;auto physical=expected[1];require(assign_free(expected,FootballAction::Pass,physical),"testexpected");e.input(held(physical));auto s=e.snapshot();require(s.draft[2].free_bindings==expected&&!s.armed&&s.status==FootballEditorStatus::ReleaseControls,"assignmentdidnotswapoccupiedcontrol");e.input(held(PhysicalControl::North));require(e.snapshot().draft[2].free_bindings==expected,"heldcontrolreassignedwithoutneutral");neutral(e);auto bad=held(PhysicalControl::East);bad.held|=physical_control_mask(PhysicalControl::North);require(!e.input(bad)&&e.snapshot().draft[2].free_bindings==expected,"multibuttonpartiallyassigned");neutral(e);auto saved=e.snapshot();bad.held=0x100;require(!e.input(bad)&&e.snapshot().draft==saved.draft,"foreignmaskchangedconfig");
 }else if(name=="priority"){
  open(e);neutral(e);auto unchanged=e.snapshot().draft;auto i=held(PhysicalControl::South);i.start=true;require(e.input(i),"Startconfirm");require(!e.snapshot().editing_free&&e.snapshot().draft==unchanged,"Start+buttonassignedinsteadconfirm");
  require(e.open_free(),"reopen");neutral(e);e.input(held(initial[2].free_bindings[1]));neutral(e);i={};i.start=true;i.cancel=true;require(e.input(i),"cancel");require(!e.snapshot().editing_free&&e.snapshot().draft==unchanged,"CanceldidnotwinandrestoreFreeentry");
 }else if(name=="end"){
  require(e.begin(initial)&&e.cycle_scheme(1)&&e.select_port(2)&&e.open_free(),"sessionsetup");neutral(e);e.input(held(initial[2].free_bindings[1]));e.end();auto s=e.snapshot();require(!s.active&&!s.editing_free&&!s.armed&&s.draft==initial,"endretaineduncommitteddraft");auto next=initial;next[1].scheme=ControllerScheme::Type5;require(e.begin(next,1)&&e.snapshot().draft==next,"newsessionignoredfreshcommittedpreferences");
 }else if(name=="snapshots"){
  require(e.begin(initial),"begin");auto reader=std::async(std::launch::async,[&]{for(unsigned i=0;i<5000;++i){auto s=e.snapshot();require(s.active&&s.selected_port<4,"tornsnapshot");for(auto&p:s.draft)require(valid_football_bindings(p.free_bindings),"invalidsnapshotmap");}});
  for(unsigned i=0;i<1000;++i){require(e.select_port(i%4)&&e.cycle_scheme(1),"concurrentnavigationfailed");}require(reader.wait_for(std::chrono::seconds(3))==std::future_status::ready,"snapshotdeadlock");reader.get();
 }else return 2;
 return 0;
}catch(const std::exception&ex){std::cerr<<ex.what()<<'\n';return 1;}}
'''
class FootballControllerEditorTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.tmp.cleanup);p=Path(cls.tmp.name);(p/'test.cpp').write_text(CODE);cls.exe=p/'test'
  q=subprocess.run(['c++','-std=c++20','-O1','-Wall','-Wextra','-Werror','-pthread','-I'+str(ROOT/'src'),str(p/'test.cpp'),str(ROOT/'src/runtime/football_controller_editor.cpp'),str(ROOT/'src/runtime/controller_schemes.cpp'),'-o',str(cls.exe)],capture_output=True,text=True)
  if q.returncode:raise RuntimeError(q.stderr)
 def run_case(self,name):
  q=subprocess.run([str(self.exe),name],capture_output=True,text=True,timeout=8);self.assertEqual(q.returncode,0,q.stderr)
 def test_begin_validates_all_ports_atomically(self):self.run_case('begin')
 def test_six_scheme_cycles_preserve_custom_and_other_ports(self):self.run_case('cycle')
 def test_free_entry_retains_stored_custom_and_fixed_owner(self):self.run_case('entry')
 def test_neutral_gate_blocks_opening_start_and_held_dpad(self):self.run_case('gate')
 def test_single_assignment_swaps_and_requires_full_neutral(self):self.run_case('swap')
 def test_start_confirm_and_cancel_priority_restore_entry_draft(self):self.run_case('priority')
 def test_session_end_discards_uncommitted_changes(self):self.run_case('end')
 def test_thread_safe_snapshot_during_port_and_preset_navigation(self):self.run_case('snapshots')
if __name__=='__main__':unittest.main()
