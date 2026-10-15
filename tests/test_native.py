"""Opt-in process-level checks; requires an actual compiled diagnostic."""
import json
import os
from pathlib import Path
import subprocess
import unittest


@unittest.skipUnless(os.environ.get('ISS2000_DIAGNOSTIC'),
                     'set ISS2000_DIAGNOSTIC to the built native diagnostic')
class NativeTests(unittest.TestCase):
    def run_diagnostic(self, *args):
        executable = str(Path(os.environ['ISS2000_DIAGNOSTIC']).resolve())
        return subprocess.run([executable, *args], capture_output=True, text=True, timeout=10)

    def test_original_entry_clears_only_its_bss_and_transfers(self):
        result = self.run_diagnostic()
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['rdram_bytes'], 8*1024*1024)
        self.assertTrue(report['bss_cleared'])
        self.assertTrue(report['outside_bss_preserved'])
        self.assertEqual(report['stack_pointer'], '0x800CEC50')
        self.assertEqual(report['continuation'], '0x800007B8')
        self.assertFalse(report['game_booted'])
        self.assertEqual(report['mode'], 'original-entry-diagnostic')

    def test_original_buffer_setup_selects_expanded_memory_addresses(self):
        result = self.run_diagnostic()
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['original_buffer_setup']['standard'],
                         ['0x80307800', '0x8032D000', '0x80281D40'])
        self.assertEqual(report['original_buffer_setup']['expanded'],
                         ['0x80500000', '0x80596000', '0x8062C000'])

    def test_unexpected_dispatch_fails_instead_of_succeeding_silently(self):
        result = self.run_diagnostic('--reject-continuation')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Unimplemented guest continuation', result.stderr)


if __name__ == '__main__':
    unittest.main()
