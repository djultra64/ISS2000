"""Build input identity checks use synthetic sources; no game execution."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest


def digest(data):return hashlib.sha256(data).hexdigest()

class VerifyNativeBuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='iss2000-build-identity-');self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.revision='iss2000-pal-en-de-rev0';self.rom='a'*64
        self.generated=self.root/'map/functions';self.generated.mkdir(parents=True)
        self.metadata=self.root/'metadata';self.metadata.mkdir()
        self.runtime=self.root/'runtime.json';self.audio=self.root/'audio.cpp';self.audio.write_bytes(b'original audio')
        (self.root/'config/roms').mkdir(parents=True);(self.root/'config/recomp').mkdir()
        self.put(self.root/'config/roms'/f'{self.revision}.json',{'revision_id':self.revision,'sha256':self.rom})
        self.put(self.root/'config/recomp/native-build-inputs.json',{'schema_version':1,'audio':{'source_sha256':digest(self.audio.read_bytes()),'revisions':{self.revision:{'rom_sha256':self.rom}}}})
        self.put(self.runtime,{'rom_sha256':self.rom})
        files={'functions/original.c':b'original CPU','functions/funcs.h':b'original header','functions/recomp_overlays.inl':b'original overlay list'}
        for name,data in files.items():(self.generated.parent/name).write_bytes(data)
        self.put(self.generated.parent/'summary.json',{'rom_sha256':self.rom,'generated_files':{n:digest(v) for n,v in files.items()}})
        self.sections=self.generated.parent/'section-analysis.json';self.sections.write_bytes(b'[]')
        outputs={n:(n+' original').encode() for n in ['native_metadata.cpp','native_bindings.cpp','native_retained.cpp']}
        for n,b in outputs.items():(self.metadata/n).write_bytes(b)
        self.put(self.metadata/'receipt.json',{'rom_sha256':self.rom,'section_analysis_sha256':digest(self.sections.read_bytes()),'runtime_manifest_sha256':digest(self.runtime.read_bytes()),'generated_files':{n:digest(b) for n,b in outputs.items()}})
    def put(self,p,v):p.write_text(json.dumps(v))
    def verify(self):
        from tools.verify_native_build import verify
        return verify(self.revision,self.generated,self.metadata,self.runtime,self.audio,root=self.root)
    def test_accepts_complete_matching_input_and_returns_compact_receipt(self):
        r=self.verify();self.assertEqual(r['rom_sha256'],self.rom);self.assertEqual(r['cpu_sources'],3);self.assertEqual(len(r['inputs_sha256']),64);self.assertNotIn('generated_files',r)
    def test_rejects_changed_original_cpu_source(self):
        (self.generated/'original.c').write_bytes(b'altered');self.assertRaisesRegex(ValueError,'source',self.verify)
    def test_rejects_missing_original_header(self):
        (self.generated/'funcs.h').unlink();self.assertRaises(ValueError,self.verify)
    def test_rejects_extra_translation_unit(self):
        (self.generated/'injected.c').write_bytes(b'injected');self.assertRaisesRegex(ValueError,'extra|inventory',self.verify)
    def test_rejects_extra_nested_header(self):
        p=self.generated/'nested';p.mkdir();(p/'injected.h').write_bytes(b'injected');self.assertRaises(ValueError,self.verify)
    def test_rejects_wrong_map_rom(self):
        p=self.generated.parent/'summary.json';r=json.loads(p.read_text());r['rom_sha256']='b'*64;self.put(p,r);self.assertRaisesRegex(ValueError,'ROM|revision',self.verify)
    def test_rejects_changed_section_analysis(self):
        self.sections.write_bytes(b'[{}]');self.assertRaisesRegex(ValueError,'section',self.verify)
    def test_rejects_changed_metadata_source(self):
        (self.metadata/'native_retained.cpp').write_bytes(b'wrong PFS');self.assertRaisesRegex(ValueError,'metadata',self.verify)
    def test_rejects_changed_runtime_manifest(self):
        self.runtime.write_bytes(self.runtime.read_bytes()+b' ');self.assertRaisesRegex(ValueError,'manifest',self.verify)
    def test_rejects_wrong_runtime_manifest_rom_even_with_fresh_receipt(self):
        self.put(self.runtime,{'rom_sha256':'b'*64});p=self.metadata/'receipt.json';r=json.loads(p.read_text());r['runtime_manifest_sha256']=digest(self.runtime.read_bytes());self.put(p,r);self.assertRaises(ValueError,self.verify)
    def test_rejects_unpinned_audio_source(self):
        self.audio.write_bytes(b'wrong audio');self.assertRaisesRegex(ValueError,'audio',self.verify)
    def test_rejects_summary_path_escape(self):
        p=self.generated.parent/'summary.json';r=json.loads(p.read_text());r['generated_files']['functions/../../outside.c']='0'*64;self.put(p,r);self.assertRaises(ValueError,self.verify)
    def test_rejects_symlinked_original_source(self):
        p=self.generated/'original.c';p.unlink();target=self.root/'elsewhere.c';target.write_bytes(b'original CPU');p.symlink_to(target);self.assertRaises(ValueError,self.verify)
    def test_rejects_missing_metadata_output_even_if_removed_from_receipt(self):
        p=self.metadata/'receipt.json';r=json.loads(p.read_text());del r['generated_files']['native_retained.cpp'];self.put(p,r);self.assertRaises(ValueError,self.verify)
    def test_rejects_unsupported_profile_before_reading_arbitrary_path(self):
        self.revision='../outside';self.assertRaises(ValueError,self.verify)
