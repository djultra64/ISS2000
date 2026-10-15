import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.build_tool import verify_receipt


class ToolReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root/'source'
        self.source.mkdir()
        self.tool = self.root/'N64Recomp'
        self.tool.write_bytes(b'known tool binary')
        self.cache = self.root/'CMakeCache.txt'
        self.cache.write_text('CMAKE_HOME_DIRECTORY:INTERNAL='+str(self.source)+'\n')
        self.graph = self.root/'build.ninja'
        self.graph.write_bytes(b'known build graph')
        self.receipt = {'schema_version': 1, 'source_commit': 'a'*40,
                        'source_path': str(self.source.resolve()),
                        'binary_sha256': hashlib.sha256(self.tool.read_bytes()).hexdigest(),
                        'cache_sha256': hashlib.sha256(self.cache.read_bytes()).hexdigest(),
                        'graph_sha256': hashlib.sha256(self.graph.read_bytes()).hexdigest()}
        (self.root/'iss2000-build-receipt.json').write_text(json.dumps(self.receipt))

    def test_controlled_build_receipt_matches_actual_artifacts(self):
        result = verify_receipt(self.tool, self.source, 'a'*40)
        self.assertEqual(result['binary_sha256'], self.receipt['binary_sha256'])

    def test_changed_or_stale_executable_is_rejected(self):
        self.tool.write_bytes(b'other stale executable')
        with self.assertRaises(ValueError):
            verify_receipt(self.tool, self.source, 'a'*40)

    def test_cache_is_not_accepted_as_the_executable(self):
        with self.assertRaises(ValueError):
            verify_receipt(self.cache, self.source, 'a'*40)

    def test_missing_receipt_is_rejected(self):
        (self.root/'iss2000-build-receipt.json').unlink()
        with self.assertRaises(ValueError):
            verify_receipt(self.tool, self.source, 'a'*40)
