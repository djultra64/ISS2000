"""Opt-in native launcher validation; these checks do not launch gameplay."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

@unittest.skipUnless(os.environ.get('ISS2000_GAME'), 'Set ISS2000_GAME to the native launcher')
class GameLaunchTests(unittest.TestCase):
    def run_game(self, *args):
        return subprocess.run([os.environ['ISS2000_GAME'],*args],capture_output=True,text=True,timeout=15)
    def test_invalid_rom_is_rejected_before_creating_portable_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'bad.z64';source.write_bytes(b'\x80\x37\x12\x40'+b'\0'*64)
            destination=root/'portable-data'
            result=self.run_game('--validate-rom',str(source),'--data-dir',str(destination))
            self.assertNotEqual(result.returncode,0,result.stdout)
            self.assertIn('ROM',result.stderr)
            self.assertFalse(destination.exists())
            self.assertEqual(source.stat().st_size,68)
    def test_missing_rom_and_unknown_arguments_fail(self):
        result=self.run_game('--validate-rom','/this-rom-does-not-exist.z64')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('ROM',result.stderr)
        result=self.run_game('--unknown-option')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('Unknown option',result.stderr)
