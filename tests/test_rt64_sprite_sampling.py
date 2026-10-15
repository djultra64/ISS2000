"""Exercise the actual pinned RT64 sampling expressions at a PAL strip boundary.

Original project work: djultra64. CPU-only; no ROM, assets or game execution.
"""
from pathlib import Path
import hashlib
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
RT64 = ROOT / '.local/deps/rt64/src'

@unittest.skipUnless(shutil.which('c++') and (RT64/'shaders/RasterPS.hlsl').is_file(),
                     'Compiler and pinned RT64 source required')
class SpriteSamplingTests(unittest.TestCase):
    def test_fractional_pal_scale_keeps_each_original_strip_at_its_own_texel_origin(self):
        shader = (RT64/'shaders/RasterPS.hlsl').read_bytes()
        self.assertEqual(hashlib.sha256(shader).hexdigest(),
            '957b283411550457573421015580f84ca750c68a050981dbc1a4fe2634507820')
        # Compile the actual upstream fragment adjustment, flag policy and
        # identity-scale predicate. A private dependency update requires review.
        adjustment = re.search(r'    if \(!renderFlagUpscale2D\(rp.flags\)\) \{.*?\n    \}',
                               shader.decode(), re.S).group()
        flag = re.search(r'    bool renderFlagUpscale2D\(uint flags\) \{.*?\n    \}',
                         (RT64/'shared/rt64_render_flags.h').read_text(), re.S).group()
        state = (RT64/'hle/rt64_state.cpp').read_text()
        policy = re.search(r'const bool forcedUpscale2D = .*?flags.upscale2D = .*?;', state, re.S).group()
        identity = re.search(r'bool DrawCall::identityRectScale\(\) const \{(.*?)\n    \}',
                            (RT64/'hle/rt64_draw_call.cpp').read_text(), re.S).group(1)
        renderer = (ROOT/'src/renderer.cpp').read_text()
        # With the old integration no assignment exists, so the real upstream
        # default ScaledOnly is used. This is the intentional fail-first case.
        assignments = re.findall(r'\bu\.upscale2D\s*=\s*[^;]+;', renderer)
        self.assertLessEqual(len(assignments), 1)
        configure = assignments[0] if assignments else ''
        code = r'''
#include <cassert>
#include <cmath>
#include <hlsl++.h>
#include "common/rt64_user_configuration.h"
using namespace hlslpp;
using RT64::UserConfiguration;
using uint=unsigned;
''' + flag + r'''
struct Config { RT64::UserConfiguration::Upscale2D upscale2D=RT64::UserConfiguration::Upscale2D::ScaledOnly; };
Config configured(){Config u;
''' + configure + r'''
return u;}
struct Call {
 struct { bool forceUpscale2D=false; } extendedFlags;
 short rectDsdx=1024,rectDtdy=1024;
 bool identityRectScale() const {
''' + identity + r'''
 }
};
bool flagFor(RT64::UserConfiguration::Upscale2D upscale2D, short dx=1024,short dy=1024){
 struct { unsigned rect=1; bool upscale2D=false; } flags;
 Call callDesc; callDesc.rectDsdx=dx;callDesc.rectDtdy=dy;
''' + policy + r'''
 return flags.upscale2D;
}
float2 sampleOrigin(bool upscale,float scale,int originalY,int originalHeight){
 float top=std::round(originalY*scale),bottom=std::round((originalY+originalHeight)*scale);
 float2 vertexUV(0,0), ddxVertexUV(1/scale,0), ddyVertexUV(0,float(originalHeight)/(bottom-top));
 float4 vertexPosition(0.5f,top+0.5f,0,1);
 struct {uint flags;} rp{upscale?(1u<<27):0u};
 struct {float2 resolutionScale;float horizontalMisalignment;} FbParams{float2(scale,scale),0};
 float2 lowResUV=vertexUV;
''' + adjustment + r'''
 return lowResUV;
}
int main(){
 using Mode=RT64::UserConfiguration::Upscale2D;
 const auto selected=configured().upscale2D;
 // Original PAL paused P1 glyph command800D3888 starts at y33, height8.
 // With a 1080/296 scale the default shader shifts it almost one row back.
 const float oldV=sampleOrigin(flagFor(Mode::ScaledOnly),1080.0f/296,33,8).y;
 assert(oldV < -0.86f && oldV > -0.87f);
 const float fixedV=sampleOrigin(flagFor(selected),1080.0f/296,33,8).y;
 assert(std::abs(fixedV)<1.e-6f);
 for(auto height:{720,900,1080,1440,1800,2160}){
  for(auto y:{29,45,48,72,104,209}){
   const float v=sampleOrigin(flagFor(selected),float(height)/296,y,16).y;
   assert(std::abs(v)<1.e-6f);
  }
 }
 // At original resolution the supported All option leaves texel origins
 // identical; scaled rectangles already used the continuous path before.
 for(auto y:{29,45,48,72,104,209}){
  assert(sampleOrigin(flagFor(selected),1,y,16).y==sampleOrigin(flagFor(Mode::ScaledOnly),1,y,16).y);
 }
 for(short dx:{short(1024),short(-1024)})for(short dy:{short(1024),short(-1024)})assert(flagFor(selected,dx,dy));
 assert(flagFor(selected,512,512)==flagFor(Mode::ScaledOnly,512,512));
}
'''
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);(folder/'test.cpp').write_text(code)
            result=subprocess.run(['c++','-std=c++20','-Wall','-Wextra','-Werror',
                '-isystem',str(RT64),'-isystem',str(RT64/'contrib/hlslpp/include'),
                '-isystem',str(RT64/'contrib'),str(folder/'test.cpp'),'-o',str(folder/'test')],
                capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(folder/'test')],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)

if __name__=='__main__':unittest.main()
