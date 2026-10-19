"""Select original PAL High by default after genuine Expansion Pak detection.

Original project work: djultra64. Current video mode, original buffers, language,
saves and scene-specific temporary High disable/restore paths remain original.
"""
import argparse
import hashlib
import json
from pathlib import Path
ROM_SHA256='6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf'
SOURCE_SHA256='80402808818c3321023f7092aced5190f9bc393a3e014259a1fe7a9fc0eb7860'
BODY_SHA256='da390875e1803aae87c5220999e666a3e6c4a20a41877662c48fcba2f01e166d'
ENTRY='iss2000_pal_fixed_high_initializer'
def derive(source:bytes)->bytes:
    if hashlib.sha256(source).hexdigest()!=SOURCE_SHA256:raise ValueError('Pinned PAL High initializer source digest mismatch')
    text=source.decode()
    # C++ COFF drops the upstream Clang extern-inline definition when this
    # private entry has no callers in its translation unit. Keep the original
    # header intact and give only this derivative a strong, non-inline entry.
    include = '#include "recomp.h"\n'
    if text.count(include) != 1:raise ValueError('Original recomp header include is not unique')
    text = text.replace(include, include +
        '#ifdef _WIN32\n#undef RECOMP_FUNC\n'
        '#define RECOMP_FUNC __declspec(noinline)\n#endif\n')
    old='RECOMP_FUNC void func_80008C30_resident('
    if text.count(old)!=1:raise ValueError('Original High initializer symbol is not unique')
    text=text.replace(old,'extern "C" RECOMP_FUNC void '+ENTRY+'(')
    old='    // 0x80008C90: sb          $zero, 0x13($v1)\n    MEM_B(0X13, ctx->r3) = 0;'
    if text.count(old)!=2:raise ValueError('Original High default delay-slot clear is not duplicated exactly twice')
    text=text.replace(old,'    // Original High request default follows genuine memory detection.\n'+old.replace('MEM_B(0X13, ctx->r3) = 0;','MEM_B(0X13, ctx->r3) = MEM_BU(ctx->r3, 0X11);'))
    return text.encode()
def prepare(rom:Path,source:Path,output:Path)->dict:
    binary=rom.read_bytes()
    if len(binary)!=0x1000000 or hashlib.sha256(binary).hexdigest()!=ROM_SHA256:raise ValueError('Pinned PAL ROM digest mismatch')
    if hashlib.sha256(binary[0x9830:0x9830+140]).hexdigest()!=BODY_SHA256:raise ValueError('Pinned PAL High initializer body mismatch')
    result=derive(source.read_bytes())
    receipt=dict(schema=2,attribution='djultra64',revision='iss2000-pal-en-de-rev0',rom_sha256=ROM_SHA256,original_entry='0x80008C30',original_rom='0x9830',original_size=140,original_body_sha256=BODY_SHA256,original_source_sha256=SOURCE_SHA256,entry=ENTRY,file='pal_fixed_high_initializer.cpp',generated_sha256=hashlib.sha256(result).hexdigest(),change='Original08C90 desired-resolution default follows original frame+11 genuine8MiB detection instead of clearing it',preserved=['original osGetMemSize and genuine memory detection','original current working video clear at80008C80','original08CBC buffer initialization','all original settings and language','original scene video requests80001D44','original buffer setup80001E40/80002D08','Career temporary High disable/restore','all original saves and input source files'])
    files={'pal_fixed_high_initializer.cpp':result,'receipt.json':(json.dumps(receipt,indent=2)+'\n').encode()}
    if output.is_symlink()or any(p.is_symlink()for p in output.absolute().parents):raise ValueError('High derivative output paths must not contain symlinks')
    if output.exists():
        if not output.is_dir()or set(p.name for p in output.iterdir())!=set(files)or any((output/k).is_symlink()or not(output/k).is_file()or(output/k).read_bytes()!=v for k,v in files.items()):raise ValueError('Refusing to alter existing High derivative')
        return receipt
    output.mkdir(parents=True,exist_ok=False)
    for name,data in files.items():
        with(output/name).open('xb')as target:target.write(data)
    return receipt

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--rom',required=True,type=Path);parser.add_argument('--source',required=True,type=Path);parser.add_argument('--output',required=True,type=Path);a=parser.parse_args();print(json.dumps(prepare(a.rom,a.source,a.output),indent=2))
if __name__=='__main__':main()
