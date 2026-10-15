import struct
import unittest
from tools.map_main import external_calls


class ExternalCallTests(unittest.TestCase):
    def test_direct_calls_outside_resident_block_are_reported_by_callsite(self):
        data = bytes(0x1000)+struct.pack('>II',
            0x0c000000 | ((0x801b050c & 0x0fffffff) >> 2),
            0x0c000000 | ((0x80000500 & 0x0fffffff) >> 2))
        self.assertEqual(external_calls(data, 0x1008),
                         {'0x801B050C': ['0x80000400']})

    def test_scan_end_must_be_aligned_and_inside_rom(self):
        for end in [0xffc, 0x1001, 0x100c]:
            with self.assertRaises(ValueError):
                external_calls(bytes(0x1008), end)
