"""The host sink transports original already-formatted guest bytes unchanged."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


@unittest.skipUnless((ROOT/'.local/deps/N64Recomp/include/recomp.h').is_file(),
                     'requires pinned private N64Recomp headers, not a ROM')
class DebugConsoleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary=tempfile.TemporaryDirectory()
        cls.root=Path(cls.temporary.name)
        source=cls.root/'debug_console_test.cpp'
        source.write_text(r'''
#include "runtime/debug_console.hpp"
#include <cassert>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>
int main(int argc,char** argv) {
    std::vector<uint8_t> ram(0x800000);
    const unsigned char text[]={'P','C','M',' ','%','d',0,'\n'};
    for(size_t i=0;i<sizeof(text);++i)ram[(0x105+i)^3]=text[i];
    std::string mode=argv[1];
    if(mode=="callback") {
        recomp_context ctx{};ctx.r4=0;ctx.r5=S32(0x80000105);ctx.r6=sizeof(text);
        ctx.r2=77;ctx.r17=0x12345678;
        iss2000::debug_console_callback(ram.data(),&ctx);
        assert(ctx.r2==1 && ctx.r17==0x12345678 && ctx.r5==S32(0x80000105));
    } else if(mode=="bounds") {
        FILE* output=tmpfile();assert(output);
        assert(!iss2000::debug_console_write_bytes(ram.data(),0x7FFFFFFF,1,output));
        assert(!iss2000::debug_console_write_bytes(ram.data(),0x807FFFFF,2,output));
        assert(!iss2000::debug_console_write_bytes(ram.data(),0x80800000,1,output));
        assert(!iss2000::debug_console_write_bytes(nullptr,0x80000000,1,output));
        assert(!iss2000::debug_console_write_bytes(ram.data(),0x80000000,1,nullptr));
        assert(ftell(output)==0);
        ram[0x7FFFFF^3]='!';
        assert(iss2000::debug_console_write_bytes(ram.data(),0x807FFFFF,1,output));
        assert(iss2000::debug_console_write_bytes(ram.data(),0x80800000,0,output));
        rewind(output);assert(fgetc(output)=='!' && fgetc(output)==EOF);fclose(output);
        recomp_context ctx{};ctx.r5=S32(0x807FFFFF);ctx.r6=2;ctx.r2=77;
        iss2000::debug_console_callback(ram.data(),&ctx);assert(ctx.r2==0);
    } else if(mode=="full") {
        FILE* output=fopen("/dev/full","wb");assert(output);
        assert(!iss2000::debug_console_write_bytes(ram.data(),0x80000105,sizeof(text),output));
        fclose(output);
    } else { return 2; }
}
''')
        cls.executable=cls.root/'debug-console-test'
        result=subprocess.run(['c++','-std=c++20','-pthread','-I',str(ROOT/'src'),
            '-I',str(ROOT/'.local/deps/N64Recomp/include'),str(source),
            str(ROOT/'src/runtime/debug_console.cpp'),'-o',str(cls.executable)],
            capture_output=True,text=True)
        if result.returncode:
            raise AssertionError('Debug console adapter build failed: '+result.stderr)

    @classmethod
    def tearDownClass(cls):cls.temporary.cleanup()

    def test_callback_preserves_formatted_bytes_embedded_nul_and_success_abi(self):
        result=subprocess.run([str(self.executable),'callback'],capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stderr,b'PCM %d\0\n')

    def test_invalid_guest_ranges_emit_nothing_and_report_callback_failure(self):
        result=subprocess.run([str(self.executable),'bounds'],capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stderr,b'')

    @unittest.skipUnless(Path('/dev/full').exists(),'requires Linux full-device write failure')
    def test_real_output_failure_is_not_reported_as_success(self):
        result=subprocess.run([str(self.executable),'full'],capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
