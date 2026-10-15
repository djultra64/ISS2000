"""Generate original boot code using the pinned N64Recomp tool.

No guest instruction is patched. This generator does not produce a complete game.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from tools.rom import ROOT, validate
from tools.build_tool import source_identity, verify_receipt

VRAM = 0x80000400
ROM_START = 0x1000


def validate_functions(functions: list[dict], section_size: int) -> None:
    if section_size <= 0 or section_size % 4:
        raise ValueError('Section size must be positive and word-aligned')
    previous_end = VRAM
    names = set()
    for function in sorted(functions, key=lambda f: f['vram']):
        start, size, name = function['vram'], function['size'], function['name']
        if not re.fullmatch(r'[A-Za-z_]\w*', name, flags=re.ASCII) or name in names:
            raise ValueError('Function name is invalid or duplicated')
        if start % 4 or size <= 0 or size % 4:
            raise ValueError('Function range must be positive and aligned')
        if start < previous_end or start+size > VRAM+section_size:
            raise ValueError('Function range overlaps or is outside section')
        previous_end = start+size
        names.add(name)


def render_symbols(functions: list[dict], section_size: int) -> str:
    validate_functions(functions, section_size)
    lines = ['[[section]]', 'name = "boot"', 'rom = 0x1000',
             'vram = 0x80000400', f'size = 0x{section_size:X}', 'functions = [']
    for f in sorted(functions, key=lambda f: f['vram']):
        lines.append(f'  {{ name = "{f["name"]}", vram = 0x{f["vram"]:X}, size = 0x{f["size"]:X} }},')
    return '\n'.join(lines+[']', ''])


def verify_tool(tool: Path, source: Path) -> dict:
    commit = source_identity(source)
    return verify_receipt(tool, source, commit)


def generate(rom: Path, output: Path, tool: Path, source: Path) -> dict:
    # All validation precedes artifact creation or subprocess invocation.
    data = rom.read_bytes()
    revision = validate(data)
    if data[:4] != bytes.fromhex('80371240'):
        raise ValueError('Recompilation requires the imported canonical big-endian image')
    definition = json.loads((ROOT/'config/recomp/boot.json').read_text())
    symbols = render_symbols(definition['functions'], definition['size'])
    if ROM_START+definition['size'] > len(data):
        raise ValueError('Section exceeds ROM')
    output = output.absolute()
    private = (ROOT/'.local').resolve()
    if (not output.resolve().is_relative_to(private) or output.resolve() == private or
            rom.resolve().is_relative_to(output.resolve()) or
            source.resolve().is_relative_to(output.resolve()) or
            output.resolve().is_relative_to(source.resolve())):
        raise ValueError('Output must be a new private directory disjoint from input/tool sources')
    if any(p.is_symlink() for p in (output, *output.parents)):
        raise ValueError('Output path must not contain symlinks')
    tool_identity = verify_tool(tool, source)
    output.mkdir(parents=True, exist_ok=False)
    (output/'symbols.toml').write_text(symbols)
    config = '[input]\n'+'\n'.join([
        'symbols_file_path = "symbols.toml"',
        'rom_file_path = '+json.dumps(str(rom.resolve())),
        'output_func_path = "functions"',
        'functions_per_output_file = 30', 'uses_mips3_float_mode = false', ''])
    (output/'recomp.toml').write_text(config)
    result = subprocess.run([str(tool.resolve()), str(output/'recomp.toml')],
                            text=True, capture_output=True, timeout=120)
    (output/'invocation.json').write_text(json.dumps({'returncode': result.returncode,
          'stdout': result.stdout, 'stderr': result.stderr}, indent=2)+'\n')
    if result.returncode:
        raise ValueError('N64Recomp failed: '+result.stderr[-3000:]+result.stdout[-3000:])
    files = {str(p.relative_to(output/'functions')): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted((output/'functions').glob('*')) if p.is_file()}
    if not any(name.endswith('.c') for name in files):
        raise ValueError('Recompiler did not produce C source')
    receipt = {'schema_version': 1, 'purpose': 'original entry and buffer-profile diagnostics only',
               'rom_sha256': revision['sha256'], 'tool': tool_identity,
               'symbols_sha256': hashlib.sha256(symbols.encode()).hexdigest(),
               'generated_files': files}
    (output/'receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--recompiler', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(generate(args.rom, args.output, args.recompiler, args.source), indent=2))
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(f'Recompile error: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
