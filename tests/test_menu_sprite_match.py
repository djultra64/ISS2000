"""Original project work: djultra64. Exact queued rectangle matching and fractional output; CPU only."""
from pathlib import Path
import shutil,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
CODE=r'''#include "runtime/menu_sprite_render.hpp"
#include <cassert>
#include <cmath>
#include <set>
#include <limits>
using namespace iss2000;
int main(){
 MenuRectSample previous{7,13,0x123,{348,316,476,380},{1,1,1,.2f},{0,0,0,1}};
 auto current=previous;current.rect={380,324,508,388};current.prim[3]=.8f;current.call_index=18;
 MenuRectFrame a{10,3,{previous}},b{11,3,{current}};std::set<float>positions,alphas;
 for(float w:{0.f,.25f,.5f,.75f,1.f}){auto matches=match_menu_rectangles(b,a,w);assert(matches.size()==1);auto&m=matches[0];assert(m.call_index==18&&m.previous==previous.rect);assert(fabs(m.prim[3]-(.2f+.6f*w))<.00001f);positions.insert(m.previous[0]+(current.rect[0]-m.previous[0])*w);alphas.insert(m.prim[3]);}
 assert(positions.size()==5&&alphas.size()==5); // distinct fractional graphics states, not timing changes
 for(unsigned n=0;n<9;++n){auto prev=a,cur=b;float w=.5f;if(n==0)prev.sequence=8;if(n==1)cur.epoch=4;if(n==2)cur.rectangles[0].uid=0;if(n==3)cur.rectangles[0].compatibility^=1;if(n==4)cur.rectangles.push_back(cur.rectangles[0]);if(n==5)prev.rectangles.push_back(prev.rectangles[0]);if(n==6)w=-.1f;if(n==7)w=1.1f;if(n==8)w=std::numeric_limits<float>::quiet_NaN();assert(match_menu_rectangles(cur,prev,w).empty());}
 auto copy=b;auto endpoint=match_menu_rectangles(b,a,1);assert(endpoint[0].prim==current.prim);assert(b.rectangles[0].rect==copy.rectangles[0].rect&&a.rectangles[0].rect==previous.rect);
}
'''
class MenuRectangleMatchTests(unittest.TestCase):
 def test_adjacent_immutable_frames_real_fractional_bounds_fades_and_cuts(self):
  self.assertTrue((ROOT/'src/runtime/menu_sprite_match.cpp').is_file(),'Menu rectangle interpolation not implemented')
  if not shutil.which('c++'):self.skipTest('C++ compiler required')
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);(p/'test.cpp').write_bytes(CODE.encode());q=subprocess.run(['c++','-std=c++20','-O1','-I'+str(ROOT/'src'),str(p/'test.cpp'),str(ROOT/'src/runtime/menu_sprite_match.cpp'),'-o',str(p/'test')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr);q=subprocess.run([str(p/'test')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
