"""Original project work: djultra64. Main Select uses the original task and font."""
from pathlib import Path
import json,unittest
import test_prompt_sprite_draw as fixture
ROOT=Path(__file__).resolve().parents[1]
class MainSelectDrawTests(unittest.TestCase):
 def test_menu_lift_footer_and_confirmation_use_original_cpu_rendering(self):
  prefix=fixture.CODE[:fixture.CODE.index('int main(')]
  code=prefix+'\n#include '+json.dumps(str(ROOT/'src/runtime/pal_main_select.cpp'))+r'''
int main(int,char**){auto base=load(".local/pal-acceptance/mainmenu09.rdram");
 PalPromptSpriteFunctions fn{func_80008A54_resident,func_80007C2C_resident,func_80041B50_resident,func_80048660_resident};
 recomp_context c{};c.r29=int32_t(0x800a4000);c.f_odd=&c.f0.u32h;

 // Actual GPU-reviewed return from Option retains the original last-selection
 // byte 1. It has the same pinned Main Select root/resource and live callback.
 auto returned=load(".local/r63-ui/runs/ui10/002-return-snapshot-ram.bin");assert(byte(returned,0x8012de74)==1);assert(pal_main_select_active(returned));
 for(unsigned value:{0u,1u,2u,3u,4u,5u,6u,7u,13u}){auto r=base;r[0x12de74^3]=value;assert(pal_main_select_active(r)&&lift_pal_main_select(r,true));}
 for(unsigned value:{8u,9u,10u,11u,12u,14u,255u}){auto r=base;r[0x12de74^3]=value;auto before=r;assert(!pal_main_select_active(r)&&!lift_pal_main_select(r,true)&&r==before);}
 assert(pal_main_select_active(base));auto lifted=base;assert(lift_pal_main_select(lifted));unsigned changed=0;
 for(unsigned p=word(base,0x800a4aa4)+8;p<word(base,0x8009e0c8);p+=8){if(word(lifted,p)==word(base,p)&&word(lifted,p+4)==word(base,p+4))continue;
  assert(word(base,p)>>24==0xe4);const auto delta=(word(base,p+4)&4095)-(word(lifted,p+4)&4095);assert(delta==64||delta==48);assert((word(lifted,p)&4095)+delta==(word(base,p)&4095));++changed;p+=16;}
 assert(changed>70&&changed<105);assert(memcmp(lifted.data()+0x13c47c,base.data()+0x13c47c,273*60)==0);

 // The actual lamp emitter changes descriptors through all twelve original
 // animation frames. A partial entry/exit frame must receive the same lift.
 for(unsigned frame=0;frame<12;++frame){auto r=base;put(r,0x8009e0c8,word(r,0x800a4aa4)+8);
  put(r,0x8013cbfc+20,0x803d8384+12*frame);c.r4=int32_t(0x8013cbfc);
  // Use a genuine lamp object with its own one-piece lamp segment.
  put(r,0x8013cbfc+48,0x803d736c);func_80041B50_resident(r.data(),&c);
  const auto before=r;assert(lift_pal_main_select(r));unsigned rectangles=0;
  for(auto p=word(r,0x800a4aa4)+8;p<word(r,0x8009e0c8);p+=8)if(word(r,p)>>24==0xe4){
   assert((word(r,p)&4095)+64==(word(before,p)&4095));
   assert((word(r,p+4)&4095)+64==(word(before,p+4)&4095));++rectangles;p+=16;}
  assert(rectangles==1);
 }

 // Draw every original ball layer, including the shared grid and moving icons.
 // Geometry and UVs remain exactly the original emitter's; only its alignment
 // and full-width scissor are scoped, and the row lift must leave it alone.
 for(unsigned slot=58;slot<=64;++slot){auto plain=base,wide=base;
  const auto head=word(base,0x800a4aa4)+8;put(plain,0x8009e0c8,head);put(wide,0x8009e0c8,head);
  recomp_context a{};a.r29=int32_t(0x800a4000);a.f_odd=&a.f0.u32h;a.r4=int32_t(0x8013c47c+60*slot);
  func_80041B50_resident(plain.data(),&a);a={};a.r29=int32_t(0x800a4000);a.f_odd=&a.f0.u32h;a.r4=int32_t(0x8013c47c+60*slot);
  assert(draw_pal_main_ball(wide,a,true,func_80041B50_resident));
  assert(word(wide,head+32)==0x64000006&&word(wide,head+36)==0);
  const auto end=word(wide,0x8009e0c8);assert(word(wide,end-24)==0x64000006&&word(wide,end-20)==0x00800800&&word(wide,end-8)==0x64000018);
  auto rects=[&](const Bytes&r){std::vector<std::array<uint32_t,6>> out;for(auto p=head;p<word(r,0x8009e0c8);p+=8){auto op=word(r,p);if(op==0x64000006||op==0x64000005){p+=8;continue;}if(op>>24==0xe4){std::array<uint32_t,6>v;for(unsigned n=0;n<6;++n)v[n]=word(r,p+4*n);out.push_back(v);p+=16;}}return out;};
  const auto original=rects(plain);assert(!original.empty()&&rects(wide)==original);
  assert(lift_pal_main_select(wide)&&rects(wide)==original);
  assert(memcmp(wide.data()+0x13c47c,base.data()+0x13c47c,273*60)==0);
 }

 for(unsigned frame=0;frame<16;++frame){auto r=base;put(r,0x8009e0c8,word(r,0x800a4aa4)+8);
  put(r,0x8013d304+20,0x803d9ba8+12*frame);recomp_context a{};a.r29=int32_t(0x800a4000);a.f_odd=&a.f0.u32h;a.r4=int32_t(0x8013d304);
  assert(draw_pal_main_ball(r,a,true,func_80041B50_resident));
 }
 const unsigned descriptors[]{0x803d9c68,0x803d9c68,0x803d9c74,0x803d9c74,0x803d9c74,0x803d9c68,0x803d9c68,0x803d9c74};
 const unsigned pieces[]{0x803d74e0,0x803d74ec,0x803d7504,0x803d7510,0x803d751c,0x803d7528,0x803d7534,0x803d754c};
 for(unsigned n=0;n<8;++n){auto r=base;put(r,0x8009e0c8,word(r,0x800a4aa4)+8);put(r,0x8013d2c8+20,descriptors[n]);put(r,0x8013d2c8+48,pieces[n]);
  recomp_context a{};a.r29=int32_t(0x800a4000);a.f_odd=&a.f0.u32h;a.r4=int32_t(0x8013d2c8);assert(draw_pal_main_ball(r,a,true,func_80041B50_resident));
 }
 // The five original selected-label atlases must follow the same row as its
 // normal label, including the previously unshifted Option glow.
 for(unsigned n=0;n<5;++n){auto r=base;put(r,0x8009e0c8,word(r,0x800a4aa4)+8);put(r,0x8013c968+20,0x803d9ca4+12*n);
  recomp_context a{};a.r29=int32_t(0x800a4000);a.f_odd=&a.f0.u32h;a.r4=int32_t(0x8013c968);func_80041B50_resident(r.data(),&a);auto before=r;
  assert(lift_pal_main_select(r));unsigned rects=0;
  for(auto p=word(r,0x800a4aa4)+8;p<word(r,0x8009e0c8);p+=8)if(word(r,p)>>24==0xe4){assert((word(r,p+4)&4095)+64==(word(before,p+4)&4095));++rects;p+=16;}
  assert(rects>0);
 }
 for(unsigned bad=0;bad<5;++bad){auto r=base;recomp_context a{};a.r29=int32_t(0x800a4000);a.f_odd=&a.f0.u32h;a.r4=int32_t(0x8013d214);
  if(bad==1)a.r4=int32_t(0x8013cbfc);if(bad==2)put(r,0x803d6ee0,0);if(bad==3)put(r,0x803d8384,0);if(bad==4)put(r,0x80143d6c,0);
  auto before=r;assert(!draw_pal_main_ball(r,a,bad!=0,func_80041B50_resident)&&r==before);
 }

 {auto wide=base;assert(lift_pal_main_select(wide,true));uint32_t texture=0;unsigned text=0,background=0;std::array<int,9> insets;insets.fill(-1);
  for(auto p=word(base,0x800a4aa4)+8;p<word(base,0x8009e0c8);p+=8){auto a=word(base,p),b=word(base,p+4);if(a>>24==0xfd)texture=b&0x7fffff;if(a>>24!=0xe4)continue;
   auto now=word(wide,p);if(now==0x64000002){assert(word(wide,p+4)==((b>>24)&7));const int inset=int(b>>12&4095)-int16_t(word(wide,p+8)>>16);
    assert(int(a>>12&4095)-int16_t(word(wide,p+12)>>16)==inset);
    if(texture==0x239640||texture==0x23cb00)assert(inset==0);
    else{const int row=(int(b&4095)/4-51)/20;if(row>=0&&row<9){constexpr int wanted[]{-30,20,16,12,-27,-31,-64,-61,-57};assert(inset==wanted[row]);if(insets[row]==-1)insets[row]=inset;else assert(insets[row]==inset);}}
    assert(word(wide,p+16)==word(base,p+12)&&word(wide,p+20)==word(base,p+20));++text;}
   else if(texture==0x23ef00||texture==0x23f500){assert(now>>24==0xe4);assert((now>>12&4095)==(a>>12&4095)&&(word(wide,p+4)>>12&4095)==(b>>12&4095));++background;}
   p+=16;
  }assert(text>30&&background>=50);constexpr int wanted[]{-30,20,16,12,-27,-31,-64,-61,-57};for(unsigned row=0;row<9;++row)assert(insets[row]==wanted[row]);
 }
 const char*north[]{"Y","Triangle","X","Y"};const char*accept[]{"A","Cross","B","Z"};const char*cancel[]{"B","Circle","A","X"};
 for(unsigned f=1;f<=4;++f)for(unsigned port=0;port<4;++port)for(unsigned modal=0;modal<3;++modal){auto r=base;MainExitView view{true,modal!=0,modal==2};std::array<PromptGlyphRequest,3> prompts{{{PromptGlyphFamily(f),north[f-1],port},{PromptGlyphFamily(f),accept[f-1],port},{PromptGlyphFamily(f),cancel[f-1],port}}};
  r[0x165d63^3]=0; // Actual Main Select inherits a transparent previous sprite material.
  const auto before=r;const auto caller=c;assert(draw_pal_main_exit(r,c,view,prompts,fn));assert(memcmp(r.data()+0x13c47c,before.data()+0x13c47c,273*60)==0);assert(memcmp(&c,&caller,sizeof(c))==0);
  unsigned count=0;uint32_t texture=0,primitive=0;for(auto p=word(before,0x8009e0c8);p<word(r,0x8009e0c8);p+=8){auto a=word(r,p),b=word(r,p+4);if(a>>24==0xfd)texture=b&0x7fffff;if(a>>24==0xfa)primitive=b;if(a>>24==0xe4){if(texture>=0x352800&&texture<0x355800)assert((primitive&255)==255);if(!modal)assert((b&4095)/4>=213&&(a&4095)/4<=229);++count;p+=16;}}
  assert(count>=(modal?30u:17u));
 }
 for(unsigned k=0;k<6;++k){auto r=base;auto badfn=fn;auto caller=c;std::array<PromptGlyphRequest,3> prompts{{{PromptGlyphFamily::Xbox,"Y",0},{PromptGlyphFamily::Xbox,"A",0},{PromptGlyphFamily::Xbox,"B",0}}};
  if(k==0)badfn.draw_text=nullptr;if(k==1)caller.r29=0;if(k==2)caller.f_odd=(uint32_t*)r.data();if(k==3)prompts[1].label="Missing";if(k==4)put(r,0x80352800,0);if(k==5)put(r,0x80048660,0);
  const auto before=r;assert(!draw_pal_main_exit(r,caller,{true,true,false},prompts,badfn)&&r==before);
 }
 for(unsigned k=0;k<4;++k){auto r=base;if(k==0)put(r,0x80143d6c,0);if(k==1)put(r,0x803c29fc,0);if(k==2)put(r,0x80077390,0);if(k==3)put(r,0x8013b42c,0);const auto before=r;assert(!pal_main_select_active(r));assert(!lift_pal_main_select(r)&&r==before);}
}
'''
  old=fixture.CODE
  try:
   fixture.CODE=code
   runner=fixture.PromptSpriteDrawTests('test_native_region_glyph_art_palette_ink_and_transaction')
   runner.test_native_region_glyph_art_palette_ink_and_transaction()
  finally:fixture.CODE=old
