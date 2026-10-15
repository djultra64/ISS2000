"""The native importer accepts only the revision compiled into its build."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
MINIZ=ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz'
ARCHIVE=ROOT/'.local/runtime-deps-build/librecomp/miniz/libminiz.a'
class NativeRomRevisionTests(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('ISS2000_PAL_ROM') and os.environ.get('ISS2000_ROM'),'set both private ROM paths')
    def test_build_revision_selects_exact_input_and_rejects_other_region(self):
        if not shutil.which('c++') or not ARCHIVE.exists():self.skipTest('requires C++ compiler and pinned miniz build')
        with tempfile.TemporaryDirectory(prefix='iss2000-revision-') as tmp:
            p=Path(tmp); source=p/'read.cpp'
            source.write_text(r'''#include "runtime/rom_image.hpp"
#include <iostream>
int main(int,char**argv){try{auto b=iss2000::read_rom_image(argv[1]);std::cout<<b.size();return 0;}catch(const std::exception& e){std::cerr<<e.what();return 1;}}
''')
            for pal in (False,True):
                exe=p/('pal' if pal else 'us')
                args=['c++','-std=c++20','-O2','-I'+str(ROOT/'src'),'-I'+str(MINIZ),'-I'+str(ARCHIVE.parent),str(source),str(ROOT/'src/runtime/rom_image.cpp'),str(ARCHIVE),'-o',str(exe)]
                if pal:args.append('-DISS2000_PAL_ENGLISH')
                build=subprocess.run(args,capture_output=True,text=True)
                self.assertEqual(build.returncode,0,build.stderr)
                for candidate in (False,True):
                    result=subprocess.run([str(exe),os.environ['ISS2000_PAL_ROM' if candidate else 'ISS2000_ROM']],capture_output=True,text=True)
                    self.assertEqual(result.returncode,0 if candidate==pal else 1,result.stderr)
                    if candidate==pal:self.assertEqual(result.stdout,'16777216')
