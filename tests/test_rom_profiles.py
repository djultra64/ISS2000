"""Revision selection must never accept a different game build implicitly."""
import hashlib
import os
from pathlib import Path
import unittest
from tools import rom

class RomProfileTests(unittest.TestCase):
    def test_known_profiles_have_separate_exact_identities(self):
        us = rom.load_manifest('iss2000-us-rev0')
        pal = rom.load_manifest('iss2000-pal-en-de-rev0')
        self.assertEqual(us['cartridge_id'], 'NISE')
        self.assertEqual(pal['cartridge_id'], 'NISX')
        self.assertEqual(pal['sha256'], '6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf')
        self.assertNotEqual(us['sha256'], pal['sha256'])

    def test_unknown_or_path_revision_is_rejected(self):
        for revision in ('../iss2000-us-rev0', '/tmp/rom', 'iss2000-pal-other'):
            with self.subTest(revision=revision), self.assertRaises(rom.RomError):
                rom.load_manifest(revision)

    @unittest.skipUnless(os.environ.get('ISS2000_PAL_ROM'), 'set ISS2000_PAL_ROM for private PAL integration')
    def test_pal_validates_only_with_explicit_profile_and_checksums(self):
        data = Path(os.environ['ISS2000_PAL_ROM']).read_bytes()
        with self.assertRaises(rom.RomError):
            rom.validate(data)
        pal = rom.load_manifest('iss2000-pal-en-de-rev0')
        result = rom.audit(data, pal)
        self.assertEqual(result['revision_id'], 'iss2000-pal-en-de-rev0')
        self.assertEqual(result['sha256'], hashlib.sha256(data).hexdigest())
        self.assertTrue(result['checksum']['match'])
        self.assertEqual(result['checksum']['stored'], ['336364A0', '06C8D5BF'])
