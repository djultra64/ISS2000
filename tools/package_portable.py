"""Package an explicit executable and explicit shared libraries into a fresh folder.

This copies build artifacts only. It does not build or test a game, discover
libraries, search for ROMs, or collect assets and captures from the workspace.
Original project work: djultra64.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shlex
import shutil
import stat
import sys


def _file(path):
    path=Path(path).absolute()
    if not path.is_file():
        raise ValueError(f'Input must be an existing regular file: {path}')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9 ._()+-]*',path.name):
        raise ValueError(f'Unsupported portable filename: {path.name}')
    return path


def _windows_name(name):
    if name.endswith((' ', '.')) or re.fullmatch(
            r'(?:con|prn|aux|nul|com[1-9]|lpt[1-9])',
            name.split('.')[0].rstrip(' .'), re.IGNORECASE):
        raise ValueError('Filename must be portable on Windows: '+name)


ROOT=Path(__file__).resolve().parents[1]
REVISIONS=('iss2000-pal-en-de-rev0','iss2000-us-rev0')


def _build_identity(revision, executable, release, build_dir):
    if revision not in REVISIONS:
        raise ValueError('Unsupported package ROM revision')
    profile=json.loads((ROOT/'config/roms'/f'{revision}.json').read_text())
    identity={key:profile[key] for key in ('revision_id','sha256','size','cartridge_id')}
    identity['language']='en'
    build={'kind':'production-prepared' if release else 'development',
           'input_testing':None,'runtime_acceptance':'not established by packaging'}
    if release:
        if build_dir is None:
            raise ValueError('Release preparation requires the matching build directory')
        build_dir=Path(build_dir).resolve()
        cache=build_dir/'CMakeCache.txt'
        if cache.is_symlink() or not cache.is_file():
            raise ValueError('Release preparation requires a regular CMakeCache.txt')
        values={}
        for line in cache.read_text().splitlines():
            match=re.fullmatch(r'([A-Za-z0-9_]+):[^=]+=(.*)',line)
            if match:values[match[1]]=match[2]
        if values.get('ISS2000_ROM_REVISION')!=revision:
            raise ValueError('Build revision differs from package revision')
        if values.get('ISS2000_ENABLE_INPUT_TESTING','').upper() not in ('OFF','FALSE','NO','0'):
            raise ValueError('Release preparation requires ISS2000_ENABLE_INPUT_TESTING=OFF')
        if executable.resolve().parent not in (build_dir,build_dir/'Release',build_dir/'RelWithDebInfo'):
            raise ValueError('Executable does not belong to the selected build directory')
        if executable.stat().st_mtime_ns<cache.stat().st_mtime_ns:
            raise ValueError('Executable predates the selected build configuration; rebuild it')
        build['input_testing']=False
    return identity,build


def _write_build_info(output, platform, identity, build):
    files={}
    for path in sorted(output.rglob('*')):
        if path.is_file():
            data=path.read_bytes()
            files[path.relative_to(output).as_posix()]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
    info={'schema_version':1,'project':'ISS2000','attribution':'djultra64',
          'platform':platform,'supported_rom':identity,'build':build,'files':files}
    (output/'build-info.json').write_text(json.dumps(info,indent=2,sort_keys=True)+'\n',encoding='utf-8')


def package(platform, executable, output, libraries=(), notices=(), *,
            revision=REVISIONS[0], release=False, build_dir=None):
    """Validate first, then copy supplied files; preserve every source input.

    Notices are explicit (source, destination filename) pairs copied to licenses/.
    Dependencies may be symlinks, but package copies contain regular files under
    the supplied dependency name. Windows layouts are prepared without executing
    the supplied program. No runnable/game compatibility claim is implied.
    """
    if platform not in ('linux','windows'):
        raise ValueError('Platform must be linux or windows')
    executable=_file(executable)
    identity,build=_build_identity(revision,executable,release,build_dir)
    if platform=='windows' and executable.suffix.lower()!='.exe':
        raise ValueError('Windows executable must have an .exe filename')
    libraries=[_file(path) for path in libraries]
    if release:
        for path in [executable,*libraries]:
            data=path.read_bytes()
            if re.search(rb'(?:/var)?/home/[A-Za-z0-9_.-]+/|/Users/[A-Za-z0-9_.-]+/|[A-Za-z]:\\Users\\',data):
                raise ValueError('Embedded developer home path in release input: '+path.name)
    if platform=='windows':
        for path in [executable,*libraries]:_windows_name(path.name)
    pattern=r'[A-Za-z0-9][A-Za-z0-9_+.-]*\.so(?:\.[0-9]+)*' if platform=='linux' else r'[A-Za-z0-9][A-Za-z0-9 ._()+-]*\.dll'
    seen=set()
    for library in libraries:
        if not re.fullmatch(pattern,library.name,re.IGNORECASE if platform=='windows' else 0):
            raise ValueError(f'Only explicit {platform} shared-library filenames are allowed: {library.name}')
        key=library.name.casefold() if platform=='windows' else library.name
        if key in seen:
            raise ValueError(f'Duplicate dependency destination: {library.name}')
        seen.add(key)
    validated_notices=[]
    notice_names=set()
    for source,name in notices:
        source=_file(source)
        if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9 ._()+-]*',name):
            raise ValueError('Notice destination must be a portable filename without directories')
        _windows_name(name)
        if name.casefold() in notice_names:
            raise ValueError(f'Duplicate notice destination: {name}')
        notice_names.add(name.casefold())
        if source.stat().st_size>1024*1024:
            raise ValueError(f'Notice exceeds 1 MiB: {source}')
        try:
            contents=source.read_bytes()
            contents.decode('utf-8')
            if b'\0' in contents:raise ValueError('Notice contains binary data')
        except UnicodeError as error:
            raise ValueError(f'Notice must be UTF-8 text: {source}') from error
        validated_notices.append((source,name))
    reserved={'data','screenshots','lib','licenses','readme.txt','launch.sh','build-info.json'}
    if executable.name.casefold() in reserved:
        raise ValueError('Executable filename conflicts with portable layout')
    if platform=='windows' and executable.name.casefold() in seen:
        raise ValueError('Executable and dependency names collide')
    output=Path(output).absolute()
    if output.exists() or any(path.is_symlink() for path in (output,*output.parents)):
        raise ValueError('Output must be a fresh folder without symlinked parents')
    resolved=output.resolve()
    for source in [executable,*libraries,*[source for source,_ in validated_notices]]:
        source=source.resolve()
        if resolved.is_relative_to(source) or source.is_relative_to(resolved):
            raise ValueError('Output must be disjoint from every input file')
    # Existing parent is required: a failed operation must not create unrelated
    # parent directories outside the one fresh package folder owned here.
    if not output.parent.is_dir():
        raise ValueError('Output parent directory must already exist')
    output.mkdir()
    try:
        shutil.copy2(executable.resolve(),output/executable.name)
        if platform=='linux':
            app=output/executable.name
            app.chmod(app.stat().st_mode|stat.S_IXUSR|stat.S_IXGRP|stat.S_IXOTH)
            dependency_dir=output/'lib';dependency_dir.mkdir()
        else:
            dependency_dir=output
        for library in libraries:
            shutil.copy2(library.resolve(),dependency_dir/library.name)
        if validated_notices:
            notice_dir=output/'licenses';notice_dir.mkdir()
            for source,name in validated_notices:
                shutil.copy2(source.resolve(),notice_dir/name)
        (output/'data').mkdir()
        (output/'screenshots').mkdir()
        if platform=='linux':
            launcher=output/'launch.sh'
            launcher.write_text('#!/bin/sh\nset -eu\n'
                'BASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\n'
                'export LD_LIBRARY_PATH="$BASE/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"\n'
                'cd -- "$BASE"\n'
                'exec "$BASE"/'+shlex.quote(executable.name)+' "$@" >>"$BASE/data/runtime.log" 2>&1\n')
            launcher.chmod(0o755)
        launch='Run ./launch.sh' if platform=='linux' else 'Run '+executable.name
        (output/'README.txt').write_text('ISS2000 portable folder\n\n'+launch+'.\n'
            'Original project work: djultra64.\n'
            'Source and releases: https://github.com/djultra64/ISS2000\n'
            f'Supported ROM: {identity["revision_id"]} (English).\n'
            f'Canonical SHA-256: {identity["sha256"]}\n'
            'The application prompts for your supported ROM on first launch.\n'
            'Keep portable settings and saves in data/ beside the executable.\n'
            'On Linux, launch.sh appends execution details to data/runtime.log for troubleshooting.\n'
            'Open Option, then PC Settings, for graphics, presentation and controllers.\n'
            'Original game Resolution is fixed at High; PC render resolution is separate.\n'
            'Filtering selects 2D Original or 2D Bilinear; Original is the default.\n'
            'screenshots/ is reserved for captures made after launch.\n\n'
            'Independent fan project, not affiliated with Konami or Nintendo.\n'
            'Original project code: GPL-3.0-or-later; dependencies retain their licenses.\n'
            'Original game and trademark rights are not granted by that license.\n'
            'See licenses/ and the public source repository for complete notices.\n'
            'Created with OpenAI Codex assistance under the direction of djultra64.\n\n'
            'No ROM, game assets, saves, source code or research captures are included.\n'
            'Only the supplied executable, explicitly selected libraries and text notices were copied.\n'
            'Packaging does not establish that this build boots or is playable.\n')
        _write_build_info(output,platform,identity,build)
    except BaseException:
        shutil.rmtree(output)
        raise
    return output


def _notice_argument(value):
    source,separator,name=value.rpartition('=')
    if not separator or not source or not name:
        raise argparse.ArgumentTypeError('Notice must be SOURCE=DESTINATION_FILENAME')
    return Path(source),name


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--platform',choices=['linux','windows'],required=True)
    parser.add_argument('--executable',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--library',type=Path,action='append',default=[])
    parser.add_argument('--revision',choices=REVISIONS,default=REVISIONS[0])
    parser.add_argument('--release',action='store_true',help='Require a completed matching build with the input fixture disabled')
    parser.add_argument('--build-dir',type=Path,help='Matching CMake build directory required by --release')
    parser.add_argument('--notice',type=_notice_argument,action='append',default=[],metavar='SOURCE=DESTINATION_FILENAME')
    args=parser.parse_args()
    try:
        result=package(args.platform,args.executable,args.output,args.library,args.notice,
                       revision=args.revision,release=args.release,build_dir=args.build_dir)
    except (OSError,ValueError) as error:
        print(f'Portable packaging error: {error}',file=sys.stderr)
        return 1
    print(f'Portable {args.platform} layout created: {result}')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
