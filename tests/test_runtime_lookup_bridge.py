"""Link tests for the portable source-specific runtime lookup bridge."""
import json
import os
import sys
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / 'cmake/runtime_lookup_bridge.cmake'
COMPILER_AVAILABLE = any(shutil.which(name) for name in ('c++', 'clang-cl', 'cl'))
BUILD_TOOLS_AVAILABLE = shutil.which('cmake') and COMPILER_AVAILABLE and (os.name != 'nt' or shutil.which('ninja'))
CMAKE_GENERATOR = ['-G', 'Ninja'] if shutil.which('ninja') else []

@unittest.skipUnless(BUILD_TOOLS_AVAILABLE, 'CMake, C++ compiler and native build tool required')
class RuntimeLookupBridgeTests(unittest.TestCase):
    def build_fixture(self, automatic):
        with tempfile.TemporaryDirectory(prefix='iss2000 lookup bridge ') as directory:
            source = Path(directory)
            runtime = source / 'runtime'
            runtime.mkdir()
            (runtime / 'CMakeLists.txt').write_text('project(NestedRuntime LANGUAGES CXX)\nadd_library(librecomp STATIC overlays.cpp thread.cpp)\n')
            (runtime / 'overlays.cpp').write_text('extern "C" int get_function(int x) { return x + 17; }\nextern "C" int retained_overlay_symbol() { return 5; }\n')
            (runtime / 'thread.cpp').write_text('extern "C" int get_function(int);\nextern "C" int thread_entry_lookup() { return get_function(3); }\n')
            (source / 'main.cpp').write_text('extern "C" int get_function(int x) { return x + 29; }\nextern "C" int iss2000_upstream_get_function(int);\nextern "C" int thread_entry_lookup();\nextern "C" int retained_overlay_symbol();\nint main() { return thread_entry_lookup()==32 && iss2000_upstream_get_function(3)==20 && retained_overlay_symbol()==5 ? 0 : 1; }\n')
            lines = ['cmake_minimum_required(VERSION 3.20)', 'project(BridgeFixture LANGUAGES CXX)',
                     'set(CMAKE_EXPORT_COMPILE_COMMANDS ON)', 'add_subdirectory(runtime)']
            if not automatic:
                lines += [f'include("{HOOK.as_posix()}")', 'iss2000_enable_runtime_lookup_bridge(librecomp)', 'iss2000_enable_runtime_lookup_bridge(librecomp)']
            lines += ['add_executable(probe main.cpp)', 'target_link_libraries(probe PRIVATE librecomp)']
            (source / 'CMakeLists.txt').write_text('\n'.join(lines))
            command = ['cmake', '-S', str(source), '-B', str(source / 'build'), *CMAKE_GENERATOR]
            if automatic:
                command += [f'-DCMAKE_PROJECT_INCLUDE={HOOK}', '-DISS2000_RUNTIME_LOOKUP_BRIDGE_AUTO=ON']
            configured = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(configured.returncode, 0, configured.stdout + configured.stderr)
            built = subprocess.run(['cmake', '--build', str(source / 'build')], capture_output=True, text=True)
            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
            executable = source / ('build/probe.exe' if os.name == 'nt' else 'build/probe')
            self.assertEqual(subprocess.run([str(executable)]).returncode, 0)
            commands = json.loads((source / 'build/compile_commands.json').read_text())
            for entry in commands:
                self.assertEqual('get_function=iss2000_upstream_get_function' in entry['command'], Path(entry['file']).name == 'overlays.cpp')
            self.assertNotIn('iss2000_upstream_get_function', (runtime / 'overlays.cpp').read_text())

    def test_explicit_target_hook_links_and_is_idempotent(self):
        self.build_fixture(False)

    def test_deferred_project_hook_links(self):
        self.build_fixture(True)

    def test_missing_overlay_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source / 'thread.cpp').write_text('int x;')
            (source / 'CMakeLists.txt').write_text(f'cmake_minimum_required(VERSION 3.20)\nproject(Invalid LANGUAGES CXX)\nadd_library(librecomp STATIC thread.cpp)\ninclude("{HOOK.as_posix()}")\niss2000_enable_runtime_lookup_bridge(librecomp)\n')
            result = subprocess.run(['cmake', '-S', str(source), '-B', str(source / 'build'), *CMAKE_GENERATOR], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('exactly one overlays.cpp', result.stdout + result.stderr)


@unittest.skipUnless(BUILD_TOOLS_AVAILABLE, 'CMake, C++ compiler and native build tool required')
class RuntimeLookupModeTests(unittest.TestCase):
    # Missing source-only rename, a target-wide rename, or choosing WRAP for a
    # renamed archive must break these real static-library/external-caller links.
    def configure(self, directory, mode, bridge):
        source = Path(directory)
        runtime = source / 'runtime'
        runtime.mkdir()
        (runtime / 'CMakeLists.txt').write_text('add_library(librecomp STATIC overlays.cpp thread.cpp)\n')
        (runtime / 'overlays.cpp').write_text('extern "C" int get_function(int x) { return x + 17; }\nextern "C" int retained_overlay_symbol() { return 5; }\n')
        (runtime / 'thread.cpp').write_text('extern "C" int get_function(int);\nextern "C" int thread_entry_lookup(int x) { return get_function(x); }\n')
        (source / 'main.cpp').write_text('''#include <cstdlib>
#ifdef ISS2000_LOOKUP_DIRECT
extern "C" int get_function(int x) {
#else
extern "C" int __wrap_get_function(int x) {
#endif
    if (x != 3) std::exit(47);
    return 32;
}
extern "C" int thread_entry_lookup(int);
extern "C" int retained_overlay_symbol();
#ifdef ISS2000_LOOKUP_DIRECT
extern "C" int iss2000_upstream_get_function(int);
#endif
int main(int argc, char**) {
    if (argc > 1) return thread_entry_lookup(99);
    if (thread_entry_lookup(3) != 32 || retained_overlay_symbol() != 5) return 1;
#ifdef ISS2000_LOOKUP_DIRECT
    if (iss2000_upstream_get_function(3) != 20) return 2;
#endif
    return 0;
}
''')
        lines = ['cmake_minimum_required(VERSION 3.20)', 'project(ModeFixture LANGUAGES CXX)',
                 f'include("{HOOK.as_posix()}")', 'add_subdirectory(runtime)']
        if bridge:
            lines += ['iss2000_enable_runtime_lookup_bridge(librecomp)']
        lines += ['add_executable(probe main.cpp)',
                  'iss2000_configure_runtime_lookup(probe "${CMAKE_BINARY_DIR}")',
                  'target_link_libraries(probe PRIVATE librecomp)']
        (source / 'CMakeLists.txt').write_text('\n'.join(lines))
        result = subprocess.run(['cmake', '-S', str(source), '-B', str(source / 'build'),
                                 f'-DISS2000_RUNTIME_LOOKUP_MODE={mode}', *CMAKE_GENERATOR], capture_output=True, text=True)
        return source, result

    def assert_linked(self, mode, bridge):
        with tempfile.TemporaryDirectory(prefix='iss2000 lookup mode ') as directory:
            source, result = self.configure(directory, mode, bridge)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result = subprocess.run(['cmake', '--build', str(source / 'build')], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            executable = source / ('build/probe.exe' if os.name == 'nt' else 'build/probe')
            self.assertEqual(subprocess.run([str(executable)]).returncode, 0)
            self.assertEqual(subprocess.run([str(executable), '--unknown']).returncode, 47)
            return result

    def test_direct_uses_project_registry_for_runtime_callers_and_unknowns(self):
        self.assert_linked('DIRECT', True)

    @unittest.skipUnless(sys.platform.startswith('linux'), 'GNU ELF wrapping fixture requires Linux')
    def test_wrap_retains_project_registry_and_unknown_failure(self):
        self.assert_linked('WRAP', False)

    def test_direct_rejects_unrenamed_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            _, result = self.configure(directory, 'DIRECT', False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('source-specific lookup bridge', ' '.join((result.stdout + result.stderr).split()))

    def test_wrap_rejects_renamed_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            _, result = self.configure(directory, 'WRAP', True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('unrenamed runtime', result.stdout + result.stderr)

    def test_unknown_lookup_mode_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            _, result = self.configure(directory, 'IGNORED', False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('AUTO, DIRECT or WRAP', result.stdout + result.stderr)
