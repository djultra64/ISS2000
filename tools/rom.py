"""Normalize, validate and privately import the supported ISS2000 ROM.

Usage: python3 -m tools.rom SOURCE --output .local/rom.z64
Original project work: djultra64. No ROM data is shipped with this tool.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REVISION = 'iss2000-us-rev0'
SUPPORTED_REVISIONS = ('iss2000-us-rev0', 'iss2000-pal-en-de-rev0')
MANIFEST = ROOT/'config/roms'/f'{DEFAULT_REVISION}.json'


class RomError(ValueError):
    """Input is unsupported or output would replace existing data."""


def load_manifest(revision_id: str = DEFAULT_REVISION) -> dict:
    """Select exact input identity explicitly; never infer a runtime from size/title."""
    if revision_id not in SUPPORTED_REVISIONS:
        raise RomError('Unsupported ROM profile: '+str(revision_id))
    expected = json.loads((ROOT/'config/roms'/f'{revision_id}.json').read_text())
    if expected.get('revision_id') != revision_id:
        raise RomError('ROM profile identity does not match its filename')
    return expected


def normalize(data: bytes) -> bytes:
    if len(data) < 0x1040 or len(data) % 4:
        raise RomError('ROM is truncated or not word-aligned')
    magic = data[:4]
    if magic == bytes.fromhex('80371240'):
        return data
    if magic == bytes.fromhex('37804012'):
        result = bytearray(data)
        result[0::2], result[1::2] = data[1::2], data[0::2]
        return bytes(result)
    if magic == bytes.fromhex('40123780'):
        result = bytearray(len(data))
        for index in range(4):
            result[index::4] = data[3-index::4]
        return bytes(result)
    raise RomError('Unrecognized N64 ROM byte-order magic')


def validate(data: bytes, manifest: dict | None = None) -> dict:
    expected = manifest if manifest is not None else json.loads(MANIFEST.read_text())
    canonical = normalize(data)
    digest = hashlib.sha256(canonical).hexdigest()
    if len(canonical) != expected['size'] or digest != expected['sha256']:
        raise RomError('Unsupported ROM revision or corrupted image: expected '+expected['revision_id'])
    cartridge = canonical[0x3b:0x3f].decode('ascii', errors='replace')
    if cartridge != expected['cartridge_id'] or canonical[0x3f] != expected['revision']:
        raise RomError('ROM cartridge identifier or revision does not match')
    entry = struct.unpack_from('>I', canonical, 8)[0]
    if 'entry_point' in expected and entry != expected['entry_point']:
        raise RomError('ROM entry point does not match')
    return {'schema_version': 1, 'revision_id': expected['revision_id'],
            'size': len(canonical), 'sha256': digest,
            'sha1': hashlib.sha1(canonical).hexdigest(), 'byte_order': 'big-endian',
            'cartridge_id': cartridge, 'revision': canonical[0x3f],
            'entry_point': f'0x{entry:08X}',
            'title': canonical[0x20:0x34].decode('ascii', errors='replace').rstrip()}


def cic6102_checksum(data: bytes) -> tuple[int, int]:
    if len(data) < 0x101000:
        raise RomError('ROM is too small for the CIC-6102 checksum range')
    t1 = t2 = t3 = t4 = t5 = t6 = 0xF8CA4DDC
    for (word,) in struct.iter_unpack('>I', data[0x1000:0x101000]):
        total = (t6+word) & 0xffffffff
        if total < t6:
            t4 = (t4+1) & 0xffffffff
        t6 = total
        t3 ^= word
        shift = word & 31
        rotate = ((word << shift) | (word >> (32-shift))) & 0xffffffff
        t5 = (t5+rotate) & 0xffffffff
        t2 ^= rotate if t2 > word else t6 ^ word
        t1 = (t1+(t5 ^ word)) & 0xffffffff
    return t6 ^ t4 ^ t3, t5 ^ t2 ^ t1


def audit(data: bytes, manifest: dict | None = None) -> dict:
    canonical = normalize(data)
    result = validate(canonical, manifest)
    stored = struct.unpack_from('>II', canonical, 0x10)
    computed = cic6102_checksum(canonical)
    result['checksum'] = {'algorithm': 'CIC-6102', 'stored': [f'{v:08X}' for v in stored],
                          'computed': [f'{v:08X}' for v in computed], 'match': stored == computed}
    result['bootcode_crc32'] = f'{zlib.crc32(canonical[0x40:0x1000]):08X}'
    result['microcode_markers'] = []
    for marker in [b'RSP Gfx ucode F3DEX', b'RSP Gfx ucode F3DLX.Rej']:
        start = 0
        while (offset := canonical.find(marker, start)) >= 0:
            result['microcode_markers'].append({'rom_offset': f'0x{offset:X}',
                                                'marker': marker.decode('ascii'),
                                                'status': 'static marker; active dispatch unverified'})
            start = offset+len(marker)
    return result


def read_source(source: Path, expected_size: int) -> bytes:
    try:
        if zipfile.is_zipfile(source):
            with zipfile.ZipFile(source) as archive:
                members = [i for i in archive.infolist() if not i.is_dir() and
                           Path(i.filename).suffix.lower() in ('.z64', '.v64', '.n64')]
                if len(members) != 1:
                    raise RomError('Archive must contain exactly one ROM member')
                member = members[0]
                if member.file_size != expected_size:
                    raise RomError('Archive member has unsupported decompressed size')
                with archive.open(member) as stream:
                    return stream.read(expected_size+1)
        if source.stat().st_size != expected_size:
            raise RomError('Input has unsupported size')
        with source.open('rb') as stream:
            return stream.read(expected_size+1)
    except (OSError, zipfile.BadZipFile, zlib.error, RuntimeError, NotImplementedError) as exc:
        raise RomError(f'Cannot read ROM: {exc}') from exc


def import_rom(source: Path, destination: Path, manifest: dict | None = None) -> dict:
    expected = manifest if manifest is not None else json.loads(MANIFEST.read_text())
    canonical = normalize(read_source(source, expected['size']))
    result = validate(canonical, expected)
    # Validate everything before creating the destination tree. Reject aliases,
    # existing entries (including dangling links) and symlinked parent paths.
    destination = destination.absolute()
    if any(p.is_symlink() for p in (destination, *destination.parents)):
        raise RomError('Output paths must not contain symlinks')
    if os.path.lexists(destination):
        raise RomError('Destination already exists; refusing to overwrite it')
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open('xb') as output:
            try:
                output.write(canonical)
            except BaseException:
                destination.unlink()
                raise
    except FileExistsError as exc:
        raise RomError('Destination already exists; refusing to overwrite it') from exc
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--revision', choices=SUPPORTED_REVISIONS, default=DEFAULT_REVISION)
    args = parser.parse_args()
    try:
        expected = load_manifest(args.revision)
        if args.output:
            result = import_rom(args.source, args.output, expected)
            result.update(audit(args.output.read_bytes(), expected))
        else:
            result = audit(read_source(args.source, expected['size']), expected)
        print(json.dumps(result, indent=2, sort_keys=True))
    except (RomError, OSError) as exc:
        print(f'ROM error: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
