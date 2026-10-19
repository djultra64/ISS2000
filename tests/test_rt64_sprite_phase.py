"""Original project work: djultra64. Genuine SelectTraining DL and pinned RT64 viewport/sampling geometry."""
from pathlib import Path
import json,re,shutil,subprocess,tempfile,unittest
from tools.prepare_rt64_sprite_phase import derive,prepare
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'.local/deps/rt64/src/render/rt64_framebuffer_renderer.cpp'
class SpritePhaseTests(unittest.TestCase):
 def test_actual_training_rectangles_preserve_texel_phase_all_resolutions(self):
  snapshot=ROOT/'.local/ui-redesign-01/select-training49-completed.rdram'
  if not shutil.which('c++') or not SOURCE.is_file() or not snapshot.is_file() or not(ROOT/'.local/training-timing-01/free-training-high43-completed.rdram').is_file():self.skipTest('Private original PAL completed frame and compiler required')
  original=SOURCE.read_text();generated=derive(SOURCE.read_bytes()).decode()
  def function(text,name):return re.search(r'    (?:static )?(?:RenderViewport|bool) '+name+r'\(.*?\n    \}',text,re.S).group()
  sampler=(ROOT/'.local/deps/rt64/src/shaders/TextureSampler.hlsli').read_text()
  self.assertIn('static const float LowPrecision = 128.0f;',sampler)
  self.assertIn('uvCoord = round(uvCoord * LowPrecision) / LowPrecision;',sampler)
  self.assertIn('int2 texelBaseInt = floor(uvCoord);',sampler)
  self.assertIn('(masks - 1) - modulo(texelInt.x, masks)',sampler)
  math_source=(ROOT/'.local/deps/rt64/src/shaders/Math.hlsli').read_text()
  modulo=re.search(r'^int modulo\(.*?^}',math_source,re.S|re.M).group()
  precision=re.search(r'static const float LowPrecision = .*?;',sampler).group()
  quantize=re.search(r'uvCoord = round\(uvCoord \* LowPrecision\) / LowPrecision;',sampler).group().replace('round(','shader_round(')
  begin=sampler.index('    const int masks = round(');end=sampler.index('    const int maskt = round(',begin)
  mirror_source=sampler[begin:end]
  # Scalar x-axis adapter executes pinned shader expressions; HLSL round maps
  # to ties-to-even nearbyint. Pixel centers and RT64 half-pixel offset cancel.
  pinned_sampler=modulo+'\n'+precision+"""
static float shader_round(float value){return std::nearbyint(value);}
static int pinned_radar_point(float uvCoord){
 QUANTIZE
 struct{float x=1;}tcScale;
 struct{unsigned cms=G_TX_MIRROR;float masks=512;}rdpTile;
 struct{int x;}texelInt{int(floor(uvCoord))};
 SAMPLER_BODY
 return texelInt.x;
}
""".replace('QUANTIZE',quantize).replace('SAMPLER_BODY',mirror_source)
  common=(ROOT/'.local/deps/rt64/src/common/rt64_common.cpp').read_text()
  methods='\n'.join(re.search(r'    int32_t FixedRect::'+name+r'\(.*?\n    \}',common,re.S).group()for name in ['left','top','right','bottom','width','height'])
  code=r'''#include <cassert>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <cstdio>
#include <vector>
#include <algorithm>
#define F3DEX_GBI_2
#include "rt64_extended_gbi.h"
#include "shared/rt64_f3d_defines.h"
namespace hlslpp{struct float2{float x,y;float operator[](int i)const{return i?y:x;}};}
struct RenderViewport{float x,y,width,height;};
struct FixedRect {int ulx,uly,lrx,lry;bool isNull()const{return false;}
 int32_t left(bool)const;int32_t top(bool)const;int32_t right(bool)const;int32_t bottom(bool)const;int32_t width(bool,bool)const;int32_t height(bool,bool)const;};
''' + methods+'\n'+function(original,'convertViewportRect')+'\n'+function(generated,'iss2000_native_sprite_phase')+'\n'+function(generated,'iss2000_intro_canvas_phase')+'\n'+function(generated,'iss2000_high_sprite_scale')+'\n'+(function(generated,'iss2000_high_sprite_edge') if 'iss2000_high_sprite_edge(' in generated else 'static bool iss2000_high_sprite_edge(int32_t,int16_t,int16_t,FixedRect){return false;}')+'\n'+function(generated,'iss2000_interpolate_sprite_viewport')+'\n'+function(generated,'iss2000_sprite_viewport_rect')+'\n'+pinned_sampler+r'''
int main(int argc,char**argv){assert(argc==3);FILE*f=fopen(argv[1],"rb");assert(f);std::vector<uint8_t>r(0x800000);assert(fread(r.data(),1,r.size(),f)==r.size());fclose(f);auto word=[&](uint32_t a){uint32_t v;memcpy(&v,r.data()+(a&0x7fffff),4);return v;};
 struct Piece{FixedRect rect;int u,v,ds,dt;};std::vector<Piece>pieces;uint32_t texture=0;
 for(unsigned p=word(0x800a4aa4)+8;p<word(0x8009e0c8);p+=8){auto a=word(p),b=word(p+4);if(a>>24==0xfd)texture=b&0x7fffff;if(a>>24!=0xe4)continue;if(texture==0x279600&&(b&4095)<=130*4&&(b&4095)>=73*4&&((b&4095)-73*4)%(19*4)==0){assert(word(p+8)==0xe1000000&&word(p+16)==0xf1000000);auto uv=word(p+12),step=word(p+20);pieces.push_back({{int(b>>12&4095),int(b&4095),int(a>>12&4095),int(a&4095)},int16_t(uv>>16),int16_t(uv),int16_t(step>>16),int16_t(step)});}p+=16;}
 assert(pieces.size()==76); // four genuine original background bars,19pieces each
 unsigned bad_before=0,bad_after=0,checks=0;
 auto sample=[](float origin,float length,float pos,float uv,float extent){return uv+(pos-origin)*extent/length;};
 for(unsigned height:{720u,900u,1080u,1440u,1800u,2160u})for(bool wide:{false,true}){
  hlslpp::float2 scale{height*(wide?16.f/9:4.f/3)/320,height/232.f};const float aspect=wide?.75f:1.f;
  for(const auto&p:pieces){auto old=convertViewportRect(p.rect,scale,320,aspect,1,0,G_EX_ORIGIN_NONE,G_EX_ORIGIN_NONE);auto now=iss2000_sprite_viewport_rect(p.rect,scale,320,aspect,1,0,G_EX_ORIGIN_NONE,G_EX_ORIGIN_NONE,true);
   const float ideal_x=(160+(p.rect.left(true)-160)*aspect)*scale.x,ideal_y=p.rect.top(true)*scale.y;
   const float sx=scale.x*aspect,sy=scale.y;assert(fabs(now.x-ideal_x)<.001&&fabs(now.y-ideal_y)<.001);
   for(bool vertical:{false,true}){const float uv=(vertical?p.v:p.u)/32.f,extent=vertical?p.rect.height(true,true):p.rect.width(true,true);const float deriv=(vertical?p.dt:p.ds)/1024.f;const float origin=vertical?now.y:now.x,rate=vertical?sy:sx;const float len=extent*rate;
    for(int pixel=int(ceil(origin));pixel<int(ceil(origin+len));++pixel){auto expected=uv+(pixel-origin)/rate*deriv;auto before=sample(vertical?old.y:old.x,vertical?old.height:old.width,pixel,uv,extent*deriv);auto after=sample(origin,vertical?now.height:now.width,pixel,uv,extent*deriv);
     bad_before+=int(floor(before+.0001f))!=int(floor(expected+.0001f));bad_after+=int(floor(after+.0001f))!=int(floor(expected+.0001f));++checks;
    }
   }
  }
 }
 assert(bad_before>500&&bad_after==0&&checks>10000);printf("Actual original bar samples:%u, phase mismatches original:%u corrected:%u\n",checks,bad_before,bad_after);

 // The actual fractional renderer consumes paired previous/current viewports.
 // Endpoint branches retain exact source endpoints; intermediate bounds differ.
 {auto a=iss2000_sprite_viewport_rect({100,200,300,400},{4.2f,3.8f},320,.75f,1,0,G_EX_ORIGIN_NONE,G_EX_ORIGIN_NONE,true);auto b=iss2000_sprite_viewport_rect({132,208,332,408},{4.2f,3.8f},320,.75f,1,0,G_EX_ORIGIN_NONE,G_EX_ORIGIN_NONE,true);float last=-1;for(float weight:{0.f,.25f,.5f,.75f,1.f}){auto v=iss2000_interpolate_sprite_viewport(a,b,weight);assert(v.x>last);last=v.x;assert(fabs(v.x-(a.x+(b.x-a.x)*weight))<.001f);}auto z=iss2000_interpolate_sprite_viewport(a,b,0),one=iss2000_interpolate_sprite_viewport(a,b,1);assert(!memcmp(&a,&z,sizeof a)&&!memcmp(&b,&one,sizeof b));}
 // Genuine direct-CI8 white side canvases must touch the fractional center
 // without gaps OR double-alpha overlaps at any scale/aspect/device width.
 for(unsigned height:{720u,900u,1080u,1440u,1800u,2160u})for(float adjustment:{.75f,.777f}){
  hlslpp::float2 scale{height/232.f*4.f/3.f,height/232.f};
  auto center=iss2000_sprite_viewport_rect({0,0,1280,960},scale,320,adjustment,1,0,G_EX_ORIGIN_NONE,G_EX_ORIGIN_NONE,true);
  assert(iss2000_intro_canvas_phase(true,G_CYC_1CYCLE,G_TF_POINT,G_EX_ASPECT_ADJUST,0,0,-4,0,0,960,G_EX_ORIGIN_LEFT,G_EX_ORIGIN_NONE));
  assert(iss2000_intro_canvas_phase(true,G_CYC_1CYCLE,G_TF_POINT,G_EX_ASPECT_ADJUST,0,0,1280,0,1284,960,G_EX_ORIGIN_NONE,G_EX_ORIGIN_RIGHT));
  auto left=iss2000_sprite_viewport_rect({-4,0,0,960},scale,320,adjustment,1,0,G_EX_ORIGIN_LEFT,G_EX_ORIGIN_NONE,false,true);
  auto right=iss2000_sprite_viewport_rect({1280,0,1284,960},scale,320,adjustment,1,0,G_EX_ORIGIN_NONE,G_EX_ORIGIN_RIGHT,false,true);
  assert(fabs(left.x+left.width-center.x)<.001f&&fabs(right.x-center.x-center.width)<.001f);
  for(unsigned n=0;n<6;++n)assert(!iss2000_intro_canvas_phase(n!=0,n==1?G_CYC_COPY:G_CYC_1CYCLE,n==2?G_TF_BILERP:G_TF_POINT,n==3?G_EX_ASPECT_AUTO:G_EX_ASPECT_ADJUST,n==4?1024:0,0,-4,0,0,960,n==5?G_EX_ORIGIN_NONE:G_EX_ORIGIN_LEFT,G_EX_ORIGIN_NONE));
 }
 // The real14 High radar segments each include a512/512 body, a1024/512
 // one-pixel right repair, and a512/1024 bottom repair. Excluding these edge
 // strips gives them a different viewport phase at fractional output scales.
 assert(argc==3);f=fopen(argv[2],"rb");assert(f);assert(fread(r.data(),1,r.size(),f)==r.size());fclose(f);std::vector<Piece>radar;
 for(unsigned pc=0x800d1ea8;pc<0x800d2300;pc+=8){auto a=word(pc),b=word(pc+4);if(a>>24!=0xe4)continue;auto uv=word(pc+12),step=word(pc+20);assert(word(pc+8)==0xe1000000&&word(pc+16)==0xf1000000);if(step==0x02000200||step==0x04000200||step==0x02000400)radar.push_back({{int(b>>12&4095),int(b&4095),int(a>>12&4095),int(a&4095)},int16_t(uv>>16),int16_t(uv),int16_t(step>>16),int16_t(step)});pc+=16;}
 assert(radar.size()==42);assert(word(0x800d1e98)==0xf5400800&&word(0x800d1e9c)==0x00f64190);unsigned radar_before=0,radar_after=0,mirrored=0;auto mirror=[](float value){return pinned_radar_point(value);};
 for(unsigned height:{720u,900u,1080u,1440u,1800u,2160u})for(bool wide:{false,true}){hlslpp::float2 scale{height*(wide?16.f/9:4.f/3)/640,height/524.f};float aspect=wide?.75f:1.f;
  for(auto&p:radar){const bool eligible=iss2000_high_sprite_scale(640,p.ds,p.dt)||iss2000_high_sprite_edge(640,p.ds,p.dt,p.rect);if(p.u==0x7d00||p.u==0x7fd8)++mirrored;auto before=convertViewportRect(p.rect,scale,640,aspect,1,0,G_EX_ORIGIN_NONE,G_EX_ORIGIN_NONE);auto now=iss2000_sprite_viewport_rect(p.rect,scale,640,aspect,1,0,G_EX_ORIGIN_NONE,G_EX_ORIGIN_NONE,eligible);
   for(bool vertical:{false,true}){float origin=vertical?now.y:now.x,rate=vertical?scale.y:scale.x*aspect,length=vertical?now.height:now.width,uv=(vertical?p.v:p.u)/32.f,deriv=(vertical?p.dt:p.ds)/1024.f,extent=(vertical?p.rect.height(true,true):p.rect.width(true,true))*deriv;
    for(int pixel=int(ceil(origin));pixel<int(ceil(origin+length));++pixel){float ideal_origin=(vertical?p.rect.top(true):(320+(p.rect.left(true)-320)*aspect))*(vertical?scale.y:scale.x);float expected=uv+(pixel-ideal_origin)/rate*deriv,old=sample(vertical?before.y:before.x,vertical?before.height:before.width,pixel,uv,extent),after=sample(origin,length,pixel,uv,extent);radar_before+=mirror(old)!=mirror(expected);radar_after+=mirror(after)!=mirror(expected);}
   }
  }
 }assert(mirrored>=4&&radar_before>20&&radar_after==0);printf("Actual14 High radar pieces plus28 edge strips, POINT128 mirror mismatches original:%u corrected:%u\n",radar_before,radar_after);
 // Only the exact aligned one-native-pixel original repair geometry qualifies.
 assert(iss2000_high_sprite_edge(640,1024,512,{1280,1360,1284,1808}));
 assert(iss2000_high_sprite_edge(640,512,1024,{960,1808,1280,1812}));
 for(unsigned variant=0;variant<9;++variant){auto rect=FixedRect{1280,1360,1284,1808};int width=640,ds=1024,dt=512;
  if(variant==0)width=320;if(variant==1)ds=512;if(variant==2)dt=1024;if(variant==3)rect.lrx+=4;
  if(variant==4){++rect.ulx;++rect.lrx;}if(variant==5)++rect.uly;if(variant==6)rect.lry=rect.uly;if(variant==7)ds=-1024;if(variant==8)dt=-512;
  assert(!iss2000_high_sprite_edge(width,ds,dt,rect));}
 for(unsigned n=0;n<6;++n)assert(!iss2000_high_sprite_scale(n==0?320:640,n==1?1024:n==2?0:512,n==3?1024:n==4?0:n==5?-1024:512));
 // Guard excludes originalsized/nonupscaled,foreignorigin/tilecopy,scaled,
 // bilinear,COPY,2cycle/fill and3Dcaller paths (only rectanglecallsite changes).
 assert(iss2000_native_sprite_phase(true,false,true,true,G_CYC_1CYCLE,G_TF_POINT));
 for(unsigned n=0;n<8;++n)assert(!iss2000_native_sprite_phase(n!=0,n==1,n!=2,n!=3,n==4?G_CYC_COPY:n==6?G_CYC_2CYCLE:n==7?G_CYC_FILL:G_CYC_1CYCLE,n==5?G_TF_BILERP:G_TF_POINT));
 for(auto p:pieces){auto old=convertViewportRect(p.rect,{1,1},320,1,1,0,G_EX_ORIGIN_NONE,G_EX_ORIGIN_NONE);auto now=iss2000_sprite_viewport_rect(p.rect,{1,1},320,1,1,0,G_EX_ORIGIN_NONE,G_EX_ORIGIN_NONE,true);assert(!memcmp(&old,&now,sizeof old));auto inactive=iss2000_sprite_viewport_rect(p.rect,{4.2f,3.8f},320,.75f,1,0,G_EX_ORIGIN_NONE,G_EX_ORIGIN_NONE,false);auto normal=convertViewportRect(p.rect,{4.2f,3.8f},320,.75f,1,0,G_EX_ORIGIN_NONE,G_EX_ORIGIN_NONE);assert(!memcmp(&inactive,&normal,sizeof normal));for(bool active:{false,true}){auto rejected=iss2000_sprite_viewport_rect(p.rect,{4.2f,3.8f},320,.75f,1,0,G_EX_ORIGIN_LEFT,G_EX_ORIGIN_LEFT,active);auto previous=convertViewportRect(p.rect,{4.2f,3.8f},320,.75f,1,0,G_EX_ORIGIN_LEFT,G_EX_ORIGIN_LEFT);assert(!memcmp(&rejected,&previous,sizeof previous));}}
}
'''
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);(p/'test.cpp').write_bytes(code.encode());q=subprocess.run(['c++','-std=c++20','-O1','-I'+str(ROOT/'.local/deps/rt64/include'),'-I'+str(ROOT/'.local/deps/rt64/src'),str(p/'test.cpp'),'-o',str(p/'test')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
   q=subprocess.run([str(p/'test'),str(snapshot),str(ROOT/'.local/training-timing-01/free-training-high43-completed.rdram')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr);print(q.stdout.strip())
 def test_exact_source_pin_and_immutable_output(self):
  if not SOURCE.is_file():self.skipTest('Pinned private RT64 dependency required')
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);receipt=prepare(SOURCE,p/'out');self.assertEqual(prepare(SOURCE,p/'out'),receipt);output=p/'out/rt64_framebuffer_renderer.cpp';self.assertNotIn(b'\r',output.read_bytes());output.write_bytes(output.read_bytes()+b'\n')
   with self.assertRaises(ValueError):prepare(SOURCE,p/'out')
   with self.assertRaises(ValueError):derive(SOURCE.read_bytes()+b'\n')
