"""Prepare the exact PAL steady-field HIGH frame pacing derivative.

Original project work: djultra64. Original ROM and generated sources stay intact.
"""
import argparse
import hashlib
import json
from pathlib import Path
ROM_SHA256='6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf'
SOURCE_SHA256='0ea1d11a153c80b2deaa2076313cb227bbba7c03a2ce09cdfd4fb5f6be3c8136'
BODY_SHA256='6fac9fbf788c9a44cc3c11713a6e087ff764fee0c777a458f749f13f31113935'
ORIGINAL='func_80000C30_resident'
ENTRY='iss2000_pal_native_frame_pace'
FILE='pal_native_frame_pace.cpp'

def derive(source:bytes)->bytes:
    if hashlib.sha256(source).hexdigest()!=SOURCE_SHA256:
        raise ValueError('Pinned PAL frame source digest mismatch')
    text=source.decode()
    include='#include "recomp.h"\n'
    if text.count(include)!=1:raise ValueError('Original recomp include is not unique')
    text=text.replace(include,include+'#ifdef _WIN32\n#undef RECOMP_FUNC\n#define RECOMP_FUNC __declspec(noinline)\n#endif\n')
    declaration='RECOMP_FUNC void '+ORIGINAL+'('
    if text.count(declaration)!=1:raise ValueError('Original frame entry is not unique')
    text=text.replace(declaration,'extern "C" RECOMP_FUNC void '+ENTRY+'(')
    helper="""static bool iss2000_steady_high_field(uint8_t* rdram) {
    return uint32_t(MEM_W(0, S32(0x8009E02C))) == 0x8013B418u &&
        MEM_BU(0, S32(0x8013B42A)) == 1 &&
        MEM_BU(0, S32(0x8013B446)) == 6 &&
        MEM_BU(0, S32(0x8013B44C)) == 4;
}
"""
    text=text.replace('extern "C" RECOMP_FUNC void '+ENTRY+'(',helper+'extern "C" RECOMP_FUNC void '+ENTRY+'(')
    local='    int c1cs = 0;\n'
    if text.count(local)!=1:raise ValueError('Original frame locals are not unique')
    text=text.replace(local,local+'    const bool iss2000_entered_steady_field = iss2000_steady_high_field(rdram);\n    bool iss2000_skip_second_field_step = false;\n')
    call="""    // 0x800010C4: jal         0x80002D90
    // 0x800010C8: nop

    LOOKUP_FUNC(0x80002D90)(rdram, ctx);"""
    if text.count(call)!=1:raise ValueError('Original duplicate stage call is not unique')
    text=text.replace(call,call.replace('    LOOKUP_FUNC(0x80002D90)(rdram, ctx);',
        '    // The native HIGH task already ran its full steady-field step at D34.\n'
        '    iss2000_skip_second_field_step = iss2000_entered_steady_field && iss2000_steady_high_field(rdram);\n'
        '    if (!iss2000_skip_second_field_step)\n'
        '        LOOKUP_FUNC(0x80002D90)(rdram, ctx);'))
    geometry='''    // 0x800010CC: jal         0x80031E74
    // 0x800010D0: nop

    LOOKUP_FUNC(0x80031E74)(rdram, ctx);'''
    if text.count(geometry)!=1:raise ValueError('Original duplicate skeletal update call is not unique')
    text=text.replace(geometry,geometry.replace('    LOOKUP_FUNC(0x80031E74)(rdram, ctx);',
        '    // 31E74 also advances skeletal phase through 300D0/2F448.\n'
        '    // Keep its admission paired with the full simulation step above.\n'
        '    if (!iss2000_skip_second_field_step)\n'
        '        LOOKUP_FUNC(0x80031E74)(rdram, ctx);'))
    return text.encode('utf-8')

def prepare(rom:Path,source:Path,output:Path)->dict:
    image=rom.read_bytes()
    if len(image)!=0x1000000 or hashlib.sha256(image).hexdigest()!=ROM_SHA256:
        raise ValueError('Pinned PAL ROM digest mismatch')
    if hashlib.sha256(image[0x1830:0x1D28]).hexdigest()!=BODY_SHA256:
        raise ValueError('Pinned PAL original frame body digest mismatch')
    result=derive(source.read_bytes())
    receipt=dict(schema=2,attribution='djultra64',revision='iss2000-pal-en-de-rev0',
        rom_sha256=ROM_SHA256,original_entry='0x80000C30',original_symbol=ORIGINAL,
        original_rom='0x1830',original_size=1272,original_body_sha256=BODY_SHA256,
        original_source_sha256=SOURCE_SHA256,entry=ENTRY,file=FILE,
        generated_sha256=hashlib.sha256(result).hexdigest(),
        changed_callsite='0x800010C4',paired_skeletal_callsite='0x800010CC',
        first_callsite_unchanged='0x80000D34',first_skeletal_callsite_unchanged='0x80000E54',
        guard='Original frame pointer 8013B418, HIGH 1 and scene 0604 at entry and second call',
        preserved=['first stage update','other scenes and transitions','input reads and SI waits',
            'first original skeletal update and pose bake','camera and replay calls','HIGH framebuffer and VI state','audio and rendering'],
        no_game_execution=True)
    files={FILE:result,'receipt.json':(json.dumps(receipt,indent=2)+'\n').encode('utf-8')}
    if output.is_symlink() or any(p.is_symlink() for p in output.absolute().parents):
        raise ValueError('PAL pace output paths must not contain symlinks')
    if output.exists():
        if not output.is_dir() or set(p.name for p in output.iterdir())!=set(files) or any(
            (output/name).is_symlink() or not (output/name).is_file() or (output/name).read_bytes()!=data
            for name,data in files.items()):
            raise ValueError('Refusing to alter existing PAL pace derivatives')
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
