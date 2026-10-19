"""Original project work: djultra64. Authentic CC0 tile and bounded CI4 adaptation checks."""
from pathlib import Path
import hashlib
import os
import shutil
import subprocess
import tempfile
import unittest
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'assets/controller-prompts/greatdocbrown'
MINIZ=ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz'
MINIZ_BUILD=ROOT/'.local/runtime-deps-build/librecomp/miniz'

class GdbSourceTests(unittest.TestCase):
 def test_official_tiles_generate_reproducibly_and_changed_download_is_rejected(self):
  from tools.prepare_prompt_glyphs import prepare
  with tempfile.TemporaryDirectory() as directory:
   folder=Path(directory);output=folder/'glyphs.inc'
   receipt=prepare(ASSETS,output)
   self.assertGreater(receipt['glyph_count'],40)
   self.assertEqual(prepare(ASSETS,output),receipt)
   self.assertEqual(output.read_bytes(),(ROOT/'src/runtime/gdb_prompt_glyphs.inc').read_bytes())
   copied=folder/'source';shutil.copytree(ASSETS,copied)
   sheet=copied/'gdb-xbox-2.png';sheet.write_bytes(sheet.read_bytes()+b'changed')
   with self.assertRaises(ValueError):prepare(copied,folder/'rejected.inc')
   self.assertFalse((folder/'rejected.inc').exists())

