"""Behavioral import tests use synthetic images; original data stays private."""
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile

from tools.rom import normalize, validate, import_rom, RomError


def image():
    data = bytearray(0x1040)
    data[:4] = bytes.fromhex('80371240')
    struct.pack_into('>I', data, 8, 0x80000400)
    data[0x3b:0x3f] = b'NISE'
    return bytes(data)


def manifest(data):
    return {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
            'revision_id': 'synthetic', 'cartridge_id': 'NISE', 'revision': 0}


class NormalizationTests(unittest.TestCase):
    def test_all_byte_orders_ignore_extension(self):
        canonical = image()
        swapped = bytearray(canonical)
        swapped[0::2], swapped[1::2] = canonical[1::2], canonical[0::2]
        little = b''.join(canonical[i:i+4][::-1] for i in range(0, len(canonical), 4))
        for data in [canonical, bytes(swapped), little]:
            self.assertEqual(normalize(data), canonical)

    def test_truncated_or_malformed_images_fail(self):
        for data in [b'', b'BAD!', image()[:-1], image()[:32]]:
            with self.assertRaises(RomError):
                normalize(data)

    def test_revision_is_checked_after_normalization(self):
        data = image()
        self.assertEqual(validate(data, manifest(data))['revision_id'], 'synthetic')
        with self.assertRaises(RomError):
            validate(data[:-4]+b'FAIL', manifest(data))


class ImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root/'source.n64'
        self.source.write_bytes(image())
        self.target = self.root/'private'/'rom.z64'

    def test_import_produces_exact_bytes_without_changing_source(self):
        result = import_rom(self.source, self.target, manifest(image()))
        self.assertEqual(self.target.read_bytes(), image())
        self.assertEqual(self.source.read_bytes(), image())
        self.assertEqual(result['sha256'], hashlib.sha256(image()).hexdigest())

    def test_source_or_existing_destination_is_never_overwritten(self):
        for dest in [self.source, self.root/'existing.z64']:
            if dest != self.source:
                dest.write_bytes(b'keep me')
            before = dest.read_bytes()
            with self.assertRaises(RomError):
                import_rom(self.source, dest, manifest(image()))
            self.assertEqual(dest.read_bytes(), before)

    def test_symlink_destination_is_rejected(self):
        dest = self.root/'link.z64'
        dest.symlink_to(self.source)
        with self.assertRaises(RomError):
            import_rom(self.source, dest, manifest(image()))
        self.assertEqual(self.source.read_bytes(), image())

    def test_ambiguous_zip_does_not_create_output(self):
        source = self.root/'ambiguous.zip'
        with zipfile.ZipFile(source, 'w') as archive:
            archive.writestr('a.z64', image())
            archive.writestr('b.n64', image())
        with self.assertRaises(RomError):
            import_rom(source, self.target, manifest(image()))
        self.assertFalse(self.target.exists())

    def test_zip_with_large_member_is_rejected_before_reading(self):
        source = self.root/'large.zip'
        with zipfile.ZipFile(source, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('large.z64', image()+bytes(100))
        with self.assertRaises(RomError):
            import_rom(source, self.target, manifest(image()))
        self.assertFalse(self.target.exists())

    def test_failed_revision_does_not_mutate_destination_tree(self):
        self.source.write_bytes(image()[:-4]+b'FAIL')
        with self.assertRaises(RomError):
            import_rom(self.source, self.target, manifest(image()))
        self.assertFalse(self.target.parent.exists())

    def test_zip_member_path_is_not_used_for_extraction(self):
        source = self.root/'traversal.zip'
        with zipfile.ZipFile(source, 'w') as archive:
            archive.writestr('../../escape.z64', image())
        import_rom(source, self.target, manifest(image()))
        self.assertEqual(self.target.read_bytes(), image())
        self.assertFalse((self.root.parent/'escape.z64').exists())


if __name__ == '__main__':
    unittest.main()
