"""Original work: djultra64. Reserved PAL banks and immutable interpolation ownership."""
from pathlib import Path
import subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class ExtendedMatrixBankTests(unittest.TestCase):
 def test_both_field_banks_keep_ids_and_original_menu_banks_remain_supported(self):
  code=r'''#include "runtime/pal_game_layout.hpp"
#include "runtime/transform_tracker.hpp"
#include <vector>
#include <cassert>
#include <cstring>
using namespace iss2000;
void put(std::vector<uint8_t>&r,uint32_t a,uint32_t v){memcpy(r.data()+(a&0x7fffff),&v,4);}
int main(){auto l=verified_pal_transform_layout();TransformTracker tracker(l);tracker.begin_scene(0x604);auto owner=tracker.allocate(0x80145624);std::vector<uint8_t>r(0x800000);put(r,0x8009e02c,0x8013b418);r[0x13b429^3]=1;r[0x13b446^3]=6;r[0x13b44c^3]=4;put(r,0x8013b42c,0x014000f0);
 std::shared_ptr<const TransformTaskSnapshot> retained;
 for(unsigned b=0;b<2;++b){put(r,0x8009ded0,b);put(r,0x800b1a48,0x800a7848+b*0x5100);put(r,0x800b1a4c,0x800ac948+b*0x5100);
  assert(extend_pal_field_matrix_arena(r));const uint32_t start=0x807c0000+b*0x10000;
  auto frame=tracker.begin_frame(b,start,start+0x10000);TransformMatrixCapture c{.frame=frame,.record=0x80145624,.flags=0x80000000,.matrix_before=0,.matrix_after=start,.cursor_before=start,.cursor_after=start+64,.flags_after=0x80400000,.builder=TransformMatrixBuilder::Unconditional25710};assert(tracker.capture_matrix(c));
  auto token=tracker.publish_task(frame,0x800d0328);auto snap=tracker.consume_task(token.sequence,0x800d0328);assert(snap&&snap->lookup(start)&&snap->lookup(start)->id==owner.id);if(!b)retained=snap;else assert(retained->lookup(0x807c0000)->id==snap->lookup(start)->id);
 }
 auto menu=tracker.begin_frame(0,0x800a7848,0x800ac948);assert(menu&&retained->lookup(0x807c0000));
 for(unsigned fault=0;fault<6;++fault){auto bad=r;put(bad,0x8009ded0,0);put(bad,0x800b1a48,0x800a7848);put(bad,0x800b1a4c,0x800ac948);
  if(fault==0)bad[0x13b429^3]=0;if(fault==1)bad[0x13b44c^3]=7;if(fault==2)put(bad,0x8009ded0,2);if(fault==3)put(bad,0x800b1a48,0x800a784c);if(fault==4)put(bad,0x8013b42c,0);if(fault==5)put(bad,0x800b1a4c,0x800ac988);auto same=bad;assert(!extend_pal_field_matrix_arena(bad)&&bad==same);}
 for(unsigned b=0;b<2;++b){bool rejected=false;try{tracker.begin_frame(b,0x807c0000+b*0x10000,0x807d0000+b*0x10000+64);}catch(const std::invalid_argument&){rejected=true;}assert(rejected);}
}
'''
  with tempfile.TemporaryDirectory()as directory:
   p=Path(directory);(p/'test.cpp').write_text(code);q=subprocess.run(['c++','-std=c++20','-O1','-pthread','-I'+str(ROOT/'src'),str(p/'test.cpp'),str(ROOT/'src/runtime/transform_tracker.cpp'),'-o',str(p/'test')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr);q=subprocess.run([str(p/'test')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