@unittest.skipUnless(shutil.which('c++') and (MINIZ_BUILD/'libminiz.a').is_file(),'Compiler and pinned miniz required')
class GdbRuntimeTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.temp.cleanup);folder=Path(cls.temp.name)
  (folder/'main.cpp').write_text(r'''#include "runtime/prompt_textures.hpp"
#include <cstdlib>
#include <iostream>
using namespace iss2000;
int main(int argc,char**argv){
 if(argc!=3 && argc!=4)return 2;
 std::array<uint8_t,32> palette{}; // transparent0; opaque grayscale1..15
 for(unsigned n=1;n<16;++n){unsigned level=(n-1)*31/14;uint16_t color=(level<<11)|(level<<6)|(level<<1)|1;palette[n*2]=color>>8;palette[n*2+1]=color;}
 if(argc==4){std::string input=argv[3];if(input.size()!=64)return 2;for(unsigned n=0;n<32;++n)palette[n]=uint8_t(std::strtoul(input.substr(n*2,2).c_str(),nullptr,16));}
 auto pixels=prompt_detail::glyph_pixels({PromptGlyphFamily(std::atoi(argv[1])),argv[2]},palette);
 if(!pixels)return 3;
 std::cout.write(reinterpret_cast<const char*>(pixels->data()),pixels->size());
}''')
  cls.binary=folder/'probe'
  result=subprocess.run(['c++','-std=c++20','-O1','-Wall','-Wextra','-Werror','-pthread','-I'+str(ROOT/'src'),'-I'+str(MINIZ),'-I'+str(MINIZ_BUILD),str(folder/'main.cpp'),str(ROOT/'src/runtime/prompt_textures.cpp'),str(ROOT/'src/runtime/rom_image.cpp'),str(MINIZ_BUILD/'libminiz.a'),'-o',str(cls.binary)],capture_output=True,text=True)
  if result.returncode:raise AssertionError(result.stderr)
 def run_glyph(self,family,label,palette=None):
  args=[str(self.binary),str(family),label]
  if palette is not None:args.append(palette.hex())
  return subprocess.run(args,capture_output=True)
 def test_face_and_keyboard_glyphs_are_exact_artist_tiles_quantized_to_supplied_palette(self):
  # Coordinates independently read from the official sheets, not the manifest.
  cases=[(1,'LB','gdb-xbox-2.png',224,496),(1,'RB','gdb-xbox-2.png',224,512),(1,'A','gdb-xbox-2.png',16,48),(1,'B','gdb-xbox-2.png',16,80),
   (2,'×','gdb-playstation-3.png',16,192),(2,'○','gdb-playstation-3.png',16,176),
   (3,'B','gdb-switch-2.png',16,32),(3,'A','gdb-switch-2.png',16,48),
   (4,'Left Shift','gdb-keyboard-2.png',32,80),(4,'Z','gdb-keyboard-2.png',64,80),(4,'X','gdb-keyboard-2.png',80,80)]
  palette=[(0,0,0,0)]+[(level*255//31,)*3+(255,) for n in range(1,16) for level in [(n-1)*31//14]]
  def luminance(c):return c[0]*77+c[1]*150+c[2]*29
  for family,label,sheet,x,y in cases:
   with self.subTest(family=family,label=label):
    tile=Image.open(ASSETS/sheet).crop((x,y,x+(32 if label=='Left Shift' else 16),y+16))
    if label=='Left Shift':
     source=tile.resize((16,8),Image.Resampling.NEAREST);tile=Image.new('RGBA',(16,16));tile.paste(source,(0,4))
    indices=[]
    for c in tile.getdata():
     index=0 if c[3]==0 else min(range(1,16),key=lambda i:(abs(luminance(c)-luminance(palette[i])),sum(w*(c[j]-palette[i][j])**2 for j,w in enumerate([77,150,29])),i))
     indices.append(index)
    expected=bytes((indices[n]<<4)|indices[n+1] for n in range(0,256,2))
    result=self.run_glyph(family,label);self.assertEqual(result.returncode,0,result.stderr)
    self.assertEqual(result.stdout,expected)
  self.assertNotEqual(self.run_glyph(1,'A').stdout,self.run_glyph(3,'A').stdout)
 def test_right_stick_directions_combine_authentic_stick_and_direction_tiles(self):
  # Both source rectangles are independently pinned here. The composite is a
  # nearest-neighbor derivative, never a newly drawn letter or arrow.
  sheets=[(family,'gdb-xbox-2.png',280,32) for family in [1,2,3]]
  directions=[('R←',16,144),('R→',16,112),('R↑',16,96),('R↓',16,128)]
  palette=[(0,0,0,0)]+[(level*255//31,)*3+(255,) for n in range(1,16) for level in [(n-1)*31//14]]
  def luma(c):return c[0]*77+c[1]*150+c[2]*29
  for family,sheet,x,y in sheets:
   for label,dx,dy in directions:
    with self.subTest(family=family,label=label):
     stick=Image.open(ASSETS/sheet).convert('RGBA').crop((x,y,x+16,y+16)).resize((12,12),Image.Resampling.NEAREST)
     arrow=Image.open(ASSETS/'gdb-switch-2.png').convert('RGBA').crop((dx,dy,dx+16,dy+16)).resize((8,8),Image.Resampling.NEAREST)
     tile=Image.new('RGBA',(16,16));tile.alpha_composite(stick,(0,0));tile.alpha_composite(arrow,(8,8))
     indices=[0 if c[3]==0 else min(range(1,16),key=lambda i:(abs(luma(c)-luma(palette[i])),sum(w*(c[j]-palette[i][j])**2 for j,w in enumerate([77,150,29])),i)) for c in tile.getdata()]
     expected=bytes((indices[n]<<4)|indices[n+1] for n in range(0,256,2))
     result=self.run_glyph(family,label);self.assertEqual(result.returncode,0,result.stderr)
     self.assertEqual(result.stdout,expected)

 def test_unknown_family_or_unavailable_art_does_not_invent_an_icon(self):
  for family,label in [(0,'A'),(99,'A'),(1,'Unbound'),(2,'Paddle 1')]:
   result=self.run_glyph(family,label);self.assertEqual(result.returncode,3);self.assertEqual(result.stdout,b'')

 def test_palettes_without_both_transparent_and_opaque_entries_are_rejected(self):
  for palette in [bytes(32),bytes([255])*32]:
   result=self.run_glyph(1,'A',palette);self.assertEqual(result.returncode,3);self.assertEqual(result.stdout,b'')
 @unittest.skipUnless(os.environ.get('ISS2000_PAL_ROM'),'set ISS2000_PAL_ROM for private original-palette integration')
 def test_original_pal_icon_palettes_preserve_artist_opacity_for_all_families(self):
  rom=Path(os.environ['ISS2000_PAL_ROM']).read_bytes()
  self.assertEqual(hashlib.sha256(rom).hexdigest(),'6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf')
  cases=[(1,'LB','gdb-xbox-2.png',224,496),(1,'RB','gdb-xbox-2.png',224,512),(1,'A','gdb-xbox-2.png',16,48),(1,'B','gdb-xbox-2.png',16,80),
   (2,'×','gdb-playstation-3.png',16,192),(2,'○','gdb-playstation-3.png',16,176),
   (3,'B','gdb-switch-2.png',16,32),(3,'A','gdb-switch-2.png',16,48),
   (4,'Left Shift','gdb-keyboard-2.png',32,80),(4,'Z','gdb-keyboard-2.png',64,80),(4,'X','gdb-keyboard-2.png',80,80)]
  for start in [0x35B0A0,0x35B0C0,0x35B120]:
   palette=rom[start:start+32]
   for family,label,sheet,x,y in cases:
    tile=Image.open(ASSETS/sheet).crop((x,y,x+(32 if label=='Left Shift' else 16),y+16))
    if label=='Left Shift':
     source=tile.resize((16,8),Image.Resampling.NEAREST);tile=Image.new('RGBA',(16,16));tile.paste(source,(0,4))
    result=self.run_glyph(family,label,palette);self.assertEqual(result.returncode,0,result.stderr)
    indices=[index for value in result.stdout for index in [value>>4,value&15]]
    self.assertEqual([bool(palette[i*2+1]&1) for i in indices],[bool(pixel[3]) for pixel in tile.getdata()])
    self.assertGreater(len(set(indices)),3) # relief shading survives reduction
