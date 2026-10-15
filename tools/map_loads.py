"""Conservative local constant analysis for ISS2000 CPU DMA load research.

Transfers identify initialized bytes, not executable text or runtime reachability.
Original instruction evidence and all ROM-derived output belong under .local/.
"""
import struct

DMA = 0x80003964


def _step(word, registers):
    op, rs, rt, rd = word >> 26, word >> 21 & 31, word >> 16 & 31, word >> 11 & 31
    imm = word & 0xFFFF
    signed = imm if imm < 0x8000 else imm - 0x10000
    value = None
    destination = None
    if op == 15:
        destination, value = rt, imm << 16
    elif op in (8, 9, 12, 13, 14):
        destination = rt
        if rs in registers:
            source = registers[rs]
            value = {8: lambda: source + signed, 9: lambda: source + signed,
                     12: lambda: source & imm, 13: lambda: source | imm,
                     14: lambda: source ^ imm}[op]()
    elif op == 0:
        fn = word & 63
        if fn in (0, 2, 3):
            destination = rd
            if rt in registers:
                source, shift = registers[rt], word >> 6 & 31
                value = source << shift if fn == 0 else source >> shift
                if fn == 3 and source & 0x80000000:
                    value = (source - 0x100000000) >> shift
        elif fn in (32, 33, 34, 35, 36, 37, 38, 45):
            destination = rd
            if rs in registers and rt in registers:
                a, b = registers[rs], registers[rt]
                value = {32: lambda: a+b, 33: lambda: a+b, 34: lambda: a-b,
                         35: lambda: a-b, 36: lambda: a&b, 37: lambda: a|b,
                         38: lambda: a^b, 45: lambda: a+b}[fn]()
        elif fn not in (8, 12, 13, 15, 17, 19, 24, 25, 26, 27):
            destination = rd
    elif op in (16, 17):
        if rs in (0, 1, 2):
            destination = rt
    elif op in (10, 11, 24, 25, 26, 27, 32, 33, 34, 35, 36, 37, 38, 39, 48, 52, 55):
        destination = rt
    if destination:
        if value is None:
            registers.pop(destination, None)
        else:
            registers[destination] = value & 0xFFFFFFFF
    registers[0] = 0


