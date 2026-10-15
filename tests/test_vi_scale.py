"""PAL original VI scale factors affect actual next retrace registers."""
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
class ViScaleTests(unittest.TestCase):
 def test_original_fixed_point_scale_and_field_offsets(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp); source=p/'test.cpp'
   source.write_text(r'''#include "runtime/vi_scale.hpp"
#include <stdexcept>
#include <limits>
void check(bool v){if(!v)throw std::runtime_error("VI scale mismatch");}
int main(){
 iss2000::ViScaleState s;
 check(s.x_register(0x12340200)==0x12340200);
 check(s.y_register(0x02000800)==0x02000800);
 s.set_x(0.96f);s.set_y(0.88125f);
 check(s.x_register(0x12340200)==0x123401EB);
 check(s.y_register(0x02000400)==0x02000386);
 check(s.y_register(0x01000800)==0x0100070C);
 s.set_y(1.0f);check(s.y_register(0x01000800)==0x01000800);
 s.set_x(1.0f);check(s.x_register(0x12000200)==0x12000200);
 s.set_y(0);check(s.y_register(0x01000400)==0x01000000);
 s.reset();check(s.x_register(0x200)==0x200);
 try{s.set_y(std::numeric_limits<float>::quiet_NaN());return 3;}catch(const std::invalid_argument&){}
}
''')
   result=subprocess.run(['c++','-std=c++20','-Wall','-Wextra','-Werror','-I',str(ROOT/'src'),str(source),'-o',str(p/'test')],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
   result=subprocess.run([str(p/'test')],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
