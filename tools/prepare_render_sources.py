"""Prepare private, receipted local-aspect edits to reviewed original CPU sources.

Original inputs stay unchanged. Original project work: djultra64.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
from tools.rom import load_manifest


def transform(data:bytes,pc:int,register:int,expected_sha256:str)->bytes:
    if hashlib.sha256(data).hexdigest()!=expected_sha256:
        raise ValueError('Original render source digest mismatch')
    if register<0 or register>31 or pc%4:
        raise ValueError('Invalid reviewed aspect-load register/PC')
    text=data.decode()
    pattern=rf'(?m)^([ \t]*)// 0x{pc:08X}: lwc1[ \t]+\$f{register},[^\n]*\n([ \t]*ctx->f{register}\.u32l = MEM_W\([^\n]+;\n)'
    hits=list(re.finditer(pattern,text))
    if len(hits)!=1:raise ValueError('Reviewed original aspect-load instruction is not unique')
    match=hits[0]
    injected=f'    ctx->f{register}.fl = iss2000_marker_aspect(ctx->f{register}.fl);\n'
    text=text[:match.end()]+injected+text[match.end():]
    return ('extern float iss2000_marker_aspect(float);\n'+text).encode()


def prepare(generated:Path,manifest_path:Path,output:Path)->dict:
    manifest=json.loads(manifest_path.read_text())
    identity=load_manifest(manifest['revision_id'])
    summary=json.loads((generated.parent/'summary.json').read_text())
    if summary['rom_sha256']!=identity['sha256'] or manifest['rom_sha256']!=identity['sha256']:
        raise ValueError('Render patch revision does not match original code map')
    files={};sources={}
    for item in manifest['patches']:
        filename=item['source']
        if Path(filename).name!=filename or not filename.endswith('.c') or filename in files:
            raise ValueError('Invalid or duplicate render patch source')
        data=(generated/filename).read_bytes()
        digest=item['source_sha256']
        if summary['generated_files'].get('functions/'+filename)!=digest:
            raise ValueError('Reviewed source digest disagrees with generation receipt')
        files[filename]=transform(data,int(item['instruction_pc'],0),item['float_register'],digest)
        sources[filename]=digest
    receipt=dict(revision_id=manifest['revision_id'],rom_sha256=identity['sha256'],
        manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        original_sources=sources,generated_files={name:hashlib.sha256(data).hexdigest() for name,data in files.items()})
    files['receipt.json']=(json.dumps(receipt,indent=2)+'\n').encode()
    if output.exists():
        if output.is_symlink() or any(not(output/name).is_file() or (output/name).is_symlink() or (output/name).read_bytes()!=data for name,data in files.items()):
            raise ValueError('Refusing to change existing private render adaptation output')
        return receipt
    if any(parent.is_symlink() for parent in output.absolute().parents):
        raise ValueError('Render output parents must not contain symlinks')
    output.mkdir(parents=True,exist_ok=False)
    for filename,data in files.items():
        with (output/filename).open('xb') as target:target.write(data)
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generated',type=Path,required=True)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(prepare(args.generated,args.manifest,args.output),indent=2))
if __name__=='__main__':main()
