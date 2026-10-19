"""Original project work: djultra64. Exit is an explicit logical modal action."""
from pathlib import Path
import subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
CODE=r'''
#include "runtime/main_exit_menu.hpp"
#include <cassert>
using namespace iss2000;
int main(){MainExitMenu menu;MainExitInput i{};i.focused=true;menu.publish(true);
 i.north=i.any=true;assert(!menu.input(i).quit&&!menu.view().open); // Held during scene entry.
 i={};i.focused=true;menu.input(i);i.north=i.any=true;assert(menu.input(i).suppress&&menu.view().open&&!menu.view().yes);
 i.accept=true;assert(!menu.input(i).quit); // Opening/held shortcut cannot confirm.
 i={};i.focused=true;menu.input(i);i.accept=i.any=true;assert(!menu.input(i).quit&&!menu.view().open); // No default.
 assert(menu.input(i).suppress);i={};i.focused=true;assert(!menu.input(i).suppress);
 for(unsigned device=0;device<8;++device){i={};i.focused=true;i.device=device;menu.input(i);i.north=i.any=true;menu.input(i);assert(menu.view().open&&!menu.view().yes);
  i={};i.focused=true;i.device=device;menu.input(i);i.right=i.any=true;menu.input(i);assert(menu.view().yes);assert(!menu.input(i).quit);
  i.device=device+20;assert(!menu.input(i).quit&&!menu.view().yes); // New device defaults to No.
  i={};i.focused=true;i.device=device+20;menu.input(i);i.right=i.any=true;menu.input(i);i.right=false;i.any=false;menu.input(i);i.accept=i.any=true;assert(menu.input(i).quit);
  i={};i.focused=true;i.device=device+20;menu.input(i);
 }
 i={};i.focused=true;menu.input(i);i.north=i.any=true;menu.input(i);assert(menu.view().open);i.focused=false;menu.input(i);assert(!menu.view().yes);menu.publish(false);assert(!menu.view().open);assert(menu.input(i).suppress);i={};i.focused=true;assert(!menu.input(i).suppress);
 menu.publish(true);menu.input(i);i.north=i.any=true;menu.input(i);i={};i.focused=true;menu.input(i);i.cancel=i.any=true;assert(menu.input(i).suppress&&!menu.view().open);assert(menu.input(i).suppress);
}
'''
class MainExitMenuTests(unittest.TestCase):
 def test_default_no_edges_device_changes_and_closing_release(self):
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);(p/'test.cpp').write_text(CODE)
   q=subprocess.run(['c++','-std=c++20','-Wall','-Wextra','-Werror','-pthread','-I'+str(ROOT/'src'),str(p/'test.cpp'),'-o',str(p/'test')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
   q=subprocess.run([str(p/'test')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
