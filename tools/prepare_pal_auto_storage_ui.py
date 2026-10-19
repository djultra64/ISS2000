"""Prepare silent PAL startup using the genuine save/create workers.

Original project work: djultra64. Actual original storage status and errors remain authoritative.
"""
import argparse
import hashlib
import json
from pathlib import Path
ROM_SHA256='6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf'
SOURCE_SHA256='01ea25bcc1eb2a04e20841538a7ede03375d104290178349de85c8b3381c792f'
BODY_SHA256='3446154b49d6f214d28c974d2def591239cd946ad6bec9b92d863336beffb617'
ORIGINAL='func_802B1CC8_overlay_481680_802b1070'
ENTRY='iss2000_pal_automatic_storage_ui'
UPDATE_ORIGINAL='func_802B1D84_overlay_481680_802b1070'
UPDATE_ENTRY='iss2000_pal_automatic_storage_update'
UPDATE_SOURCE_SHA256='466871b69202f51628b5c6de8df82be3abe8ff8c0c90a5b80254e0b0db4dacbe'
UPDATE_BODY_SHA256='c68ff24f903e47ed3ac8a8f859a26de20471bed7e8f545a31d1a999c18212834'

# Only the insertion state invokes the same genuine probe used by the original
# A handler at 802B2BD4. Copying context preserves every register at the added
# boundary; the callee owns its normal guest stack scratch. No input is created.
# 1FDC initializes flags5, while original803CAAF0 can set active bit4 alone.
# Bit0 controls a separate background phase. Closed flags0 must stay closed.
CONTINUE_INSERTION='''
    if ((MEM_BU(0, 0xFFFFFFFF8012E167ull) & 0xFEu) == 4 && MEM_BU(0, 0xFFFFFFFF802B4819ull) == 15) {
        auto storage_context = *ctx;
        LOOKUP_FUNC(0x802B2144)(rdram, &storage_context);
    }
'''

def derive_update(source:bytes)->bytes:
    if hashlib.sha256(source).hexdigest()!=UPDATE_SOURCE_SHA256:
        raise ValueError('Pinned PAL storage callback source digest mismatch')
    text=source.decode().replace('RECOMP_FUNC void '+UPDATE_ORIGINAL+'(',
        'extern "C" RECOMP_FUNC void '+UPDATE_ENTRY+'(')
    anchor='    after_2:\n'
    if text.count(anchor)!=1:
        raise ValueError('Original input-dispatch return is not unique')
    # Yes at state3 legitimately returns to insertion15. Resolve it before the
    # frame is drawn, and handle an already-pending request without pressing A.
    text=text.replace(anchor,anchor+CONTINUE_INSERTION)
    first='    // 0x802B1D84: addiu'
    if text.count(first)!=1:raise ValueError('Original callback prologue is not unique')
    return text.replace(first,CONTINUE_INSERTION+first).encode()

def derive(source:bytes)->bytes:
    if hashlib.sha256(source).hexdigest()!=SOURCE_SHA256:
        raise ValueError('Pinned PAL automatic storage UI source digest mismatch')
    text=source.decode()
    # C++ COFF drops the upstream Clang extern-inline definition when this
    # private entry has no callers in its translation unit. Keep the original
    # header intact and give only this derivative a strong, non-inline entry.
    include = '#include "recomp.h"\n'
    if text.count(include) != 1:
        raise ValueError('Original recomp header include is not unique')
    text = text.replace(include, include +
        '#ifdef _WIN32\n#undef RECOMP_FUNC\n'
        '#define RECOMP_FUNC __declspec(noinline)\n#endif\n');old='RECOMP_FUNC void '+ORIGINAL+'('
    if text.count(old)!=1:raise ValueError('Original automatic storage UI entry is not unique')
    text=text.replace(old,'extern "C" RECOMP_FUNC void '+ENTRY+'(')
    original_branch="""    // 0x802B1D38: beq         $v1, $v0, L_802B1D58
    if (ctx->r3 == ctx->r2) {
        // 0x802B1D3C: addiu       $v0, $zero, 0xE
        ctx->r2 = ADD32(0, 0XE);
            goto L_802B1D58;
    }"""
    if text.count(original_branch)!=1:raise ValueError('Pinned insertion-only initializer branch is not unique')
    text=text.replace(original_branch,'    // Automatic storage: enter the genuine original probe instead of waiting for insertion.\n'+original_branch.replace('if (ctx->r3 == ctx->r2)','if (false)'))
    anchor='L_802B1D58:\n'
    if text.count(anchor)!=1:raise ValueError('Original startup continuation is not unique')
    # A fresh probe can itself produce insertion15. Run its original continuation
    # once more. The separately scoped startup helper owns any automatic choice;
    # this probe-only derivative never manufactures success.
    text=text.replace(anchor,anchor+CONTINUE_INSERTION)
    return text.encode()

