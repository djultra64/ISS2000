"""Automatic save storage survives legacy accessory choices; no game/physical-motor claim.
Original project work: djultra64.
"""
from pathlib import Path
import subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class AutomaticAccessoriesTests(unittest.TestCase):
 def test_each_connected_player_has_storage_without_pack_selection(self):
  code=r'''#include "runtime/pak_services.hpp"
#include <fstream>
#include <cassert>
#include <vector>
using namespace iss2000;
int main(int,char**argv){
 std::filesystem::path dir=argv[1];std::filesystem::create_directories(dir);
 const std::string legacy=R"({"schemaVersion":1,"ports":["none","rumble","none","controller"]})";
 {std::ofstream out(dir/"controller-paks.json");out<<legacy;}
 configure_paks(dir,true);
 std::vector<uint8_t>ram(0x800000);auto*rdram=ram.data();recomp_context ctx{};ctx.r4=0xffffffff80110000ull;ctx.r7=0xffffffff80100000ull;ctx.r29=0xffffffff807ff000ull;MEM_W(16,ctx.r29)=0;
 for(unsigned p=0;p<4;++p){assert(pak_accessory(p)==PakAccessory::Controller);set_pak_port_connected(p,true);ctx.r5=p;ctx.r6=40;
  for(unsigned n=0;n<32;++n)MEM_B(n,ctx.r7)=uint8_t(n+p*39);
  pak_service_lookup(0x80062000)(rdram,&ctx);assert(ctx.r2==0);
 }
 shutdown_paks();configure_paks(dir,true);
 for(unsigned p=0;p<4;++p){set_pak_port_connected(p,true);ctx.r5=p;ctx.r6=40;pak_service_lookup(0x80061e10)(rdram,&ctx);assert(ctx.r2==0);for(unsigned n=0;n<32;++n)assert(MEM_BU(n,ctx.r7)==uint8_t(n+p*39));}
 set_pak_port_connected(2,false);ctx.r5=2;pak_service_lookup(0x80061e10)(rdram,&ctx);assert(ctx.r2==4);
 std::ifstream in(dir/"controller-paks.json");assert(std::string((std::istreambuf_iterator<char>(in)),{})==legacy);shutdown_paks();
}'''
  with tempfile.TemporaryDirectory()as tmp:
   p=Path(tmp);(p/'test.cpp').write_text(code)
   r=subprocess.run(['c++','-std=c++20','-DISS2000_PAL_ENGLISH','-pthread','-I'+str(ROOT/'src'),'-I'+str(ROOT/'.local/deps/N64Recomp/include'),'-I'+str(ROOT/'.local/deps/N64ModernRuntime/thirdparty'),str(p/'test.cpp'),str(ROOT/'src/runtime/pak_services.cpp'),str(ROOT/'src/runtime/controller_pak.cpp'),'-o',str(p/'test')],capture_output=True,text=True)
   self.assertEqual(r.returncode,0,r.stderr)
   r=subprocess.run([str(p/'test'),str(p/'saves')],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
