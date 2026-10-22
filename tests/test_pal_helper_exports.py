"""Compile real PAL derivatives as separate units; exported entries must exist.

Original project work: djultra64. No game or compiled probe is executed.
"""
import importlib.util
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PalHelperExportTests(unittest.TestCase):
    def test_real_derivative_objects_export_all_entries(self):
        generated = ROOT / '.local/pal-map-bound-01/functions'
        include = ROOT / '.local/deps/N64Recomp/include'
        windows = os.name == 'nt'
        compiler = shutil.which('clang-cl' if windows else 'c++')
        symbols = shutil.which('dumpbin' if windows else 'nm')
        if not (generated.is_dir() and (include / 'recomp.h').is_file() and compiler and symbols):
            self.skipTest('Private original CPU inputs, compiler and symbol inspector required')

        def load(name):
            spec = importlib.util.spec_from_file_location(name, ROOT / ('tools/' + name + '.py'))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module

        cases = []
        for name, original, entry in [
            ('prepare_pal_sky', 'func_80035CC0_resident', 'iss2000_pal_wide_sky'),
            ('prepare_pal_expansion_ui', 'func_802B1FDC_overlay_481680_802b1070', 'iss2000_pal_skip_expansion_notice'),
            ('prepare_pal_auto_storage_ui', 'func_802B1CC8_overlay_481680_802b1070', 'iss2000_pal_automatic_storage_ui'),
            ('prepare_pal_framebuffer_ownership', 'func_8001D480_resident', 'iss2000_pal_framebuffer_allocator'),
            ('prepare_pal_formation_persistence', 'func_802A3464_overlay_3e83d0_8029eea0', 'iss2000_pal_formation_save'),
            ('prepare_pal_fixed_high', 'func_80008C30_resident', 'iss2000_pal_fixed_high_initializer'),
            ('prepare_pal_high_sprites', 'func_807AA008_overlay_515890_807aa000', 'iss2000_pal_high_sprite_edges'),
            ('prepare_pal_native_pace', 'func_80000C30_resident', 'iss2000_pal_native_frame_pace'),
        ]:
            module = load(name)
            cases.append((entry, module.derive((generated / (original + '.c')).read_bytes())))
        for name in ['prepare_pal_max_detail', 'prepare_pal_rumble_ui']:
            module = load(name)
            for key, profile in module.PROFILES.items():
                cases.append((profile['entry'], module.derive(
                    (generated / (profile['original'] + '.c')).read_bytes(), key)))
        module=load("prepare_pal_auto_storage_ui")
        # The callback is compiled together with its initializer and startup
        # helpers in production. Its COFF linkage macro is supplied by that
        # complete unit; an isolated inline fragment is not a build fixture.
        rom=ROOT/'.local/inputs/pal-en-de/rom.z64'
        if not rom.is_file():
            self.skipTest('Private PAL ROM required for the production storage unit')
        with tempfile.TemporaryDirectory(prefix='iss2000-storage-exports-') as staging:
            output=Path(staging)/'source'
            module.prepare(rom,generated/(module.ORIGINAL+'.c'),output)
            cases.append((module.UPDATE_ENTRY,(output/'pal_automatic_storage_ui.cpp').read_bytes()))
        self.assertEqual(len(cases), 16)
        with tempfile.TemporaryDirectory(prefix='iss2000-pal-exports-') as folder:
            folder = Path(folder)
            for entry, data in cases:
                with self.subTest(entry=entry):
                    source = folder / (entry + '.cpp')
                    obj = source.with_suffix('.obj' if windows else '.o')
                    source.write_bytes(data)
                    command = ([compiler, '/nologo', '/c', '/Od', '/GS-', '/I' + str(include), str(source), '/Fo' + str(obj)]
                               if windows else [compiler, '-std=c++20', '-O0', '-c', '-I' + str(include), str(source), '-o', str(obj)])
                    built = subprocess.run(command, capture_output=True, text=True)
                    self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
                    inspected = subprocess.run([symbols, '/symbols' if windows else '--defined-only', str(obj)],
                                               capture_output=True, text=True)
                    self.assertEqual(inspected.returncode, 0, inspected.stderr)
                    pattern = (r'^.*\bSECT\w+\b.*\bExternal\b.*\|\s*' + re.escape(entry) + r'\s*$'
                               if windows else r'^\w+\s+[TW]\s+' + re.escape(entry) + r'\s*$')
                    self.assertRegex(inspected.stdout, re.compile(pattern, re.MULTILINE),
                                     'A separately compiled derivative must define its unmangled external entry')