def encode(text:str)->bytes:
    result=[]
    for c in text:
        if c==' ':result.append(0)
        elif '0'<=c<='9':result.append(ord(c)-ord('0')+1)
        elif 'A'<=c<='Z':result.append(ord(c)-ord('A')+11)
        elif 'a'<=c<='z':result.append(ord(c)-ord('a')+37)
        elif c in '.?:/,':result.append({'.':63,'?':64,':':66,'/':67,',':74}[c])
        elif c=="'":result.append(81)
        else:raise ValueError('Unsupported original PAL storage glyph')
    return bytes(result)

# Exact English whole-message extents in the original data-only overlay.
# Each line stays inside its original glyph run; all FF/control bytes survive.
WORDING={
    (0x514B56,94):['  Save game data.','If no saved data exists,','a new file will be created.'],
    (0x514BCA,45):['    Save Game?',''],
    (0x514C16,55):['  Save storage unavailable,',"game can't be saved."],
    (0x514C88,79):['Save storage is full.','Free some space before','saving game data.'],
    (0x514CD7,81):[' Save storage is full.','Free some space before','saving game data.'],
    (0x514D4C,35):['Save storage is unavailable.'],
    (0x514E6A,63):['  Save data is damaged or','storage is unavailable.'],
    (0x514ECB,85):[' There is a possibility that','saved game data may','be damaged. Repair?'],
    (0x514FA0,94):['Repair:  Repairing save data.',' There is a possibility that saved data',' may be lost.'],
}

def wording(binary:bytes)->tuple[bytes,list]:
    declarations=['#include <cstddef>\nstatic void storage_wording(uint8_t* rdram) {']
    evidence=[]
    for number,((rom,count),lines) in enumerate(WORDING.items()):
        original=binary[rom:rom+count]; changed=bytearray(original)
        if not original.endswith(b'\xff\x11'):
            raise ValueError('Storage message has no original terminator')
        start=0;line=0
        while start<count-2:
            end=original.index(b'\xff',start)
            if end>start:
                if line>=len(lines):raise ValueError('Storage wording line count mismatch')
                run=encode(lines[line]);capacity=end-start
                if len(run)>capacity:raise ValueError('Storage wording exceeds original glyph run')
                if any(x>=0xF5 for x in original[start:end]):raise ValueError('Storage wording owns a control')
                changed[start:end]=run+bytes(capacity-len(run));line+=1
            start=end+2
        if line!=len(lines):raise ValueError('Storage wording line count mismatch')
        guest=0x802DD400+rom-0x514950
        def data(x):return ','.join(str(v)for v in x)
        declarations.extend([f'    static constexpr uint8_t original_{number}[]={{'+data(original)+'};',
            f'    static constexpr uint8_t changed_{number}[]={{'+data(changed)+'};',
            f'    bool match_{number}=true;',
            f'    for (size_t n=0;n<{count};++n) match_{number} &= uint8_t(MEM_BU(n,0xFFFFFFFF{guest:X}ull))==original_{number}[n];',
            f'    if(match_{number}) for(size_t n=0;n<{count};++n) MEM_B(n,0xFFFFFFFF{guest:X}ull)=changed_{number}[n];'])
        evidence.append(dict(rom=hex(rom),guest=hex(guest),bytes=count,
            original_sha256=hashlib.sha256(original).hexdigest(),
            changed_sha256=hashlib.sha256(changed).hexdigest(),lines=lines))
    declarations.append('}\n')
    return ('\n'.join(declarations)).encode(),evidence

RENDER_ORIGINAL='func_80041A44_resident'
RENDER_ENTRY='iss2000_pal_automatic_storage_render'
RENDER_SOURCE_SHA256='9c0aa11bb6069f420e89253b645fd7f6793cd67a72ed9dc939365df13f310632'
RENDER_BODY_SHA256='377c9399ef3807b66f4a65a7ef5ec1338c95c7409a9a2e435e36fccc7e8036f1'

