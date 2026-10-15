"""Paired world/edge calculations use the target aspect without changing RAM."""
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
class MarkerAspectTests(unittest.TestCase):
    def test_projection_inverse_and_indicator_angle_share_one_aspect(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);s=p/'aspect.cpp'
            s.write_text(r'''#include "runtime/marker_aspect.hpp"
#include <cmath>
#include <limits>
#include <stdexcept>
void check(bool x){if(!x)throw std::runtime_error("Marker projection mismatch");}
int main(){
 for(bool wide:{false,true}){
  const float aspect=iss2000::marker_aspect(4.f/3.f,wide);
  check(std::abs(aspect-(wide?16.f/9.f:4.f/3.f))<1e-6);
  for(float x:{-140.f,-20.f,0.f,30.f,160.f}){
   const float y=35,vertical=100;
   const float nx=x/(vertical*aspect),ny=y/vertical;
   check(std::abs(nx*vertical*aspect-x)<1e-4);
   check(std::abs(ny*vertical-y)<1e-4);
   check(std::abs(std::atan2(nx*aspect,ny)-std::atan2(x,y))<1e-6);
  }
 }
 check(iss2000::marker_aspect(16.f/9.f,true)==16.f/9.f);
 check(iss2000::marker_aspect(2.f,true)==2.f);
 check(std::isnan(iss2000::marker_aspect(std::numeric_limits<float>::quiet_NaN(),true)));
}
''')
            exe=p/'aspect';b=subprocess.run(['c++','-std=c++20','-Wall','-Wextra','-Werror','-I',str(ROOT/'src'),str(s),'-o',str(exe)],capture_output=True,text=True)
            self.assertEqual(b.returncode,0,b.stderr)
            result=subprocess.run([str(exe)],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
