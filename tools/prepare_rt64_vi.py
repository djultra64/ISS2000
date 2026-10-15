"""Prepare pinned private RT64 VI identity/rate observations; never edit upstream.

Original project work: djultra64. Physical guest VI registers are preserved.
"""
import argparse,hashlib,json
from pathlib import Path
SOURCE_SHA256='9b3cf39bb15fc0c7d52085566197042f4960cc410b241e38457bb817f2501e5b'
REPLACEMENTS={
 '        uint8_t siz = fbSiz();':'        uint8_t siz = fbSiz();\n        const uint32_t hostIdentity = iss2000_resolve_vi_framebuffer(origin, width, siz);\n        if (hostIdentity != UINT32_MAX) return hostIdentity;',
 'const uint32_t FullRate = 60; // TODO: PAL support.':'const uint32_t FullRate = iss2000_vi_original_rate(top().vi.vSync);',
}
def prepare(source:Path,output:Path)->dict:
 if output.is_symlink() or any(p.is_symlink() for p in output.absolute().parents):raise ValueError('VI output paths must not contain symlinks')
 original=source.read_bytes()
 if hashlib.sha256(original).hexdigest()!=SOURCE_SHA256:raise ValueError('Pinned RT64 VI source digest mismatch')
 text=original.decode()
 for old,new in REPLACEMENTS.items():
  if text.count(old)!=1:raise ValueError('Reviewed RT64 VI boundary is not unique')
  text=text.replace(old,new)
 generated=('#include "runtime/vi_framebuffer.hpp"\n'+text).encode()
 receipt=dict(source_sha256=SOURCE_SHA256,generated_sha256=hashlib.sha256(generated).hexdigest(),behavior='Authoritative host framebuffer identity with original fallback; actual VI vSync selects50/60 base cadence. Physical VI registers/geometry remain unchanged.')
 files={'rt64_vi.cpp':generated,'receipt.json':(json.dumps(receipt,indent=2)+'\n').encode()}
 if output.exists():
  if any(not (output/n).is_file() or (output/n).is_symlink() or (output/n).read_bytes()!=raw for n,raw in files.items()):raise ValueError('Refusing to overwrite changed private RT64 VI output')
  return receipt
 output.mkdir(parents=True,exist_ok=False)
 for name,raw in files.items():
  with (output/name).open('xb') as target:target.write(raw)
 return receipt

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();print(json.dumps(prepare(args.source,args.output),indent=2))
if __name__=='__main__':main()
