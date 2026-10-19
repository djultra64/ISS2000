"""Bounded factory-name replacement leaves game data and user edits untouched."""
from pathlib import Path
import shutil,subprocess,tempfile,unittest,json,copy
from tools.generate_pal_real_names import generate,DATA,OUTPUT
ROOT=Path(__file__).resolve().parents[1]
CODE=r'''#include "runtime/pal_real_names.hpp"
#include <cassert>
#include <fstream>
#include <iterator>
#include <vector>
using namespace iss2000;
int main(int,char**argv){
 std::ifstream file(argv[1],std::ios::binary);std::vector<uint8_t>rom{std::istreambuf_iterator<char>(file),{}};auto original=rom;
 std::vector<std::string_view>names(106*22,"Real");names[0]="Kahn";names.back()="Last";
 PalRealNames patch;std::vector<uint8_t>ram(0x800000,0xA5);auto pristine=ram;
 assert(!patch.apply(ram,0x2DEE70,0x801AD820,0x35C10));assert(ram==pristine);
 assert(!patch.configure(std::span<const uint8_t>(rom).first(4096),names));
 auto bad=rom;bad[0]^=1;assert(!patch.configure(bad,names));
 assert(patch.configure(rom,names)&&rom==original);
 // Genuine owner load copied in the runtime's word-swapped RDRAM format.
 auto load=[&](unsigned offset,unsigned dest,unsigned size){for(unsigned i=0;i<size;++i)ram[((dest&0x7fffff)+i)^3]=rom[offset+i];};
 load(0x2DEE70,0x801AD820,0x35C10);pristine=ram;
 auto count=patch.apply(ram,0x2DEE70,0x801AD820,0x35C10);assert(count==106*22*8);
 for(unsigned a=0;a<ram.size();++a){unsigned guest=a^3;bool name=guest>=0x1bfc40&&guest<0x1dfa60&&(guest-0x1bfc40)%56>=24&&(guest-0x1bfc40)%56<32;if(!name)assert(ram[a]==pristine[a]);}
 const unsigned first=0x1bfc40+24;assert(ram[first^3]==0x15&&ram[(first+1)^3]==0x25&&ram[(first+2)^3]==0x2c&&ram[(first+3)^3]==0x32);
 auto complete=ram;
 // Fragmented and unaligned DMAs must produce the same patched bytes.
 ram=pristine;unsigned off=0x2F1290,dest=0x801BFC40,remaining=106*22*56;
 for(unsigned n=0;remaining;++n){unsigned size=std::min(remaining,(n%79)+1);load(off,dest,size);patch.apply(ram,off,dest,size);off+=size;dest+=size;remaining-=size;}
 assert(ram==complete);
 // Only newly loaded ranges change; editing a different factory name survives.
 ram[first^3]=0x0b;load(0x2F1290+56,0x801BFC40+56,56);assert(patch.apply(ram,0x2F1290+56,0x801BFC40+56,56)==8);assert(ram[first^3]==0x0b);
 auto edited=ram;
 for(auto guest:{0x801675CCu,0x8012E120u,0x801A583Cu,0x80010000u})assert(!patch.apply(ram,0x2F1290,guest,56));
 assert(!patch.apply(ram,0x2F1290,0x801BFC40,0));assert(!patch.apply(std::span<uint8_t>(ram).first(4096),0x2F1290,0x801BFC40,56));assert(!patch.apply(ram,0x2F1290,0xFFFFFFFF,0xFFFFFFFF));assert(ram==edited);
 // Reload restores real defaults; foreign/invalid data disables the override.
 load(0x2DEE70,0x801AD820,0x35C10);patch.apply(ram,0x2DEE70,0x801AD820,0x35C10);assert(ram==complete);
 names[0]="TooLongName";assert(!patch.configure(rom,names));pristine=ram;assert(!patch.apply(ram,0x2DEE70,0x801AD820,0x35C10)&&ram==pristine);
 names[0]="Real";names.pop_back();assert(!patch.configure(rom,names));assert(rom==original);
 assert(patch.configure(rom,pal_default_real_names()));
 assert(pal_default_real_names().size()==106*22);
 assert(pal_default_real_names()[0]=="Kahn"&&pal_default_real_names()[69*22+10]=="Ronaldo");
 for(auto name:pal_default_real_names())assert(encode_pal_player_name(name));
 load(0x2DEE70,0x801AD820,0x35C10);assert(patch.apply(ram,0x2DEE70,0x801AD820,0x35C10)==2332*8);
 for(unsigned i=0;i<2332;++i){auto encoded=*encode_pal_player_name(pal_default_real_names()[i]);for(unsigned b=0;b<8;++b)assert(ram[(0x1bfc40+i*56+24+b)^3]==encoded[b]);}
 assert(encode_pal_player_name("A.z 9"));assert(!encode_pal_player_name(""));assert(!encode_pal_player_name("Bjørn"));assert(!encode_pal_player_name("123456789"));assert(!encode_pal_player_name("Real!"));
}
'''
class PalRealNamesTests(unittest.TestCase):
 def test_names_only_with_exact_identity_reload_fragments_and_user_data(self):
  rom=ROOT/'.local/inputs/pal-en-de/rom.z64';mb=ROOT/'.local/runtime-deps-build/librecomp/miniz'
  if not shutil.which('c++') or not rom.is_file() or not(mb/'libminiz.a').is_file():self.skipTest('Private PAL ROM, compiler and pinned miniz required')
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);(p/'test.cpp').write_text(CODE)
   result=subprocess.run(['c++','-std=c++20','-O1','-I'+str(ROOT/'src'),'-I'+str(ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz'),'-I'+str(mb),str(p/'test.cpp'),str(ROOT/'src/runtime/pal_real_names.cpp'),str(ROOT/'src/runtime/pal_real_names_data.cpp'),str(ROOT/'src/runtime/rom_image.cpp'),str(mb/'libminiz.a'),'-o',str(p/'test')],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
   result=subprocess.run([str(p/'test'),str(rom)],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)

 def test_complete_sourced_dataset_special_provenance_and_explicit_exceptions(self):
  data=json.loads(DATA.read_text());self.assertEqual(generate(data),OUTPUT.read_bytes())
  self.assertEqual(len(data['players']),2332)
  self.assertEqual(sum(p['periodException']for p in data['players'][:2200]),24)
  for mutate in [lambda d:d['players'].pop(),lambda d:d['players'][0].update(displayName='Too long name'),lambda d:d['players'][0].update(source=''),lambda d:d['players'][100*22].update(displayName='Foreign'),lambda d:d.update(ordinaryPeriodExceptions=0)]:
   broken=copy.deepcopy(data);mutate(broken)
   with self.assertRaises(ValueError):generate(broken)
  # The two-star-team copies and every combined slot use their authenticated
  # source-country/slot identity, rather than a new heuristic assignment.
  for p in data['players'][2200:]:
   original=data['players'][p['originTeamId']*22+p['originSlot']]
   self.assertEqual((p['displayName'],p['fullName']),(original['displayName'],original['fullName']))
