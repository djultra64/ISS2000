"""Generate a private hash-pinned PAL sky-only widescreen derivative.

Original project work: djultra64. Original CPU source/ROM remain read-only.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROM_SHA256='6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf'
BODY_SHA256='00e12ea2a061178dbfb543dd78a6b181bfa8d04e52e77d26c9b536a5e53f6c75'
SOURCE_SHA256='bbd8b1ea3d9cade27636145f3a23aef21d366f2f7b0128d5ad8172ce7b9340d2'

def derive(source: bytes)->bytes:
    if hashlib.sha256(source).hexdigest()!=SOURCE_SHA256:
        raise ValueError('Pinned PAL sky generated source digest mismatch')
    text=source.decode()
    # C++ COFF drops the upstream Clang extern-inline definition when this
    # private entry has no callers in its translation unit. Keep the original
    # header intact and give only this derivative a strong, non-inline entry.
    include = '#include "recomp.h"\n'
    if text.count(include) != 1:
        raise ValueError('Original recomp header include is not unique')
    text = text.replace(include, include +
        '#ifdef _WIN32\n#undef RECOMP_FUNC\n'
        '#define RECOMP_FUNC __declspec(noinline)\n#endif\n')
    def replace(old,new):
        nonlocal text
        if text.count(old)!=1:raise ValueError('PAL sky source expression is not unique')
        text=text.replace(old,new)
    replace('RECOMP_FUNC void func_80035CC0_resident(', 'extern \"C\" RECOMP_FUNC void iss2000_pal_wide_sky(')
    replace('    ctx->r11 = ctx->r6 + 0;',
            '    ctx->r11 = (uint32_t(ctx->r6) - 1u) & 1u;\n    ctx->r14 = SUB32(ctx->r14, 0X40);')
    replace('    ctx->r2 = SIGNED(ctx->r16) < 0X6 ? 1 : 0;',
            '    ctx->r2 = SIGNED(ctx->r16) < 0X8 ? 1 : 0;')
    replace('L_80036174:\n', 'L_80036174:\n    iss2000_pal_sky_aspect(rdram, 1);\n')
    begin=text.index('    // 0x80036360: daddu')
    end=text.index('L_800364DC:',begin)
    text=text[:begin]+'''    // Bounded derivative of the original sky rectangle emitter only.
    ctx->r7 = MEM_H(ctx->r15, 0X0);
    ctx->r9 = MEM_H(ctx->r15, 0X2);
    MEM_W(0X0, ctx->r17) = iss2000_pal_sky_emit(rdram,
        (uint32_t)MEM_W(ctx->r17, 0X0), (int32_t)ctx->r7,
        (int32_t)ctx->r9, (uint32_t)ctx->r4,
        MEM_BU(MEM_W((gpr)(int32_t)0X8009E02C, 0X0), 0X12) != 0);
    ctx->r15 = ADD32(ctx->r15, 0X8);
'''+text[end:]
    replace('    // 0x800364FC: lui',
            '    iss2000_pal_sky_aspect(rdram, 0);\n    // 0x800364FC: lui')
    # Generated CPU inputs compile as C++; retain their original implementation
    # and introduce only three small host geometry calls in a private derivative.
    prefix='''#include <stdint.h>
extern "C" uint32_t iss2000_pal_sky_emit(uint8_t*,uint32_t,int32_t,int32_t,uint32_t,int);
extern "C" void iss2000_pal_sky_aspect(uint8_t*,int);
'''
    return (prefix+text).encode()

def prepare(rom:Path,source:Path,output:Path)->dict:
    binary=rom.read_bytes()
    if hashlib.sha256(binary).hexdigest()!=ROM_SHA256 or hashlib.sha256(binary[0x368c0:0x371ec]).hexdigest()!=BODY_SHA256:
        raise ValueError('Pinned PAL ROM/sky body digest mismatch')
    generated=derive(source.read_bytes())
    receipt=dict(rom_sha256=ROM_SHA256,original_body_sha256=BODY_SHA256,
        original_source_sha256=SOURCE_SHA256,generated_sha256=hashlib.sha256(generated).hexdigest(),
        entry='iss2000_pal_wide_sky',original_entry='0x80035CC0',
        change='8 sky columns; reciprocal horizontal geometry/sampling; scoped sky-only rectangle aspect',
        original_rom_bounds=['0x368C0','0x371EC'])
    files={'pal_wide_sky.cpp':generated,'receipt.json':(json.dumps(receipt,indent=2)+'\n').encode()}
    if output.exists():
        if output.is_symlink() or any(not (output/k).is_file() or (output/k).is_symlink() or (output/k).read_bytes()!=v for k,v in files.items()):
            raise ValueError('Refusing to alter existing PAL sky derivative')
        return receipt
    if any(p.is_symlink() for p in output.absolute().parents):raise ValueError('PAL sky output parent paths must not contain symlinks')
    output.mkdir(parents=True,exist_ok=False)
    for key,value in files.items():
        with (output/key).open('xb') as target:target.write(value)
    return receipt

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',required=True,type=Path)
    p.add_argument('--source',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();print(json.dumps(prepare(a.rom,a.source,a.output),indent=2))
if __name__=='__main__':main()
