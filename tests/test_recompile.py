import unittest

from tools.recompile import validate_functions, render_symbols


class MetadataTests(unittest.TestCase):
    def test_boot_metadata_is_deterministic(self):
        functions = [{'name': 'func_80000400', 'vram': 0x80000400, 'size': 0x40}]
        text = render_symbols(functions, 0x40)
        self.assertEqual(text, render_symbols(list(reversed(functions)), 0x40))
        self.assertIn('rom = 0x1000', text)
        self.assertIn('vram = 0x80000400', text)
        self.assertIn('size = 0x40', text)

    def test_overlapping_unaligned_and_outside_functions_fail(self):
        base = {'name': 'entry', 'vram': 0x80000400, 'size': 0x40}
        cases = [[base, {'name': 'overlap', 'vram': 0x80000420, 'size': 4}],
                 [{'name': 'unaligned', 'vram': 0x80000401, 'size': 4}],
                 [{'name': 'outside', 'vram': 0x80000500, 'size': 4}],
                 [{'name': 'zero', 'vram': 0x80000400, 'size': 0}],
                 [{'name': 'invalid"name', 'vram': 0x80000400, 'size': 4}]]
        for functions in cases:
            with self.subTest(functions=functions), self.assertRaises(ValueError):
                validate_functions(functions, 0x40)


if __name__ == '__main__':
    unittest.main()
