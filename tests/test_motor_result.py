"""Original project work: djultra64. Unit policy, no game or SDL execution."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class MotorInitResultTests(unittest.TestCase):
    def test_preserves_error_priority_and_only_translates_absent_controller_pak(self):
        source='''#include "runtime/motor_result.hpp"
int main(){
 using iss2000::PakAccessory;
 for(auto accessory:{PakAccessory::None,PakAccessory::Rumble,PakAccessory::Controller})
   for(int result:{-1,0,1,2,4,5,10,11}){
     const int expected=result==1&&accessory==PakAccessory::Controller?11:result;
     if(iss2000::motor_init_result(result,accessory)!=expected)return 1;
   }
 return 0;
}
'''
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'main.cpp').write_text(source)
            subprocess.run(['c++','-std=c++20','-I'+str(ROOT/'src'),str(root/'main.cpp'),'-o',str(root/'run')],check=True,capture_output=True)
            subprocess.run([str(root/'run')],check=True,capture_output=True)
