"""ISS2000 section-aware CPU translation research; this is not a game runtime.

A DMA load extent is not an executable extent. Unknown text ranges stay in the
inventory but are not submitted to the compiler. Overlays sharing a guest PC
retain distinct section names and generated function identities.
"""
import re


def _integer(value):
    if isinstance(value, bool):
        raise ValueError('Boolean is not an address or size')
    if isinstance(value, str):
        return int(value, 0)
    if not isinstance(value, int):
        raise ValueError('Expected integer address or size')
    return value


def validate_sections(sections, rom_size):
    result, names = [], set()
    if not sections:
        raise ValueError('Section inventory is empty')
    for original in sections:
        item = dict(original)
        name = item.get('name', '')
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z_]\w*', name, re.ASCII) or name in names:
            raise ValueError('Section name must be a distinct C identifier')
        names.add(name)
        for key in ['rom', 'vram', 'load_size', 'text_size', 'bss_end', 'loader']:
            value=item.get(key)
            if value is None and key in ['text_size', 'bss_end', 'loader']:
                item[key]=None
            else:
                item[key]=_integer(value)
        rom, vram, load, text=item['rom'],item['vram'],item['load_size'],item['text_size']
        if rom < 0 or load <= 0 or rom+load > rom_size or rom % 4 or load % 4:
            raise ValueError('Invalid aligned ROM load range')
        if vram % 4 or vram < 0x80000000 or vram+load > 0x80800000:
            raise ValueError('Load must fit in 8 MiB guest RDRAM')
        if text is not None and (text <= 0 or text % 4 or text > load):
            raise ValueError('Known text size must be aligned and inside load range')
        bss=item['bss_end']
        if bss is not None and (bss < vram+load or bss > 0x80800000 or bss % 4):
            raise ValueError('BSS end must follow initialized load and fit RDRAM')
        item['seeds']=[_integer(value) for value in item.get('seeds', [])]
        if text is not None and any(v % 4 or not vram <= v < vram+text for v in item['seeds']):
            raise ValueError('Function seed is outside known text')
        item['function_spans']=_validated_function_spans(item)
        if not item.get('confidence'):
            raise ValueError('Section evidence/confidence is required')
        result.append(item)
    return result


def _validated_function_spans(section):
    result=[]
    end=section['vram']
    for original in sorted(section.get('function_spans',[]),key=lambda span:_integer(span['vram'])):
        span=dict(original)
        span['vram'],span['size']=_integer(span['vram']),_integer(span['size'])
        start,size=span['vram'],span['size']
        evidence=span.get('evidence')
        if (section['text_size'] is None or start % 4 or size <= 0 or size % 4
                or start < end or start+size > section['vram']+section['text_size']):
            raise ValueError('Reviewed function span overlaps or exceeds known aligned CPU text')
        if not isinstance(evidence,str) or not evidence.strip():
            raise ValueError('Reviewed function span requires explicit evidence')
        end=start+size
        result.append(span)
    return result


def apply_function_spans(section):
    """Merge only explicitly reviewed contiguous function extents, per ROM owner.

    Never invent instructions or a fallback return: all covered words remain
    original CPU text and the compiler must still validate its jump targets.
    """
    functions=[dict(f) for f in sorted(section['functions'],key=lambda f:f['vram'])]
    for span in _validated_function_spans(section):
        start,end=span['vram'],span['vram']+span['size']
        overlapping=[f for f in functions if f['vram'] < end and f['vram']+f['size'] > start]
        cursor=start
        for function in overlapping:
            if function['vram'] != cursor or function['vram']+function['size'] > end:
                raise ValueError('Reviewed function span must cover complete contiguous analyzed functions')
            cursor=function['vram']+function['size']
        if not overlapping or cursor != end:
            raise ValueError('Reviewed function span lacks an analyzed start or contains gaps')
        merged=dict(overlapping[0],size=span['size'],privileged=any(f.get('privileged',False) for f in overlapping),
                    span_evidence=span['evidence'])
        functions=[f for f in functions if f not in overlapping]+[merged]
        functions.sort(key=lambda f:f['vram'])
    return functions


def function_name(section, address):
    return f'func_{address:08X}_{section}'


def render_symbols(sections):
    lines=[]
    for section in sections:
        text=section['text_size']
        if text is None:
            continue
        lines += ['[[section]]', f'name = "{section["name"]}"',
                  f'rom = 0x{section["rom"]:X}', f'vram = 0x{section["vram"]:X}',
                  f'size = 0x{text:X}', 'functions = [']
        end=section['vram']
        for function in sorted(section['functions'],key=lambda f:f['vram']):
            address,size=function['vram'],function['size']
            if address % 4 or size <= 0 or size % 4 or address < end or address+size > section['vram']+text:
                raise ValueError('Function overlaps or exceeds known CPU text')
            end=address+size
            name=function_name(section['name'],address)
            lines.append(f'  {{ name = "{name}", vram = 0x{address:X}, size = 0x{size:X} }},')
        lines += [']','']
    return '\n'.join(lines)


