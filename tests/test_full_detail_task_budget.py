"""Original work: djultra64. Full-detail task traversal remains complete and bounded."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = r'''#include "runtime/graphics_task_bank.hpp"
#include "runtime/pal_game_layout.hpp"
#include <cassert>
#include <cstring>
#include <fstream>
#include <string>
#include <vector>
using namespace iss2000;
int main(int argc,char**argv){
 assert(argc>=2);std::vector<uint8_t> ram(0x800000);auto layout=verified_pal_transform_layout();
 auto word=[&](uint32_t a,uint32_t v){std::memcpy(ram.data()+a,&v,4);};
 auto cmd=[&](uint32_t a,uint32_t w,uint32_t v=0){word(a,w);word(a+4,v);};
 const std::string mode=argv[1];uint32_t root=0x1000;
 if(mode=="capture"){
  assert(argc==4);std::ifstream file(argv[2],std::ios::binary);file.read(reinterpret_cast<char*>(ram.data()),ram.size());assert(file.gcount()==ram.size());root=std::stoul(argv[3],nullptr,16);
 }else{
  // A valid task larger than the former16K budget, with a real extended-bank LOAD.
  const uint32_t tail=root+22000*8;
  cmd(tail,0xDA380007,layout.perspective_matrices[0]);
  cmd(tail+8,0xDA380003,layout.extended_arena_base);cmd(tail+16,0xDF000000);
  if(mode=="cycle")cmd(root,0xDE010000,root);
  if(mode=="malformed")cmd(tail+16,0x04000000);
  if(mode=="too_long"){std::fill(ram.begin(),ram.end(),0);cmd(root+200000*8,0xDF000000);}
 }
 const auto before=ram;
 auto result=graphics_task_model_references(ram,root,layout);
 assert(ram==before);
 if(mode=="cycle"||mode=="malformed"||mode=="too_long"){assert(!result);return 0;}
 assert(result&&"Valid all22-player tasks must not lose interpolation maps at16K slots");
 assert(result->perspective_bank&&*result->perspective_bank<2);
 if(mode=="capture")assert(result->loads.size()>2000);
 else assert(result->loads.size()==1&&result->loads[0]==layout.extended_arena_base);
 assert(graphics_task_reaches_list(ram,root,root&0x1fffffff,layout));
}
'''

class FullDetailTaskBudgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        p = Path(cls.temp.name)
        (p / 'test.cpp').write_text(SOURCE)
        cls.binary = p / 'test'
        subprocess.run(['c++', '-std=c++20', '-O1', '-I'+str(ROOT/'src'),
                        str(p/'test.cpp'), str(ROOT/'src/runtime/graphics_task_bank.cpp'),
                        '-o', str(cls.binary)], check=True, capture_output=True)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def run_case(self, *args):
        result = subprocess.run([str(self.binary), *map(str, args)], capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_valid_large_task_preserves_extended_bank_model_and_camera_references(self):
        self.run_case('large')

    def test_cycles_oversized_tasks_and_unsupported_control_flow_remain_rejected(self):
        for mode in ('cycle', 'too_long', 'malformed'):
            with self.subTest(mode=mode):
                self.run_case(mode)

    def test_actual_all22_player_tasks_from_both_preserved_field_banks(self):
        folder = ROOT/'.local/corrections-r55/final'
        files = [folder/'field-final-a.rdram', folder/'field-final-b.rdram']
        if not all(p.is_file() for p in files):
            self.skipTest('Private original game snapshots are not distributed')
        for path in files:
            for root in ('800d0328', '800e0388'):
                with self.subTest(capture=path.name, root=root):
                    self.run_case('capture', path, root)
