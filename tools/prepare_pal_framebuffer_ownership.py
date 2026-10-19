"""Keep the displayed PAL framebuffer owned until original VI retirement.

Original project work: djultra64. Original allocation order, busy flags, queue
completion and VI retirement remain unchanged. No scene whitelist or clock edits.
"""
import argparse
import hashlib
import json
from pathlib import Path
ROM_SHA256='6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf'
SOURCE_SHA256='a86e24fe6106a9ffea0c22268acc36b3c0ffc543563edef10702e6013f4d3100'
BODY_SHA256='3240546f4f3d1ec6ce6bafdc0f4cc16d7c56d131df30d114ffb80ceb39c5132f'
ENTRY='iss2000_pal_framebuffer_allocator'
def derive(source:bytes)->bytes:
    if hashlib.sha256(source).hexdigest()!=SOURCE_SHA256:raise ValueError('Pinned PAL framebuffer allocator source digest mismatch')
    text=source.decode()
    # C++ COFF drops the upstream Clang extern-inline definition when this
    # private entry has no callers in its translation unit. Keep the original
    # header intact and give only this derivative a strong, non-inline entry.
    include = '#include "recomp.h"\n'
    if text.count(include) != 1:raise ValueError('Original recomp header include is not unique')
    text = text.replace(include, include +
        '#ifdef _WIN32\n#undef RECOMP_FUNC\n'
        '#define RECOMP_FUNC __declspec(noinline)\n#endif\n')
    helper=r"""
// A three-entry completion ring uses read==write for empty. During a video
// reconfiguration the displayed buffer can be outside the new pool, leaving
// all three slots free. Keep at most two outstanding until original VI
// retirement adopts this pool; otherwise fast native completions wrap the ring.
static bool framebuffer_completion_capacity(uint8_t* rdram) {
    if(uint32_t(MEM_W(0,0xffffffff8009dea0ull))!=3u)return true;
    const auto shown=uint32_t(MEM_W(0,0xffffffff80077630ull));
    unsigned busy=0;
    for(unsigned n=0;n<3;++n){
        if(uint32_t(MEM_W(n*8,0xffffffff801a07b8ull))==shown)return true;
        busy+=MEM_W(n*8,0xffffffff801a07b4ull)!=0;
    }
    return busy<2;
}
"""
    text=text.replace(include,include+helper)
    old='RECOMP_FUNC void func_8001D480_resident('
    if text.count(old)!=1:raise ValueError('Original framebuffer allocator symbol is not unique')
    text=text.replace(old,'extern "C" RECOMP_FUNC void '+ENTRY+'(')
    entry='extern \"C\" RECOMP_FUNC void '+ENTRY+'(uint8_t* rdram, recomp_context* ctx) {'
    if text.count(entry)!=1:raise ValueError('Original allocator entry is not unique')
    text=text.replace(entry,entry+'\n    if(!framebuffer_completion_capacity(rdram)){ctx->r2=0;return;}')
    old='    // 0x8001D4AC: bne         $v0, $zero, L_8001D4BC\n    if (ctx->r2 != 0) {'
    if text.count(old)!=1:raise ValueError('Original framebuffer availability branch is not unique')
    text=text.replace(old, '    // Reconfiguration clears busy flags, including the displayed slot.\n'
        '    // Keep that slot owned until original VI retirement observes a new address.\n'
        '    if (ctx->r2 != 0 || MEM_W(ctx->r4, 4) == MEM_W(0xffffffff80077630ull, 0)) {')
    return text.encode()
def prepare(rom:Path,source:Path,output:Path)->dict:
    binary=rom.read_bytes()
    if len(binary)!=0x1000000 or hashlib.sha256(binary).hexdigest()!=ROM_SHA256:raise ValueError('Pinned PAL ROM digest mismatch')
    if hashlib.sha256(binary[0x1e080:0x1e080+80]).hexdigest()!=BODY_SHA256:raise ValueError('Pinned PAL framebuffer allocator body mismatch')
    result=derive(source.read_bytes())
    receipt=dict(schema=3,attribution='djultra64',revision='iss2000-pal-en-de-rev0',rom_sha256=ROM_SHA256,original_entry='0x8001D480',original_rom='0x1E080',original_size=80,original_body_sha256=BODY_SHA256,original_source_sha256=SOURCE_SHA256,entry=ENTRY,file='pal_framebuffer_allocator.cpp',generated_sha256=hashlib.sha256(result).hexdigest(),change='Preserve displayed ownership and reserve completion-ring capacity until VI adopts the new pool',preserved=['original first-free ordering and pool count','original busy flags and completion messages','original VI cadence and retirement','all scenes and original input/save behavior'])
    files={'pal_framebuffer_allocator.cpp':result,'receipt.json':(json.dumps(receipt,indent=2)+'\n').encode()}
    if output.is_symlink()or any(p.is_symlink()for p in output.absolute().parents):raise ValueError('framebuffer derivative output paths must not contain symlinks')
    if output.exists():
        if not output.is_dir()or set(p.name for p in output.iterdir())!=set(files)or any((output/k).is_symlink()or not(output/k).is_file()or(output/k).read_bytes()!=v for k,v in files.items()):raise ValueError('Refusing to alter existing framebuffer derivative')
        return receipt
    output.mkdir(parents=True,exist_ok=False)
    for name,data in files.items():
        with(output/name).open('xb')as target:target.write(data)
    return receipt

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--rom',required=True,type=Path);parser.add_argument('--source',required=True,type=Path);parser.add_argument('--output',required=True,type=Path);a=parser.parse_args();print(json.dumps(prepare(a.rom,a.source,a.output),indent=2))
if __name__=='__main__':main()
