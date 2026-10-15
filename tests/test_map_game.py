"""Regressions for metadata safety at the overlay/compiler boundary."""
import copy
import tomllib
import unittest
from tools import map_game


def section(name, rom=0x100, vram=0x801B00B0, load_size=0x100, text_size=0x20):
    return dict(name=name, rom=rom, vram=vram, load_size=load_size,
                text_size=text_size, bss_end=None, loader=0x80002E4C,
                confidence='synthetic instruction evidence')


class SectionMetadataTests(unittest.TestCase):
    def test_overlapping_addresses_retain_both_rom_identities(self):
        sections = [section('alias_a'), section('alias_b', rom=0x300)]
        normalized = map_game.validate_sections(sections, 0x1000)
        mapped = [dict(s, functions=[dict(vram=0x801B00B0, size=0x20)])
                  for s in normalized]
        output = tomllib.loads(map_game.render_symbols(mapped))['section']
        self.assertEqual([s['rom'] for s in output], [0x100, 0x300])
        self.assertEqual([s['functions'][0]['name'] for s in output],
                         ['func_801B00B0_alias_a', 'func_801B00B0_alias_b'])

    def test_unknown_text_range_is_not_emitted_as_executable(self):
        metadata = map_game.validate_sections([section('known'),
                       section('unknown', rom=0x300, text_size=None)], 0x1000)
        metadata[0]['functions'] = [dict(vram=0x801B00B0, size=0x20)]
        metadata[1]['functions'] = []
        output = tomllib.loads(map_game.render_symbols(metadata))['section']
        self.assertEqual([s['name'] for s in output], ['known'])
        self.assertEqual(output[0]['size'], 0x20)  # Not the larger DMA load size.

    def test_invalid_section_ranges_and_duplicate_identity_are_rejected(self):
        invalid = [dict(text_size=0x104), dict(load_size=0), dict(rom=0xFF0),
                   dict(vram=0x807FFFF0), dict(bss_end=0x801B0100),
                   dict(text_size=3), dict(name='bad-name'), dict(rom=-4)]
        for changed in invalid:
            with self.subTest(changed=changed):
                candidate=section('x'); candidate.update(changed)
                with self.assertRaises(ValueError):
                    map_game.validate_sections([candidate], 0x1000)
        with self.assertRaises(ValueError):
            map_game.validate_sections([section('x'), section('x', rom=0x300)], 0x1000)

    def test_functions_cannot_enter_loaded_data_or_overlap(self):
        for functions in [[dict(vram=0x801B00B0, size=0x24)],
                          [dict(vram=0x801B00B0, size=0x10),
                           dict(vram=0x801B00B8, size=0x10)]]:
            with self.subTest(functions=functions), self.assertRaises(ValueError):
                map_game.render_symbols([dict(section('x'), functions=functions)])

    def test_hex_integer_fields_are_normalized_without_changing_source(self):
        metadata=section('x', rom='0x100', load_size='0x100', text_size='0x20')
        original=copy.deepcopy(metadata)
        result=map_game.validate_sections([metadata], 0x1000)
        self.assertEqual(result[0]['rom'],0x100)
        self.assertEqual(metadata, original)


class CallCoverageTests(unittest.TestCase):
    def test_same_section_wins_and_external_aliases_remain_explicit(self):
        sections=[dict(section('a'),functions=[dict(vram=0x801B00B0,size=0x20)]),
                  dict(section('b',rom=0x300),functions=[dict(vram=0x801B00B0,size=0x20)]),
                  dict(section('resident',rom=0x500,vram=0x80000400),
                       functions=[dict(vram=0x80000400,size=0x20)])]
        self.assertEqual(map_game.call_candidates(sections,'a',0x801B00B0),
                         ['func_801B00B0_a'])
        self.assertEqual(map_game.call_candidates(sections,'resident',0x801B00B0),
                         ['func_801B00B0_a','func_801B00B0_b'])
        self.assertEqual(map_game.call_candidates(sections,'resident',0x8023E684),[])


class PrivateOutputTests(unittest.TestCase):
    def test_rejects_existing_outputs_input_overlap_and_symlink_escapes(self):
        from pathlib import Path
        import tempfile
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); private=root/'.local'; private.mkdir()
            source=private/'source'; source.mkdir()
            outside=root/'outside'; outside.mkdir()
            (private/'link').symlink_to(outside, target_is_directory=True)
            for path in [private, source, source/'result', root/'public', private/'link'/'result']:
                with self.subTest(path=path), self.assertRaises(ValueError):
                    map_game.validate_output(path, private, [source])
            self.assertEqual(map_game.validate_output(private/'new', private, [source]),
                             private/'new')