# A host-lifetime first-entry token identifies startup. Guest dirty/save flags
# are intentionally not treated as startup provenance. Ownership is checked at
# every added boundary, and an error permanently returns this entry to manual UI.
STARTUP_HELPERS=r'''
static bool storage_startup_seen=false, storage_startup_active=false;
static bool storage_owner(uint8_t* rdram) {
    if (uint32_t(MEM_W(0,0xFFFFFFFF8009E02Cull)) != 0x8013B418u ||
        uint32_t(MEM_W(0,0xFFFFFFFF80143D6Cull)) != 0x802B4174u) return false;
    static constexpr uint32_t resource[]={0x00100000,0x0A000000,0,0xB8000000,0x803F3358,0x05000000,0xB8000000,0x802B4770,0xB8000000,0x803F34C0,0x05000000};
    for (size_t n=0;n<sizeof(resource)/sizeof(resource[0]);++n)
        if(uint32_t(MEM_W(n*4,0xFFFFFFFF802B4174ull))!=resource[n]) return false;
    return true;
}
static void storage_startup_enter(uint8_t* rdram) {
    storage_startup_active=!storage_startup_seen && storage_owner(rdram);
    storage_startup_seen=true;
}
static bool storage_startup_owned(uint8_t* rdram) {
    if(storage_startup_active && !storage_owner(rdram)) storage_startup_active=false;
    return storage_startup_active;
}
static bool storage_startup_healthy(uint8_t* rdram) {
    if(!storage_startup_owned(rdram)) return false;
    // Original2758 labels completion2 even after a failed SDK write. Only
    // status0 is success; a real failure uses the existing unavailable dialog.
    if(MEM_BU(0,0xFFFFFFFF802B4819ull)==2 && MEM_W(0,0xFFFFFFFF800C1124ull)!=0) {
        MEM_B(0,0xFFFFFFFF802B4819ull)=3;
        storage_startup_active=false;
        return false;
    }
    switch(MEM_BU(0,0xFFFFFFFF802B4819ull)) {
        case 0:case 1:case 2:case 4:case 5:case 15:return true;
        default:storage_startup_active=false;return false;
    }
}
extern "C" bool iss2000_pal_storage_loading(uint8_t* rdram) {
    return storage_startup_healthy(rdram) && (MEM_BU(0,0xFFFFFFFF8012E167ull)&0xFEu)==4;
}
static void storage_startup_continue(uint8_t* rdram,recomp_context* ctx) {
    for(unsigned n=0;n<3 && storage_startup_healthy(rdram);++n) {
        if((MEM_BU(0,0xFFFFFFFF8012E167ull)&0xFEu)!=4) return;
        const auto state=MEM_BU(0,0xFFFFFFFF802B4819ull);
        if(state!=0 && state!=4 && state!=2) return;
        if(state!=2 && MEM_BU(0,0xFFFFFFFF802B4818ull)!=0) return;
        auto saved=*ctx;
        LOOKUP_FUNC(0x802B2868)(rdram,&saved);
        if(MEM_BU(0,0xFFFFFFFF802B4819ull)==state) return;
    }
}
// Only UI presentation delays for the first healthy automatic entry are
// shortened. Genuine callbacks, allocation, write completion and errors run.
extern "C" void iss2000_pal_storage_schedule(uint8_t* rdram,recomp_context* ctx,recomp_func_t* original) {
    const auto callback=uint32_t(ctx->r4);
    if(storage_startup_healthy(rdram) &&
       (callback==0x802B22F8u||callback==0x802B2780u||callback==0x802B27C8u||callback==0x802B2758u))
        ctx->r5=1;
    original(rdram,ctx);
}
static bool storage_startup_hide(uint8_t* rdram,uint32_t queue) {
    if(!storage_startup_healthy(rdram)) return false;
    constexpr uint32_t first=0x8013B418u+0x5060u;
    return queue>=first && queue<first+12u*0x488u && (queue-first)%0x488u==0;
}
'''

def derive_render(source:bytes)->bytes:
    if hashlib.sha256(source).hexdigest()!=RENDER_SOURCE_SHA256:
        raise ValueError('Pinned PAL UI queue render source digest mismatch')
    text=source.decode().replace('RECOMP_FUNC void '+RENDER_ORIGINAL+'(',
        'extern "C" RECOMP_FUNC void '+RENDER_ENTRY+'(')
    anchor='    uint64_t hi = 0, lo = 0, result = 0;'
    if text.count(anchor)!=1:raise ValueError('Original UI queue render prologue is not unique')
    text=text.replace(anchor,'    const bool hide_startup=storage_startup_hide(rdram,uint32_t(ctx->r4));\n'+anchor)
    for address in ['0x80041B50','0x80048660']:
        call='LOOKUP_FUNC('+address+')(rdram, ctx);'
        if text.count(call)!=1:raise ValueError('Original UI draw call is not unique')
        text=text.replace(call,'if(!hide_startup) '+call)
    return text.encode()