def constant_calls(image, rom_start, size, vram, target):
    """Recover constant args at direct calls; stop propagation across branches.

    The call delay slot executes before arguments are observed. Ordinary calls
    invalidate volatile ABI registers, and unknown writes invalidate constants.
    This intentionally misses computed/indirect loads instead of guessing.
    """
    if (rom_start < 0 or size < 0 or rom_start % 4 or size % 4 or
            rom_start + size > len(image) or vram % 4):
        raise ValueError('Scan bounds must be aligned and inside the image')
    words = struct.unpack_from('>'+str(size//4)+'I', image, rom_start)
    registers, calls = {0: 0}, []
    i = 0
    while i < len(words):
        word = words[i]
        op, fn = word >> 26, word & 63
        transfer = op in (1, 2, 3, 4, 5, 6, 7, 20, 21, 22, 23) or (op == 0 and fn in (8, 9))
        if transfer:
            if i+1 >= len(words):
                break
            _step(words[i+1], registers)
            if op == 3:
                address = ((vram+4*i+4) & 0xF0000000) | ((word & 0x3FFFFFF) << 2)
                if address == target:
                    calls.append({'callsite': vram+4*i,
                                  'args': [registers.get(x) for x in (4, 5, 6, 7)]})
                for r in (*range(1, 16), 24, 25, 31):
                    registers.pop(r, None)
            else:
                registers = {0: 0}
            i += 2
        else:
            _step(word, registers)
            i += 1
    return calls


def constant_transfers(image, rom_start, size, vram):
    """Return separately identified raw transfers to guest RDRAM."""
    transfers = []
    for call in constant_calls(image, rom_start, size, vram, DMA):
        rom, ram, count, _ = call['args']
        if (rom is not None and ram is not None and count is not None and
                0x80000000 <= ram < 0x80800000 and 0 < count <= 0x800000 and
                ram+count <= 0x80800000):
            transfers.append({'rom': rom, 'vram': ram, 'load_size': count,
                              'callsite': call['callsite']})
    # 8005568C divides [a0,a1) into aligned chunks and advances ROM/RAM
    # together; its final DMA copies the exact remaining bytes.
    for call in constant_calls(image, rom_start, size, vram, 0x8005568C):
        start, end, ram, chunks = call['args']
        if (all(x is not None for x in (start,end,ram,chunks)) and
                0 < chunks and start < end and
                0x80000000 <= ram < ram+end-start <= 0x80800000):
            transfers.append({'rom':start,'vram':ram,'load_size':end-start,
                              'callsite':call['callsite'],'transfer_kind':'chunked-dma'})
    transfers.sort(key=lambda x:x['callsite'])
    return transfers


def candidate_text_size(image, rom, size):
    """Provisional endpoint only: final jr ra, delay slot and 16-byte padding.

    This heuristic needs instruction/data transition review. It cannot prove
    absence of executable islands or tail-only functions after the final return.
    """
    last = None
    for offset in range(rom, rom+size-4, 4):
        if struct.unpack_from('>I', image, offset)[0] == 0x03E00008:
            last = offset
    if last is None:
        return None
    end = min((last+8+15) & ~15, rom+size)
    return end-rom


def recover_map(image, initial):
    """Follow locally proven constant DMA calls, preserving reused addresses.

    Neither successful translation nor matching range membership is a boot
    verification. Every discovered text endpoint remains explicitly provisional.
    """
    sections = [dict(x) for x in initial]
    identities = {(x['rom'], x['vram'], x['load_size']): x for x in sections}
    cursor = 0
    while cursor < len(sections):
        parent = sections[cursor]
        cursor += 1
        size = parent.get('text_size')
        if size is None:
            continue
        transfers = constant_transfers(image, parent['rom'], size, parent['vram'])
        for transfer in transfers:
            rom, ram, count = transfer['rom'], transfer['vram'], transfer['load_size']
            if rom % 4 or count % 4 or rom+count > len(image):
                continue
            identity = rom, ram, count
            call = transfer['callsite']
            call_rom = parent['rom']+call-parent['vram']
            # Restrict the following-clear probe to the enclosing local return.
            stop = min(call_rom+8+0x80, parent['rom']+size)
            for offset in range(call_rom+8, stop, 4):
                if struct.unpack_from('>I', image, offset)[0] == 0x03E00008:
                    stop = min(stop, offset+8)
                    break
            clear_calls = constant_calls(image, call_rom+8, max(0,stop-call_rom-8),
                                         call+8, 0x8005C5A0)
            bss_end = None
            for clear in clear_calls:
                start, length = clear['args'][:2]
                if start == ram+count and length is not None and start+length <= 0x80800000:
                    bss_end = start+length
                    break
            if identity in identities:
                section = identities[identity]
                section.setdefault('callsites', []).append(call)
                if bss_end is not None:
                    section['bss_end'] = bss_end
                continue
            section = {'name': f'overlay_{rom:06x}_{ram:08x}', 'rom': rom,
                       'vram': ram, 'load_size': count,
                       'text_size': candidate_text_size(image, rom, count),
                       'bss_end': bss_end, 'loader': call, 'callsites': [call],
                       'loaded_by_section': parent['name'],
                       'confidence': 'constant-dma; text-boundary-provisional-final-return'}
            sections.append(section)
            identities[identity] = section
    return sections


def main():
    import argparse
    import hashlib
    import json
    from pathlib import Path
    from tools.rom import ROOT, validate
    from tools.map_main import external_calls
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        image = args.rom.read_bytes()
        validate(image)
        output = args.output.absolute()
        local = (ROOT/'.local').resolve()
        if (not output.resolve().is_relative_to(local) or output.resolve() == local or
                any(p.is_symlink() for p in (output,*output.parents)) or
                args.rom.resolve().is_relative_to(output.resolve())):
            raise ValueError('Output must be a fresh private directory disjoint from the ROM')
        initial = [{'name':'main','rom':0x1000,'vram':0x80000400,
                    'load_size':0xA0200,'text_size':0x68D80,'bss_end':0x801AFD80,
                    'loader':None,'confidence':'provisional-resident-text'}]
        sections = recover_map(image, initial)
        calls = external_calls(image, 0x69D80)
        coverage = {}
        for address, sites in calls.items():
            target = int(address,16)
            aliases = [{'section':s['name'],'rom':s['rom']+target-s['vram']}
                       for s in sections if s['text_size'] and
                       s['vram'] <= target < s['vram']+s['text_size']]
            coverage[address] = {'callsites':sites,'candidate_text_aliases':aliases}
        unresolved = {}
        for section in sections:
            if not section['text_size']:
                continue
            for target in (0x80007DE8,0x80053150):
                found = constant_calls(image,section['rom'],section['text_size'],
                                       section['vram'],target)
                if found:
                    unresolved.setdefault(section['name'],{})[f'{target:08X}'] = found
        summary = {'status':'provisional-static-load-map','runtime_boot_verified':False,
                   'rom_sha256':hashlib.sha256(image).hexdigest(),
                   'section_count':len(sections),'external_target_count':len(calls),
                   'external_targets_in_candidate_text':sum(bool(x['candidate_text_aliases']) for x in coverage.values()),
                   'limitations':['Text ends are final-return heuristics, requiring instruction/data review.',
                                  'Range membership does not resolve aliases or prove runtime load ordering.',
                                  'Indirect or decompression-derived executable loads remain unproven.',
                                  'Loader values identify DMA callsites, not necessarily function starts.']}
        output.mkdir(parents=True,exist_ok=False)
        for name,value in [('sections.json',sections),('coverage.json',coverage),
                           ('unresolved-decoder-calls.json',unresolved),('summary.json',summary)]:
            (output/name).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
        print(json.dumps(summary,indent=2))
        return 0
    except (OSError, ValueError) as exc:
        print(f'Load-map error: {exc}')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
