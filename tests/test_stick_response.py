"""Original work: djultra64. Physical stick precision and genuine guest conversion."""
from pathlib import Path
import re,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class StickResponseTests(unittest.TestCase):
 def test_precision_curve_preserves_full_speed_and_removes_deadzone_jump(self):
  s=(ROOT/'.local/deps/N64ModernRuntime/ultramodern/src/input.cpp').read_text();original=re.search(r'void convert_to_n64_range\(.*?\n\}',s,re.S).group()
  code='''#include "runtime/stick_response.hpp"
#include <cmath>
#include <cstdint>
#include <cassert>
'''+original+'''
int main(){using iss2000::gameplay_stick_response;
 for(float v:{-.14f,0.f,.14f}){auto s=gameplay_stick_response(v,0);assert(s.x==0&&s.y==0);}
 int8_t previous=0;for(int n=150;n<=1000;++n){float raw=n/1000.f;auto s=gameplay_stick_response(raw,0);int8_t x,y;convert_to_n64_range(s.x,s.y,x,y);assert(x>=previous);previous=x;
  if(n==151)assert(x==0);if(n==300)assert(x>0&&x<12);if(n==500)assert(x>15&&x<30);}
 for(auto xy:{iss2000::StickPosition{1,0},{0,1},{-1,0},{0,-1},{.70710678f,.70710678f}}){auto s=gameplay_stick_response(xy.x,xy.y);int8_t a,b,c,d;convert_to_n64_range(xy.x,xy.y,a,b);convert_to_n64_range(s.x,s.y,c,d);assert(std::abs(int(a)-c)<=1&&std::abs(int(b)-d)<=1);}
 auto diagonal=gameplay_stick_response(.4f,.4f);assert(diagonal.x==diagonal.y&&diagonal.x>0&&diagonal.x<.4f);
 auto negative=gameplay_stick_response(-.4f,-.4f);assert(negative.x==-diagonal.x&&negative.y==-diagonal.y);
 auto invalid=gameplay_stick_response(NAN,0);assert(invalid.x==0&&invalid.y==0);
}
'''
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);(p/'test.cpp').write_text(code);q=subprocess.run(['c++','-std=c++20','-O1','-I'+str(ROOT/'src'),str(p/'test.cpp'),'-o',str(p/'test')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr);q=subprocess.run([str(p/'test')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
