"""Prepare a private PAL High COPY/POINT sprite edge sampling derivative.

Original project work: djultra64. Original CPU/ROM and sprite assets stay intact.
"""
import argparse
import hashlib
import json
from pathlib import Path
ROM_SHA256 = '6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf'
SOURCE_SHA256 = '412e14435313bdffd7c48f8b7c2a907efe2bfa6946daca49beff5876ad259e2d'
BODY_SHA256 = '62ff104079488a6d81386c421054368bde897818652c8d1365a597881342fe50'
ORIGINAL = 'func_807AA008_overlay_515890_807aa000'
ENTRY = 'iss2000_pal_high_sprite_edges'
PREFIX = r'''
// Local C++ COFF definition; the pinned upstream header remains unchanged.
#ifdef _WIN32
#undef RECOMP_FUNC
#define RECOMP_FUNC __declspec(noinline)
#endif
static bool iss2000_pal_high_edge_span(uint32_t begin) {
    return !(begin & 7u) &&
        ((begin >= 0x800D0328u && begin <= 0x800E0328u - 72u) ||
         (begin >= 0x800E0388u && begin <= 0x800F0388u - 72u));
}
static bool iss2000_pal_high_fix_edge_words(uint8_t* rdram, uint32_t begin, bool one_cycle = false) {
    if (!iss2000_pal_high_edge_span(begin) ||
        uint32_t(MEM_W(0, (gpr)(int32_t)0x8009E0C8u)) != begin + 72u) return false;
    for (uint32_t delta = 0; delta < 72; delta += 24) {
        if ((uint32_t(MEM_W(delta, (gpr)(int32_t)begin)) >> 24) != 0xE4u ||
            uint32_t(MEM_W(delta + 8, (gpr)(int32_t)begin)) != 0xE1000000u ||
            uint32_t(MEM_W(delta + 16, (gpr)(int32_t)begin)) != 0xF1000000u) return false;
    }
    const uint32_t a = MEM_W(0, (gpr)(int32_t)begin), b = MEM_W(4, (gpr)(int32_t)begin);
    const uint32_t right = MEM_W(24, (gpr)(int32_t)begin), right_top = MEM_W(28, (gpr)(int32_t)begin);
    const uint32_t bottom = MEM_W(48, (gpr)(int32_t)begin), bottom_top = MEM_W(52, (gpr)(int32_t)begin);
    const uint32_t x = (a >> 12) & 4095u, y = a & 4095u;
    if (x > 4090u || y > 4091u ||
        ((right >> 12) & 4095u) != x + 5u || (right & 4095u) != y ||
        ((right_top >> 12) & 4095u) != x + 1u || (right_top & 4095u) != (b & 4095u) ||
        ((bottom >> 12) & 4095u) != x + 1u || (bottom & 4095u) != y + 4u ||
        ((bottom_top >> 12) & 4095u) != ((b >> 12) & 4095u) || (bottom_top & 4095u) != y) return false;
    // ONE_CYCLE already covers the complete main rectangle with exclusive
    // endpoints. Its extra strips overlap adjacent chunks and double alpha.
    // Keep command count/cursor and source words; make only these strips empty.
    if (one_cycle) {
        MEM_W(24, (gpr)(int32_t)begin) = (right & 0xFF000FFFu) | (right_top & 0x00FFF000u);
        MEM_W(48, (gpr)(int32_t)begin) = (bottom & 0xFFFFF000u) | (bottom_top & 0x00000FFFu);
        return true;
    }
    // Preserve the last genuine source column/row across the whole COPY edge.
    // The original -8/32 starts a quarter texel before it; the original full
    // derivative then crosses into adjacent atlas texels when upscaled.
    MEM_W(36, (gpr)(int32_t)begin) = uint32_t(MEM_W(36, (gpr)(int32_t)begin)) + 0x00080000u;
    MEM_W(44, (gpr)(int32_t)begin) = uint32_t(MEM_W(44, (gpr)(int32_t)begin)) & 0x0000FFFFu;
    MEM_W(60, (gpr)(int32_t)begin) = (uint32_t(MEM_W(60, (gpr)(int32_t)begin)) & 0xFFFF0000u) |
        uint16_t(uint32_t(MEM_W(60, (gpr)(int32_t)begin)) + 8u);
    MEM_W(68, (gpr)(int32_t)begin) = uint32_t(MEM_W(68, (gpr)(int32_t)begin)) & 0xFFFF0000u;
    return true;
}
'''
CAPTURE = r'''
    // Original materials0 (COPY) and2 (one-cycle POINT) share this leaf.
    // Capture after the original format decode, before any emitted rectangles.
    if ((ctx->r2 == 0 || ctx->r2 == 2) && uint64_t(ctx->r15) == uint64_t(int64_t(int32_t(0x8009E0C8u))) &&
        MEM_HU(0, (gpr)(int32_t)0x800BDB26u) == uint32_t(ctx->r2) && uint32_t(MEM_W(0, (gpr)(int32_t)0x8009E02Cu)) == 0x8013B418u &&
        MEM_BU(0, (gpr)(int32_t)0x8013B42Au) == 1 && MEM_HU(0, (gpr)(int32_t)0x8013B42Cu) == 640 &&
        MEM_HU(0, (gpr)(int32_t)0x8013B42Eu) == 544) {
        iss2000_high_one_cycle = ctx->r2 == 2;
        iss2000_high_begin = uint32_t(MEM_W(0, ctx->r15));
        iss2000_high_candidate = iss2000_pal_high_edge_span(iss2000_high_begin);
    }
'''

