"""Prepare the PAL enhanced-memory informational notice's original continuation.

Original project work: djultra64. Actual memory configuration remains original.
"""
import argparse
import hashlib
import json
from pathlib import Path
ROM_SHA256='6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf'
SOURCE_SHA256='105a1a42bed3b09a6d03a006979c950b0346c9bf429113974a8e88c82a1e9f75'
BODY_SHA256='cf2b45ac7c5053ed3764a9aa6d876ba62e3b4c46826faed3a64f3c363fd21344'
ORIGINAL='func_802B1FDC_overlay_481680_802b1070'
ENTRY='iss2000_pal_skip_expansion_notice'
def derive(source:bytes)->bytes:
    if hashlib.sha256(source).hexdigest()!=SOURCE_SHA256:
        raise ValueError('Pinned PAL expansion UI source digest mismatch')
    text=source.decode()
    # C++ COFF drops the upstream Clang extern-inline definition when this
    # private entry has no callers in its translation unit. Keep the original
    # header intact and give only this derivative a strong, non-inline entry.
    include = '#include "recomp.h"\n'
    if text.count(include) != 1:
        raise ValueError('Original recomp header include is not unique')
    text = text.replace(include, include +
        '#ifdef _WIN32\n#undef RECOMP_FUNC\n'
        '#define RECOMP_FUNC __declspec(noinline)\n#endif\n');old='RECOMP_FUNC void '+ORIGINAL+'('
    if text.count(old)!=1:raise ValueError('Original expansion UI entry is not unique')
    text=text.replace(old,'extern "C" RECOMP_FUNC void '+ENTRY+'(')
    original_branch="""    // 0x802B2024: bne         $v0, $v1, L_802B2050
    if (ctx->r2 != ctx->r3) {
        // 0x802B2028: addiu       $v0, $zero, 0xE
        ctx->r2 = ADD32(0, 0XE);
            goto L_802B2050;
    }"""
    if text.count(original_branch)!=1:raise ValueError('Pinned enhanced-memory UI branch is not unique')
    replacement=original_branch.replace('if (ctx->r2 != ctx->r3)','if (true)').replace(
        'goto L_802B2050;','goto L_802B2060;')
    text=text.replace(original_branch,
        '    // PC informational notice omitted; retain real memory and Pak selection.\n'+replacement)
    return text.encode()

def prepare(rom:Path,source:Path,output:Path)->dict:
    binary=rom.read_bytes()
    if len(binary)!=0x1000000 or hashlib.sha256(binary).hexdigest()!=ROM_SHA256:
        raise ValueError('Pinned PAL ROM digest mismatch')
    if hashlib.sha256(binary[0x4825EC:0x482728]).hexdigest()!=BODY_SHA256:
        raise ValueError('Pinned PAL expansion selector body digest mismatch')
    result=derive(source.read_bytes())
    receipt=dict(schema=1,attribution='djultra64',revision='iss2000-pal-en-de-rev0',
        rom_sha256=ROM_SHA256,original_entry='0x802B1FDC',original_symbol=ORIGINAL,
        original_rom='0x4825EC',original_size=0x13C,original_body_sha256=BODY_SHA256,
        original_source_sha256=SOURCE_SHA256,entry=ENTRY,file='pal_skip_expansion_notice.cpp',
        generated_sha256=hashlib.sha256(result).hexdigest(),
        change='High-memory informational UI branch802B2024 uses original2060 continuation instead of notice14',
        preserved=['actual memory/detection/configuration','original high-memory buffers',
            'Controller Pak prompts and filesystem','noExpansion notice16','input state'],
        no_game_execution=True)
    files={'pal_skip_expansion_notice.cpp':result,'receipt.json':(json.dumps(receipt,indent=2)+'\n').encode()}
    if output.is_symlink() or any(p.is_symlink() for p in output.absolute().parents):
        raise ValueError('Expansion UI output paths must not contain symlinks')
    if output.exists():
        if not output.is_dir() or set(p.name for p in output.iterdir())!=set(files):
            raise ValueError('Refusing to alter existing PAL expansion UI derivative')
        if any((output/name).is_symlink() or not (output/name).is_file() or
               (output/name).read_bytes()!=data for name,data in files.items()):
            raise ValueError('Refusing to alter existing PAL expansion UI derivative')
        return receipt
    output.mkdir(parents=True,exist_ok=False)
    for name,data in files.items():
        with (output/name).open('xb') as target:target.write(data)
    return receipt

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',required=True,type=Path)
    parser.add_argument('--source',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    print(json.dumps(prepare(args.rom,args.source,args.output),indent=2))
if __name__=='__main__':main()
