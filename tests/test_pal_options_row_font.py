"""Original project work: djultra64. Exact original Options row-face pixel ownership."""
from pathlib import Path
import hashlib,shutil,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
CODE=r'''#include "runtime/pal_options_row_font.hpp"
#include "runtime/rom_image.hpp"
#include <cassert>
#include <cstdio>
#include <vector>
using namespace iss2000;
std::vector<uint8_t>load(const char*p){FILE*f=fopen(p,"rb");assert(f);std::vector<uint8_t>b(0x2c00);assert(fread(b.data(),1,b.size(),f)==b.size());fclose(f);return b;}
unsigned pixel(const std::vector<uint8_t>&b,unsigned width,unsigned x,unsigned y){auto n=y*width+x;return n&1?b[n/2]&15:b[n/2]>>4;}
int main(int argc,char**argv){assert(argc==2);auto asset=load(argv[1]),before=asset;
 for(auto word:{"Game Setting","Create Player","Resolution","Setting"}){
  auto a=pal_options_row_bitmap(asset,word);assert(a&&a->width==128&&a->height==16&&a->pixels.size()==1024);
  unsigned off=0,w=112,y=16,x=0,source_width=112;
  if(std::string_view(word)=="Create Player"){off=0x700;w=96;source_width=96;}
  if(std::string_view(word)=="Resolution"){off=0xd00;w=128;source_width=128;}
  if(std::string_view(word)=="Setting"){x=42;w=49;}
  std::vector<uint8_t>src(asset.begin()+off,asset.end());
  for(unsigned row=0;row<16;++row)for(unsigned col=0;col<128;++col)assert(pixel(a->pixels,128,col,row)==(col<w?pixel(src,source_width,x+col,y+row):0));
 }
 auto a=pal_options_row_bitmap(asset,"PC Settings");assert(a&&a->advance==83&&a->width==128&&a->height==16);
 assert(rom_detail::sha256_hex(a->pixels)=="886a8bfdfcbeffed201ab265a8fc0cc3ff264bf2c5ed703686cd99ad47fa3051");
 const std::pair<const char*,const char*> body[]={
  {"Graphics","15d9dc2c6e672457079655065d9eb62dea1604ac29ab4aa5c5be33ba78015183"},
  {"Controls","28ee3ceefa92bf575ed37689c714d0bf2a5495e5592ce13e0af127d01a432a87"},

  {"Cancel","3c7a68749d0a5f2d9f2a10c4ccba1c6b406d41af7c2bffebce049fc11ec2ee29"},
  {"Aspect","487066ecae10522dc6456b3ae260c96192099bc5d9a00cb3c6af3452b4bad46f"},
  {"Frame rate","0478b009663b06dba0a7da0c27b86a2842c2ecbf3c6bc908630b6f777383faea"},
  {"Screen","5533f51486cf48f4d88f5e1e65bebe0a5037f8c84cd0dcbd34795df1cf18a5bf"}};
 for(const auto& [text,pin]:body){auto row=pal_options_row_bitmap(asset,text);assert(row&&row->width==128&&row->height==16&&rom_detail::sha256_hex(row->pixels)==pin);}

 // New device rows use only these intact original source columns; the row
 // title alphabet is intentionally not a substitute for this exact face.
 struct Slice{unsigned offset,stride,x,y,width;};
 const Slice controller[]={{0x700,96,0,16,10},{0xd00,128,25,16,8},{0,112,74,16,8},{0x700,96,33,16,6},{0x700,96,10,16,7},{0xd00,128,25,16,8},{0xd00,128,33,16,3},{0xd00,128,33,16,3},{0x700,96,17,16,8},{0x700,96,10,16,7}};
 const Slice rumble[]={{0xd00,128,0,16,11},{0xd00,128,36,16,7},{0,112,18,16,11},{0,112,24,0,8},{0xd00,128,33,16,3},{0x700,96,17,16,8}};
 auto recipe=[&](const char*name,auto&& slices){auto row=pal_options_row_bitmap(asset,name);assert(row);unsigned at=0;
  for(const auto&part:slices){std::vector<uint8_t>src(asset.begin()+part.offset,asset.end());for(unsigned y=0;y<16;++y)for(unsigned x=0;x<part.width;++x)assert(pixel(row->pixels,128,at+x,y)==pixel(src,part.stride,part.x+x,part.y+y));at+=part.width;}
  assert(row->advance==at);for(unsigned y=0;y<16;++y)for(unsigned x=at;x<128;++x)assert(pixel(row->pixels,128,x,y)==0);return *row;};
 auto ctr=recipe("Controller type",controller);assert(ctr.pixels==pal_options_row_bitmap(asset,"Controller")->pixels&&ctr.advance==68);
 auto vib=recipe("Vibration",rumble);assert(vib.pixels==pal_options_row_bitmap(asset,"Rumble")->pixels&&vib.advance==48);
 const Slice player[]={{0x700,96,48,16,48}};assert(recipe("Player",player).advance==48);
 // New user labels must exist as distinct complete words in the row face.
 auto save=pal_options_row_bitmap(asset,"Save options");assert(save&&save->advance<=128);
 assert(save->pixels==pal_options_row_bitmap(asset,"Save")->pixels);
 assert(save->pixels!=pal_options_row_bitmap(asset,"Store")->pixels);
 auto limit=pal_options_row_bitmap(asset,"Framerate limit");assert(limit&&limit->advance<=128);
 // Independent same-face source proof for the new p and v crops.
 // Save: S(9),a(8),v(6),e(8),space(5),o(8),p(9).
 for(unsigned y=0;y<16;++y){for(unsigned x=0;x<6;++x){std::vector<uint8_t>tail(asset.begin()+0x2000,asset.end());assert(pixel(save->pixels,128,17+x,y)==pixel(tail,64,24+x,y));}
 for(unsigned x=0;x<9;++x){std::vector<uint8_t>tail(asset.begin()+0x2000,asset.end());assert(pixel(save->pixels,128,44+x,y)==pixel(tail,64,20+x,48+y));}}
 assert(asset==before);auto saved=a->pixels;asset[0]^=1;assert(!pal_options_row_bitmap(asset,"PC Settings"));assert(a->pixels==saved);asset=before;
 for(auto text:{"","Unproven body z","PC settings","Invented@font"})assert(!pal_options_row_bitmap(asset,text));assert(!pal_options_row_bitmap(std::span<const uint8_t>(asset).first(1024),"PC Settings"));
}
'''
class OriginalRowFontTests(unittest.TestCase):
 def test_exact_original_word_recomposition_and_pc_settings(self):
  self.assertTrue((ROOT/'src/runtime/pal_options_row_font.cpp').is_file(),'Missing exact original row-face composer')
  snapshot=ROOT/'.local/training-timing-01/options38-completed.rdram';rom=ROOT/'.local/inputs/pal-en-de/rom.z64';mb=ROOT/'.local/runtime-deps-build/librecomp/miniz'
  if not shutil.which('c++') or not snapshot.is_file() or not rom.is_file() or not (mb/'libminiz.a').is_file():self.skipTest('Original private PAL CPU fixtures/compiler required')
  ram=snapshot.read_bytes();asset=bytes(ram[(0x276940+i)^3]for i in range(0x2c00));self.assertEqual(hashlib.sha256(asset).hexdigest(),'5dbf56dd71d5c280fc0fad104003a23898312e4fd9468a76fd023db8d221a3e8')
  image=rom.read_bytes()
  for guest,offset,pin in [(0x3ef6c0,0x35e3e0,'b51101957be8c54798b3c72fa1ebe1abaa375a434b4c646f74f80ace37435c95'),(0x3ef6e0,0x353890,'18721d075d73e4c8a94d4d98473ca46fc3235d1c4697d359c63611e412da1c9d')]:
   self.assertEqual(bytes(ram[(guest+i)^3]for i in range(32)),image[offset:offset+32]);self.assertEqual(hashlib.sha256(image[offset:offset+32]).hexdigest(),pin)
  with tempfile.TemporaryDirectory()as temp:
   p=Path(temp);(p/'test.cpp').write_text(CODE);(p/'asset.bin').write_bytes(asset)
   q=subprocess.run(['c++','-std=c++20','-O1','-I'+str(ROOT/'src'),'-I'+str(ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz'),'-I'+str(mb),str(p/'test.cpp'),str(ROOT/'src/runtime/pal_options_row_font.cpp'),str(ROOT/'src/runtime/rom_image.cpp'),str(mb/'libminiz.a'),'-o',str(p/'test')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
   q=subprocess.run([str(p/'test'),str(p/'asset.bin')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
if __name__=='__main__':unittest.main()
