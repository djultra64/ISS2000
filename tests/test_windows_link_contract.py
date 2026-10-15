"""Configure the real platform-link block using synthetic libraries, not Windows."""
from pathlib import Path
import subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class WindowsLinkContractTests(unittest.TestCase):
    def configure(self,missing=False):
        with tempfile.TemporaryDirectory(prefix='iss2000-windows-link-') as t:
            p=Path(t);deps=p/'deps/src/contrib/dxc/lib/x64';deps.mkdir(parents=True)
            if not missing:(deps/'dxcompiler.lib').write_bytes(b'synthetic import library')
            cmake=(ROOT/'cmake/game.cmake').read_text();start=cmake.index('target_link_libraries(iss2000 PRIVATE SDL2::SDL2 Threads::Threads ${CMAKE_DL_LIBS})');end=cmake.index('set_source_files_properties(src/renderer.cpp',start)
            (p/'probe.cpp').write_text('int main(){return 0;}')
            (p/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\nproject(LinkProbe LANGUAGES CXX)\nadd_executable(iss2000 probe.cpp)\nadd_library(SDL2::SDL2 INTERFACE IMPORTED)\nadd_library(Threads::Threads INTERFACE IMPORTED)\nset(WIN32 TRUE)\nset(UNIX FALSE)\nset(CMAKE_DL_LIBS "")\nset(ISS2000_RT64_SOURCE "'+(p/'deps').as_posix()+'")\n'+cmake[start:end]+'\nget_target_property(links iss2000 LINK_LIBRARIES)\nfile(WRITE "${CMAKE_BINARY_DIR}/links.txt" "${links}")\n')
            run=subprocess.run(['cmake','-S',str(p),'-B',str(p/'build')],capture_output=True,text=True)
            return run,(p/'build/links.txt').read_text() if (p/'build/links.txt').exists() else ''
    def test_windows_sdk_and_dxc_imports_survive_flattened_archives(self):
        run,links=self.configure();self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        for name in ['delayimp','D3D12','DXGI','Shcore','ole32','shell32','uuid','user32','dxcompiler.lib']:
            self.assertIn(name,links)
    def test_absent_windows_dxc_import_library_is_rejected(self):
        run,_=self.configure(missing=True);self.assertNotEqual(run.returncode,0)
        self.assertIn('DXC',run.stdout+run.stderr)
