"""Prepare allocation-owned radar metadata; original project work: djultra64."""
from pathlib import Path
import argparse,hashlib,json
ROM_SHA256='6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf'
SOURCE_SHA256='d43b12f3bf23075c9445a2ed9e4a1fa1f6209003e83e1d236e81d0e4347f8824'
ENTRY='iss2000_pal_radar_callback'
FILE='pal_radar_callback.cpp'
PRELUDE=r'''#include "runtime/pal_radar_interpolation.hpp"
#include "runtime/menu_sprite_runtime.hpp"
#include "runtime/transform_runtime.hpp"
using namespace iss2000;
namespace {
thread_local PalRadarCapture* radar_capture{};
uint32_t radar_word(uint8_t*rdram,uint64_t a){auto p=uint32_t(a);if(p<0x80000000||p>0x807ffffc||p%4)return 0;return uint32_t(MEM_W(0,S32(p)));}
uint32_t radar_player_root(uint8_t*r,uint64_t p){auto player=uint32_t(p);if(player<0x801313d0||(player-0x801313d0)%0x138||(player-0x801313d0)/0x138>=28)return 0;return radar_word(r,radar_word(r,player+0x9c));}
void radar_call(uint8_t*rdram,recomp_context*ctx,uint32_t root,uint32_t role,recomp_func_t*original){
 role |= uint32_t(MEM_BU(0,S32(0x8012e6a3))) << 16;
 const auto tag=lookup_transform_record(root);const uint32_t begin=radar_word(rdram,0x802b4400);
 original(rdram,ctx); // Exactly once, original delay slot has already executed.
 if(!radar_capture)return;
 const uint32_t end=radar_word(rdram,0x802b4400);
 if(begin%8||end<begin||end-begin>0x960)return;
 for(uint32_t p=begin;p<end;p+=8)if(radar_word(rdram,p)>>24==0xe4){
  radar_capture->emit({rdram,0x800000},p,p+24,tag.value_or(TransformTag{}),role);p+=16;
 }
}
}
'''
SUFFIX=r'''
extern "C" void iss2000_pal_radar_callback(uint8_t*rdram,recomp_context*ctx){
 const uint32_t root=uint32_t(ctx->r4);const auto tag=lookup_transform_record(root);
 const unsigned bank=uint16_t(MEM_HU(0,S32(0x8013b418)));
 const uint32_t begin=0x802b4408+bank*0x960;
 PalRadarCapture capture;auto*previous=radar_capture;radar_capture=nullptr;
 if(bank<2){
  retire_menu_radar_bank(begin);
  if(tag && radar_word(rdram,0x802b2950)==root && radar_word(rdram,root+0x7c)==0x802a5290 &&
     (radar_word(rdram,root+0x28)&0x80000000u) && capture.begin({rdram,0x800000},*tag,bank,begin))radar_capture=&capture;
 }
 radar_original_callback(rdram,ctx);
 if(radar_capture && radar_word(rdram,root+0x24)==begin && capture.finish({rdram,0x800000},radar_word(rdram,0x802b4400)))observe_menu_radar({rdram,0x800000},capture);
 radar_capture=previous;
}
'''
def derive(source:bytes)->bytes:
 if hashlib.sha256(source).hexdigest()!=SOURCE_SHA256:raise ValueError('Pinned PAL radar source digest mismatch')
 text=source.decode();text=text.replace('#include "recomp.h"','#include "recomp.h"\n'+PRELUDE,1)
 text=text.replace('RECOMP_FUNC void func_802A5290_overlay_376010_802a4380(', 'static void radar_original_callback(',1)
 old='LOOKUP_FUNC(0x802A5230)(rdram, ctx);'
 assert text.count(old)==1
 text=text.replace(old,'radar_call(rdram, ctx, radar_player_root(rdram,ctx->r4), 1, LOOKUP_FUNC(0x802A5230));')
 old='LOOKUP_FUNC(0x802A5180)(rdram, ctx);'
 assert text.count(old)==2
 text=text.replace(old,'radar_call(rdram, ctx, radar_player_root(rdram,ctx->r6), 2, LOOKUP_FUNC(0x802A5180));',1)
 text=text.replace(old,'radar_call(rdram, ctx, radar_player_root(rdram,ctx->r6), 3, LOOKUP_FUNC(0x802A5180));',1)
 old='LOOKUP_FUNC(ctx->r20)(rdram, ctx);'
 assert text.count(old)==4
 for actor,role in [('radar_player_root(rdram,ctx->r18)','0x100u + uint32_t(ctx->r16)'),('radar_player_root(rdram,ctx->r18)','0x200u + uint32_t(ctx->r16)'),('radar_player_root(rdram,radar_word(rdram,ctx->r5+0x94))','0x300u'),('radar_word(rdram,0x802b57d0)','0x400u')]:
  text=text.replace(old,f'radar_call(rdram, ctx, {actor}, {role}, LOOKUP_FUNC(ctx->r20));',1)
 return (text+SUFFIX).encode()
def prepare(rom:Path,source:Path,output:Path):
 image=rom.read_bytes()
 if len(image)!=0x1000000 or hashlib.sha256(image).hexdigest()!=ROM_SHA256:raise ValueError('Pinned PAL ROM mismatch')
 data=derive(source.read_bytes());receipt=dict(attribution='djultra64',rom_sha256=ROM_SHA256,source_sha256=SOURCE_SHA256,generated_sha256=hashlib.sha256(data).hexdigest(),entry=ENTRY,file=FILE,metadata_only=True)
 files={FILE:data,'receipt.json':(json.dumps(receipt,indent=2)+'\n').encode()}
 if output.is_symlink() or any(p.is_symlink() for p in output.absolute().parents):raise ValueError('No symlink output paths')
 if output.exists():
  if not output.is_dir() or set(p.name for p in output.iterdir())!=set(files) or any((output/n).is_symlink() or not (output/n).is_file() or (output/n).read_bytes()!=v for n,v in files.items()):raise ValueError('Refusing to overwrite radar derivatives')
 else:
  output.mkdir(parents=True)
  for n,v in files.items():(output/n).write_bytes(v)
 return receipt
def main():
 p=argparse.ArgumentParser();p.add_argument('--rom',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(prepare(a.rom,a.source,a.output),indent=2))
if __name__=='__main__':main()
