"""Original work: djultra64. Exact Handicap L/Z and R resource."""
import json,unittest
from unittest.mock import patch
import test_high_field_prompts as original
EXTRA=r'''
 {auto r=load(SNAPSHOT);recomp_context c{};c.r29=int32_t(0x800a4000);c.f_odd=&c.f0.u32h;
  constexpr uint32_t object=0x8013d940;
  c.r4=int32_t(object);func_80008A54_resident(r.data(),&c);
  c.r4=int32_t(object);func_801DE398_overlay_287ab0_801db100(r.data(),&c);
  c.r4=int32_t(object);c.r5=int32_t(0x802ab264);func_80007C2C_resident(r.data(),&c);
  assert(word(r,object+48)==0x802aafc0);
  prompt_detail::TextureGuard guard(pal_en_prompt_texture_layout());
  for(unsigned port=0;port<4;++port)for(auto family:{PromptGlyphFamily::Xbox,PromptGlyphFamily::PlayStation,PromptGlyphFamily::Nintendo,PromptGlyphFamily::Keyboard}){
   const auto saved=r;std::array<PromptGlyphRequest,2>ab{};std::array<PromptGlyphRequest,4>dirs{};
   const char*l=family==PromptGlyphFamily::PlayStation?"L1":family==PromptGlyphFamily::Nintendo?"L":family==PromptGlyphFamily::Keyboard?"Q":"LB";
   const char*z=family==PromptGlyphFamily::PlayStation?"L2":family==PromptGlyphFamily::Nintendo?"ZL":family==PromptGlyphFamily::Keyboard?"Left Shift":"LT";
   const char*b=family==PromptGlyphFamily::PlayStation?"R1":family==PromptGlyphFamily::Nintendo?"R":family==PromptGlyphFamily::Keyboard?"E":"RB";
   std::array<PromptGlyphRequest,3>shoulders{{{family,l,port},{family,z,port},{family,b,port}}};
   const auto result=guard.prepare_sprite(r.data(),object,ab,dirs,PromptGlyphRequest{family,"Return",port},shoulders);
   assert(result.status==PromptSpriteStatus::TextFallback&&result.line_count==2&&guard.sprite_port(r.data(),object,port)==port&&r==saved);
   assert(result.lines[0].x>=20&&result.lines[0].x+int(result.lines[0].text.size())*6<=52);
   assert(result.lines[1].text==b&&result.lines[1].x>=275&&result.lines[1].x+int(result.lines[1].text.size())*6<=307);
   assert(!draw(r,result).empty());
   for(unsigned change=0;change<5;++change){auto bad=r;
    if(change==0)byte(bad,0x802aafc0,0);
    if(change==1)byte(bad,word(bad,word(bad,object+20)+8),bad[(word(bad,word(bad,object+20)+8)&0x7fffff)^3]^1);
    if(change==2)byte(bad,0x80352800,bad[0x352800^3]^1);
    if(change==3)byte(bad,0x8013b42a,1);
    if(change==4)put(bad,object+32,0x00010000);
    const auto before=bad;assert(!guard.sprite_port(bad.data(),object,port)&&guard.prepare_sprite(bad.data(),object,ab,dirs,PromptGlyphRequest{family,"Return",port},shoulders).status==PromptSpriteStatus::RejectedKnown&&bad==before);
   }
   shoulders[0].port=(port+1)%4;assert(guard.prepare_sprite(r.data(),object,ab,dirs,PromptGlyphRequest{family,"Return",port},shoulders).status==PromptSpriteStatus::RejectedKnown&&r==saved);
  }
 }
'''
class HandicapPromptTests(unittest.TestCase):
 def test_exact_original_handicap_resource_keeps_both_left_actions_and_active_family(self):
  snapshot=original.ROOT/'.local/hidden-test-01/team16-completed.rdram'
  if not snapshot.is_file():self.skipTest('Private menu atlas fixture required')
  code=original.CODE;end=code.rfind('\n}');code=code[:end]+EXTRA.replace('SNAPSHOT',json.dumps(str(snapshot)))+code[end:]
  case=original.HighFieldPromptTests();case.extra_entries=[0x80008A54]
  with patch.object(original,'CODE',code):case.test_original_constructors_font_scaled_geometry_physical_ports_and_strict_high_guards()
if __name__=='__main__':unittest.main()