def prepare(rom:Path,source:Path,output:Path)->dict:
    binary=rom.read_bytes()
    if len(binary)!=0x1000000 or hashlib.sha256(binary).hexdigest()!=ROM_SHA256:
        raise ValueError('Pinned PAL ROM digest mismatch')
    if hashlib.sha256(binary[0x4822D8:0x482394]).hexdigest()!=BODY_SHA256:
        raise ValueError('Pinned PAL startup storage initializer body digest mismatch')
    callback=source.with_name(UPDATE_ORIGINAL+'.c').read_bytes()
    if hashlib.sha256(binary[0x482394:0x482484]).hexdigest()!=UPDATE_BODY_SHA256:
        raise ValueError('Pinned PAL startup storage callback body digest mismatch')
    wording_source,messages=wording(binary)
    render=source.with_name(RENDER_ORIGINAL+'.c').read_bytes()
    if hashlib.sha256(binary[0x42644:0x42750]).hexdigest()!=RENDER_BODY_SHA256:
        raise ValueError('Pinned PAL UI queue render body digest mismatch')
    result=derive(source.read_bytes())+b'\n'+derive_update(callback)
    arm=b'    after_1:\n'
    # Only the initializer contains the scene-resource load at this label.
    initializer,update=result.split(b'extern "C" RECOMP_FUNC void '+UPDATE_ENTRY.encode(),1)
    if initializer.count(arm)!=1:raise ValueError('Original resource load return is not unique')
    initializer=initializer.replace(arm,arm+b'    storage_startup_enter(rdram);\n')
    result=initializer+b'extern "C" RECOMP_FUNC void '+UPDATE_ENTRY.encode()+update
    result=result.replace(CONTINUE_INSERTION.encode(),(CONTINUE_INSERTION+'    storage_startup_continue(rdram,ctx);\n').encode())
    result+=b'\n'+derive_render(render)
    # The original text overlay is loaded before the initializer's final callback
    # registration. Apply guarded wording on that return and each input frame.
    result=result.replace(b'    if ((MEM_BU(0, 0xFFFFFFFF8012E167ull) & 0xFEu) == 4 && MEM_BU(0, 0xFFFFFFFF802B4819ull) == 15)',
        b'    storage_wording(rdram);\n    if ((MEM_BU(0, 0xFFFFFFFF8012E167ull) & 0xFEu) == 4 && MEM_BU(0, 0xFFFFFFFF802B4819ull) == 15)')
    include=b'#include "recomp.h"\n'
    result=result.replace(include,include+wording_source+STARTUP_HELPERS.encode(),1)
    receipt=dict(schema=3,attribution='djultra64',revision='iss2000-pal-en-de-rev0',
        rom_sha256=ROM_SHA256,original_entry='0x802B1CC8',original_symbol=ORIGINAL,
        original_rom='0x4822D8',original_size=0xBC,original_body_sha256=BODY_SHA256,
        original_source_sha256=SOURCE_SHA256,entry=ENTRY,file='pal_automatic_storage_ui.cpp',
        generated_sha256=hashlib.sha256(result).hexdigest(),
        update_entry=UPDATE_ENTRY,update_original_entry='0x802B1D84',
        update_original_symbol=UPDATE_ORIGINAL,update_original_rom='0x482394',
        update_original_size=0xF0,update_source_sha256=UPDATE_SOURCE_SHA256,
        update_body_sha256=UPDATE_BODY_SHA256,wording_messages=messages,
        render_entry=RENDER_ENTRY,render_original_entry='0x80041A44',render_source_sha256=RENDER_SOURCE_SHA256,render_body_sha256=RENDER_BODY_SHA256,
        change='First genuine DataChange entry silently follows original2868 save/create and completion handlers; only its healthy sprite/font queue calls are suppressed; errors permanently restore manual UI',
        preserved=['original storage probe and SDK result interpretation','filesystem/save errors and later manual creation prompts','memory notices14/16','input state','non-insertion states in non-startup mode'],
        no_game_execution=True)
    files={'pal_automatic_storage_ui.cpp':result,'receipt.json':(json.dumps(receipt,indent=2)+'\n').encode()}
    if output.is_symlink() or any(p.is_symlink() for p in output.absolute().parents):
        raise ValueError('Automatic storage UI output paths must not contain symlinks')
    if output.exists():
        if not output.is_dir() or set(p.name for p in output.iterdir())!=set(files):
            raise ValueError('Refusing to alter existing PAL automatic storage UI derivative')
        if any((output/name).is_symlink() or not (output/name).is_file() or
               (output/name).read_bytes()!=data for name,data in files.items()):
            raise ValueError('Refusing to alter existing PAL automatic storage UI derivative')
        return receipt
    output.mkdir(parents=True,exist_ok=False)
    for name,data in files.items():
        with (output/name).open('xb') as target:target.write(data)
    return receipt

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',required=True,type=Path)
    parser.add_argument('--source',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    print(json.dumps(prepare(args.rom,args.source,args.output),indent=2))
if __name__=='__main__':main()
