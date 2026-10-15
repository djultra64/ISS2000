"""Prepare exact PAL UI continuations without physical Rumble Pak swap notices.

Original project work: djultra64. Original inputs and all SDK/probe results stay intact.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
ROM_SHA256='6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf'
PROFILES = {'802B5574': {'address': 2150323572,
              'rom': 4188596,
              'size': 256,
              'original': 'func_802B5574_overlay_3fc9f0_802b35b0',
              'entry': 'iss2000_pal_skip_rumble_802B5574',
              'source_sha256': 'bd91dafeb97a9290957c34653e1cbe6682b2199348cedba2a820dd5984dc9fb8',
              'body_sha256': '99922b71ad8e9296ed3699fcb0df97521e2d03a5f77e9b543af943a9f57d752a',
              'branches': [(2150323660, 'beq', True), (2150323688, 'bne', False)]},
 '802BA770': {'address': 2150344560,
              'rom': 4209536,
              'size': 140,
              'original': 'func_802BA770_overlay_401910_802b8500',
              'entry': 'iss2000_pal_skip_rumble_802BA770',
              'source_sha256': '1540e94e8b7c5a3ea2c4b8458de54eeb1bccf546da5ccd257b06de56498d0196',
              'body_sha256': '079e62c185e7711b9007e59693fa2c317ba7712f9745132e97411c308cf8b2ff',
              'branches': [(2150344608, 'bne', False)]},
 '802BE1B8': {'address': 2150359480,
              'rom': 4224456,
              'size': 152,
              'original': 'func_802BE1B8_overlay_401910_802b8500',
              'entry': 'iss2000_pal_skip_rumble_802BE1B8',
              'source_sha256': '2f2fc23dc2e158f9c4f7dc448796249bdb5f82cae31a26da1ac044161c41871b',
              'body_sha256': 'a893cb33d3a4d1ed8a7ffb5f9ca140c8e9ec11c67986cd9b6404abf4f7c3980a',
              'branches': [(2150359524, 'bne', False)]},
 '802C6D34': {'address': 2150395188,
              'rom': 4259908,
              'size': 200,
              'original': 'func_802C6D34_overlay_40c7a0_802c3490',
              'entry': 'iss2000_pal_skip_rumble_802C6D34',
              'source_sha256': '2bb40a48a88227f95e57963f5ab4734582565034d75abfac945ad408468d0dd1',
              'body_sha256': '1ce0ad2ca758d864cde1f4d9d9d6a01f08418fbedc126da3d8644792a34c3d1b',
              'branches': [(2150395280, 'bne', False)]},
 '803D2F34': {'address': 2151493428,
              'rom': 5770612,
              'size': 88,
              'original': 'func_803D2F34_overlay_57f870_803d1a30',
              'entry': 'iss2000_pal_skip_rumble_803D2F34',
              'source_sha256': 'c87cbe58c50954e76fd985657af3e8deaf89142bc10c37bce81a5c23b8ad537a',
              'body_sha256': '2aa912de794ae0ace64c31f5f60f8b394aa318ea48b2301ba8040b011ec3aaf8',
              'branches': [(2151493448, 'bne', False)]}}

def derive(source: bytes, key: str) -> bytes:
    profile=PROFILES[key]
    if hashlib.sha256(source).hexdigest()!=profile['source_sha256']:
        raise ValueError('Pinned PAL UI source digest mismatch')
    text=source.decode()
    old='RECOMP_FUNC void '+profile['original']+'('
    if text.count(old)!=1:raise ValueError('Original UI entry is not unique')
    text=text.replace(old,'extern "C" RECOMP_FUNC void '+profile['entry']+'(')
    # Keep the genuine probe, its return value and all branch delay slots.
    # Only the UI decision to enqueue the physical swap notice changes.
    for pc,mnemonic,taken in profile['branches']:
        pattern=(r'(    // 0x'+f'{pc:08X}'+': '+mnemonic+
                 r'[^\n]*\n    if \()[^\n]+(?=\) \{)')
        text,count=re.subn(pattern,lambda m:m.group(1)+('true' if taken else 'false'),text)
        if count!=1:raise ValueError('Pinned Rumble UI branch is not unique')
    return text.encode()


def prepare(rom: Path, generated: Path, output: Path) -> dict:
    binary=rom.read_bytes()
    if len(binary)!=0x1000000 or hashlib.sha256(binary).hexdigest()!=ROM_SHA256:
        raise ValueError('Pinned PAL ROM digest mismatch')
    files,functions={},{}
    for key,profile in PROFILES.items():
        body=binary[profile['rom']:profile['rom']+profile['size']]
        if hashlib.sha256(body).hexdigest()!=profile['body_sha256']:
            raise ValueError('Pinned PAL original UI body digest mismatch')
        result=derive((generated/(profile['original']+'.c')).read_bytes(),key)
        filename='pal_rumble_ui_'+key+'.cpp'
        files[filename]=result
        functions[key]=dict(original_entry=f"0x{profile['address']:08X}",
            original_symbol=profile['original'],original_rom=f"0x{profile['rom']:X}",
            original_size=profile['size'],original_body_sha256=profile['body_sha256'],
            original_source_sha256=profile['source_sha256'],entry=profile['entry'],file=filename,
            generated_sha256=hashlib.sha256(result).hexdigest(),
            ui_branch_decisions=[dict(pc=f"0x{pc:08X}",take_original_branch=taken)
                for pc,_,taken in profile['branches']])
    receipt=dict(schema=1,attribution='djultra64',revision='iss2000-pal-en-de-rev0',
        rom_sha256=ROM_SHA256,functions=functions,
        change='Five original UI callers use existing nonmodal continuations before queuing Rumble swap notice',
        preserved=['original accessory probes and their results','Controller Pak prompts and errors',
            'Controller Pak filesystem and saves','game inputs','original unrelated UI branches'],
        no_game_execution=True)
    files['receipt.json']=(json.dumps(receipt,indent=2)+'\n').encode()
    if output.is_symlink() or any(p.is_symlink() for p in output.absolute().parents):
        raise ValueError('PAL Rumble UI output paths must not contain symlinks')
    if output.exists():
        if not output.is_dir() or set(p.name for p in output.iterdir())!=set(files):
            raise ValueError('Refusing to alter existing PAL Rumble UI derivatives')
        if any((output/name).is_symlink() or not (output/name).is_file() or
               (output/name).read_bytes()!=data for name,data in files.items()):
            raise ValueError('Refusing to alter existing PAL Rumble UI derivatives')
        return receipt
    output.mkdir(parents=True,exist_ok=False)
    for name,data in files.items():
        with (output/name).open('xb') as target:target.write(data)
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',required=True,type=Path)
    parser.add_argument('--generated',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    print(json.dumps(prepare(args.rom,args.generated,args.output),indent=2))
if __name__=='__main__':main()
