"""Original work: djultra64. Exercise genuine original set-play constructors."""
from unittest.mock import patch
import unittest
import test_high_field_prompts as original

EXTRA=r'''
 // The original801DF7B0 dispatches six distinct sets of three resources.
 struct Variant {unsigned base,action,consumer,lines;};
 for(auto variant:{Variant{0x159,0x223,0x25ea00,4},Variant{0x15c,0x224,0x25eea4,6},
    Variant{0x15f,0x225,0x25f384,5},Variant{0x165,0x226,0x25f84c,5},
    Variant{0x16e,0x227,0x25fbac,2},Variant{0x229,0x22c,0x260230,3}}){
  for(unsigned highmode=0;highmode<2;++highmode){auto r=load(argv[2]);
   if(highmode){for(auto a:{0x13b428u,0x13b42cu,0x13b430u})memcpy(r.data()+a,video.data()+a,4);memcpy(r.data()+0x7aa008,video.data()+0x7aa008,0x2b4);}
   recomp_context c{};c.r29=int32_t(0x800a4000);c.f_odd=&c.f0.u32h;
   c.r4=variant.base;c.r5=variant.action;c.r6=(variant.base==0x159||variant.base==0x16e||variant.base==0x229)?0x221:0x222;
   func_801DF89C_overlay_287ab0_801db100(r.data(),&c);
   assert(word(r,0x8013d910)==(0x80000000u|variant.consumer));
   prompt_detail::TextureGuard guard(pal_en_prompt_texture_layout());
   for(unsigned port=0;port<4;++port)for(auto family:{PromptGlyphFamily::Xbox,PromptGlyphFamily::PlayStation,PromptGlyphFamily::Nintendo,PromptGlyphFamily::Keyboard}){
    byte(r,0x8012de37,port+1);const auto saved=r;
    std::array<PromptGlyphRequest,2>ab{};std::array<PromptGlyphRequest,4>dirs{};
    std::array<PromptGlyphRequest,3>shoulders{{{family,"L1",port},{family,"LT",port},{family,"RB",port}}};
    auto result=guard.prepare_sprite(r.data(),0x8013d8e0,ab,dirs,std::nullopt,shoulders);
    if(result.status!=PromptSpriteStatus::TextFallback)fprintf(stderr,"missing set-play variant %x high %u\n",variant.base,highmode);
    assert(result.status==PromptSpriteStatus::TextFallback&&result.line_count==variant.lines&&guard.sprite_port(r.data(),0x8013d8e0)==port&&r==saved);
    for(unsigned n=0;n<result.line_count;++n){const auto&l=result.lines[n];assert(l.x>=16&&l.x+int(l.text.size())*6<=304&&l.y>=190&&l.y<=217&&l.text.find("Z Button")==std::string::npos&&l.text.find("R Button")==std::string::npos);}
    assert(!draw(r,result).empty());
    auto foreign=r;byte(foreign,variant.consumer,0);const auto before=foreign;
    assert(!guard.sprite_port(foreign.data(),0x8013d8e0)&&guard.prepare_sprite(foreign.data(),0x8013d8e0,ab,dirs,std::nullopt,shoulders).status==PromptSpriteStatus::RejectedKnown&&foreign==before);
    shoulders[1].port=(port+1)%4;assert(guard.prepare_sprite(r.data(),0x8013d8e0,ab,dirs,std::nullopt,shoulders).status==PromptSpriteStatus::RejectedKnown&&r==saved);
   }
  }
 }
'''

class SetplayVariantTests(unittest.TestCase):
 def test_all_original_setplay_variants_render_for_low_high_four_ports_and_families(self):
  code=original.CODE.replace('std::array<EngineTextLine,4>lines','std::array<EngineTextLine,8>lines')
  end=code.rfind('\n}')
  code=code[:end]+EXTRA+code[end:]
  with patch.object(original,'CODE',code):
   original.HighFieldPromptTests().test_original_constructors_font_scaled_geometry_physical_ports_and_strict_high_guards()

if __name__=='__main__':unittest.main()
