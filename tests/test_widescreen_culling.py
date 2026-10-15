"""Pure native camera-bound checks; never execute original game code."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

HARNESS=r'''
#include "runtime/widescreen_culling.hpp"
#include <array>
#include <cassert>
#include <cmath>
#include <cstring>
#include <limits>
#include <span>
#include <string>
#include <vector>
using Bytes=std::vector<uint8_t>;
constexpr size_t ASPECT=0xA07E8,H=0xA0984,V=0xA08D0,FH=0xAA104,FV=0xAA108;
void put(Bytes& b,size_t p,float f){std::memcpy(b.data()+p,&f,4);}
float get(const Bytes& b,size_t p){float f;std::memcpy(&f,b.data()+p,4);return f;}
Bytes initialized(){Bytes b(0x800000,0xCD);put(b,ASPECT,4.f/3.f);put(b,H,1.f);put(b,V,.75f);put(b,FH,100.f);put(b,FV,75.f);return b;}
bool close(float a,float b){return std::abs(a-b)<1.e-5f*std::max(1.f,std::abs(b));}
void only_changed(const Bytes& before,const Bytes& after,const std::vector<size_t>& fields){
 for(size_t i=0;i<before.size();++i){bool allowed=false;for(auto f:fields)allowed|=i>=f&&i<f+4;if(!allowed)assert(before[i]==after[i]);}
}
constexpr std::array<size_t,3> AXES={0xC5D3C,0x177ED0,0x1A2FF0};
using Vec=std::array<float,3>;
std::array<Vec,4> corners(const Bytes& b,const std::array<size_t,3>& axes=AXES){std::array<Vec,4> c{};for(int i=0;i<4;++i)for(int a=0;a<3;++a)c[i][a]=get(b,axes[a]+i*4);return c;}
void make_rotated_corners(Bytes& b,const std::array<size_t,3>& axes=AXES){
 // Common orthonormal basis rotated about both worldY and worldZ.
 const float yaw=.7f,pitch=.4f;
 Vec right={std::cos(yaw),0.f,-std::sin(yaw)};
 Vec up={std::sin(yaw)*std::sin(pitch),std::cos(pitch),std::cos(yaw)*std::sin(pitch)};
 Vec forward={std::sin(yaw)*std::cos(pitch),-std::sin(pitch),std::cos(yaw)*std::cos(pitch)};
 for(int i=0;i<4;++i){float x=(i%2==0?.3f:-.3f),y=(i<2?.2f:-.2f);for(int a=0;a<3;++a)put(b,axes[a]+i*4,x*right[a]+y*up[a]-forward[a]);}
}
int main(int argc,char** argv){assert(argc==2);std::string mode=argv[1];
 if(mode=="original"){
  auto b=initialized();make_rotated_corners(b);put(b,H,std::numeric_limits<float>::quiet_NaN());auto old=b;
  assert(iss2000::apply_widescreen_culling(b,false));assert(iss2000::apply_widescreen_far_extents(b,false));assert(iss2000::apply_widescreen_world_corners(b,false));assert(b==old);
 }else if(mode=="horizontal"){
  auto b=initialized(),old=b;assert(iss2000::apply_widescreen_culling(b,true));
  assert(close(get(b,H),4.f/3.f));assert(close(get(b,FH),100.f*4.f/3.f));assert(get(b,V)==.75f&&get(b,FV)==75.f);
  // Independent point/bound comparisons: visible only in the added horizontal area.
  const float depth=10.f,x=12.f,y=8.f;
  assert(x>depth*get(old,H));assert(x<depth*get(b,H));
  assert(y>depth*get(old,V));assert(y>depth*get(b,V));
  only_changed(old,b,{H,FH});
 }else if(mode=="refresh"){
  auto b=initialized();assert(iss2000::apply_widescreen_culling(b,true));auto once=b;
  assert(!iss2000::apply_widescreen_culling(b,true));assert(b==once);
  put(b,H,1.f);put(b,FH,100.f);assert(iss2000::apply_widescreen_culling(b,true));assert(b==once);
 }else if(mode=="invalid"){
  for(size_t p:{ASPECT,H,V,FH,FV})for(float bad:{-1.f,0.f,std::numeric_limits<float>::quiet_NaN(),std::numeric_limits<float>::infinity()}){
   auto b=initialized();put(b,p,bad);auto old=b;assert(!iss2000::apply_widescreen_culling(b,true));assert(b==old);
  }
  for(auto change:std::array<std::pair<size_t,float>,3>{{{ASPECT,16.f/9.f},{H,2.f},{FV,33.f}}}){
   auto b=initialized();put(b,change.first,change.second);auto old=b;assert(!iss2000::apply_widescreen_culling(b,true));assert(b==old);
  }
  Bytes short_buffer(128,0xCD),old=short_buffer;assert(!iss2000::apply_widescreen_culling(short_buffer,true));assert(short_buffer==old);
 }else if(mode=="far_rewriter"){
  auto b=initialized();assert(iss2000::apply_widescreen_culling(b,true));
  // Original228D0 replaces only the far-plane pair while wide angular limits persist.
  put(b,FH,200.f);put(b,FV,150.f);auto old=b;
  assert(iss2000::apply_widescreen_far_extents(b,true));assert(close(get(b,FH),200.f*4.f/3.f));
  assert(get(b,H)==get(old,H));only_changed(old,b,{FH});auto once=b;
  assert(!iss2000::apply_widescreen_far_extents(b,true));assert(b==once);
  put(b,FV,-1.f);old=b;assert(!iss2000::apply_widescreen_far_extents(b,true));assert(b==old);
 }else if(mode=="ensure_far"){
  auto b=initialized();assert(iss2000::apply_widescreen_culling(b,true));auto wide=b;
  assert(iss2000::ensure_widescreen_far_extents(b,true));assert(b==wide);
  put(b,FH,200.f);put(b,FV,150.f);auto old=b;
  assert(iss2000::ensure_widescreen_far_extents(b,true));only_changed(old,b,{FH});
  assert(250.f>get(old,FH)&&250.f<get(b,FH));assert(get(b,FV)==150.f);
  auto once=b;for(int corner=0;corner<8;++corner){assert(iss2000::ensure_widescreen_far_extents(b,true));assert(b==once);}
  put(b,FH,900.f);old=b;assert(!iss2000::ensure_widescreen_far_extents(b,true));assert(b==old);
 }else if(mode=="corners"){
  auto b=initialized();make_rotated_corners(b);auto old=b;auto before=corners(b);
  assert(iss2000::apply_widescreen_world_corners(b,true));auto after=corners(b);
  for(int pair=0;pair<4;pair+=2)for(int a=0;a<3;++a){
   assert(close((after[pair][a]+after[pair+1][a])/2,(before[pair][a]+before[pair+1][a])/2));
   assert(close(after[pair][a]-after[pair+1][a],(before[pair][a]-before[pair+1][a])*4.f/3.f));
  }
  // Matching corner vertical differences and common forward center are preserved.
  for(int a=0;a<3;++a){assert(close(after[0][a]-after[2][a],before[0][a]-before[2][a]));assert(close(after[1][a]-after[3][a],before[1][a]-before[3][a]));}
  std::vector<size_t> fields;for(auto axis:AXES)for(int i=0;i<4;++i)fields.push_back(axis+i*4);only_changed(old,b,fields);
 }else if(mode=="invalid_corners"){
  for(float bad:{std::numeric_limits<float>::quiet_NaN(),std::numeric_limits<float>::infinity()}){
   auto b=initialized();make_rotated_corners(b);put(b,AXES[1]+4,bad);auto old=b;assert(!iss2000::apply_widescreen_world_corners(b,true));assert(b==old);
  }
  auto b=initialized();make_rotated_corners(b);put(b,AXES[0]+12,100.f);auto old=b;assert(!iss2000::apply_widescreen_world_corners(b,true));assert(b==old);
 }else if(mode=="pal_layout"){
  constexpr size_t pa=0x9DF00,ph=0x9E09C,pv=0x9DFE8,pfh=0xA7824,pfv=0xA7828;
  constexpr std::array<size_t,3> axes={0xC345C,0x1755F0,0x1A0760};
  const auto layout=iss2000::verified_pal_widescreen_layout();
  Bytes b(0x800000,0xCD);put(b,pa,4.f/3.f);put(b,ph,1.f);put(b,pv,.75f);put(b,pfh,100.f);put(b,pfv,75.f);
  make_rotated_corners(b,axes);auto old=b;auto before=corners(b,axes);
  assert(iss2000::apply_widescreen_culling(b,true,layout));
  assert(close(get(b,ph),4.f/3.f)&&close(get(b,pfh),100.f*4.f/3.f));
  assert(get(b,pv)==.75f&&get(b,pfv)==75.f);only_changed(old,b,{ph,pfh});
  auto wide=b;assert(iss2000::ensure_widescreen_far_extents(b,true,layout));assert(b==wide);
  put(b,pfh,200.f);put(b,pfv,150.f);old=b;
  assert(iss2000::apply_widescreen_far_extents(b,true,layout));only_changed(old,b,{pfh});
  old=b;assert(iss2000::apply_widescreen_world_corners(b,true,layout));auto after=corners(b,axes);
  for(int pair=0;pair<4;pair+=2)for(int axis=0;axis<3;++axis){
   assert(close((after[pair][axis]+after[pair+1][axis])*.5f,(before[pair][axis]+before[pair+1][axis])*.5f));
   assert(close(after[pair][axis]-after[pair+1][axis],(before[pair][axis]-before[pair+1][axis])*4.f/3.f));
  }
  std::vector<size_t> fields;for(auto axis:axes)for(int i=0;i<4;++i)fields.push_back(axis+i*4);only_changed(old,b,fields);
  // Every old US camera address is a sentinel: selecting PAL must leave it untouched.
  for(auto offset:std::array<size_t,8>{ASPECT,H,V,FH,FV,AXES[0],AXES[1],AXES[2]})for(int i=0;i<4;++i)assert(b[offset+i]==0xCD);
  old=b;assert(iss2000::apply_widescreen_culling(b,false,layout));assert(iss2000::apply_widescreen_world_corners(b,false,layout));assert(b==old);
 }else if(mode=="invalid_layout"){
  for(int bad=0;bad<5;++bad){
   auto layout=iss2000::verified_us_widescreen_layout();
   if(bad==0)layout.aspect=0x800A07E9;
   if(bad==1)layout.far_vertical=0x80800000;
   if(bad==2)layout.horizontal=layout.vertical;
   if(bad==3)layout.corner_axes[0]=0x807FFFF4;
   if(bad==4)layout.corner_axes[1]=layout.aspect;
   auto b=initialized();make_rotated_corners(b);auto old=b;
   assert(!iss2000::apply_widescreen_culling(b,true,layout));
   assert(!iss2000::apply_widescreen_far_extents(b,true,layout));
   assert(!iss2000::ensure_widescreen_far_extents(b,true,layout));
   assert(!iss2000::apply_widescreen_world_corners(b,true,layout));assert(b==old);
  }
 }else return 2;
}
'''

@unittest.skipUnless(shutil.which('c++'), 'Native C++ compiler required')
class WidescreenCullingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.root=Path(cls.temp.name)
        (cls.root/'test.cpp').write_text(HARNESS)
        cls.binary=cls.root/'test'
        result=subprocess.run(['c++','-std=c++20','-O2','-Wall','-Wextra','-Werror','-I'+str(ROOT/'src'),str(cls.root/'test.cpp'),str(ROOT/'src/runtime/widescreen_culling.cpp'),'-o',str(cls.binary)],text=True,capture_output=True)
        if result.returncode:raise RuntimeError(result.stderr)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def run_case(self,name):subprocess.run([str(self.binary),name],check=True,capture_output=True)
    def test_original_mode_is_byte_exact_no_op(self):self.run_case('original')
    def test_horizontal_visibility_expands_with_vertical_and_sentinels_unchanged(self):self.run_case('horizontal')
    def test_original_refresh_allows_new_correction_without_accumulation(self):self.run_case('refresh')
    def test_invalid_camera_state_rejected_without_any_mutation(self):self.run_case('invalid')
    def test_alternate_far_extent_rewriter_preserves_wide_angular_terms(self):self.run_case('far_rewriter')
    def test_far_test_entry_is_idempotent_across_corners_and_rewriters(self):self.run_case('ensure_far')
    def test_rotated_corner_pairs_widen_only_local_horizontal_direction(self):self.run_case('corners')
    def test_invalid_rotated_corner_state_rejected_without_any_mutation(self):self.run_case('invalid_corners')

    def test_pal_layout_widens_only_pal_fields_and_preserves_us_sentinels(self):self.run_case('pal_layout')
    def test_invalid_guest_layout_is_rejected_before_any_write(self):self.run_case('invalid_layout')
