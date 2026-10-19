"""Behavioral ownership checks; original project work: djultra64."""
import subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class RadarOwnershipTests(unittest.TestCase):
 def test_bounded_parent_and_generation_ownership(self):
  self.assertTrue((ROOT/'src/runtime/pal_radar_interpolation.cpp').is_file(), 'Radar ownership implementation missing')
  source=r"""
#include "runtime/pal_radar_interpolation.hpp"
#include <cassert>
#include <cstring>
#include <vector>
using namespace iss2000;
static void put(std::vector<uint8_t>&r,uint32_t p,uint32_t v){memcpy(r.data()+(p&0x7fffff),&v,4);}
int main(){
 std::vector<uint8_t> r(0x800000);constexpr uint32_t list=0x802b4408, root=0x800d0328;
 put(r,root,0xde000000);put(r,root+4,list);put(r,root+8,0xdf000000);
 put(r,list,0xe4001040);put(r,list+4,0);put(r,list+8,0xe1000000);put(r,list+16,0xf1000000);put(r,list+20,0x04000400);put(r,list+24,0xdf000000);
 PalRadarCapture c;TransformTag owner{1,0x145624,1,1},actor{2,0x1456bc,4,1};
 assert(c.begin(r,owner,0,list));assert(c.emit(r,list,list+24,actor,7));assert(c.finish(r,list+32));
 assert(c.commands().size()==1);assert(c.reachable(r,root));auto original=r;
 assert(!c.reachable(r,root+8));put(r,list+12,17);assert(!c.reachable(r,root));r=original;
 assert(c.reachable(r,root));assert(r==original);
 assert(!c.emit(r,list,list+24,actor,7));
 PalRadarCapture wrong;assert(!wrong.begin(r,owner,2,list));assert(!wrong.begin(r,owner,1,list));
 assert(wrong.begin(r,owner,0,list));assert(!wrong.emit(r,list,list+16,actor,7));
 assert(wrong.begin(r,owner,0,list));assert(wrong.emit(r,list,list+24,actor,7));assert(!wrong.emit(r,list,list+24,actor,8));
 assert(wrong.begin(r,owner,0,list));actor.generation=0;assert(!wrong.emit(r,list,list+24,actor,7));
 assert(wrong.begin(r,owner,0,list));actor.generation=4;assert(wrong.emit(r,list,list+24,actor,7));assert(!wrong.finish(r,list+0x968));
 put(r,root,0xde010000);put(r,root+4,root);assert(!c.reachable(r,root));
}
"""
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);(p/'test.cpp').write_text(source)
   cmd=['c++','-std=c++20','-O1','-I'+str(ROOT/'src'),str(p/'test.cpp'),str(ROOT/'src/runtime/pal_radar_interpolation.cpp'),str(ROOT/'src/runtime/graphics_task_bank.cpp'),'-o',str(p/'test')]
   q=subprocess.run(cmd,capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
   q=subprocess.run([str(p/'test')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
