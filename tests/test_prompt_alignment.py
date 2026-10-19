"""Original work: djultra64. Actual original prompt geometry, no full game run."""
from pathlib import Path
import hashlib,struct,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
MINIZ=ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz'
BUILD=ROOT/'.local/runtime-deps-build/librecomp/miniz'
class PromptAlignmentTests(unittest.TestCase):
 def test_training_icons_keep_original_ink_band_and_text_gutter(self):
  snap=ROOT/'.local/ui-redesign-01/training-prep49-completed.rdram';asset=ROOT/'.local/team-visual-assets-01/asset_015.bin'
  if not all(p.exists()for p in [snap,asset,BUILD/'libminiz.a']):self.skipTest('Private original Training frame and decoded asset required')
  ram=bytearray(snap.read_bytes());original=asset.read_bytes()
  self.assertEqual(hashlib.sha256(original).hexdigest(),'2a00a6356e10fb53d1a6fa23c9061b3a3265edacb7aae393b47c60b1248f4c27')
  def read(p,n):return bytes(ram[((p+i)&0x7fffff)^3]for i in range(n))
  def word(p):return int.from_bytes(read(p,4),'big')
  bank=word(0x76b30);cases=[]
  for sprite,index,x in [(0x8013c9a4,5,42),(0x8013c9e0,6,95)]:
   d=word(sprite+20);self.assertEqual(d,bank+index*12);texture=word(d+8);palette=read(word(sprite+52),32)
   self.assertEqual(read(word(sprite+48),12),struct.pack('>BBBBhhHH',0x90,16,16,0,x,209,0,0))
   pixels=original[texture-0x80212700:][:128]
   for n,v in enumerate(pixels):ram[((texture+n)&0x7fffff)^3]=v
   cases.append((texture,palette,pixels,x))
  text_sprite=0x8013ca94;text_d=word(text_sprite+20);self.assertEqual(text_d,bank)
  tw,th,fmt,tt=struct.unpack('>HHII',read(text_d,12));self.assertEqual((tw,th,fmt),(128,32,0x03030000))
  text=original[tt-0x80212700:][:tw*th//2];text_bounds=[]
  for n,expected in enumerate([(0x10,32,16,0,55,209,0,0),(0x80,32,16,0,109,209,1024,0)]):
   segment=struct.unpack('>BBBBhhHH',read(word(text_sprite+48)+n*12,12));self.assertEqual(segment,expected)
   tag,width,height,pad,x,y,u,v=segment;u//=32;v//=32
   ink=[(x+xx,y+yy)for yy in range(height)for xx in range(width)if(text[((v+yy)*tw+u+xx)//2]>>(4 if(u+xx)%2==0 else 0))&15]
   text_bounds.append((min(x for x,y in ink),min(y for x,y in ink),max(x for x,y in ink),max(y for x,y in ink)))
  self.assertEqual(text_bounds,[(56,211,84,219),(109,211,140,219)])
  names=['80041B50','800419F8','800423FC','8004250C','80042D0C','80047558','80047500']
  code=r'''#include "runtime/prompt_textures.hpp"
#include "recomp.h"
#include <cstring>
#include <cassert>
#include <cstdlib>
extern "C" void do_break(uint32_t){std::abort();}
DECLARATIONS
extern "C" recomp_func_t* get_function(int32_t a){switch(uint32_t(a)){ROUTES default:assert(false);return nullptr;}}
#include <fstream>
#include <vector>
#include <cassert>
using namespace iss2000;
int main(int argc,char**argv){assert(argc==4);std::vector<uint8_t>m(0x800000);std::ifstream f(argv[1],std::ios::binary);f.read((char*)m.data(),m.size());assert(f);auto before=m;
 auto commands=[&](std::vector<uint8_t> image){auto*rdram=image.data();const uint32_t begin=0x800e0388;std::memcpy(rdram+0x9e0c8,&begin,4);
 for(uint32_t sprite:{0x8013c9a4u,0x8013c9e0u,0x8013ca94u}){recomp_context c{};c.r4=int32_t(sprite);c.r29=int32_t(0x807ff000);c.f_odd=&c.f0.u32h;func_80041B50_resident(rdram,&c);assert(c.r29==uint64_t(int64_t(int32_t(0x807ff000))));}
 uint32_t end;std::memcpy(&end,rdram+0x9e0c8,4);assert(end>begin&&end<0x800f0388);return std::vector<uint8_t>(image.begin()+(begin&0x7fffff),image.begin()+(end&0x7fffff));};
 const auto original_commands=commands(m);
 std::array<PromptGlyphRequest,2> ab{{{PromptGlyphFamily(unsigned(argv[3][0]-'0')),argv[3][0]=='2'?"Cross":"A"},{PromptGlyphFamily(unsigned(argv[3][0]-'0')),argv[3][0]=='2'?"Circle":"B"}}};
 std::array<PromptGlyphRequest,4> c{};prompt_detail::TextureGuard guard(pal_en_prompt_texture_layout());
 for(auto s:{0x8013c9a4u,0x8013c9e0u})assert(guard.prepare_sprite(m.data(),s,ab,c).status==PromptSpriteStatus::Applied);
 assert(commands(m)==original_commands);
 std::ofstream out(argv[2],std::ios::binary);out.write((char*)m.data(),m.size());out.close();guard.restore(m.data());assert(m==before);
}'''.replace('DECLARATIONS','\n'.join('extern \"C\" void func_'+n+'_resident(uint8_t*,recomp_context*);'for n in names)).replace('ROUTES',''.join('case0x'+n+':return func_'+n+'_resident;'for n in names).replace('case0x','case 0x'))
  with tempfile.TemporaryDirectory()as td:
   d=Path(td);(d/'test.cpp').write_text(code);(d/'input').write_bytes(ram)
   objects=[];include=ROOT/'.local/deps/N64Recomp/include'
   for name in names:
    obj=d/(name+'.o');source=ROOT/'.local/pal-map-bound-01/functions'/('func_'+name+'_resident.c')
    compiled=subprocess.run(['cc','-O1','-I'+str(include),'-c',str(source),'-o',str(obj)],capture_output=True,text=True);self.assertEqual(compiled.returncode,0,compiled.stderr);objects.append(str(obj))
   built=subprocess.run(['c++','-std=c++20','-O1','-Wall','-Wextra','-Werror','-pthread','-I'+str(ROOT/'src'),'-I'+str(MINIZ),'-I'+str(BUILD),str(d/'test.cpp'),str(ROOT/'src/runtime/prompt_textures.cpp'),str(ROOT/'src/runtime/rom_image.cpp'),str(BUILD/'libminiz.a'),'-I'+str(include),*objects,'-o',str(d/'test')],capture_output=True,text=True);self.assertEqual(built.returncode,0,built.stderr)
   for family in [1,2,3,4]:
    with self.subTest(family=family):
     run=subprocess.run([str(d/'test'),str(d/'input'),str(d/'output'),str(family)],capture_output=True,text=True);self.assertEqual(run.returncode,0,run.stderr)
     result=(d/'output').read_bytes();changed=set()
     for (texture,palette,pixels,x),text_ink in zip(cases,text_bounds):
      colors=struct.unpack('>16H',palette)
      def bounds(p):
       ink=[(i%16,i//16)for i in range(256)if colors[(p[i//2]>>(4 if i%2==0 else 0))&15]&1]
       return min(x for x,y in ink),min(y for x,y in ink),max(x for x,y in ink),max(y for x,y in ink)
      self.assertEqual(bounds(pixels),(0,0,11,11))
      out=bytes(result[((texture+n)&0x7fffff)^3]for n in range(128));b=bounds(out)
      self.assertLessEqual(b[2],11,'replacement enters the original right-hand text gutter')
      self.assertLessEqual(b[3],11,'replacement drops below the original icon ink band')
      self.assertLessEqual(abs(b[0]+b[2]-11),1);self.assertLessEqual(abs(b[1]+b[3]-11),1)
      # Actual original Enter and GoBack I4 segments start at x55/109;
      # first opaque columns are56/109. Both have visible rows211..219.
      text_first=text_ink[0]
      self.assertGreaterEqual(text_first-(x+b[2])-1,2)
      self.assertLessEqual(abs((209+(b[1]+b[3])/2)-(text_ink[1]+text_ink[3])/2),0.5)
      changed.update(((texture+n)&0x7fffff)^3 for n in range(128))
     self.assertTrue(all(a==b for n,(a,b)in enumerate(zip(ram,result))if n not in changed),'sprite geometry, palette, text and all other memory must remain exact')
