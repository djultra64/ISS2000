"""Generate guarded PAL English save wording for the original font renderer.

Original project work: djultra64. No filesystem, status, input or SDK changes.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from tools.prepare_pal_auto_storage_ui import ROM_SHA256,WORDING,encode

ENTRY='iss2000_pal_storage_text'
# Exact original English message extents; player names and other languages are
# deliberately not a dictionary-replacement domain. Every original control and
# fixed glyph-run capacity is preserved, including original Yes/No choices.
MESSAGES={
 (0x316C18,114):['         Vibration ready.','         Controls settings.',' ',' ',' ',' ','     Press the A Button to proceed.'],
 (0x316C8C,116):['         Saved data available.','         Continue the game.',' ',' ',' ',' ','     Press the A Button to proceed.'],
 (0x329820,61):['Saved data is damaged or','storage is unavailable.'],
 (0x32985D,88):['   There is a possibility that data','in saved games may be','damaged. Repair?'],
 (0x3298D4,78):['Unable to access saved game data.','Please retry.','Please press the START.'],
 (0x32992E,16):['   Retry'],
 (0x329961,80):['   Saved data has changed.','Press the START','to reload data.'],
 (0x3299B1,60):['   Unable to access','saved game data.'],
 (0x3299ED,100):['   Repair',' Repair saved game data.',' There is a possibility that saved',' data may be lost.'],
 (0x329A51,70):['   Retry','Try accessing saved game data','once more.'],
 (0x50C3F8,34):['Loading data','Saved game 1'],
 (0x50C41A,36):['  Loading data','Saved game 2'],
 (0x50F871,64):['   Saved data is damaged or','storage is unavailable.'],
 (0x50F90A,191):['  Repair','Restore saved game data. Doing so','may erase saved game data and','will also interrupt','the game in progress, and return you','to the Main Selection Screen.'],
 (0x50FADB,28):[' No saved game data.'],
 (0x50FAF7,50):['   Saved data is not','  available.'],
 (0x50FB29,32):['   Retry saved data.'],
 (0x50FB49,38):['   Saved data is unavailable.'],
 (0x50FB6F,30):['     Saved data error.'],
 (0x50FBC2,37):['  Could not repair saved data.'],
 (0x50FBE7,28):[' Saved data repaired.'],
 (0x510193,116):[' Start without saved game data.','Saved data is unavailable.','Please retry to save the game','or continue.'],
 (0x510207,177):[' Create saved game data?','No saved data found.','Create saved game data.','','','             Yes   No'],
 (0x5102B8,19):['  Data created.'],
 (0x5102CB,22):[' Unable to save.'],
 (0x5102E1,39):['   Play without data?','    Yes   No'],
 (0x510308,90):['Saved data is damaged.',' Recover? Data may be lost.',' Retry saved data.'],
 (0x510362,60):['   ','Saved data error.','Start without saved game data.'],
 (0x514B56,94):['  Save Game.','If no saved data exists,','a new file will be created.'],
 (0x514BB4,20):['Load Game.'],
 (0x514BCA,45):['    Save Game?',''],
 (0x514C16,55):['  Save data is unavailable,',"game can't be saved."],
 (0x514C4D,59):['   No saved game data.','Create saved game data?'],
 (0x514C88,79):['Unable to save data.','Check existing saved data','and try again.'],
 (0x514CD7,81):[' Unable to save data.','Check existing saved data','and try again.'],
 (0x514D28,16):['Create data'],
 (0x514D4C,35):['Saved data is unavailable.'],
 (0x514D6F,26):['      Load Game?'],
 (0x514D89,36):['        No saved game data.'],
 (0x514E0E,88):['  Accessing saved data.','Please wait.',' ','Press the A Button to proceed.'],
 (0x514E6A,63):['  Saved data is damaged or','storage is unavailable.'],
 (0x514ECB,85):[' There is a possibility that','saved game data may','be damaged. Repair?'],
 (0x514FA0,94):['Repair:  Repairing saved data.',' There is a possibility that saved data',' may be lost.'],
}
BANKS=[(0x315400,0x1900,0x801ED700),(0x326630,0x3CD0,0x801EF060),
       (0x50C3E0,0x3FF0,0x803FAF60),(0x514950,0x810,0x802DD400)]

def change_message(original,lines):
 changed=bytearray(original);start=0;line=0
 if not original.endswith(b'\xff\x11'):raise ValueError('Storage message terminator mismatch')
 while start<len(original)-2:
  end=original.index(b'\xff',start)
  if end>start:
   if line>=len(lines):raise ValueError('Storage wording line count mismatch')
   encoded=encode(lines[line]);capacity=end-start
   if len(encoded)>capacity:raise ValueError('Storage wording exceeds original glyph run')
   if any(x>=0xF5 for x in original[start:end]):raise ValueError('Storage wording owns a control')
   changed[start:end]=encoded+bytes(capacity-len(encoded));line+=1
  start=end+2
 if line!=len(lines):raise ValueError('Storage wording line count mismatch')
 return bytes(changed)

def profiles(binary):
 if len(binary)!=0x1000000 or hashlib.sha256(binary).hexdigest()!=ROM_SHA256:
  raise ValueError('Pinned PAL ROM digest mismatch')
 result=[]
 for (rom,size),lines in MESSAGES.items():
  original=binary[rom:rom+size]
  try:changed=change_message(original,lines)
  except ValueError as e:raise ValueError(f'{rom:X}: {e}')from e
  bank=next((s for s in BANKS if s[0]<=rom<rom+size<=s[0]+s[1]),None)
  if bank is None:raise ValueError('Storage message outside proven original bank')
  guest=bank[2]+rom-bank[0];pointers=[];references=[]
  # Original pointer-table targets can skip alignment padding. Admit only those
  # exact proven words; never accept an arbitrary interior substring pointer.
  for skip in range(9):
   if skip and original[skip-1]!=0:break
   needle=struct.pack('>I',guest+skip);position=0
   while (position:=binary.find(needle,position))>=0:
    if position%4==0:
     pointers.append(guest+skip);references.append(position)
    position+=4
  pointers=sorted(set(pointers))
  basis='original pointer-table target'
  if not pointers:
   # These four known strings have no recovered whole-word reference. The
   # proven loader still fixes their exact source bytes/address. Admit only
   # leading alignment spaces, never an interior glyph/control address, and
   # require the complete message image below. This does not claim execution.
   if rom not in (0x329961,0x3299B1,0x3299ED,0x329A51):
    raise ValueError(f'No original storage pointer for{rom:X}')
   basis='exact original message leading padding; actual consumer unverified'
   pointers=[guest]
   while len(pointers)<=8 and original[len(pointers)-1]==0:
    pointers.append(guest+len(pointers))
  for pointer in pointers:
   if any(changed[:pointer-guest]):raise ValueError('Replacement overwrites skipped source padding')
  variants=[original,changed]
  if (rom,size)in WORDING:variants.append(change_message(original,WORDING[(rom,size)]))
  result.append(dict(rom=rom,guest=guest,size=size,pointers=pointers,references=references,pointer_basis=basis,
    original=original,changed=changed,variants=list(dict.fromkeys(variants)),lines=lines))
 return result

def generate(binary):
 owned=profiles(binary);code=['// Private original-ROM derivative. Original project work: djultra64.',
 '#include <cstdint>\n#include <cstring>\n#include <cstddef>',
 'namespace {',
 'bool address(uint64_t value,uint32_t size,uint32_t& p){const auto lo=uint32_t(value),hi=uint32_t(value>>32);if(hi&&(hi!=0xffffffffu||!(lo&0x80000000u)))return false;if((lo&0xff800000u)!=0x80000000u)return false;p=lo&0x7fffffu;return size<=0x800000u-p;}',
 'uint8_t byte(const uint8_t*r,uint32_t p){return r[p^3u];}',
 'uint32_t word(const uint8_t*r,uint32_t p){uint32_t v;std::memcpy(&v,r+p,4);return v;}',
 '}\nextern "C" bool '+ENTRY+'(uint8_t* ram,uint64_t object){',
 'uint32_t p;if(!ram||!address(object,0x24,p)||(p&3)||byte(ram,p+5)!=0)return false;',
 'uint32_t source;if(!address(word(ram,p+0x14),1,source))return false;']
 evidence=[]
 for n,m in enumerate(owned):
  code.append('if('+ '||'.join(f'source==0x{x&0x7fffff:X}u'for x in m['pointers'])+'){')
  for v,variant in enumerate(m['variants']):code.append(f'static constexpr uint8_t v{n}_{v}[]={{'+','.join(map(str,variant))+'};')
  code.append(f'bool matches[{len(m["variants"])}]={{'+','.join('true'for _ in m['variants'])+'};')
  for v in range(len(m['variants'])):code.append(f'for(size_t i=0;i<{m["size"]};++i)matches[{v}]&=byte(ram,0x{m["guest"]&0x7fffff:X}u+uint32_t(i))==v{n}_{v}[i];')
  code.append('if(!('+ '||'.join(f'matches[{v}]'for v in range(len(m['variants'])))+'))return false;')
  code.append(f'for(size_t i=0;i<{m["size"]};++i)ram[(0x{m["guest"]&0x7fffff:X}u+uint32_t(i))^3u]=v{n}_1[i];return true;}}')
  evidence.append({k:([hex(x)for x in value]if k in('pointers','references')else hex(value)if k in('rom','guest')else value)for k,value in m.items()if k not in('original','changed','variants')})
  evidence[-1]['original_sha256']=hashlib.sha256(m['original']).hexdigest();evidence[-1]['changed_sha256']=hashlib.sha256(m['changed']).hexdigest()
 code.append('return false;}\n')
 return '\n'.join(code).encode(),evidence

def prepare(rom,output):
 generated,messages=generate(rom.read_bytes());receipt=dict(schema=1,attribution='djultra64',revision='iss2000-pal-en-de-rev0',rom_sha256=ROM_SHA256,entry=ENTRY,
  signature='bool(uint8_t* rdram8MiB,uint64_t original_font_object)',call_boundary='before exact original80048660; no standalone renderer',
  file='pal_storage_text.cpp',generated_sha256=hashlib.sha256(generated).hexdigest(),messages=messages,
  preserved=['all original control bytes and source extents','save creation/overwrite/repair/error actions','SDK and filesystem results','player names','four-controller labels'],
  limits=['English messages only','four generic messages have bounded byte ownership but no recovered actual consumer','capacity digits require original producer ownership before suppression','CPU fixture is not GPU acceptance'])
 files={'pal_storage_text.cpp':generated,'receipt.json':(json.dumps(receipt,indent=2)+'\n').encode()}
 if output.is_symlink()or any(p.is_symlink()for p in output.absolute().parents):raise ValueError('Storage text output must not contain symlinks')
 if output.exists():
  if not output.is_dir()or set(p.name for p in output.iterdir())!=set(files)or any((output/n).is_symlink()or not(output/n).is_file()or(output/n).read_bytes()!=v for n,v in files.items()):raise ValueError('Refusing to alter existing storage text derivative')
  return receipt
 output.mkdir(parents=True,exist_ok=False)
 for name,data in files.items():
  with(output/name).open('xb')as f:f.write(data)
 return receipt

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rom',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args();print(json.dumps(prepare(args.rom,args.output),indent=2))
if __name__=='__main__':main()