def call_candidates(sections, caller_section, target):
    matches=[]
    for section in sections:
        for function in section.get('functions',[]):
            if function['vram'] == target:
                name=function_name(section['name'],target)
                if section['name'] == caller_section:
                    return [name]
                matches.append(name)
    return matches


def attach_runtime_bindings(sections, bindings):
    ignored=[]
    for binding in bindings:
        address,rom=_integer(binding['address']),_integer(binding['rom_offset'])
        found=False
        for section in sections:
            if section['rom']+address-section['vram'] != rom:
                continue
            for function in section.get('functions',[]):
                if function['vram']==address:
                    function['runtime_symbol']=binding['runtime_symbol']
                    ignored.append(function_name(section['name'],address))
                    found=True
        if not found:
            raise ValueError(f'Reviewed runtime binding at {address:08X} has no matching mapped ROM owner')
    return ignored


def validate_output(output, private, inputs):
    from pathlib import Path
    output,private=Path(output).absolute(),Path(private).resolve()
    if (output.exists() or output.resolve()==private or not output.resolve().is_relative_to(private)
            or any(p.is_symlink() for p in (output,*output.parents))):
        raise ValueError('Output must be a fresh directory below private .local without symlinks')
    for source in inputs:
        source=Path(source).resolve()
        if output.resolve().is_relative_to(source) or source.is_relative_to(output.resolve()):
            raise ValueError('Output overlaps an input')
    return output


def render_config(rom, ignored, dynamic_lookup=False):
    if dynamic_lookup:
        raise ValueError('Pinned N64Recomp CLI cannot enable dynamic lookup; requires a separately verified driver')
    import json
    return ('[input]\nsymbols_file_path = "symbols.toml"\nrom_file_path = '+json.dumps(str(rom))+
            '\noutput_func_path = "functions"\nfunctions_per_output_file = 1\nuses_mips3_float_mode = false\n'+
            ('use_lookup_for_all_function_calls = true\n' if dynamic_lookup else '')+
            '[patches]\nignored = '+json.dumps(ignored)+'\n')


