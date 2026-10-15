"""RSP dispatch must select the exact program of the compiled revision."""
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
class AudioRspTests(unittest.TestCase):
    def test_pal_and_us_program_addresses_are_isolated(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp); source=p/'rsp.cpp'
            source.write_text(r'''#include "runtime/audio_rsp.hpp"
#include <vector>
#include <cstring>
int main(){
 std::vector<uint8_t> ram(0x800000);uint32_t a=0x20180360,b=0x20170F90;
 auto code=iss2000::active_revision().audio_ucode;
 std::memcpy(ram.data()+code,&a,4);std::memcpy(ram.data()+code+4,&b,4);
 if(!iss2000::matches_audio_rsp(ram,2,code))return 1;
 if(!iss2000::matches_audio_rsp(ram,2,0x80000000u|code))return 2;
 if(iss2000::matches_audio_rsp(ram,1,code))return 3;
 if(iss2000::matches_audio_rsp(ram,2,code==0x6B770?0x6BFF0:0x6B770))return 4;
 a=0;std::memcpy(ram.data()+code,&a,4);
 if(iss2000::matches_audio_rsp(ram,2,code))return 5;
 if(iss2000::matches_audio_rsp(std::span<const uint8_t>{},2,code))return 6;
}
''')
            for pal in (False,True):
                exe=p/('pal' if pal else 'us')
                build=subprocess.run(['c++','-std=c++20','-Wall','-Wextra','-Werror',*(['-DISS2000_PAL_ENGLISH'] if pal else []),'-I',str(ROOT/'src'),str(source),'-o',str(exe)],capture_output=True,text=True)
                self.assertEqual(build.returncode,0,build.stderr)
                result=subprocess.run([str(exe)],capture_output=True,text=True)
                self.assertEqual(result.returncode,0,result.stderr)
