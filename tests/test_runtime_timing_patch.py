"""Build adaptation pins upstream source and preserves existing artifacts."""
from pathlib import Path
import tempfile
import unittest
from tools import prepare_runtime_timing as timing
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'.local/deps/N64ModernRuntime/ultramodern/src/events.cpp'
class RuntimeTimingPatchTests(unittest.TestCase):
    def test_modified_dependency_is_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp); source=p/'events.cpp'; source.write_text('modified dependency')
            with self.assertRaisesRegex(ValueError,'digest'):
                timing.prepare(source,p/'out')
            self.assertFalse((p/'out').exists())
    @unittest.skipUnless(SOURCE.exists(),'requires pinned local runtime source')
    def test_pinned_source_preparation_is_reproducible_and_preserves_input(self):
        original=SOURCE.read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'out'; first=timing.prepare(SOURCE,p)
            self.assertEqual(timing.prepare(SOURCE,p),first)
            self.assertEqual(SOURCE.read_bytes(),original)
            self.assertEqual(first['source_sha256'],timing.SOURCE_SHA256)
            self.assertEqual(first['vi_hz'],50)
            self.assertNotEqual(first['generated_sha256'],first['source_sha256'])
            (p/'events.cpp').write_text('preserve changed output')
            with self.assertRaisesRegex(ValueError,'existing'):
                timing.prepare(SOURCE,p)
            self.assertEqual((p/'events.cpp').read_text(),'preserve changed output')
