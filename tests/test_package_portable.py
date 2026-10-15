"""Portable layout and launcher contracts, exercised without a game or ROM."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

from tools.package_portable import package


class PortablePackageTests(unittest.TestCase):
    def test_linux_launcher_handles_spaces_cwd_environment_and_arguments(self):
        with tempfile.TemporaryDirectory(prefix='portable package ') as temporary:
            root=Path(temporary); source=root/'original game';source.write_text(
                '#!/bin/sh\nprintf "%s\\n" "$PWD" "$LD_LIBRARY_PATH" "$@"\n')
            source.chmod(0o755)
            library=root/'libaudio.so.1';library.write_bytes(b'synthetic dependency')
            rom=root/'private-rom.z64';rom.write_bytes(b'never package me')
            output=root/'Linux portable folder'
            package('linux',source,output,[library])
            environment=dict(os.environ,LD_LIBRARY_PATH='/existing library path')
            run=subprocess.run([str(output/'launch.sh'),'two words','literal;$(nothing)'],
                cwd=root,env=environment,text=True,capture_output=True,check=True)
            self.assertEqual(run.stdout.splitlines(),[str(output),
                str(output/'lib')+':/existing library path','two words','literal;$(nothing)'])
            self.assertEqual((output/'lib/libaudio.so.1').read_bytes(),b'synthetic dependency')
            self.assertTrue((output/'data').is_dir())
            self.assertTrue((output/'screenshots').is_dir())
            self.assertFalse((output/rom.name).exists())
            self.assertEqual(source.read_text(),'#!/bin/sh\nprintf "%s\\n" "$PWD" "$LD_LIBRARY_PATH" "$@"\n')

    def test_linux_launcher_works_without_preexisting_library_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'game'
            source.write_text('#!/bin/sh\nprintf "%s" "$LD_LIBRARY_PATH"\n')
            source.chmod(0o755)
            output=root/'portable'
            package('linux',source,output)
            environment=dict(os.environ);environment.pop('LD_LIBRARY_PATH',None)
            run=subprocess.run([str(output/'launch.sh')],env=environment,text=True,capture_output=True,check=True)
            self.assertEqual(run.stdout,str(output/'lib'))

    def test_windows_copies_only_explicit_executable_and_root_dlls_without_running(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'ISS2000.exe';source.write_bytes(b'synthetic exe')
            library=root/'SDL3.dll';library.write_bytes(b'synthetic dll')
            output=root/'windows'
            package('windows',source,output,[library])
            self.assertEqual((output/'ISS2000.exe').read_bytes(),b'synthetic exe')
            self.assertEqual((output/'SDL3.dll').read_bytes(),b'synthetic dll')
            self.assertFalse((output/'launch.sh').exists())
            self.assertTrue((output/'data').is_dir())

    def test_dependency_symlink_is_copied_as_regular_file_without_modifying_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'game';source.write_bytes(b'game')
            actual=root/'actual library';actual.write_bytes(b'dependency')
            link=root/'libsound.so.2';link.symlink_to(actual)
            output=root/'portable';package('linux',source,output,[link])
            self.assertFalse((output/'lib/libsound.so.2').is_symlink())
            self.assertEqual((output/'lib/libsound.so.2').read_bytes(),b'dependency')
            self.assertTrue(link.is_symlink())
            self.assertEqual(actual.read_bytes(),b'dependency')

    def test_invalid_inputs_fail_before_creating_output_or_changing_existing_tree(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'game';source.write_bytes(b'game')
            dll=root/'audio.dll';dll.write_bytes(b'dll')
            so=root/'libaudio.so';so.write_bytes(b'so')
            private=root/'rom.z64';private.write_bytes(b'private')
            output=root/'portable'
            cases=[('other',source,[]),('linux',root/'missing',[]),
                   ('linux',source,[private]),('linux',source,[dll]),
                   ('windows',source,[so]),('linux',source,[root/'missing.so']),
                   ('linux',source,[so,so])]
            for platform,exe,libraries in cases:
                with self.subTest(platform=platform,exe=exe,libraries=libraries):
                    with self.assertRaises(ValueError):package(platform,exe,output,libraries)
                    self.assertFalse(output.exists())
            output.mkdir();(output/'keep.txt').write_text('keep')
            with self.assertRaises(ValueError):package('linux',source,output)
            self.assertEqual((output/'keep.txt').read_text(),'keep')
            self.assertEqual(source.read_bytes(),b'game')

    def test_output_cannot_contain_input_or_follow_symlinked_output_parent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);inputs=root/'inputs';inputs.mkdir()
            source=inputs/'game';source.write_bytes(b'game')
            alias=root/'alias';alias.symlink_to(inputs,target_is_directory=True)
            for output in [inputs,alias/'portable',source/'nested']:
                with self.subTest(output=output),self.assertRaises(ValueError):
                    package('linux',source,output)
            self.assertEqual(source.read_bytes(),b'game')

    def test_copy_failure_removes_only_the_new_partial_package(self):
        from unittest.mock import patch
        import shutil
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'game';source.write_bytes(b'game')
            library=root/'libaudio.so';library.write_bytes(b'library')
            output=root/'portable';original_copy=shutil.copy2
            def fail_dependency(src,dst,*args,**kwargs):
                if Path(src)==library:
                    raise OSError('synthetic I/O failure')
                return original_copy(src,dst,*args,**kwargs)
            with patch('tools.package_portable.shutil.copy2',side_effect=fail_dependency):
                with self.assertRaises(OSError):package('linux',source,output,[library])
            self.assertFalse(output.exists())
            self.assertEqual(source.read_bytes(),b'game')
            self.assertEqual(library.read_bytes(),b'library')

    def test_windows_dependency_collisions_are_case_insensitive(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'ISS2000.exe';source.write_bytes(b'exe')
            upper=root/'SDL3.dll';upper.write_bytes(b'a')
            lower=root/'sdl3.DLL';lower.write_bytes(b'b')
            output=root/'portable'
            with self.assertRaises(ValueError):package('windows',source,output,[upper,lower])
            self.assertFalse(output.exists())


class PortableNoticeTests(unittest.TestCase):
    def test_explicit_notices_preserve_bytes_and_original_authors(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);exe=root/'game';exe.write_bytes(b'game')
            notice=root/'LICENSE';body=b'MIT License\nCopyright Original Author\n';notice.write_bytes(body)
            out=root/'out';package('linux',exe,out,notices=[(notice,'RT64-LICENSE.txt')])
            self.assertEqual((out/'licenses/RT64-LICENSE.txt').read_bytes(),body)
            self.assertEqual(notice.read_bytes(),body)
            self.assertFalse((out/'licenses/LICENSE').exists())
    def test_invalid_notice_destinations_and_binary_fail_before_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);exe=root/'game';exe.write_bytes(b'game')
            notice=root/'LICENSE';notice.write_text('license')
            binary=root/'binary';binary.write_bytes(b'\xff\x00')
            for notices in [[(notice,'../escape')],[(notice,'/absolute')],[(notice,'nested/license.txt')],[(notice,'CON.txt')],[(notice,'license.')],
                            [(notice,'same.txt'),(notice,'SAME.TXT')],[(binary,'binary.txt')],[(root/'missing','license.txt')]]:
                out=root/'out'
                with self.subTest(notices=notices),self.assertRaises(ValueError):package('linux',exe,out,notices=notices)
                self.assertFalse(out.exists())
            self.assertEqual(notice.read_text(),'license')
    def test_notice_symlink_keeps_selected_destination_filename(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);exe=root/'game';exe.write_bytes(b'game')
            actual=root/'actual';actual.write_text('copyright');link=root/'COPYING';link.symlink_to(actual)
            out=root/'out';package('windows',self.exe(root),out,notices=[(link,'Dependency.txt')])
            self.assertFalse((out/'licenses/Dependency.txt').is_symlink());self.assertTrue(link.is_symlink())
            self.assertEqual((out/'licenses/Dependency.txt').read_text(),'copyright')
    def exe(self,root):
        path=root/'game.exe';path.write_bytes(b'exe');return path
    def test_cli_accepts_repeatable_explicit_notice_mapping(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);exe=root/'game';exe.write_bytes(b'game')
            a=root/'LICENSE';a.write_text('A');b=root/'COPYING';b.write_text('B');out=root/'out'
            run=subprocess.run([__import__('sys').executable,'-m','tools.package_portable','--platform','linux','--executable',str(exe),'--output',str(out),'--notice',str(a)+'=A.txt','--notice',str(b)+'=B.txt'],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertEqual((out/'licenses/A.txt').read_text(),'A');self.assertEqual((out/'licenses/B.txt').read_text(),'B')

class WindowsPortableFilenameTests(unittest.TestCase):
    def test_reserved_executable_names_fail_before_output_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            for name in ['CON.exe','nul.exe','AUX.exe','LPT1.exe','COM9.exe','NUL .exe']:
                exe=root/name;exe.write_bytes(b'synthetic executable');out=root/'out'
                with self.subTest(name=name),self.assertRaises(ValueError):package('windows',exe,out)
                self.assertFalse(out.exists())
    def test_reserved_dll_names_fail_before_output_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);exe=root/'game.exe';exe.write_bytes(b'synthetic executable')
            for name in ['NUL.dll','con.DLL','COM1.dll','LPT9.dll','PRN .dll']:
                dll=root/name;dll.write_bytes(b'synthetic library');out=root/'out'
                with self.subTest(name=name),self.assertRaises(ValueError):package('windows',exe,out,[dll])
                self.assertFalse(out.exists())

class PortableBuildMetadataTests(unittest.TestCase):
    def test_default_pal_metadata_pins_only_relative_packaged_files(self):
        import hashlib,json
        with tempfile.TemporaryDirectory(prefix='private developer ') as t:
            root=Path(t);exe=root/'iss2000';exe.write_bytes(b'synthetic binary');lib=root/'libaudio.so.1';lib.write_bytes(b'synthetic library');notice=root/'COPYING';notice.write_text('Original author license')
            out=root/'out';package('linux',exe,out,[lib],[(notice,'Runtime.txt')])
            raw=(out/'build-info.json').read_text();info=json.loads(raw)
            self.assertNotIn(str(root),raw);self.assertEqual(info['attribution'],'djultra64')
            self.assertEqual(info['supported_rom']['revision_id'],'iss2000-pal-en-de-rev0')
            self.assertEqual(info['supported_rom']['sha256'],'6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf')
            self.assertEqual(info['build']['kind'],'development');self.assertIsNone(info['build']['input_testing'])
            for name,item in info['files'].items():
                self.assertFalse(Path(name).is_absolute());self.assertEqual(hashlib.sha256((out/name).read_bytes()).hexdigest(),item['sha256'])
            self.assertIn('lib/libaudio.so.1',info['files']);self.assertIn('licenses/Runtime.txt',info['files'])
            self.assertEqual(list((out/'data').iterdir()),[]);self.assertEqual(list((out/'screenshots').iterdir()),[])
    def test_explicit_us_metadata_never_uses_pal_rom_identity(self):
        import json
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);exe=root/'game.exe';exe.write_bytes(b'synthetic');out=root/'out'
            package('windows',exe,out,revision='iss2000-us-rev0')
            info=json.loads((out/'build-info.json').read_text());self.assertEqual(info['supported_rom']['revision_id'],'iss2000-us-rev0');self.assertTrue(info['supported_rom']['sha256'].startswith('e18e87'))
    def test_release_requires_matching_completed_build_with_input_fixture_off(self):
        import json
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);build=root/'build';build.mkdir();cache=build/'CMakeCache.txt'
            cache.write_text('ISS2000_ROM_REVISION:STRING=iss2000-pal-en-de-rev0\nISS2000_ENABLE_INPUT_TESTING:BOOL=OFF\n')
            exe=build/'iss2000';exe.write_bytes(b'synthetic production binary');out=root/'out'
            package('linux',exe,out,release=True,build_dir=build)
            info=json.loads((out/'build-info.json').read_text());self.assertEqual(info['build']['kind'],'production-prepared');self.assertIs(info['build']['input_testing'],False)
            self.assertNotIn('CMakeCache.txt',[p.name for p in out.iterdir()])
    def test_release_rejects_fixture_on_wrong_revision_stale_or_unrelated_binary(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);build=root/'build';build.mkdir();exe=build/'iss2000';out=root/'out';cache=build/'CMakeCache.txt'
            cases=[('ON','iss2000-pal-en-de-rev0',False,False),('OFF','iss2000-us-rev0',False,False),('OFF','iss2000-pal-en-de-rev0',True,False),('OFF','iss2000-pal-en-de-rev0',False,True)]
            for fixture,revision,stale,external in cases:
                cache.write_text(f'ISS2000_ROM_REVISION:STRING={revision}\nISS2000_ENABLE_INPUT_TESTING:BOOL={fixture}\n')
                source=root/'external' if external else exe;source.write_bytes(b'synthetic')
                if stale:os.utime(source,ns=(1,1))
                with self.subTest(cases=(fixture,revision,stale,external)),self.assertRaises(ValueError):package('linux',source,out,release=True,build_dir=build)
                self.assertFalse(out.exists())
    def test_release_without_build_directory_is_rejected_before_mutation(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);exe=root/'game';exe.write_bytes(b'synthetic')
            with self.assertRaises(ValueError):package('linux',exe,root/'out',release=True)
            self.assertFalse((root/'out').exists())
    def test_build_metadata_filename_is_reserved(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);exe=root/'build-info.json';exe.write_bytes(b'synthetic')
            with self.assertRaises(ValueError):package('linux',exe,root/'out')
            self.assertFalse((root/'out').exists())

class PortableProductionPathTests(unittest.TestCase):
    def test_release_rejects_embedded_developer_home_paths_in_program_or_library(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);build=root/'build';build.mkdir()
            (build/'CMakeCache.txt').write_text('ISS2000_ROM_REVISION:STRING=iss2000-pal-en-de-rev0\nISS2000_ENABLE_INPUT_TESTING:BOOL=OFF\n')
            exe=build/'iss2000';lib=root/'libaudio.so.1';out=root/'out'
            for payload,target in [(b'/home/developer/project/file.cpp',exe),(b'/var/home/developer/deps/file.cpp',lib),(b'C:\\Users\\Developer\\project\\file.cpp',exe)]:
                exe.write_bytes(b'synthetic executable');lib.write_bytes(b'synthetic library');target.write_bytes(payload)
                with self.subTest(payload=payload),self.assertRaisesRegex(ValueError,'path'):
                    package('linux',exe,out,[lib],release=True,build_dir=build)
                self.assertFalse(out.exists())
