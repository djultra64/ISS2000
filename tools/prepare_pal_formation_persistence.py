"""Persist explicit PAL formation saves through the original storage worker.

Original project work: djultra64. Original probe, asynchronous write, error handling and completion remain intact.
The physical-accessory choice must not turn portable Save into RAM-only storage.
"""
import argparse
import hashlib
import json
from pathlib import Path
ROM_SHA256='6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf'
SOURCE_SHA256='cc082d9a3f690dab3f5cdf2a6e310dd43b14b67b09f7c72fc69b5197c576d0ed'
BODY_SHA256='32baa07d2653ebc5924b7e8db2fec7d0e84ee6ab0658269f47148c579c523045'
ENTRY='iss2000_pal_formation_save'
def derive(source:bytes)->bytes:
    if hashlib.sha256(source).hexdigest()!=SOURCE_SHA256:raise ValueError('Pinned PAL formation save source digest mismatch')
    text=source.decode()
    # C++ COFF drops the upstream Clang extern-inline definition when this
    # private entry has no callers in its translation unit. Keep the original
    # header intact and give only this derivative a strong, non-inline entry.
    include = '#include "recomp.h"\n'
    if text.count(include) != 1:raise ValueError('Original recomp header include is not unique')
    text = text.replace(include, include +
        '#ifdef _WIN32\n#undef RECOMP_FUNC\n'
        '#define RECOMP_FUNC __declspec(noinline)\n#endif\n')
    old='RECOMP_FUNC void func_802A3464_overlay_3e83d0_8029eea0('
    if text.count(old)!=1:raise ValueError('Original formation save symbol is not unique')
    text=text.replace(old,'extern "C" RECOMP_FUNC void '+ENTRY+'(')
    old='    // 0x802A3518: bne         $v0, $v1, L_802A36AC\n    if (ctx->r2 != ctx->r3) {'
    if text.count(old)!=1:raise ValueError('Original formation storage branch is not unique')
    text=text.replace(old, '    // Explicit portable Save uses the genuine original probe/write path.\n'
        '    // Preserve the original path outside its two supported logical ports.\n'
        '    if (ctx->r2 != ctx->r3 && uint32_t(ctx->r4) >= 2u) {')
    # The original C switch temporary can be jumped over. Hoist only its
    # declaration for C++, retaining the assignment at the original instruction.
    declaration='    gpr jr_addend_802A3558 = ctx->r2;'
    anchor='    int c1cs = 0;'
    if text.count(declaration)!=1 or text.count(anchor)!=1:raise ValueError('Original switch temporary is not unique')
    text=text.replace(anchor,anchor+'\n    gpr jr_addend_802A3558;').replace(declaration,'    jr_addend_802A3558 = ctx->r2;')
    return text.encode()
def prepare(rom:Path,source:Path,output:Path)->dict:
    binary=rom.read_bytes()
    if len(binary)!=0x1000000 or hashlib.sha256(binary).hexdigest()!=ROM_SHA256:raise ValueError('Pinned PAL ROM digest mismatch')
    if hashlib.sha256(binary[0x3ec994:0x3ec994+0x2bc]).hexdigest()!=BODY_SHA256:raise ValueError('Pinned PAL formation save body mismatch')
    result=derive(source.read_bytes())
    receipt=dict(schema=2,attribution='djultra64',revision='iss2000-pal-en-de-rev0',rom_sha256=ROM_SHA256,original_entry='0x802A3464',original_rom='0x3EC994',original_size=0x2BC,original_body_sha256=BODY_SHA256,original_source_sha256=SOURCE_SHA256,entry=ENTRY,file='pal_formation_save.cpp',generated_sha256=hashlib.sha256(result).hexdigest(),change='Route explicit formation Save through original asynchronous persistent storage',preserved=['original SDK probe and write results','original asynchronous write and error callbacks','original logical port and slot selection','no changes to accessory-choice flags or save payload'])
    files={'pal_formation_save.cpp':result,'receipt.json':(json.dumps(receipt,indent=2)+'\n').encode()}
    if output.is_symlink()or any(p.is_symlink()for p in output.absolute().parents):raise ValueError('formation derivative output paths must not contain symlinks')
    if output.exists():
        if not output.is_dir()or set(p.name for p in output.iterdir())!=set(files)or any((output/k).is_symlink()or not(output/k).is_file()or(output/k).read_bytes()!=v for k,v in files.items()):raise ValueError('Refusing to alter existing formation derivative')
        return receipt
    output.mkdir(parents=True,exist_ok=False)
    for name,data in files.items():
        with(output/name).open('xb')as target:target.write(data)
    return receipt

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--rom',required=True,type=Path);parser.add_argument('--source',required=True,type=Path);parser.add_argument('--output',required=True,type=Path);a=parser.parse_args();print(json.dumps(prepare(a.rom,a.source,a.output),indent=2))
if __name__=='__main__':main()
