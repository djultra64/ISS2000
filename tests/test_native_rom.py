"""Portable native ROM importer checks with synthetic files only."""
import hashlib
import os
from pathlib import Path
import shutil
import struct
import sys
import subprocess
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MINIZ = Path(os.environ.get('ISS2000_MINIZ_SOURCE',ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz'))
MINIZ_BUILD = Path(os.environ.get('ISS2000_MINIZ_BUILD',ROOT/'.local/runtime-deps-build/librecomp/miniz'))


class NativeRomDependencyDiscoveryTests(unittest.TestCase):
    def test_source_only_discovery_explicitly_skips_unbuilt_native_dependency(self):
        with tempfile.TemporaryDirectory(prefix='iss2000-no-miniz-') as empty:
            env=dict(os.environ,ISS2000_MINIZ_SOURCE=empty,ISS2000_MINIZ_BUILD=empty)
            result=subprocess.run([sys.executable,'-m','unittest',
                                   'tests.test_native_rom.NativeRomTests','-v'],
                                  cwd=ROOT,env=env,capture_output=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn(b'skipped',result.stderr)
        self.assertIn(b'native ROM tests require the pinned miniz build',result.stderr)
        self.assertIn(b'Ran 0 tests',result.stderr)


class NativeRomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (MINIZ/'miniz.h').is_file() or not (MINIZ_BUILD/'libminiz.a').is_file():
            raise unittest.SkipTest('native ROM tests require the pinned miniz build')
        if not shutil.which('c++'):
            raise unittest.SkipTest('native ROM tests require a C++20 compiler')
        # Synthetic compiler fixtures also work from a read-only checkout.
        cls.build = tempfile.TemporaryDirectory(prefix='iss2000-native-rom-')
        cls.folder = Path(cls.build.name)
        harness = cls.folder/'harness.cpp'
        harness.write_text(r'''
#include "runtime/rom_image.hpp"
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>
std::vector<std::uint8_t> bytes(const std::filesystem::path& path) {
    std::ifstream input(path, std::ios::binary);
    if (!input) throw std::runtime_error("test input missing");
    return {std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
}
int main(int argc, char** argv) {
    try {
        std::string mode = argv[1];
        if (mode == "hash") std::cout << iss2000::rom_detail::sha256_hex(bytes(argv[2]));
        else if (mode == "normalize") {
            auto result = iss2000::rom_detail::normalize_byte_order(bytes(argv[2]));
            std::cout.write(reinterpret_cast<const char*>(result.data()), result.size());
        } else if (mode == "read") {
            auto result = iss2000::read_rom_image(argv[2]);
            std::cout << result.size() << " " << iss2000::rom_detail::sha256_hex(result);
        } else if (mode == "store") {
            iss2000::rom_detail::write_bytes_exclusive(argv[3], bytes(argv[2]));
        } else if (mode == "validate-store") {
            iss2000::write_rom_exclusive(argv[3], bytes(argv[2]));
        } else if (mode == "ensure") {
            iss2000::ensure_rom_storage(argv[3], bytes(argv[2]));
        } else if (mode == "ensure-bytes") {
            iss2000::rom_detail::ensure_bytes_storage(argv[3], bytes(argv[2]));
        } else if (mode == "import") {
            auto result = iss2000::read_rom_image(argv[2]);
            iss2000::write_rom_exclusive(argv[3], result);
        } else throw std::runtime_error("unknown test mode");
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n'; return 1;
    }
}
''')
        cls.binary = cls.folder/'rom-test'
        command = [shutil.which('c++') or 'c++','-std=c++20','-O2','-Wall','-Wextra',
                   '-I'+str(ROOT/'src'),'-I'+str(MINIZ),'-I'+str(MINIZ_BUILD),
                   str(harness),str(ROOT/'src/runtime/rom_image.cpp'),
                   str(MINIZ_BUILD/'libminiz.a'),'-o',str(cls.binary)]
        subprocess.run(command,check=True,capture_output=True,text=True)

    @classmethod
    def tearDownClass(cls):
        cls.build.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='iss2000-rom-input-')
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def run_native(self, mode, source, destination=None):
        args=[str(self.binary),mode,str(source)]
        if destination is not None: args.append(str(destination))
        return subprocess.run(args,capture_output=True,timeout=20)

    def write(self, name, data):
        path=self.root/name
        path.write_bytes(data)
        return path

    def test_sha256_published_empty_abc_and_padding_boundary_vectors(self):
        # Wrong round constants, message length or padding fail these vectors.
        for value,want in [(b'', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'),
                           (b'abc','ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'),
                           (b'abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq',
                            '248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1')]:
            result=self.run_native('hash',self.write('vector',value))
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(result.stdout.decode(),want)

    def test_sha256_multiple_blocks_match_independent_digest(self):
        value=bytes(range(256))*13
        result=self.run_native('hash',self.write('vector',value))
        self.assertEqual(result.stdout.decode(),hashlib.sha256(value).hexdigest())

    def test_normalizes_all_byte_orders_using_magic_despite_extension(self):
        canonical=bytes.fromhex('803712401122334455667788')
        fixtures=[canonical,bytes.fromhex('378040122211443366558877'),
                  bytes.fromhex('401237804433221188776655')]
        for value in fixtures:
            result=self.run_native('normalize',self.write('misleading.zip',value))
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(result.stdout,canonical)

    def test_unknown_magic_and_unaligned_data_are_rejected(self):
        for value in [b'',bytes.fromhex('8037124000'),b'invalid!']:
            self.assertNotEqual(self.run_native('normalize',self.write('bad',value)).returncode,0)

    def test_rejects_wrong_revision_without_creating_destination(self):
        source=self.write('synthetic.z64',bytes.fromhex('80371240')+bytes(16*1024*1024-4))
        destination=self.root/'new'/'rom.z64'
        result=self.run_native('import',source,destination)
        self.assertNotEqual(result.returncode,0)
        self.assertIn(b'SHA-256',result.stderr)
        self.assertFalse(destination.parent.exists())
        self.assertEqual(source.stat().st_size,16*1024*1024)

    def test_rejects_truncated_raw_before_storage(self):
        source=self.write('truncated.n64',bytes.fromhex('37804012'))
        result=self.run_native('read',source)
        self.assertNotEqual(result.returncode,0)
        self.assertIn(b'size',result.stderr.lower())

    def test_zip_ambiguity_is_rejected_before_decompression(self):
        source=self.root/'ambiguous.zip'
        with zipfile.ZipFile(source,'w') as archive:
            archive.writestr('one.z64',b'bad')
            archive.writestr('two.N64',b'bad')
        result=self.run_native('read',source)
        self.assertNotEqual(result.returncode,0)
        self.assertIn(b'exactly one',result.stderr)

    def test_zip_claimed_size_bomb_is_rejected_before_extract(self):
        source=self.root/'bomb.zip'
        with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('rom.n64',b'tiny')
        value=bytearray(source.read_bytes())
        central=value.index(b'PK\x01\x02')
        struct.pack_into('<I',value,central+24,16*1024*1024+1)
        source.write_bytes(value)
        result=self.run_native('read',source)
        self.assertNotEqual(result.returncode,0)
        self.assertIn(b'decompressed size',result.stderr)

    def test_corrupt_zip_and_member_paths_never_extract_files(self):
        source=self.root/'corrupt.bin'
        with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('../escaped.z64',bytes.fromhex('80371240')+bytes(16*1024*1024-4))
        value=bytearray(source.read_bytes())
        name_size,extra_size=struct.unpack_from('<HH',value,26)
        value[30+name_size+extra_size] ^= 0xFF
        source.write_bytes(value)
        before=set(self.root.iterdir())
        result=self.run_native('read',source)
        self.assertNotEqual(result.returncode,0)
        self.assertIn(b'extract',result.stderr.lower())
        self.assertEqual(set(self.root.iterdir()),before)
        self.assertFalse((self.root.parent/'escaped.z64').exists())

    def test_zip_wrong_identity_uses_magic_and_never_mutates_source(self):
        source=self.root/'renamed-input.bin'
        with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('nested/wrong.z64',bytes.fromhex('37804012')+bytes(16*1024*1024-4))
        before=source.read_bytes()
        result=self.run_native('read',source)
        self.assertNotEqual(result.returncode,0)
        self.assertIn(b'SHA-256',result.stderr)
        self.assertEqual(source.read_bytes(),before)

    def test_exclusive_store_preserves_source_and_existing_destination(self):
        source=self.write('source',b'source')
        destination=self.write('destination',b'preserved')
        result=self.run_native('store',source,destination)
        self.assertNotEqual(result.returncode,0)
        self.assertEqual(source.read_bytes(),b'source')
        self.assertEqual(destination.read_bytes(),b'preserved')
        self.assertEqual(set(p.name for p in self.root.iterdir()),{'source','destination'})
        self.assertNotEqual(self.run_native('store',source,source).returncode,0)
        self.assertEqual(source.read_bytes(),b'source')

    def test_exclusive_store_commits_complete_bytes_and_leaves_no_temp_files(self):
        source=self.write('source',bytes(range(256))*19)
        destination=self.root/'new'/'destination'
        result=self.run_native('store',source,destination)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(destination.read_bytes(),source.read_bytes())
        self.assertEqual(list(destination.parent.iterdir()),[destination])

    def test_store_rejects_symlink_destinations_and_parent_paths(self):
        source=self.write('source',b'untouched')
        dangling=self.root/'link'
        dangling.symlink_to(self.root/'missing')
        self.assertNotEqual(self.run_native('store',source,dangling).returncode,0)
        real=self.root/'real';real.mkdir()
        parent=self.root/'parent';parent.symlink_to(real,target_is_directory=True)
        self.assertNotEqual(self.run_native('store',source,parent/'rom').returncode,0)
        self.assertEqual(list(real.iterdir()),[])
        self.assertEqual(source.read_bytes(),b'untouched')

    def test_exclusive_publish_race_has_one_complete_winner(self):
        first=self.write('first',b'A'*(1024*1024))
        second=self.write('second',b'B'*(1024*1024))
        destination=self.root/'winner'
        processes=[subprocess.Popen([str(self.binary),'store',str(p),str(destination)],
                                    stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                   for p in (first,second)]
        for process in processes: process.communicate(timeout=20)
        self.assertEqual(sorted(p.returncode for p in processes),[0,1])
        self.assertIn(destination.read_bytes(),[first.read_bytes(),second.read_bytes()])
        self.assertEqual(set(p.name for p in self.root.iterdir()),{'first','second','winner'})

    def test_rejects_oversized_container_without_creating_output(self):
        source=self.write('huge.zip',b'PK\x03\x04')
        with source.open('r+b') as stream: stream.truncate(64*1024*1024+1)
        result=self.run_native('read',source)
        self.assertNotEqual(result.returncode,0)
        self.assertIn(b'64 MiB',result.stderr)

    def test_rejects_encrypted_zip_member_before_extract(self):
        source=self.root/'encrypted.zip'
        with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('rom.v64',bytes(16*1024*1024))
        value=bytearray(source.read_bytes());central=value.index(b'PK\x01\x02')
        struct.pack_into('<H',value,6,1)
        struct.pack_into('<H',value,central+8,1)
        source.write_bytes(value)
        result=self.run_native('read',source)
        self.assertNotEqual(result.returncode,0)
        self.assertIn(b'encrypted',result.stderr)

    def test_recovery_validates_before_mutating_existing_storage_or_backups(self):
        source=self.write('invalid',b'not the supported ROM')
        stored=self.write('stored.z64',b'corrupt existing input')
        backup=self.write('stored.z64.invalid-backup',b'previous backup')
        before={p.name:p.read_bytes() for p in self.root.iterdir()}
        result=self.run_native('ensure',source,stored)
        self.assertNotEqual(result.returncode,0)
        self.assertEqual({p.name:p.read_bytes() for p in self.root.iterdir()},before)
        missing=self.root/'missing'/'stored.z64'
        self.assertNotEqual(self.run_native('ensure',source,missing).returncode,0)
        self.assertFalse(missing.parent.exists())

    def test_recovery_preserves_corrupt_bytes_and_existing_backup_collision(self):
        source=self.write('replacement',b'validated replacement bytes')
        stored=self.write('stored.z64',b'corrupt stored bytes')
        backup=self.write('stored.z64.invalid-backup',b'older preserved backup')
        result=self.run_native('ensure-bytes',source,stored)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(stored.read_bytes(),source.read_bytes())
        self.assertEqual(backup.read_bytes(),b'older preserved backup')
        self.assertEqual((self.root/'stored.z64.1.invalid-backup').read_bytes(),b'corrupt stored bytes')
        self.assertEqual(source.read_bytes(),b'validated replacement bytes')

    def test_recovery_same_bytes_is_noop_without_lock_or_backup_creation(self):
        source=self.write('replacement',b'already valid')
        stored=self.write('stored.z64',b'already valid')
        before=stored.stat().st_mtime_ns
        result=self.run_native('ensure-bytes',source,stored)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(stored.stat().st_mtime_ns,before)
        self.assertEqual(set(p.name for p in self.root.iterdir()),{'replacement','stored.z64'})

    def test_concurrent_recovery_preserves_exactly_one_corrupt_backup(self):
        source=self.write('replacement',b'complete replacement'*(64*1024))
        stored=self.write('stored.z64',b'corrupt original')
        processes=[subprocess.Popen([str(self.binary),'ensure-bytes',str(source),str(stored)],
                                    stdout=subprocess.PIPE,stderr=subprocess.PIPE) for _ in range(2)]
        outputs=[process.communicate(timeout=20) for process in processes]
        self.assertEqual([process.returncode for process in processes],[0,0],outputs)
        self.assertEqual(stored.read_bytes(),source.read_bytes())
        backups=list(self.root.glob('*.invalid-backup'))
        self.assertEqual(len(backups),1)
        self.assertEqual(backups[0].read_bytes(),b'corrupt original')

    @unittest.skipUnless(os.environ.get('ISS2000_ROM'),'set ISS2000_ROM for private verified-ROM recovery')
    def test_optin_exact_rom_recovers_corrupt_storage_and_preserves_original(self):
        source=Path(os.environ['ISS2000_ROM']).resolve()
        original_hash=hashlib.sha256(source.read_bytes()).hexdigest()
        private=ROOT/'.local/native-rom-test'
        private.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='recovery-',dir=private) as folder:
            stored=Path(folder)/'stored.z64'
            stored.write_bytes(b'corrupt private storage')
            backup=Path(folder)/'stored.z64.invalid-backup'
            backup.write_bytes(b'older backup remains')
            result=self.run_native('ensure',source,stored)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(hashlib.sha256(stored.read_bytes()).hexdigest(),
                             'e18e87c062a66002c0cbd7e2dd793ef755609e70675d5679df0396d4b6c67850')
            self.assertEqual(backup.read_bytes(),b'older backup remains')
            self.assertEqual((Path(folder)/'stored.z64.1.invalid-backup').read_bytes(),b'corrupt private storage')
            before_names=set(Path(folder).iterdir())
            before_time=stored.stat().st_mtime_ns
            self.assertEqual(self.run_native('ensure',source,stored).returncode,0)
            self.assertEqual(set(Path(folder).iterdir()),before_names)
            self.assertEqual(stored.stat().st_mtime_ns,before_time)
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),original_hash)

    @unittest.skipUnless(os.environ.get('ISS2000_ROM'),'set ISS2000_ROM for private canonical-storage recovery')
    def test_optin_stored_swapped_rom_is_replaced_by_physical_canonical_bytes(self):
        source=Path(os.environ['ISS2000_ROM']).resolve()
        canonical=source.read_bytes()
        expected='e18e87c062a66002c0cbd7e2dd793ef755609e70675d5679df0396d4b6c67850'
        self.assertEqual(hashlib.sha256(canonical).hexdigest(),expected)
        private=ROOT/'.local/native-rom-test';private.mkdir(parents=True,exist_ok=True)
        for word_size in (2,4):
            swapped=bytearray(len(canonical))
            for index in range(word_size): swapped[index::word_size]=canonical[word_size-1-index::word_size]
            with tempfile.TemporaryDirectory(prefix='noncanonical-',dir=private) as folder:
                stored=Path(folder)/'stored.z64';stored.write_bytes(swapped)
                result=self.run_native('ensure',source,stored)
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertEqual(hashlib.sha256(stored.read_bytes()).hexdigest(),expected)
                self.assertEqual((Path(folder)/'stored.z64.invalid-backup').read_bytes(),swapped)
        self.assertEqual(source.read_bytes(),canonical)

    @unittest.skipUnless(os.environ.get('ISS2000_ROM'),'set ISS2000_ROM for private canonical-storage recovery')
    def test_optin_stored_zip_is_preserved_before_physical_canonical_replacement(self):
        source=Path(os.environ['ISS2000_ROM']).resolve()
        before_source=hashlib.sha256(source.read_bytes()).hexdigest()
        private=ROOT/'.local/native-rom-test';private.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='archived-storage-',dir=private) as folder:
            stored=Path(folder)/'stored.z64'
            with zipfile.ZipFile(stored,'w',zipfile.ZIP_DEFLATED) as archive:
                archive.write(source,'nested/original.n64')
            archive_bytes=stored.read_bytes()
            result=self.run_native('ensure',source,stored)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(hashlib.sha256(stored.read_bytes()).hexdigest(),
                             'e18e87c062a66002c0cbd7e2dd793ef755609e70675d5679df0396d4b6c67850')
            self.assertEqual((Path(folder)/'stored.z64.invalid-backup').read_bytes(),archive_bytes)
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),before_source)

    def test_public_writer_validates_before_creating_tree(self):
        source=self.write('bad',b'not the supported ROM')
        destination=self.root/'new'/'rom'
        result=self.run_native('validate-store',source,destination)
        self.assertNotEqual(result.returncode,0)
        self.assertFalse(destination.parent.exists())


if __name__ == '__main__':
    unittest.main()
