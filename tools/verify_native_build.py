"""Check all original native build inputs against their reviewed receipts.

Read-only; does not execute guest code. Original project work: djultra64.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

ROOT = Path(__file__).resolve().parents[1]
REVISIONS = {'iss2000-us-rev0', 'iss2000-pal-en-de-rev0'}
METADATA_FILES = {'native_metadata.cpp', 'native_bindings.cpp', 'native_retained.cpp'}


def file_digest(path: Path, label: str) -> str:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f'Missing or symlinked {label}: {path.name}')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict:
    file_digest(path, 'receipt/profile')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate receipt/profile key')
            result[key] = value
        return result
    result = json.loads(path.read_text(), object_pairs_hook=unique)
    if not isinstance(result, dict):
        raise ValueError('Receipt/profile must be an object')
    return result


def check_digest(path: Path, expected: str, label: str) -> str:
    if not isinstance(expected, str) or not re.fullmatch('[0-9a-f]{64}', expected):
        raise ValueError(f'Invalid {label} digest')
    actual = file_digest(path, label)
    if actual != expected:
        raise ValueError(f'Changed {label}: {path.name}')
    return actual


def verify(revision: str, generated: Path, metadata: Path, runtime_symbols: Path,
           audio: Path, *, root: Path = ROOT) -> dict:
    if revision not in REVISIONS:
        raise ValueError('Unsupported native ROM revision')
    generated, metadata, runtime_symbols, audio = map(Path, (generated, metadata, runtime_symbols, audio))
    profile = read_json(root / 'config/roms' / f'{revision}.json')
    if profile.get('revision_id') != revision:
        raise ValueError('ROM profile identity mismatch')
    rom = profile.get('sha256')
    if not isinstance(rom, str) or not re.fullmatch('[0-9a-f]{64}', rom):
        raise ValueError('Invalid ROM profile digest')
    summary_path, sections = generated.parent / 'summary.json', generated.parent / 'section-analysis.json'
    summary, receipt = read_json(summary_path), read_json(metadata / 'receipt.json')
    manifest = read_json(runtime_symbols)
    if any(item.get('rom_sha256') != rom for item in (summary, receipt, manifest)):
        raise ValueError('Native map, metadata or runtime manifest ROM identity differs from revision')
    hashes = {}
    hashes['section_analysis'] = check_digest(sections, receipt.get('section_analysis_sha256'), 'section analysis')
    hashes['runtime_manifest'] = check_digest(runtime_symbols, receipt.get('runtime_manifest_sha256'), 'runtime manifest')
    sources = summary.get('generated_files')
    if not isinstance(sources, dict) or not sources:
        raise ValueError('Missing original source inventory')
    if generated.is_symlink() or not generated.is_dir():
        raise ValueError('Invalid original source directory')
    expected_sources = set()
    source_hashes = {}
    for name, expected in sources.items():
        relative = PurePosixPath(name)
        if (relative.is_absolute() or len(relative.parts) < 2 or relative.parts[0] != 'functions'
                or any(part in ('.', '..') for part in relative.parts) or '\\' in name
                or str(relative) != name):
            raise ValueError('Unsafe original source inventory path')
        local = Path(*relative.parts[1:])
        path = generated / local
        if any(parent.is_symlink() for parent in path.parents if parent != generated.parent and generated in parent.parents):
            raise ValueError('Symlinked original source directory')
        source_hashes[str(local)] = check_digest(path, expected, 'original CPU source')
        expected_sources.add(local)
    actual_sources = {p.relative_to(generated) for p in generated.rglob('*') if p.suffix in ('.c', '.h', '.inl')}
    if actual_sources != {p for p in expected_sources if p.suffix in ('.c', '.h', '.inl')}:
        raise ValueError('Original CPU source inventory contains extra or missing inputs')
    outputs = receipt.get('generated_files')
    if not isinstance(outputs, dict) or set(outputs) != METADATA_FILES:
        raise ValueError('Unexpected native metadata source inventory')
    for name, expected in sorted(outputs.items()):
        hashes[name] = check_digest(metadata / name, expected, 'native metadata source')
    provenance_path = root / 'config/recomp/native-build-inputs.json'
    provenance = read_json(provenance_path)
    if provenance.get('schema_version') != 1:
        raise ValueError('Unsupported native input provenance schema')
    audio_proof = provenance.get('audio', {})
    if audio_proof.get('revisions', {}).get(revision, {}).get('rom_sha256') != rom:
        raise ValueError('Audio source provenance does not identify selected ROM')
    hashes['audio'] = check_digest(audio, audio_proof.get('source_sha256'), 'audio generated source')
    hashes['source_inventory'] = hashlib.sha256(json.dumps(source_hashes, sort_keys=True).encode()).hexdigest()
    hashes['summary'] = file_digest(summary_path, 'map summary')
    hashes['metadata_receipt'] = file_digest(metadata / 'receipt.json', 'metadata receipt')
    hashes['input_provenance'] = file_digest(provenance_path, 'input provenance')
    aggregate = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    return dict(revision_id=revision, rom_sha256=rom, cpu_sources=len(sources),
                metadata_sources=len(outputs), audio_sha256=hashes['audio'], inputs_sha256=aggregate)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', required=True, choices=sorted(REVISIONS))
    for name in ('generated', 'metadata', 'runtime-symbols', 'audio'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.revision, args.generated, args.metadata, args.runtime_symbols, args.audio)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, f'Native build input verification failed: {error}\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
