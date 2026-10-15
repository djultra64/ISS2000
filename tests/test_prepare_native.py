"""Original project work: djultra64."""
import hashlib
import json
from pathlib import Path
import tempfile
import subprocess
import unittest
from tools.prepare_native import render_sources, prepare


class PrepareNativeTests(unittest.TestCase):
    def fixture(self):
        rom=bytes(range(64))
        binding=dict(address='0x80000408',name='osGetCount',runtime_symbol='osGetCount_recomp',rom_offset='0x18',size=8,sha256=hashlib.sha256(rom[24:32]).hexdigest(),status='verified-instructions-and-abi',evidence='mfc0 Count')
        manifest=dict(schema_version=1,rom_sha256=hashlib.sha256(rom).hexdigest(),bindings=[binding])
        section=dict(name='resident',rom=16,vram=0x80000400,load_size=32,text_size=24,functions=[
            dict(name='func_80000400_resident',vram=0x80000400,size=8,privileged=False),
            dict(name='func_80000408_resident',vram=0x80000408,size=8,privileged=True,runtime_symbol='osGetCount_recomp'),
            dict(name='func_80000410_resident',vram=0x80000410,size=8,privileged=True)])
        return rom,manifest,[section]

    def test_runtime_wrappers_included_and_unknown_privileged_excluded(self):
        _,m,s=self.fixture(); metadata,wrappers=render_sources(s,m['bindings'])
        self.assertIn('&func_80000400_resident',metadata)
        self.assertIn('&func_80000408_resident',metadata)
        self.assertNotIn('func_80000410_resident',metadata+wrappers)
        self.assertIn('recomp::overlays::register_overlays',metadata)
        self.assertIn('iss2000::call_service(0x80000408u, "osGetCount", &osGetCount_recomp',wrappers)

    def test_overlapping_guest_addresses_keep_distinct_section_identity(self):
        _,m,s=self.fixture(); overlay=dict(name='overlay',rom=48,vram=0x80000400,load_size=8,text_size=8,functions=[dict(name='func_80000400_overlay',vram=0x80000400,size=8,privileged=False)])
        metadata,_=render_sources(s+[overlay],m['bindings'])
        self.assertIn('&func_80000400_overlay',metadata)
        self.assertIn('"overlay", 0x00000030u',metadata)

    def test_reject_unreviewed_runtime_binding_or_wrong_rom_origin(self):
        for mutation in ['name','origin']:
            _,m,s=self.fixture()
            if mutation=='name':s[0]['functions'][1]['runtime_symbol']='unreviewed_recomp'
            else:s[0]['rom']=20
            with self.assertRaisesRegex(ValueError,'reviewed binding'):
                render_sources(s,m['bindings'])

    def test_reject_injected_identifier_and_out_of_section_target(self):
        _,m,s=self.fixture();s[0]['functions'][0]['name']='function;bad'
        with self.assertRaisesRegex(ValueError,'identifier'):render_sources(s,m['bindings'])
        _,m,s=self.fixture();s[0]['functions'][0]['vram']=0x800003FC
        with self.assertRaisesRegex(ValueError,'function bounds'):render_sources(s,m['bindings'])

    def test_new_reviewed_override_does_not_require_cpu_regeneration(self):
        rom,m,s=self.fixture()
        # Original translated body remains compiled and has no runtime_symbol.
        s[0]['functions'][2]['privileged']=False
        m['bindings'].append(dict(address='0x80000410',name='osGetMemSize',runtime_symbol='osGetMemSize_recomp',rom_offset='0x20',size=8,sha256=hashlib.sha256(rom[32:40]).hexdigest(),status='verified-instructions-and-abi',evidence='memory probe ABI'))
        metadata,wrappers=render_sources(s,m['bindings'])
        self.assertIn('&func_80000410_resident',metadata)
        self.assertNotIn('extern "C" void func_80000410_resident',wrappers)
        self.assertIn('recomp_func_t* reviewed_service(uint32_t address)',wrappers)
        self.assertIn('case 0x80000410u: return &reviewed_80000410;',wrappers)
        self.assertIn('iss2000::call_service(0x80000410u, "osGetMemSize", &osGetMemSize_recomp',wrappers)
        self.assertIn('default: return nullptr;',wrappers)

    def test_fresh_output_required_and_rom_digest_checked_before_writing(self):
        rom,m,s=self.fixture()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'rom').write_bytes(rom);(root/'manifest').write_text(json.dumps(m));(root/'sections').write_text(json.dumps(s))
            out=root/'out';prepare(root/'rom',root/'sections',root/'manifest',out)
            self.assertTrue((out/'native_metadata.cpp').is_file());self.assertTrue((out/'native_bindings.cpp').is_file())
            with self.assertRaises(FileExistsError):prepare(root/'rom',root/'sections',root/'manifest',out)
            (root/'rom').write_bytes(b'wrong')
            with self.assertRaisesRegex(ValueError,'ROM digest'):prepare(root/'rom',root/'sections',root/'manifest',root/'bad')
            self.assertFalse((root/'bad').exists())

    def test_retained_original_has_unique_callable_body_and_required_input(self):
        rom,m,s=self.fixture();m['bindings'][0]['preserve_source']=True
        original='#include "recomp.h"\nRECOMP_FUNC void func_80000408_resident(uint8_t* rdram, recomp_context* ctx) {\n// 0x80000408: addiu $v0, $zero, 7\nctx->r2=7;\n// 0x8000040C: jr $ra\n}\n'
        m['bindings'][0]['preserved_source_sha256']=hashlib.sha256(original.encode()).hexdigest()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for name,value in [('rom',rom),('manifest',json.dumps(m).encode()),('sections',json.dumps(s).encode()),('original.c',original.encode())]:(root/name).write_bytes(value)
            with self.assertRaisesRegex(ValueError,'retained original'):
                prepare(root/'rom',root/'sections',root/'manifest',root/'missing')
            self.assertFalse((root/'missing').exists())
            receipt=prepare(root/'rom',root/'sections',root/'manifest',root/'out',retained_sources=[root/'original.c'])
            generated=(root/'out/native_retained.cpp').read_text()
            self.assertIn('iss2000_original_80000408',generated)
            self.assertEqual(receipt['retained_original_services'],1)
            # Compile/link the real original body with an intentionally different host
            # wrapper: the bridge must execute original7 rather than absent-device1.
            (root/'recomp.h').write_text('#include <cstdint>\n#define RECOMP_FUNC extern "C"\nstruct recomp_context { uint64_t r2; };\n')
            (root/'main.cpp').write_text('#include "recomp.h"\nextern "C" void iss2000_original_80000408(uint8_t*,recomp_context*);\nextern "C" void func_80000408_resident(uint8_t*,recomp_context* c){c->r2=1;}\nint main(){recomp_context c{};iss2000_original_80000408(nullptr,&c);return c.r2==7?0:1;}\n')
            subprocess.run(['c++','-I'+str(root),str(root/'out/native_retained.cpp'),str(root/'main.cpp'),'-o',str(root/'run')],check=True,capture_output=True)
            subprocess.run([str(root/'run')],check=True,capture_output=True)
            (root/'original.c').write_text(original.replace('ctx->r2=7','ctx->r2=1'))
            with self.assertRaisesRegex(ValueError,'source digest'):
                prepare(root/'rom',root/'sections',root/'manifest',root/'changed',retained_sources=[root/'original.c'])
            self.assertFalse((root/'changed').exists())
            (root/'original.c').write_text('RECOMP_FUNC void func_80000408_resident(uint8_t* rdram,recomp_context* ctx){ctx->r2=1;}')
            with self.assertRaisesRegex(ValueError,'instruction'):
                prepare(root/'rom',root/'sections',root/'manifest',root/'wrapper',retained_sources=[root/'original.c'])
            self.assertFalse((root/'wrapper').exists())
