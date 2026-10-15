"""Synthetic instructions verify mapping without distributing original code."""
import struct
import unittest
from tools import map_loads


class LoadMappingTests(unittest.TestCase):
    def image(self, words):
        return struct.pack('>'+str(len(words))+'I', *words)

    def scan(self, words):
        return map_loads.constant_transfers(self.image(words), 0, len(words)*4, 0x80000000)

    def test_signed_address_and_delay_slot_size(self):
        # Losing signed addiu or the call's delay slot corrupts the ROM range.
        result = self.scan([0x3C040001, 0x2484FFF0, 0x3C05801B, 0x24A500B0,
                            0x3C060001, 0x24C60020, 0x0C000E59, 0x00C43023])
        self.assertEqual([(x['rom'], x['vram'], x['load_size']) for x in result],
                         [(0xFFF0, 0x801B00B0, 0x30)])

    def test_register_loaded_from_memory_is_unresolved(self):
        # Never reuse a prior constant after a memory load overwrites it.
        self.assertEqual(self.scan([0x24040020, 0x3C05801B, 0x24060010,
                                    0x8CA40000, 0x0C000E59, 0]), [])

    def test_other_call_clobbers_argument_constants(self):
        self.assertEqual(self.scan([0x24040020, 0x3C05801B, 0x24060010,
                                    0x0C000123, 0, 0x0C000E59, 0]), [])

    def test_preserves_separate_aliases_at_same_ram_address(self):
        words=[0x24040020, 0x3C05801B, 0x24060010, 0x0C000E59, 0,
               0x24040080, 0x3C05801B, 0x24060020, 0x0C000E59, 0]
        self.assertEqual([(x['rom'],x['vram']) for x in self.scan(words)],
                         [(0x20,0x801B0000),(0x80,0x801B0000)])

    def test_unknown_branch_does_not_propagate_constants(self):
        self.assertEqual(self.scan([0x24040020,0x3C05801B,0x24060010,
                                    0x10800001,0,0x0C000E59,0]), [])

    def test_finds_following_bss_clear_without_calling_data_text(self):
        words=[0x24040080,0x3C05801B,0x24060010,0x0C000E59,0,
               0x3C04801B,0x24840010,0x24050020,0x0C017168,0,
               0x03E00008,0]
        image=self.image(words)+bytes(0x80-len(words)*4)+self.image([0x03E00008,0,0,0])
        result=map_loads.recover_map(image, [{'name':'main','rom':0,'vram':0x80000000,
                                            'load_size':len(words)*4,'text_size':len(words)*4}])
        self.assertEqual(result[1]['rom'],0x80)
        self.assertEqual(result[1]['vram'],0x801B0000)
        self.assertEqual(result[1]['bss_end'],0x801B0030)
        self.assertEqual(result[1]['text_size'],0x10)

    def test_recurses_into_new_loaded_code_and_preserves_alias_identity(self):
        main=[0x24040100,0x3C05801B,0x24060020,0x0C000E59,0,0x03E00008,0,0]
        nested=[0x24040120,0x3C05801C,0x24060010,0x0C000E59,0,0x03E00008,0,0]
        image=self.image(main)+bytes(0x100-32)+self.image(nested)+self.image([0x03E00008,0,0,0])
        result=map_loads.recover_map(image,[{'name':'main','rom':0,'vram':0x80000000,
                                           'load_size':32,'text_size':32}])
        self.assertEqual([(x['rom'],x['vram']) for x in result],
                         [(0,0x80000000),(0x100,0x801B0000),(0x120,0x801C0000)])

    def test_chunked_dma_wrapper_reconstructs_whole_contiguous_range(self):
        words=[0x24040100,0x24050120,0x3C06801B,0x0C0155A3,0x24070010]
        result=self.scan(words)
        self.assertEqual([(x['rom'],x['vram'],x['load_size']) for x in result],
                         [(0x100,0x801B0000,0x20)])

    def test_rejects_invalid_scan_bounds(self):
        with self.assertRaises(ValueError):
            map_loads.constant_transfers(b'1234', 0, 8, 0x80000000)


if __name__ == '__main__':
    unittest.main()
