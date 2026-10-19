"""Generate private PAL derivatives selecting the highest original model/shadow detail.

Original project work: djultra64. Original ROM and generated CPU inputs stay unchanged.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROM_SHA256 = '6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf'
PROFILES = {
    'models': dict(address=0x800300D0, rom=0x30CD0, size=0x660,
        source_sha256='348e924ccc8cdccdd814c4ec86d3da8707d4b6fafe7c592bc7323a9c71697acb',
        body_sha256='e13fdb5abe618af2f90892ef1057d26eb1364087ec7f8c5d28de5f7beddd6aae',
        original='func_800300D0_resident', entry='iss2000_pal_max_detail_models'),
    'shadows': dict(address=0x80037498, rom=0x38098, size=0x3FC,
        source_sha256='c05d422ac38dc23aebb0b8e8a64efdf5e92767a730cc7eea2ce3c6934f301682',
        body_sha256='d4770f6efb7ff37ec2872a9895661c7577546995409014ab38c5c0bd04f17d56',
        original='func_80037498_resident', entry='iss2000_pal_max_detail_shadows'),
}

def derive(source: bytes, kind: str) -> bytes:
    profile = PROFILES[kind]
    if hashlib.sha256(source).hexdigest() != profile['source_sha256']:
        raise ValueError('Pinned PAL '+kind+' generated source digest mismatch')
    text = source.decode()
    # C++ COFF drops the upstream Clang extern-inline definition when this
    # private entry has no callers in its translation unit. Keep the original
    # header intact and give only this derivative a strong, non-inline entry.
    include = '#include "recomp.h"\n'
    if text.count(include) != 1:
        raise ValueError('Original recomp header include is not unique')
    text = text.replace(include, include +
        '#ifdef _WIN32\n#undef RECOMP_FUNC\n'
        '#define RECOMP_FUNC __declspec(noinline)\n#endif\n')
    def replace(old, new):
        nonlocal text
        if text.count(old) != 1:
            raise ValueError('PAL '+kind+' expression is not unique')
        text = text.replace(old, new)
    replace('RECOMP_FUNC void '+profile['original']+'(',
            'extern "C" RECOMP_FUNC void '+profile['entry']+'(')
    if kind == 'models':
        # All LOD-selection branches merge here, before the original cache and
        # type-specific geometry update. Culling and animation remain original.
        replace('L_8003022C:\n', 'L_8003022C:\n'
                '    // Highest existing original detail; cache and selector agree.\n'
                '    ctx->r16 = 0;\n')
    else:
        # Both branches have already preserved the original enabled flags and
        # buffer setup. Keep the original weather/material alpha and near
        # articulated generator; special shadow mode 2 remains untouched.
        for pc, table in [('800375A4', '80083BC8'), ('80037674', '80083B90')]:
            replace('    // 0x'+pc+': addiu',
                    '    ctx->r2 = (gpr)(int32_t)0x'+table+';\n'
                    '    goto L_80037734;\n'
                    '    // 0x'+pc+': addiu')
    return text.encode()

def prepare(rom: Path, models_source: Path, shadows_source: Path, output: Path) -> dict:
    binary = rom.read_bytes()
    if len(binary) != 0x1000000 or hashlib.sha256(binary).hexdigest() != ROM_SHA256:
        raise ValueError('Pinned PAL ROM digest mismatch')
    files, entries = {}, {}
    for kind, path in [('models', models_source), ('shadows', shadows_source)]:
        profile = PROFILES[kind]
        body = binary[profile['rom']:profile['rom']+profile['size']]
        if hashlib.sha256(body).hexdigest() != profile['body_sha256']:
            raise ValueError('Pinned PAL '+kind+' original body digest mismatch')
        result = derive(path.read_bytes(), kind)
        filename = 'pal_max_detail_'+kind+'.cpp'
        files[filename] = result
        entries[kind] = dict(original_entry=f"0x{profile['address']:08X}",
            original_rom=f"0x{profile['rom']:X}", original_size=profile['size'],
            original_body_sha256=profile['body_sha256'],
            original_source_sha256=profile['source_sha256'],
            entry=profile['entry'], file=filename,
            generated_sha256=hashlib.sha256(result).hexdigest())
    receipt = dict(schema=1, attribution='djultra64', revision='iss2000-pal-en-de-rev0',
        rom_sha256=ROM_SHA256, functions=entries,
        change='Original model level 0 with truthful cache; original articulated near shadows for modes 0/1',
        preserved=['visibility/frustum', 'simulation', 'animation', 'model variants',
                   'shadow suppression', 'special shadow mode 2'])
    files['receipt.json'] = (json.dumps(receipt, indent=2)+'\n').encode()
    if output.is_symlink() or any(p.is_symlink() for p in output.absolute().parents):
        raise ValueError('PAL detail output paths must not contain symlinks')
    if output.exists():
        if not output.is_dir() or set(p.name for p in output.iterdir()) != set(files):
            raise ValueError('Refusing to alter existing PAL detail derivative')
        if any((output/k).is_symlink() or not (output/k).is_file() or (output/k).read_bytes()!=v for k,v in files.items()):
            raise ValueError('Refusing to alter existing PAL detail derivative')
        return receipt
    output.mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        with (output/name).open('xb') as target:
            target.write(data)
    return receipt

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',required=True,type=Path)
    parser.add_argument('--models-source',required=True,type=Path)
    parser.add_argument('--shadows-source',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    print(json.dumps(prepare(args.rom,args.models_source,args.shadows_source,args.output),indent=2))
if __name__ == '__main__':
    main()
