"""Original work: djultra64. Actual replay UI constructor and physical prompts."""
import unittest
from unittest.mock import patch
import test_high_field_prompts as original
EXTRA=r'''
 for(unsigned highmode=0;highmode<2;++highmode){auto r=load(argv[2]);
  if(highmode){for(auto a:{0x13b428u,0x13b42cu,0x13b430u})memcpy(r.data()+a,video.data()+a,4);memcpy(r.data()+0x7aa008,video.data()+0x7aa008,0x2b4);}
  recomp_context c{};c.r29=int32_t(0x800a4000);c.f_odd=&c.f0.u32h;
  func_801E7E58_overlay_287ab0_801db100(r.data(),&c);
  // Replay initialization constructs Cancel independently with resource1D8.
  c.r4=int32_t(0x8013e0d8);func_801DE398_overlay_287ab0_801db100(r.data(),&c);
  c.r4=int32_t(0x8013e0d8);c.r5=0x1d8;func_80007BF8_resident(r.data(),&c);
  for(unsigned port=0;port<4;++port)for(auto family:{PromptGlyphFamily::Xbox,PromptGlyphFamily::PlayStation,PromptGlyphFamily::Nintendo,PromptGlyphFamily::Keyboard}){
   const auto saved=r;prompt_detail::TextureGuard guard(pal_en_prompt_texture_layout());
   const auto a=family==PromptGlyphFamily::PlayStation?"×":family==PromptGlyphFamily::Nintendo?"B":family==PromptGlyphFamily::Keyboard?"Z":"A";
   const auto b=family==PromptGlyphFamily::PlayStation?"○":family==PromptGlyphFamily::Nintendo?"A":family==PromptGlyphFamily::Keyboard?"X":"B";
   std::array<PromptGlyphRequest,2>ab{{{family,a,port},{family,b,port}}};
   std::array<PromptGlyphRequest,4>dirs{{{family,"J",port},{family,"L",port},{family,"I",port},{family,"K",port}}};
   std::array<PromptGlyphRequest,3>shoulders{{{family,"LB",port},{family,"LT",port},{family,"RB",port}}};
   for(auto object:{0x8013e1c8u,0x8013e204u,0x8013e0d8u}){
    auto result=guard.prepare_sprite(r.data(),object,ab,dirs,PromptGlyphRequest{family,"Return",port},shoulders);
    assert(result.status==PromptSpriteStatus::TextFallback&&result.line_count>0&&r==saved&&guard.sprite_port(r.data(),object,port)==port);
    if(object==0x8013e1c8){assert(result.lines[0].text==(family==PromptGlyphFamily::PlayStation?"X":a));assert(result.lines[1].text==(family==PromptGlyphFamily::PlayStation?"O":b));}
    assert(!draw(r,result).empty());
    for(unsigned n=0;n<result.line_count;++n)assert(result.lines[n].text.find("Button")==std::string::npos);
    auto bad=r;const auto segments=word(bad,object+48);byte(bad,segments,0);const auto before=bad;
    assert(!guard.sprite_port(bad.data(),object,port)&&guard.prepare_sprite(bad.data(),object,ab,dirs,PromptGlyphRequest{family,"Return",port},shoulders).status==PromptSpriteStatus::RejectedKnown&&bad==before);
    for(unsigned change=0;change<8;++change){auto foreign=r;
     if(change==0)byte(foreign,object+5,8);
     if(change==1)put(foreign,word(foreign,object+20)+8,0x807ffffc);
     if(change==2)put(foreign,0x8009e02c,0x8013b410);
     if(change==3)byte(foreign,0x8013b44c,9);
     if(change==4)byte(foreign,0x801e7e58,0);
     if(change==5)byte(foreign,0x80352800,foreign[0x352800^3]^1);
     if(change==6)put(foreign,0x8013b42c,0x028001e0);
     if(change==7)put(foreign,object+32,0x00010000);
     const auto before=foreign;if(guard.sprite_port(foreign.data(),object,port))fprintf(stderr,"accepted variant %u object %x high %u\n",change,object,highmode);assert(!guard.sprite_port(foreign.data(),object,port)&&guard.prepare_sprite(foreign.data(),object,ab,dirs,PromptGlyphRequest{family,"Return",port},shoulders).status==PromptSpriteStatus::RejectedKnown&&foreign==before);
    }
    assert(!guard.sprite_port(nullptr,object,port)&&!guard.sprite_port(r.data(),object,4));
   }
   dirs[0].port=(port+1)%4;assert(guard.prepare_sprite(r.data(),0x8013e1c8,ab,dirs,PromptGlyphRequest{family,"Return",port},shoulders).status==PromptSpriteStatus::RejectedKnown&&r==saved);
  }
 }
'''
class ReplayPromptTests(unittest.TestCase):
 def test_original_replay_diagrams_and_cancel_follow_active_port_without_guest_writes(self):
  code=original.CODE.replace('std::array<EngineTextLine,4>lines','std::array<EngineTextLine,8>lines')
  end=code.rfind('\n}');code=code[:end]+EXTRA+code[end:]
  case=original.HighFieldPromptTests();case.extra_entries=[0x801E7E58]
  with patch.object(original,'CODE',code):
   case.test_original_constructors_font_scaled_geometry_physical_ports_and_strict_high_guards()
if __name__=='__main__':unittest.main()
