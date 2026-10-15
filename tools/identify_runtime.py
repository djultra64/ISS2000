"""Verify reviewed ISS2000 runtime-service bindings against their exact ROM bodies.

This does not infer symbols from another game or automatically approve candidates.
Original project work: djultra64.
"""
import argparse
import hashlib
import json
from pathlib import Path

DEFAULT_MANIFEST = Path(__file__).resolve().parents[1] / 'config/recomp/runtime-symbols.json'


def verify_bindings(rom: bytes, manifest: dict) -> list[dict]:
    if manifest.get('schema_version') != 1:
        raise ValueError('Unsupported runtime binding schema')
    if hashlib.sha256(rom).hexdigest() != manifest['rom_sha256']:
        raise ValueError('ROM digest does not match reviewed runtime bindings')
    addresses = set()
    names = set()
    for binding in manifest['bindings']:
        address = int(binding['address'], 0)
        if address in addresses or binding['name'] in names:
            raise ValueError('Duplicate runtime binding address or name')
        addresses.add(address)
        names.add(binding['name'])
        if binding.get('status') != 'verified-instructions-and-abi' or not binding.get('evidence'):
            raise ValueError('Unverified runtime binding')
        offset, size = int(binding['rom_offset'], 0), binding['size']
        if offset < 0 or size <= 0 or offset % 4 or size % 4 or offset + size > len(rom) or address % 4:
            raise ValueError('Runtime binding bounds/alignment invalid')
        if binding['runtime_symbol'] != binding['name'] + '_recomp':
            raise ValueError('Runtime binding symbol disagrees with reviewed name')
        if hashlib.sha256(rom[offset:offset + size]).hexdigest() != binding['sha256']:
            raise ValueError('Runtime binding body digest mismatch: ' + binding['name'])
    return manifest['bindings']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    bindings = verify_bindings(args.rom.read_bytes(), json.loads(args.manifest.read_text()))
    print(json.dumps(dict(verified_count=len(bindings), bindings=bindings), indent=2))


if __name__ == '__main__':
    main()
