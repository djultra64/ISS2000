"""Only the reviewed aspect-load instruction may be extended privately."""
import hashlib
import unittest
from tools import prepare_render_sources as patches
class RenderSourcePatchTests(unittest.TestCase):
    def source(self):
        return b'#include "recomp.h"\nvoid example(){\n    // 0x80255B74: lwc1        $f2, -0x2100($at)\n    ctx->f2.u32l = MEM_W(ctx->r1, -0X2100);\n    ctx->f20.fl = ctx->f20.fl * ctx->f2.fl;\n}\n'
    def test_exact_owned_load_is_extended_and_remaining_code_preserved(self):
        data=self.source();result=patches.transform(data,0x80255B74,2,hashlib.sha256(data).hexdigest())
        self.assertEqual(result.count(b'ctx->f2.fl = iss2000_marker_aspect(ctx->f2.fl);'),1)
        stripped=result.replace(b'extern float iss2000_marker_aspect(float);\n',b'').replace(b'    ctx->f2.fl = iss2000_marker_aspect(ctx->f2.fl);\n',b'')
        self.assertEqual(stripped,data)
    def test_changed_input_wrong_pc_or_wrong_register_fails_closed(self):
        data=self.source();digest=hashlib.sha256(data).hexdigest()
        for contents,pc,reg,sha in [(data+b'changed',0x80255B74,2,digest),(data,0x80255B78,2,digest),(data,0x80255B74,14,digest)]:
            with self.subTest(pc=pc,reg=reg),self.assertRaises(ValueError):patches.transform(contents,pc,reg,sha)
