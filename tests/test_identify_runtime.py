"""Original project work: djultra64."""
import hashlib
import json
from pathlib import Path
import unittest
from tools.identify_runtime import verify_bindings


class RuntimeBindingVerificationTests(unittest.TestCase):
    def test_framebuffer_query_is_bound_to_the_same_host_vi_state_as_swap(self):
        manifest=json.loads((Path(__file__).resolve().parents[1]/'config/recomp/runtime-symbols.json').read_text())
        bindings={int(row['address'],0):row for row in manifest['bindings']}
        getter=bindings.get(0x8005E330)
        self.assertIsNotNone(getter, 'Original VI getter must not read stale guest SDK contexts')
        self.assertEqual(getter['runtime_symbol'],'osViGetCurrentFramebuffer_recomp')
        self.assertEqual(bindings[0x8005E920]['runtime_symbol'],'osViSwapBuffer_recomp')
        self.assertEqual(getter['status'],'verified-instructions-and-abi')

    def test_pak_probe_uses_reviewed_high_level_service_instead_of_raw_si(self):
        manifest=json.loads((Path(__file__).resolve().parents[1]/'config/recomp/runtime-symbols.json').read_text())
        bindings={int(row['address'],0):row for row in manifest['bindings']}
        probe=bindings.get(0x80060550)
        self.assertIsNotNone(probe, 'Controller Pak initialization must use the host accessory profile')
        self.assertEqual(probe['runtime_symbol'],'osPfsInitPak_recomp')
        self.assertEqual(probe['status'],'verified-instructions-and-abi')
        self.assertNotIn(0x8005D930,bindings, 'Do not fabricate a successful low-level SI DMA service')

    def fixture(self):
        data = bytes(range(64))
        binding = dict(address='0x80000400', rom_offset='0x10', size=8,
                       name='osExample', runtime_symbol='osExample_recomp',
                       status='verified-instructions-and-abi', evidence='reviewed ABI',
                       sha256=hashlib.sha256(data[16:24]).hexdigest())
        return data, dict(schema_version=1, rom_sha256=hashlib.sha256(data).hexdigest(), bindings=[binding])

    def test_verified_exact_bytes_return_binding(self):
        data, manifest = self.fixture()
        self.assertEqual(verify_bindings(data, manifest), manifest['bindings'])

    def test_different_rom_rejected(self):
        data, manifest = self.fixture()
        with self.assertRaisesRegex(ValueError, 'ROM digest'):
            verify_bindings(b'x' + data[1:], manifest)

    def test_body_digest_rejected_even_with_matching_rom(self):
        data, manifest = self.fixture()
        manifest['bindings'][0]['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'body digest'):
            verify_bindings(data, manifest)

    def test_duplicate_address_and_unverified_binding_rejected(self):
        data, manifest = self.fixture()
        manifest['bindings'] *= 2
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            verify_bindings(data, manifest)
        manifest['bindings'] = manifest['bindings'][:1]
        manifest['bindings'][0]['status'] = 'candidate'
        with self.assertRaisesRegex(ValueError, 'Unverified'):
            verify_bindings(data, manifest)

    def test_out_of_bounds_or_unaligned_body_rejected(self):
        for offset, size in [('0x3C', 8), ('0x11', 8), ('0x10', 7), ('-4', 8)]:
            data, manifest = self.fixture()
            manifest['bindings'][0].update(rom_offset=offset, size=size)
            with self.assertRaisesRegex(ValueError, 'bounds/alignment'):
                verify_bindings(data, manifest)
