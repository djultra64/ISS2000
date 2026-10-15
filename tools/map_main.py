"""Reproduce ISS2000-only provisional resident mapping and translation failure.

This research tool does not establish overlay maps or runnable host bindings.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

from tools.rom import ROOT, validate
from tools.recompile import render_symbols, verify_tool

TEXT_END = 0x69D80
LOAD_SIZE = 0xA0200
BASE = 0x80000400


def external_calls(data: bytes, end: int) -> dict:
    if end <= 0x1000 or end > len(data) or end % 4:
        raise ValueError('Scan end must be aligned and inside the ROM body')
    calls = collections.defaultdict(list)
    for offset in range(0x1000, end, 4):
        word = struct.unpack_from('>I', data, offset)[0]
        if word >> 26 == 3:
            target = 0x80000000 | ((word & 0x3ffffff) << 2)
            if not BASE <= target < BASE+TEXT_END-0x1000:
                calls[f'0x{target:08X}'].append(f'0x{BASE+offset-0x1000:08X}')
    return dict(sorted(calls.items()))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--spimdisasm', type=Path, required=True)
    parser.add_argument('--packages', type=Path, required=True, help='Python package directory containing Rabbitizer')
    parser.add_argument('--recompiler', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    try:
        image = args.rom.read_bytes()
        validate(image)
        identity = verify_tool(args.recompiler, args.source)
        output = args.output.absolute()
        if (not output.resolve().is_relative_to((ROOT/'.local').resolve()) or
                output.resolve() == (ROOT/'.local').resolve() or
                any(p.is_symlink() for p in (output, *output.parents)) or
                any(p.resolve().is_relative_to(output.resolve()) or output.resolve().is_relative_to(p.resolve())
                    for p in [args.rom, args.source, args.spimdisasm, args.packages, args.recompiler])):
            raise ValueError('Research output must be a fresh private directory disjoint from inputs')
        sys.path.insert(0, str(args.packages.resolve()))
        sys.path.insert(0, str(args.spimdisasm.resolve()))
        from spimdisasm import common, mips
        common.GlobalConfig.COMPILER = common.Compiler.GCC
        common.GlobalConfig.QUIET = True
        context = common.Context()
        context.changeGlobalSegmentRanges(0, len(image), 0x80000000, 0x80800000)
        for address in [BASE, 0x80000500, 0x800007B8, 0x80000814]:
            symbol = context.globalSegment.addFunction(address, vromAddress=address-BASE+0x1000)
            symbol.name = f'func_{address:08X}'
            symbol.isUserDeclared = True
        text = mips.sections.SectionText(context, 0x1000, TEXT_END, BASE, 'main', image, 0, None)
        text.analyze()
        functions, privileged = [], []
        for function in text.symbolList:
            name = f'func_{function.vram:08X}'
            for instruction in function.instructions:
                word = instruction.getRaw()
                if (word >> 26 in (16, 47) or
                        instruction.readsRs() and ((word >> 21) & 31) in (26, 27) or
                        instruction.readsRt() and ((word >> 16) & 31) in (26, 27) or
                        instruction.getDestinationGpr() in (26, 27)):
                    privileged.append(name)
                    break
            functions.append({'name': name, 'vram': function.vram, 'size': function.sizew*4})
        symbols = render_symbols(functions, LOAD_SIZE).replace('name = "boot"', 'name = "main"')
        output.mkdir(parents=True, exist_ok=False)
        (output/'symbols.toml').write_text(symbols)
        (output/'functions.json').write_text(json.dumps(functions, indent=2)+'\n')
        (output/'privileged.json').write_text(json.dumps(privileged, indent=2)+'\n')
        config = ('[input]\nsymbols_file_path = "symbols.toml"\nrom_file_path = '+
                  json.dumps(str(args.rom.resolve()))+'\noutput_func_path = "functions"\n'+
                  'functions_per_output_file = 30\nuses_mips3_float_mode = false\n'+
                  '[patches]\nignored = '+json.dumps(privileged)+'\n')
        (output/'recomp.toml').write_text(config)
        result = subprocess.run([str(args.recompiler.resolve()), str(output/'recomp.toml')],
                                capture_output=True, text=True, timeout=120)
        (output/'recompile.log').write_text(result.stdout+result.stderr)
        summary = {'status': 'provisional-resident-map', 'full_runtime_ready': False,
                   'rom_sha256': hashlib.sha256(image).hexdigest(), 'tool': identity,
                   'candidate_text_rom_end': hex(TEXT_END), 'candidate_functions': len(functions),
                   'excluded_privileged_functions': len(privileged),
                   'external_direct_calls': external_calls(image, TEXT_END),
                   'recompiler_returncode': result.returncode,
                   'recompiler_log_tail': (result.stdout+result.stderr)[-3000:]}
        (output/'summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True)+'\n')
        print(json.dumps({'candidate_functions': len(functions), 'recompiler_returncode': result.returncode,
                           'external_target_count': len(summary['external_direct_calls']),
                           'summary': str(output/'summary.json')}, indent=2))
        return result.returncode
    except (OSError, ValueError, ImportError, subprocess.SubprocessError) as exc:
        print(f'Mapping error: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
