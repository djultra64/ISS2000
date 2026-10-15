"""Original project work: djultra64. Actual RT64 policy enums; no game execution."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
RT64 = ROOT / '.local/deps/rt64/src'

@unittest.skipUnless(shutil.which('c++') and (RT64/'common/rt64_enhancement_configuration.h').is_file(),
                     'Compiler and pinned RT64 headers required')
class RT64PresentationPolicyTests(unittest.TestCase):
    def test_enhanced_refresh_selects_history_checked_buffering_and_original_restores_console(self):
        source = r'''#include "runtime/rt64_presentation_policy.hpp"
#include <cassert>
using namespace iss2000;
int main(){
 using Mode=RT64::EnhancementConfiguration::Presentation::Mode;
 // Manual output requires the engine to select a recently presented color
 // buffer, rather than leave interpolation disabled on a rotating buffer.
 auto mode=rt64_presentation_mode(RenderRefresh::Original);
 assert(mode==Mode::Console);
 for(auto refresh:{RenderRefresh::Hz60,RenderRefresh::Hz120}){
  mode=rt64_presentation_mode(refresh);assert(mode==Mode::SkipBuffering);
  mode=rt64_presentation_mode(RenderRefresh::Original);assert(mode==Mode::Console);
 }
 assert(rt64_presentation_mode(static_cast<RenderRefresh>(99))==Mode::Console);
}
'''
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);(folder/'main.cpp').write_text(source)
            result=subprocess.run(['c++','-std=c++20','-Wall','-Wextra','-Werror',
                '-I'+str(ROOT/'src'),'-isystem',str(RT64),'-isystem',str(RT64/'contrib/hlslpp/include'),
                str(folder/'main.cpp'),'-o',str(folder/'test')],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(folder/'test')],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
