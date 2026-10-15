"""Original project work: djultra64. CPU geometry characterization; no GPU/game execution."""
from pathlib import Path
import os
import shlex
import shutil
import subprocess
import tempfile
import unittest
from tools.prepare_rt64_vi import prepare
ROOT=Path(__file__).resolve().parents[1]
RT64=ROOT/'.local/deps/rt64/src'
SDL_CONFIG=os.environ.get('ISS2000_SDL_CONFIG',shutil.which('sdl2-config') or '/home/linuxbrew/.linuxbrew/bin/sdl2-config')
SOURCE=r'''
#include "render/rt64_vi_renderer.h"
#include "render/rt64_render_target.h"
#include "runtime/graphics_settings.hpp"
#include <iostream>
#include <cassert>
#include <cmath>
using namespace RT64;
struct Dimensions final:plume::RenderSwapChain{
 uint32_t w=1920,h=1080;
 bool present(uint32_t,plume::RenderCommandSemaphore**,uint32_t)override{return false;}
 void wait()override{}bool resize()override{return false;}bool needsResize()const override{return false;}
 void setVsyncEnabled(bool)override{}bool isVsyncEnabled()const override{return true;}
 uint32_t getWidth()const override{return w;}uint32_t getHeight()const override{return h;}
 plume::RenderTexture* getTexture(uint32_t)override{return nullptr;}uint32_t getTextureCount()const override{return 0;}
 bool acquireTexture(plume::RenderCommandSemaphore*,uint32_t*)override{return false;}
 plume::RenderWindow getWindow()const override{return {};}
 bool isEmpty()const override{return false;}uint32_t getRefreshRate()const override{return 60;}
};
int main(){
 VI vi{};vi.status.word=0x13012;vi.origin=0x27D899;vi.width=320;vi.vSync=625;vi.hRegion.word=0x8802F7;vi.vRegion.word=0x43024C;vi.xTransform.word=0x1EB;vi.yTransform.word=0x386;
 auto native=vi.fbSize();std::cout<<"native "<<native.x<<"x"<<native.y<<"\n";

 assert(native.x==320 && native.y==232);
 struct Setting{iss2000::RenderResolution option;uint32_t w,h,allocation_h;};
 const Setting settings[]{
  {iss2000::RenderResolution::P720,1280,720,745},
  {iss2000::RenderResolution::P900,1600,900,931},
  {iss2000::RenderResolution::P1080,1920,1080,1117},
  {iss2000::RenderResolution::P1440,2560,1440,1490},
  {iss2000::RenderResolution::P1800,3200,1800,1862},
  {iss2000::RenderResolution::P2160,3840,2160,2234}};
 for(const auto& setting:settings){
  iss2000::GraphicsSettings profile;profile.resolution=setting.option;
  float y=iss2000::resolution_multiplier(profile,native.y),x=y*(16.f/9.f)/(float(native.x)/uint32_t(native.y));
  auto scale=RenderTarget::computeFixedResolutionScale(320,{x,y});
  uint32_t width,height,alignment;RenderTarget::computeScaledSize(320,240,scale,width,height,alignment);
  assert(width==setting.w && height==setting.allocation_h);
  Dimensions output;output.w=setting.w;output.h=setting.h;
  plume::RenderViewport viewport;plume::RenderRect scissor;
  VIRenderer::getViewportAndScissor(&output,vi,scale,1,true,viewport,scissor);
  assert(std::fabs(viewport.x)<0.001 && std::fabs(viewport.y)<0.001);
  assert(std::fabs(viewport.width-setting.w)<0.001 && std::fabs(viewport.height-setting.h)<0.001);
  assert(scissor.left==0 && scissor.top==0 && scissor.right==int32_t(setting.w) && scissor.bottom==int32_t(setting.h));
  auto video=hlslpp::float2(native)*scale;
  assert(std::fabs(float(video.x)-setting.w)<0.001 && std::fabs(float(video.y)-setting.h)<0.001);
  std::cout<<"allocation "<<width<<"x"<<height<<" video "<<float(video.x)<<"x"<<float(video.y)<<" viewport "<<viewport.x<<","<<viewport.y<<","<<viewport.width<<","<<viewport.height<<" scissor "<<scissor.left<<","<<scissor.top<<","<<scissor.right<<","<<scissor.bottom<<"\n";
 }
 assert(vi.origin==0x27D899 && vi.vRegion.word==0x43024C && vi.yTransform.word==0x386);
}

'''
@unittest.skipUnless(shutil.which('c++') and Path(SDL_CONFIG).is_file() and (RT64/'render/rt64_vi_renderer.cpp').is_file(),
                     'Compiler, SDL development config and pinned RT64 required')
class PalViGeometryTests(unittest.TestCase):
 def test_pal_visible_resolution_and_crop_remain_exact_when_texture_has_extra_rows(self):
  # Uses the actual engine CPU methods. The swapchain fixture supplies dimensions
  # only; this neither creates a graphics device nor measures rendered output.
  with tempfile.TemporaryDirectory() as directory:
   folder=Path(directory);(folder/'test.cpp').write_text(SOURCE)
   prepare(RT64/'hle/rt64_vi.cpp',folder/'adapted')
   args=['c++','-std=c++20','-O1','-ffunction-sections','-fdata-sections',
    '-DHLSL_CPU','-DFFX_GCC','-DPLUME_SDL_VULKAN_ENABLED','-DRT64_SDL_WINDOW_VULKAN',
    '-I'+str(ROOT/'src'),'-I'+str(ROOT/'.local/deps/N64ModernRuntime/thirdparty')]
   for path in [RT64,RT64/'contrib',RT64/'contrib/plume',RT64/'contrib/hlslpp/include',RT64/'hle']:
    args+=['-isystem',str(path)]
   args+=shlex.split(subprocess.run([SDL_CONFIG,'--cflags'],check=True,capture_output=True,text=True).stdout)
   args += [str(folder/'test.cpp'),str(folder/'adapted/rt64_vi.cpp'),
    str(ROOT/'src/runtime/vi_framebuffer.cpp'),str(ROOT/'src/runtime/graphics_settings.cpp'),
    str(RT64/'render/rt64_vi_renderer.cpp'),str(RT64/'render/rt64_render_target.cpp'),
    '-Wl,--gc-sections','-o',str(folder/'test')]
   compiled=subprocess.run(args,capture_output=True,text=True)
   self.assertEqual(compiled.returncode,0,compiled.stderr)
   result=subprocess.run([str(folder/'test')],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