class TranslationModeTests(unittest.TestCase):
    def test_unsupported_lookup_mode_fails_instead_of_silently_ignoring_it(self):
        with self.assertRaises(ValueError):
            map_game.render_config('/private/rom.z64',['privileged'],True)
        config=tomllib.loads(map_game.render_config('/private/rom.z64',['privileged']))
        self.assertEqual(config['patches'],{'ignored':['privileged']})


class RuntimeBindingTests(unittest.TestCase):
    def test_runtime_binding_replaces_only_matching_rom_owner(self):
        sections=[dict(section('a'),functions=[dict(vram=0x801B00B0,size=0x20)]),
                  dict(section('b',rom=0x300),functions=[dict(vram=0x801B00B0,size=0x20)])]
        binding=dict(address='0x801B00B0',rom_offset='0x100',runtime_symbol='osService_recomp')
        ignored=map_game.attach_runtime_bindings(sections,[binding])
        self.assertEqual(ignored,['func_801B00B0_a'])
        self.assertEqual(sections[0]['functions'][0]['runtime_symbol'],'osService_recomp')
        self.assertNotIn('runtime_symbol',sections[1]['functions'][0])

    def test_unmapped_runtime_binding_cannot_silently_disappear(self):
        with self.assertRaises(ValueError):
            map_game.attach_runtime_bindings([dict(section('a'),functions=[])],
                [dict(address='0x801B00B0',rom_offset='0x100',runtime_symbol='osService_recomp')])


class ReviewedFunctionSpanTests(unittest.TestCase):
    def mapped(self):
        return dict(section('overlay',text_size=0x40),functions=[
            dict(vram=0x801B00B0,size=0x10,privileged=False),
            dict(vram=0x801B00C0,size=0x10,privileged=True),
            dict(vram=0x801B00D0,size=0x10,privileged=False)])
    def test_reviewed_span_merges_case_arms_preserving_other_functions(self):
        mapped=self.mapped();mapped['function_spans']=[dict(vram=0x801B00B0,size=0x20,evidence='synthetic bounded switch')]
        original=copy.deepcopy(mapped)
        result=map_game.apply_function_spans(mapped)
        self.assertEqual([(f['vram'],f['size']) for f in result],[(0x801B00B0,0x20),(0x801B00D0,0x10)])
        self.assertTrue(result[0]['privileged']);self.assertEqual(mapped,original)
    def test_partial_overlap_gaps_missing_start_and_missing_evidence_rejected(self):
        for span in [dict(vram=0x801B00B4,size=0x1C,evidence='proof'),dict(vram=0x801B00B0,size=0x14,evidence='proof'),dict(vram=0x801B00B0,size=0x20)]:
            mapped=self.mapped();mapped['function_spans']=[span]
            with self.subTest(span=span),self.assertRaises(ValueError):map_game.apply_function_spans(mapped)
        mapped=self.mapped();mapped['functions'].pop(1);mapped['function_spans']=[dict(vram=0x801B00B0,size=0x30,evidence='proof')]
        with self.assertRaises(ValueError):map_game.apply_function_spans(mapped)
    def test_span_metadata_aligned_bounded_nonoverlapping_and_normalized(self):
        base=section('overlay',text_size=0x40)
        for spans in [[dict(vram=0x801B00B0,size=0x44,evidence='proof')],[dict(vram=0x801B00B0,size=0x20,evidence='proof'),dict(vram=0x801B00C0,size=0x20,evidence='proof')],[dict(vram=0x801B00B0,size=3,evidence='proof')]]:
            with self.subTest(spans=spans),self.assertRaises(ValueError):map_game.validate_sections([dict(base,function_spans=spans)],0x1000)
        normalized=map_game.validate_sections([dict(base,function_spans=[dict(vram='0x801B00B0',size='0x20',evidence='proof')])],0x1000)[0]
        self.assertEqual(normalized['function_spans'][0]['size'],0x20)

    def test_terminal_case_shapes_merge_only_selected_rom_owner(self):
        # Multiple return arms must remain in the switch's compiler extent;
        # another overlay at identical guest addresses retains separate entries.
        for prefix,arm,count in [(0x3C,0x14,7),(0x30,8,4)]:
            start=0x801B00B0;size=prefix+arm*count
            functions=[dict(vram=start,size=prefix,privileged=False)]+[
                dict(vram=start+prefix+i*arm,size=arm,privileged=False) for i in range(count)]
            owner=dict(section('owner',text_size=0x100),functions=functions,
                       function_spans=[dict(vram=start,size=size,evidence='synthetic guarded terminal arms')])
            alias=dict(section('alias',rom=0x300,text_size=0x100),functions=copy.deepcopy(functions))
            owner['functions']=map_game.apply_function_spans(owner)
            mapped=tomllib.loads(map_game.render_symbols([owner,alias]))['section']
            self.assertEqual(len(mapped[0]['functions']),1)
            self.assertEqual(mapped[0]['functions'][0]['size'],size)
            self.assertEqual(len(mapped[1]['functions']),count+1)
