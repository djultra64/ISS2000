"""Emit private native registration and reviewed service wrappers for ISS2000.

Original project work: djultra64. Requires an exact reviewed ROM and fresh output.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
from tools.identify_runtime import DEFAULT_MANIFEST, verify_bindings


def identifier(value):
    if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*',value):
        raise ValueError('Unsafe C identifier')
    return value


def render_sources(sections: list[dict], bindings: list[dict]) -> tuple[str,str]:
    reviewed={int(b['address'],0):b for b in bindings}
    if len(reviewed)!=len(bindings):raise ValueError('Duplicate reviewed binding address')
    for address,binding in reviewed.items():
        identifier(binding['name']);identifier(binding['runtime_symbol'])
        if binding.get('status')!='verified-instructions-and-abi' or binding['runtime_symbol']!=binding['name']+'_recomp':
            raise ValueError('Invalid reviewed binding')
        if address<0x80000000 or address>=0x80800000 or address%4:
            raise ValueError('Invalid reviewed binding address')
    reviewed_origins=set()
    selected=[]; names=set(); section_names=set(); wrappers=[]; entry=None
    for section in sections:
        section_name=identifier(section['name'])
        if section_name in section_names:raise ValueError('Duplicate section identity')
        section_names.add(section_name)
        rom,ram,size,text=(section[k] for k in ['rom','vram','load_size','text_size'])
        if not all(type(v) is int for v in [rom,ram,size]) or size<=0 or rom<0 or rom+size>0x1000000 or ram<0x80000000 or ram+size>0x80800000:
            raise ValueError('Invalid section bounds')
        functions=section['functions']
        if text is None:
            if functions:raise ValueError('Functions require established text bounds')
            continue
        if type(text) is not int or text<=0 or text>size or rom%4 or ram%4 or text%4:
            raise ValueError('Invalid section text bounds')
        entries=[]; offsets=set()
        for function in functions:
            name=identifier(function['name']);address=function['vram'];length=function['size']
            if name in names:raise ValueError('Duplicate function identity')
            names.add(name)
            if not all(type(v) is int for v in [address,length]) or address%4 or length<=0 or length%4 or address<ram or address+length>ram+text:
                raise ValueError('Invalid function bounds')
            if address in offsets:raise ValueError('Duplicate target within section')
            offsets.add(address)
            reviewed_binding=reviewed.get(address)
            if reviewed_binding and int(reviewed_binding['rom_offset'],0)==rom+address-ram and reviewed_binding['size']==length:
                reviewed_origins.add(address)
            symbol=function.get('runtime_symbol')
            if symbol:
                identifier(symbol)
                binding=reviewed.get(address)
                if (binding is None or binding.get('status')!='verified-instructions-and-abi' or
                    binding['runtime_symbol']!=symbol or int(binding['rom_offset'],0)!=rom+address-ram or binding['size']!=length):
                    raise ValueError('Service does not match reviewed binding')
                identifier(binding['name'])
                wrappers.append((name,address,symbol,binding['name']))
            elif function['privileged']:
                continue
            entries.append((address-ram,name,length))
            if section_name=='resident' and address==0x80000400:
                entry=name
        if entries:selected.append((section_name,rom,ram,size,text,entries))
    if entry is None:raise ValueError('Verified resident entrypoint is missing')
    if set(reviewed)-reviewed_origins:raise ValueError('Reviewed binding lacks matching original function bounds/origin')
    header='// Generated privately from reviewed ISS2000 metadata. Original project work: djultra64.\n#include "runtime/native_game.hpp"\n'
    metadata=[header,'#include <librecomp/overlays.hpp>\n#include <librecomp/sections.h>\n']
    for _,_,_,_,_,entries in selected:
        for _,name,_ in entries:metadata.append(f'extern "C" void {name}(uint8_t*, recomp_context*);\n')
    metadata.append('namespace {\n')
    for i,(_,_,_,_,_,entries) in enumerate(selected):
        metadata.append(f'static FuncEntry funcs_{i}[] = {{\n')
        metadata.extend(f'    {{ &{name}, 0x{offset:08X}u, 0x{length:08X}u }},\n' for offset,name,length in entries)
        metadata.append('};\n')
    metadata.append('static SectionTableEntry sections[] = {\n')
    for i,(_,rom,ram,size,_,_) in enumerate(selected):
        metadata.append(f'    {{ 0x{rom:08X}u, 0x{ram:08X}u, 0x{size:08X}u, funcs_{i}, ARRLEN(funcs_{i}), nullptr, 0, {i} }},\n')
    metadata.append('};\n}\nnamespace iss2000 {\nvoid register_generated_sections(Registry& registry) {\n')
    for section_name,rom,ram,size,text,entries in selected:
        metadata.append(f'    registry.add({{ "{section_name}", 0x{rom:08X}u, 0x{ram:08X}u, 0x{size:08X}u, 0x{text:08X}u, {{\n')
        metadata.extend(f'        {{ 0x{offset:08X}u, &{name} }},\n' for offset,name,_ in entries)
        metadata.append('    } });\n')
    metadata.append('    recomp::overlays::register_overlays({sections, ARRLEN(sections), ARRLEN(sections)}, {nullptr, 0});\n}\n')
    metadata.append(f'recomp_func_t* generated_entrypoint() {{ return &{entry}; }}\n}}\n')
    native_bindings=[header]
    for symbol in sorted({binding['runtime_symbol'] for binding in bindings}):native_bindings.append(f'extern "C" void {symbol}(uint8_t*, recomp_context*);\n')
    for name,address,symbol,service in wrappers:
        native_bindings.append(f'extern "C" void {name}(uint8_t* rdram, recomp_context* ctx) {{\n    iss2000::call_service(0x{address:08X}u, "{service}", &{symbol}, rdram, ctx);\n}}\n')
    native_bindings.append('namespace {\n')
    for address,binding in sorted(reviewed.items()):
        symbol,service=binding['runtime_symbol'],binding['name']
        native_bindings.append(f'static void reviewed_{address:08X}(uint8_t* rdram, recomp_context* ctx) {{\n    iss2000::call_service(0x{address:08X}u, "{service}", &{symbol}, rdram, ctx);\n}}\n')
    native_bindings.append('}\nnamespace iss2000 {\nrecomp_func_t* reviewed_service(uint32_t address) {\n    switch(address) {\n')
    for address in sorted(reviewed):native_bindings.append(f'    case 0x{address:08X}u: return &reviewed_{address:08X};\n')
    native_bindings.append('    default: return nullptr;\n    }\n}\n}\n')
    return ''.join(metadata),''.join(native_bindings)


def retained_originals(sections, bindings, sources):
    """Preserve reviewed generated SDK bodies under collision-free host symbols.

    Sources are private translated CPU output, never public source or ROM bytes.
    The manifest pins both original instruction bounds and translated-source hash.
    """
    required={int(b['address'],0):b for b in bindings if b.get('preserve_source') is True}
    functions={f['name']:(section,f) for section in sections for f in section['functions']}
    found={}; chunks=[]; hashes={}
    for path in sources:
        source=Path(path).read_text()
        declarations=re.findall(r'RECOMP_FUNC void ([A-Za-z_][A-Za-z_0-9]*)\s*\(',source)
        if len(declarations)!=1 or declarations[0] not in functions:
            raise ValueError('Invalid retained original function declaration')
        name=declarations[0];section,function=functions[name];address=function['vram']
        if address not in required or address in found:
            raise ValueError('Unexpected or duplicate retained original service')
        binding=required[address]
        if int(binding['rom_offset'],0)!=section['rom']+address-section['vram'] or binding['size']!=function['size']:
            raise ValueError('Retained original bounds disagree with reviewed ROM')
        instructions={int(value,16) for value in re.findall(r'// 0x([0-9A-Fa-f]{8}):',source)}
        if instructions!=set(range(address,address+binding['size'],4)):
            raise ValueError('Retained original instruction coverage is incomplete; host wrappers are not original bodies')
        digest=hashlib.sha256(source.encode()).hexdigest()
        if digest!=binding.get('preserved_source_sha256'):
            raise ValueError('Retained original generated source digest mismatch')
        unique=f'iss2000_original_{address:08X}'
        source=re.sub(r'\b'+re.escape(name)+r'\b',unique,source)
        source=source.replace('RECOMP_FUNC void '+unique,'extern "C" void '+unique,1)
        chunks.append(source);found[address]=unique;hashes[unique]=digest
    if set(found)!=set(required):raise ValueError('Missing required retained original service source')
    header='// Private original SDK translations retained under unique symbols. Original project work: djultra64.\n'
    return header+'\n'.join(chunks),hashes


def prepare(rom_path: Path, sections_path: Path, manifest_path: Path, output: Path, retained_sources=()) -> dict:
    if output.exists():raise FileExistsError('Native metadata requires a fresh output directory')
    rom=rom_path.read_bytes();manifest=json.loads(manifest_path.read_text());bindings=verify_bindings(rom,manifest)
    sections=json.loads(sections_path.read_text())
    for section in sections:
        if section['rom']+section['load_size']>len(rom):raise ValueError('Section exceeds ROM file bounds')
    metadata,wrappers=render_sources(sections,bindings)
    retained,source_hashes=retained_originals(sections,bindings,retained_sources)
    output.mkdir(parents=True,exist_ok=False)
    files={'native_metadata.cpp':metadata,'native_bindings.cpp':wrappers,'native_retained.cpp':retained}
    for name,content in files.items():(output/name).write_text(content)
    receipt=dict(rom_sha256=hashlib.sha256(rom).hexdigest(),section_analysis_sha256=hashlib.sha256(sections_path.read_bytes()).hexdigest(),runtime_manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),generated_files={name:hashlib.sha256(content.encode()).hexdigest() for name,content in files.items()},registered_sections=metadata.count('registry.add('),bound_services=len(bindings),reviewed_service_overrides=len(bindings))
    receipt['retained_original_services']=len(source_hashes)
    receipt['retained_source_sha256']=source_hashes
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--sections',type=Path,required=True)
    parser.add_argument('--runtime-symbols',type=Path,default=DEFAULT_MANIFEST)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--retained-source',type=Path,action='append',default=[],help='Private original generated CPU source required by preserve_source bindings')
    args=parser.parse_args()
    print(json.dumps(prepare(args.rom,args.sections,args.runtime_symbols,args.output,args.retained_source),indent=2))


if __name__=='__main__':main()