def derive(source: bytes) -> bytes:
    if hashlib.sha256(source).hexdigest() != SOURCE_SHA256:
        raise ValueError('Pinned PAL High sprite source digest mismatch')
    text = source.decode()
    def replace(old, new):
        nonlocal text
        if text.count(old) != 1:
            raise ValueError('Original High sprite source context is not unique')
        text = text.replace(old, new)
    replace('#include "recomp.h"\n', '#include "recomp.h"\n' + PREFIX)
    replace('RECOMP_FUNC void ' + ORIGINAL + '(', 'extern "C" RECOMP_FUNC void ' + ENTRY + '(')
    replace('    uint64_t hi = 0, lo = 0, result = 0;',
            '    uint32_t iss2000_high_begin = 0;\n    bool iss2000_high_candidate = false;\n    bool iss2000_high_one_cycle = false;\n'
            '    uint64_t hi = 0, lo = 0, result = 0;')
    replace('L_807AA0FC:\n', 'L_807AA0FC:\n' + CAPTURE)
    replace('L_807AA2A0:\n', 'L_807AA2A0:\n'
            '    if (iss2000_high_candidate) iss2000_pal_high_fix_edge_words(rdram, iss2000_high_begin, iss2000_high_one_cycle);\n')
    return text.encode()

def prepare(rom: Path, source: Path, output: Path) -> dict:
    binary = rom.read_bytes()
    if len(binary) != 0x1000000 or hashlib.sha256(binary).hexdigest() != ROM_SHA256:
        raise ValueError('Pinned PAL ROM digest mismatch')
    if hashlib.sha256(binary[0x515898:0x515B4C]).hexdigest() != BODY_SHA256:
        raise ValueError('Pinned original High sprite body mismatch')
    # The exact ROM establishes original COPY material0 and original width-1
    # endpoint construction; no guest OS result or data asset is substituted.
    if binary[0x86B90:0x86B94] != bytes.fromhex('8009cb78') or binary[0x9D778:0x9D780] != bytes.fromhex('e3000a0100200000'):
        raise ValueError('Original COPY material route mismatch')
    if binary[0x86B98:0x86B9C] != bytes.fromhex('8009cc20') or binary[0x9D820:0x9D828] != bytes.fromhex('e3000a0100000000') or binary[0x9D838:0x9D840] != bytes.fromhex('e300120100000000'):
        raise ValueError('Original one-cycle POINT material2 route mismatch')
    generated = derive(source.read_bytes())
    receipt = dict(schema=1, attribution='djultra64', revision='iss2000-pal-en-de-rev0',
        rom_sha256=ROM_SHA256, original_entry='0x807AA008', original_rom='0x515898', original_size=692,
        original_body_sha256=BODY_SHA256, original_source_sha256=SOURCE_SHA256,
        entry=ENTRY, file='pal_high_sprite_edges.cpp', generated_sha256=hashlib.sha256(generated).hexdigest(),
        guard='Original mode0/COPY or mode2/POINT matching cache; canonical original Gfx head; genuine High640x544; bounded72B exact triple pattern',
        change='COPY: four last-column/row UV/derivative words; POINT2: two strip endpoint words remove duplicate alpha coverage',
        preserved=['all original CPU instructions/register context','all72B and Gfx cursor','main geometry/UV/derivatives','COPY rectangle geometry and all main geometry','material and sprite assets','format19 and unverified modes','Low frame output'])
    files = {'pal_high_sprite_edges.cpp': generated, 'receipt.json': (json.dumps(receipt, indent=2)+'\n').encode()}
    if output.is_symlink() or any(p.is_symlink() for p in output.absolute().parents):
        raise ValueError('High sprite output paths must not contain symlinks')
    if output.exists():
        if not output.is_dir() or set(p.name for p in output.iterdir()) != set(files) or any(
                (output/k).is_symlink() or not (output/k).is_file() or (output/k).read_bytes() != v for k, v in files.items()):
            raise ValueError('Refusing to alter existing High sprite derivative')
        return receipt
    output.mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        with (output/name).open('xb') as target:
            target.write(data)
    return receipt

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom', required=True, type=Path)
    p.add_argument('--source', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    print(json.dumps(prepare(a.rom, a.source, a.output), indent=2))
if __name__ == '__main__': main()
