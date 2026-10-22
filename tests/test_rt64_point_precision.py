"""Point sprites must not sample the following atlas cell at enhanced scales.

Original project work: djultra64. CPU characterization of the shader boundary;
actual GPU captures are required independently.
"""
from pathlib import Path
import hashlib, re, shutil, subprocess, tempfile, unittest
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'.local/deps/rt64/src/shaders/TextureSampler.hlsli'

@unittest.skipUnless(SOURCE.is_file() and shutil.which('c++'), 'Pinned RT64 shader and compiler required')
class PointPrecisionTests(unittest.TestCase):
 def test_magnified_point_rectangles_do_not_round_into_adjacent_texels(self):
  raw=SOURCE.read_bytes()
  self.assertEqual(hashlib.sha256(raw).hexdigest(),'927ca2d1c748862f683b3d6115bc97a56cc2ff343474a641046a64788fecef3a')
  try:
   from tools.prepare_rt64_point_precision import derive
  except ModuleNotFoundError:
   shader=raw.decode()
  else:
   shader=derive(raw).decode()
  body=re.search(r'#if SIMULATE_LOW_PRECISION\n(.*?)\n#endif',shader,re.S).group(1)
  code=r'''#include <cassert>
#include <cmath>
#include <initializer_list>
using std::abs;
struct V {float x,y;};
V operator*(V a,float b){return {a.x*b,a.y*b};}
V operator/(V a,float b){return {a.x/b,a.y/b};}
V round(V a){return {std::nearbyint(a.x),std::nearbyint(a.y)};}
V floor(V a){return {std::floor(a.x),std::floor(a.y)};}
constexpr unsigned G_TF_POINT=0,G_CYC_1CYCLE=0;
struct Mode{unsigned filter,cycle;unsigned textFilt()const{return filter;}unsigned cycleType()const{return cycle;}};
struct Flags{bool rect,upscale,linear;};
bool renderFlagRect(Flags f){return f.rect;}
bool renderFlagUpscale2D(Flags f){return f.upscale;}
bool renderFlagLinearFiltering(Flags f){return f.linear;}
bool gpuTileFlagHighRes(unsigned f){return f!=0;}
V quantize(V uvCoord,Flags renderFlags={true,true,false},Mode otherMode={0,0},float dx=.1074074f,float dy=.1074074f,unsigned high=0){
 struct{unsigned flags;}gpuTile{high};V ddxUV{dx,0},ddyUV{0,dy};
 constexpr float LowPrecision=128.f;
 BODY
 return uvCoord;
}
int main(){
 // Authentic Stadium Select tile ends at native x115. In 4K its final
 // covered sample is U31.996296: column31, not the following atlas cell32.
 V q=quantize({31.996296f,15.996296f});
 assert(std::floor(q.x)==31 && std::floor(q.y)==15);
 q=quantize({31.888889f,15.888889f});assert(std::floor(q.x)==31 && std::floor(q.y)==15);
 // Interior boundaries, negative/mirrored coordinates and integer originals.
 for(float x:{-.003f,.003f,.997f,1.f,15.f,15.997f,31.f,31.997f}){
  q=quantize({x,x});assert(std::floor(q.x)==std::floor(x));
 }
 // 3D, original grid, smoothing, COPY and replacement coordinates retain
 // the pinned interpolation rounding exactly.
 for(int n=0;n<7;++n){Flags f{n!=0,n!=1,n==2};Mode m{n==3?2u:0u,n==4?2u:0u};
  float dx=n==5?1.f:.1f;unsigned high=n==6?1:0;
  q=quantize({31.997f,2.997f},f,m,dx,dx,high);
  if(high){assert(q.x==31.997f && q.y==2.997f);}else{assert(q.x==32.f && q.y==3.f);}
 }
}
'''.replace('BODY',body)
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);(p/'test.cpp').write_text(code)
   q=subprocess.run(['c++','-std=c++20',str(p/'test.cpp'),'-o',str(p/'test')],capture_output=True,text=True)
   self.assertEqual(q.returncode,0,q.stderr)
   q=subprocess.run([str(p/'test')],capture_output=True,text=True)
   self.assertEqual(q.returncode,0,q.stderr)

 def test_private_shader_sources_reject_tampering_and_changed_outputs(self):
  import tools.prepare_rt64_point_precision as module
  prepare=getattr(module,'prepare',None)
  self.assertIsNotNone(prepare, 'Private shader staging must verify its source and output bytes')
  source=SOURCE.parent.parent
  with tempfile.TemporaryDirectory()as directory:
   p=Path(directory);receipt=prepare(source,p/'out')
   self.assertEqual(prepare(source,p/'out'),receipt)
   self.assertEqual((p/'out/rt64_raster_shader.cpp').read_bytes(),(source/'render/rt64_raster_shader.cpp').read_bytes())
   target=p/'out/shaders/TextureSampler.hlsli';target.write_bytes(target.read_bytes()+b'\n')
   with self.assertRaises(ValueError):prepare(source,p/'out')
   for name in ('shaders/TextureSampler.hlsli','shaders/RasterPS.hlsl','render/rt64_raster_shader.cpp'):
    q=p/'input'/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((source/name).read_bytes())
   q=p/'input/shaders/RasterPS.hlsl';q.write_bytes(q.read_bytes()+b'\n')
   with self.assertRaises(ValueError):prepare(p/'input',p/'changed')
   self.assertFalse((p/'changed').exists())
