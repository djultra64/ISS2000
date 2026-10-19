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
    selected=[]; names=set(); section_names=set(); wrappers=[]; entry=None; dependencies={}
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
            spans=[]
            for dependency in function.get('native_dependencies',[]):
                offset,span_size=dependency['offset'],dependency['size']
                if (type(offset) is not int or type(span_size) is not int or offset<0 or
                    offset%4 or span_size<=0 or span_size%4 or offset+span_size>size):
                    raise ValueError('Invalid native dependency bounds')
                spans.append((offset,offset+span_size))
            dependencies[name]=spans
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
        for offset,name,length in entries:
            spans=dependencies[name]
            suffix=', {'+', '.join(f'{{ 0x{begin:08X}u, 0x{end:08X}u }}' for begin,end in spans)+'}' if spans else ''
            metadata.append(f'        {{ 0x{offset:08X}u, &{name}, 0x{length:08X}u{suffix} }},\n')
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



def collect_native_dependencies(rom: bytes, sections: list[dict], generated: Path) -> dict:
    """Verify folded control-flow tables against the actual original ROM words.

    The translator replaces these loads with C switches. Runtime lookup must
    therefore require their original data ranges as well as instruction bytes.
    """
    pattern=re.compile(r'switch\s*\([^\n]+\)\s*\{(.*?)default:\s*switch_error\(__func__,\s*0x([0-9A-Fa-f]+),\s*0x([0-9A-Fa-f]+)\);\s*\}',re.S)
    tables=[];sources={};audited=0
    for section in sections:
        for function in section['functions']:
            function.pop('native_dependencies',None)
            if function.get('runtime_symbol') or function['privileged']:continue
            name=identifier(function['name']);start=function['vram'];size=function['size']
            position=section['rom']+start-section['vram']
            words=[int.from_bytes(rom[i:i+4],'big') for i in range(position,position+size,4)]
            computed_jump=any(word>>26==0 and word&63==8 and (word>>21)&31!=31 for word in words)
            path=generated/(name+'.c')
            if not path.is_file():
                if computed_jump:raise ValueError(f'Missing original computed jump source: {name}')
                continue
            source=path.read_text()
            instructions={int(value,16) for value in re.findall(r'// 0x([0-9A-Fa-f]{8}):',source)}
            if instructions!=set(range(start,start+size,4)):
                raise ValueError(f'Original instruction coverage mismatch: {name}')
            audited+=1
            matches=list(pattern.finditer(source))
            if len(matches)!=len(re.findall(r'\bswitch_error\s*\(',source)):
                raise ValueError(f'Unparsed original folded switch: {name}')
            spans=[]
            for match in matches:
                pairs=[(int(index),int(target,16)) for index,target in re.findall(r'case (\d+): goto L_([0-9A-Fa-f]+); break;',match[1])]
                # Reject syntax changes rather than silently omitting a case.
                if not pairs or len(pairs)!=len(re.findall(r'\bcase\s+',match[1])):
                    raise ValueError(f'Unparsed original folded switch cases: {name}')
                if [index for index,_ in pairs]!=list(range(len(pairs))):
                    raise ValueError(f'Original folded switch indices are not dense: {name}')
                pc,table=int(match[2],16),int(match[3],16);length=len(pairs)*4
                offset=table-section['vram']
                if (pc not in instructions or pc%4 or table%4 or offset<0 or offset+length>section['load_size']):
                    raise ValueError(f'Original folded table target range is outside section: {name}')
                jr=words[(pc-start)//4]
                if not (jr>>26==0 and jr&63==8 and (jr>>21)&31!=31):
                    raise ValueError(f'Original folded switch is not a computed jump: {name}')
                table_rom=section['rom']+offset
                for index,target in pairs:
                    original=int.from_bytes(rom[table_rom+index*4:table_rom+index*4+4],'big')
                    if original!=target or target not in instructions:
                        raise ValueError(f'Original folded table target mismatch: {name}')
                spans.append(dict(offset=offset,size=length))
                tables.append(dict(function=name,jump_pc=pc,rom=table_rom,size=length,sha256=hashlib.sha256(rom[table_rom:table_rom+length]).hexdigest()))
            if spans:
                function['native_dependencies']=spans
                sources[name]=hashlib.sha256(source.encode()).hexdigest()
    return dict(folded_jump_tables=len(tables),dependent_functions=len(sources),audited_original_functions=audited,
                folded_table_ranges=tables,dependent_source_sha256=sources)

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


def prepare(rom_path: Path, sections_path: Path, manifest_path: Path, output: Path, retained_sources=(), generated: Path | None = None) -> dict:
    if output.exists():raise FileExistsError('Native metadata requires a fresh output directory')
    rom=rom_path.read_bytes();manifest=json.loads(manifest_path.read_text());bindings=verify_bindings(rom,manifest)
    sections=json.loads(sections_path.read_text())
    for section in sections:
        if section['rom']+section['load_size']>len(rom):raise ValueError('Section exceeds ROM file bounds')
    render_sources(sections,bindings)  # Validate identifiers and bounds before opening private source paths.
    dependencies=collect_native_dependencies(rom,sections,generated or sections_path.parent/'functions')
    metadata,wrappers=render_sources(sections,bindings)
    retained,source_hashes=retained_originals(sections,bindings,retained_sources)
    output.mkdir(parents=True,exist_ok=False)
    files={'native_metadata.cpp':metadata,'native_bindings.cpp':wrappers,'native_retained.cpp':retained}
    for name,content in files.items():(output/name).write_bytes(content.encode("utf-8"))
    receipt=dict(rom_sha256=hashlib.sha256(rom).hexdigest(),section_analysis_sha256=hashlib.sha256(sections_path.read_bytes()).hexdigest(),runtime_manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),generated_files={name:hashlib.sha256(content.encode()).hexdigest() for name,content in files.items()},registered_sections=metadata.count('registry.add('),bound_services=len(bindings),reviewed_service_overrides=len(bindings))
    receipt['native_dependencies']=dependencies
    receipt['retained_original_services']=len(source_hashes)
    receipt['retained_source_sha256']=source_hashes
    (output/'receipt.json').write_bytes((json.dumps(receipt,indent=2)+'\n').encode('utf-8'))
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--sections',type=Path,required=True)
    parser.add_argument('--runtime-symbols',type=Path,default=DEFAULT_MANIFEST)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--retained-source',type=Path,action='append',default=[],help='Private original generated CPU source required by preserve_source bindings')
    parser.add_argument('--generated',type=Path,help='Original generated CPU directory; defaults to sections sibling/functions')
    args=parser.parse_args()
    print(json.dumps(prepare(args.rom,args.sections,args.runtime_symbols,args.output,args.retained_source,args.generated),indent=2))


if __name__=='__main__':main()