def main():
    import argparse
    import hashlib
    import json
    from pathlib import Path
    import struct
    import subprocess
    import sys
    from tools.rom import ROOT,validate,load_manifest,SUPPORTED_REVISIONS,DEFAULT_REVISION
    from tools.recompile import verify_tool

    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--revision',choices=SUPPORTED_REVISIONS,default=DEFAULT_REVISION)
    parser.add_argument('--sections',type=Path,default=ROOT/'config/recomp/sections.json')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--spimdisasm',type=Path,required=True)
    parser.add_argument('--packages',type=Path,required=True)
    parser.add_argument('--recompiler',type=Path,required=True)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--runtime-bindings',type=Path,help='Verify and exclude reviewed OS bodies for real host wrappers')
    parser.add_argument('--dynamic-lookup',action='store_true',help='Generate fatal-on-unknown-runtime-lookup candidates; does not establish target coverage')
    args=parser.parse_args()
    try:
        if args.dynamic_lookup:
            render_config(args.rom,[],True)
        image=args.rom.read_bytes(); validate(image,load_manifest(args.revision))
        tool_identity=verify_tool(args.recompiler,args.source)
        inventory=json.loads(args.sections.read_text())
        sections=validate_sections(inventory['sections'],len(image))
        bindings=[]
        if args.runtime_bindings:
            from tools.identify_runtime import verify_bindings
            bindings=verify_bindings(image,json.loads(args.runtime_bindings.read_text()))
        output=validate_output(args.output,ROOT/'.local',
                               [args.rom,args.sections,args.spimdisasm,args.packages,args.source,args.recompiler])
        pins=json.loads((ROOT/'config/dependencies.json').read_text())
        spim_commit=subprocess.check_output(['git','-C',str(args.spimdisasm),'rev-parse','HEAD'],text=True).strip()
        if spim_commit != pins['spimdisasm']['commit']:
            raise ValueError('spimdisasm checkout differs from pinned commit')
        if subprocess.check_output(['git','-C',str(args.spimdisasm),'status','--porcelain','--untracked-files=no'],text=True).strip():
            raise ValueError('spimdisasm tracked source is modified')
        sys.path[:0]=[str(args.spimdisasm.resolve()),str(args.packages.resolve())]
        from spimdisasm import common,mips
        import rabbitizer
        common.GlobalConfig.COMPILER=common.Compiler.GCC
        common.GlobalConfig.QUIET=True
        ignored=[];calls=[]
        for section in sections:
            section['functions']=[]
            if section['text_size'] is None:
                continue
            # A distinct analysis context prevents aliases at the same guest PC
            # from silently replacing one another's symbols.
            context=common.Context()
            context.changeGlobalSegmentRanges(0,len(image),0x80000000,0x80800000)
            seeds=set(section['seeds'] or [section['vram']])
            for binding in bindings:
                address=_integer(binding['address'])
                if (section['rom']+address-section['vram']==_integer(binding['rom_offset'])
                        and section['vram'] <= address < section['vram']+section['text_size']):
                    seeds.add(address)
            for address in sorted(seeds):
                symbol=context.globalSegment.addFunction(address,vromAddress=section['rom']+address-section['vram'])
                symbol.name=function_name(section['name'],address);symbol.isUserDeclared=True
            text=mips.sections.SectionText(context,section['rom'],section['rom']+section['text_size'],
                                           section['vram'],section['name'],image,0,None)
            text.analyze()
            for function in text.symbolList:
                privileged=False
                for instruction in function.instructions:
                    word=instruction.getRaw()
                    if (word >> 26 in (16,47) or
                            instruction.readsRs() and ((word >> 21)&31) in (26,27) or
                            instruction.readsRt() and ((word >> 16)&31) in (26,27) or
                            instruction.getDestinationGpr() in (26,27)):
                        privileged=True
                section['functions'].append(dict(name=function_name(section['name'],function.vram),vram=function.vram,size=function.sizew*4,
                                                  privileged=privileged))
            section['functions']=apply_function_spans(section)
            ignored.extend(function_name(section['name'],f['vram']) for f in section['functions'] if f['privileged'])
            # Scan only classified candidate CPU text, not initialized data/RSP.
            for offset in range(section['rom'],section['rom']+section['text_size'],4):
                word=struct.unpack_from('>I',image,offset)[0]
                if word >> 26 == 3:
                    pc=section['vram']+offset-section['rom']
                    calls.append(dict(section=section['name'],callsite=pc,
                                      target=((pc+4)&0xF0000000)|((word&0x3FFFFFF)<<2)))
        privileged=list(ignored)
        runtime_ignored=attach_runtime_bindings(sections,bindings)
        ignored=sorted(set(ignored+runtime_ignored))
        symbols=render_symbols(sections)
        call_index={}
        for section in sections:
            for function in section['functions']:
                call_index.setdefault(function['vram'],[]).append((section['name'],function['name']))
        for call in calls:
            matches=call_index.get(call['target'],[])
            local=[name for owner,name in matches if owner==call['section']]
            call['candidates']=local or [name for owner,name in matches]
        output.mkdir(parents=True,exist_ok=False)
        (output/'symbols.toml').write_text(symbols)
        (output/'section-analysis.json').write_text(json.dumps(sections,indent=2)+'\n')
        (output/'calls.json').write_text(json.dumps(calls,indent=2)+'\n')
        (output/'privileged.json').write_text(json.dumps(ignored,indent=2)+'\n')
        config=render_config(args.rom.resolve(),ignored,args.dynamic_lookup)
        (output/'recomp.toml').write_text(config)
        run=subprocess.run([str(args.recompiler.resolve()),str(output/'recomp.toml')],capture_output=True,text=True,timeout=300)
        log=run.stdout+run.stderr
        (output/'recompile.log').write_text(log)
        generated={str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in sorted((output/'functions').glob('*')) if p.is_file()}
        summary=dict(status='provisional-section-translation-probe',full_runtime_ready=False,
                     dynamic_lookup=args.dynamic_lookup,
                     rom_sha256=hashlib.sha256(image).hexdigest(),tool=tool_identity,
                     spimdisasm_commit=spim_commit,rabbitizer_version=rabbitizer.__version__,
                     section_count=len(sections),analyzed_sections=sum(s['text_size'] is not None for s in sections),
                     candidate_functions=sum(len(s['functions']) for s in sections),
                     excluded_privileged_functions=privileged,runtime_bound_functions=runtime_ignored,unknown_text_sections=[s['name'] for s in sections if s['text_size'] is None],
                     unresolved_calls=[c for c in calls if not c['candidates']],
                     ambiguous_calls=[c for c in calls if len(c['candidates'])>1],
                     recompiler_returncode=run.returncode,recompiler_log_tail=log[-6000:],generated_files=generated,
                     limits=['Provisional text/data boundaries; static load evidence is not runtime ordering',
                             'Privileged-function exclusions have no runtime implementations',
                             'No native linking, OS bindings, game boot or playable match is claimed'])
        (output/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
        print(json.dumps({k:summary[k] for k in ['candidate_functions','analyzed_sections','unknown_text_sections','recompiler_returncode','recompiler_log_tail']},indent=2))
        return run.returncode
    except (OSError,ValueError,ImportError,KeyError,subprocess.SubprocessError) as exc:
        print(f'Section mapping error: {exc}',file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
