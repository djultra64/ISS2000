"""Build pinned N64Recomp locally and bind the executable to a build receipt."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from tools.rom import ROOT


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_identity(source: Path) -> str:
    expected = json.loads((ROOT/'config/dependencies.json').read_text())['N64Recomp']['commit']
    commit = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    dirty = subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain', '--untracked-files=no'], text=True)
    modules = subprocess.check_output(['git', '-C', str(source), 'submodule', 'status', '--recursive'], text=True)
    if commit != expected or dirty or any(line and line[0] != ' ' for line in modules.splitlines()):
        raise ValueError('N64Recomp source/submodules do not match the clean pinned revision')
    return commit


def observed_artifacts(tool: Path, source: Path, commit: str) -> dict:
    if tool.name not in ('N64Recomp', 'N64Recomp.exe'):
        raise ValueError('Tool must be the N64Recomp executable')
    cache = tool.parent/'CMakeCache.txt'
    home = [line.split('=', 1)[1] for line in cache.read_text().splitlines()
            if line.startswith('CMAKE_HOME_DIRECTORY:INTERNAL=')]
    if len(home) != 1 or Path(home[0]).resolve() != source.resolve():
        raise ValueError('Build cache is not bound to the pinned source')
    return {'schema_version': 1, 'source_commit': commit, 'source_path': str(source.resolve()),
            'binary_sha256': digest(tool), 'cache_sha256': digest(cache),
            'graph_sha256': digest(tool.parent/'build.ninja')}


def verify_receipt(tool: Path, source: Path, commit: str) -> dict:
    try:
        receipt = json.loads((tool.parent/'iss2000-build-receipt.json').read_text())
        actual = observed_artifacts(tool, source, commit)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError('Controlled-build receipt or artifact is missing/invalid') from exc
    if receipt != actual:
        raise ValueError('Recompiler differs from its controlled-build receipt; rebuild the tool')
    return receipt


def build(source: Path, destination: Path, jobs: int) -> dict:
    source = source.resolve(strict=True)
    destination = destination.absolute()
    private = (ROOT/'.local').resolve()
    if (not destination.resolve().is_relative_to(private) or destination.resolve() == private or
            destination.resolve().is_relative_to(source) or source.is_relative_to(destination.resolve()) or
            any(p.is_symlink() for p in (destination, *destination.parents))):
        raise ValueError('Build directory must be private and disjoint from source')
    if jobs < 1:
        raise ValueError('Build jobs must be positive')
    commit = source_identity(source)
    destination.mkdir(parents=True, exist_ok=True)
    receipt_path = destination/'iss2000-build-receipt.json'
    # Invalidate any previous provenance before invoking the build.
    receipt_path.unlink(missing_ok=True)
    with (destination/'iss2000-configure.log').open('w') as log:
        subprocess.run(['cmake', '-S', str(source), '-B', str(destination), '-G', 'Ninja',
                        '-DCMAKE_BUILD_TYPE=Release'], stdout=log, stderr=subprocess.STDOUT, check=True)
    with (destination/'iss2000-build.log').open('w') as log:
        subprocess.run(['cmake', '--build', str(destination), '--target', 'N64RecompCLI', 'RSPRecomp',
                        '-j', str(jobs)], stdout=log, stderr=subprocess.STDOUT, check=True)
    if source_identity(source) != commit:
        raise ValueError('Source identity changed during build')
    tool = destination/('N64Recomp.exe' if sys.platform == 'win32' else 'N64Recomp')
    receipt = observed_artifacts(tool, source, commit)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
    return verify_receipt(tool, source, commit)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--build', type=Path, default=ROOT/'.local/toolchain')
    parser.add_argument('--jobs', type=int, default=4)
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.source, args.build, args.jobs), indent=2))
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(f'Tool build error: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
