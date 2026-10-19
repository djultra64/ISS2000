"""Original work: djultra64. Genuine radar cells and pinned POINT quantization."""
from pathlib import Path
import re,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class RadarSamplingTests(unittest.TestCase):
 def test_marker_cells_do_not_sample_neighbor_at_any_supported_output_scale(self):
  fixture=ROOT/'.local/training-timing-01/free-training-high43-completed.rdram'
  if not fixture.is_file():self.skipTest('Private original radar snapshot required')
  shader=(ROOT/'.local/deps/rt64/src/shaders/TextureSampler.hlsli').read_text()
  self.assertIn('static const float LowPrecision = 128.0f;',shader)
  self.assertIn('uvCoord = round(uvCoord * LowPrecision) / LowPrecision;',shader)
  self.assertIn('int2 texelBaseInt = floor(uvCoord);',shader)
  code=r'''#include "runtime/pal_hud_widescreen.hpp"
#include <vector>
#include <cstdio>
#include <cassert>
#include <cstring>
#include <cmath>
uint32_t w(const std::vector<uint8_t>&r,uint32_t a){uint32_t v;memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
void put(std::vector<uint8_t>&r,uint32_t a,uint32_t v){memcpy(r.data()+(a&0x7fffff),&v,4);}
int main(int argc,char**argv){assert(argc==2);std::vector<uint8_t>base(0x800000);auto*f=fopen(argv[1],"rb");assert(f&&fread(base.data(),1,base.size(),f)==base.size());fclose(f);
 const auto start=w(base,w(base,0x802b2950)+0x24),end=w(base,0x802b4400);uint32_t marker=0;
 for(auto pc=start;pc<end;pc+=8)if(w(base,pc)>>24==0xe4){marker=pc;break;}assert(marker);
 unsigned before=0,after=0;auto quant=[](float u){return int(floor(std::nearbyint(u*128.f)/128.f));};
 for(unsigned h:{720u,900u,1080u,1440u,1800u,2160u})for(unsigned x=0;x<624;x+=2){
  auto r=base;put(r,marker,0xe4000000u|((x+16)*4<<12)|(356*4));put(r,marker+4,(x*4<<12)|(340*4));put(r,marker+12,24*32u<<16);put(r,marker+20,0x02000200);put(r,0x802b4400,marker+24);
  assert(iss2000::align_pal_radar_marker(r,true,marker));
  const float u1=float(w(r,marker+12)>>16)/32.f;const int ds=w(r,marker+20)>>16;
  // Same source endpoint expression as pinned RDP::drawTexRect.
  const int uls=int(w(r,marker+12)>>16),uvWidth=16*4;
  const int lrs=((uls<<7)+ds*uvWidth)>>7;const float span=lrs/32.f-u1;
  assert(u1>24&&u1+span<32);
  for(unsigned k=0;k<16;++k)assert(quant(u1+span*k/16.f)==24+int(k/2)); // Native High footprint unchanged.
  for(unsigned k=0;k<8;++k)assert(quant(u1+span*k/8.f)==24+int(k)); // Native Low footprint unchanged.
  const float rate=h/524.f,origin=h*(16.f/9.f)/2.f+(int(x)-320)*rate;
  for(int px=int(ceil(origin));px<int(ceil(origin+16*rate));++px){float fraction=(px-origin)/(16*rate);
   before+=quant(24.f+8*fraction)>=32;after+=quant(u1+span*fraction)>=32||quant(u1+span*fraction)<24;
  }
 }
 assert(before>10&&after==0);printf("Atlas-neighbor samples before:%u after:%u\n",before,after);
 auto bad=base;put(bad,0x802b4400,marker+24);put(bad,marker+12,0x03010000);auto unchanged=bad;assert(!iss2000::align_pal_radar_marker(bad,true,marker)&&bad==unchanged);
}
'''
  with tempfile.TemporaryDirectory()as directory:
   p=Path(directory);(p/'test.cpp').write_text(code)
   cmd=['c++','-std=c++20','-O1','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-I'+str(ROOT/'src'),'-I'+str(ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz'),'-I'+str(ROOT/'.local/runtime-deps-build/librecomp/miniz'),str(p/'test.cpp'),*[str(ROOT/'src/runtime'/x)for x in('pal_hud_widescreen.cpp','pal_sky_widescreen.cpp','rom_image.cpp')],'-o',str(p/'test')]
   q=subprocess.run(cmd,capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr);q=subprocess.run([str(p/'test'),str(fixture)],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr);print(q.stdout.strip())
