"""Bounded guest ABI tests for Controller Pak service adapters; no game execution.
Original project work: djultra64.
"""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless((ROOT/'.local/deps/N64Recomp/include/recomp.h').is_file(), 'Pinned recompiler headers required')
class PakServiceTests(unittest.TestCase):
 def test_guest_bridge_selection_and_restart(self):
  self.check_guest_bridge(False)
 def test_pal_guest_bridge_selection_and_restart(self):
  self.check_guest_bridge(True)
 def check_guest_bridge(self,pal):
  with tempfile.TemporaryDirectory(prefix='iss2000-pak-abi-') as directory:
   folder=Path(directory);source=folder/'abi.cpp';source.write_text(r'''
#include "runtime/pak_services.hpp"
#include <vector>
#include <fstream>
#include <stdexcept>
#include <iostream>
#ifndef _WIN32
#include <sys/stat.h>
#include <cerrno>
#endif
using namespace iss2000;
void require(bool b){if(!b)throw std::runtime_error("Pak ABI contract failed");}
#ifndef _WIN32
bool reject_directory_sync=false;
extern "C" int __real_fsync(int);
extern "C" int __wrap_fsync(int fd){
 struct stat info{};if(fstat(fd,&info)==0&&S_ISDIR(info.st_mode)&&reject_directory_sync){errno=EIO;return -1;}
 return __real_fsync(fd);
}
#endif
int main(int argc,char** argv){try{
 if(argc>2&&std::string(argv[2])=="invalid"){
  bool rejected=false;try{configure_paks(argv[1]);}catch(const std::exception&){rejected=true;}require(rejected);return 0;
 }
#ifndef _WIN32
 if(argc>2&&std::string(argv[2])=="faildir"){
  configure_paks(argv[1]);reject_directory_sync=true;
  bool failed=false;try{set_pak_accessory(0,PakAccessory::None);}catch(const std::exception&){failed=true;}
  require(failed);require(pak_accessory(0)==PakAccessory::Controller);
  // The atomic rename may have committed a new complete file before fsync failed.
  std::ifstream file(std::filesystem::path(argv[1])/"controller-paks.json");
  std::string text((std::istreambuf_iterator<char>(file)),{});require(text.find("schemaVersion")!=std::string::npos);return 0;
 }
#endif
 require(pak_accessory(0)==PakAccessory::None);require(pak_service_lookup(0x80060550)==nullptr);
 configure_paks(argv[1]);require(pak_accessory(0)==PakAccessory::Controller);require(pak_accessory(1)==PakAccessory::None);
 set_pak_accessory(1,PakAccessory::Controller);
 std::vector<uint8_t> ram(0x800000);auto* rdram=ram.data();recomp_context ctx{};
 constexpr gpr buffer=0xFFFFFFFF80100000ull,queue=0xFFFFFFFF80110000ull;
 ctx.r4=queue;ctx.r5=1;pak_service_lookup(0x80060880)(rdram,&ctx);require(ctx.r2==4);
 set_pak_port_connected(1,true);pak_service_lookup(0x80060880)(rdram,&ctx);require(ctx.r2==2);pak_service_lookup(0x80060880)(rdram,&ctx);require(ctx.r2==0);
 set_pak_port_connected(1,false);pak_service_lookup(0x80060880)(rdram,&ctx);require(ctx.r2==4);
 set_pak_port_connected(1,true);pak_service_lookup(0x80060880)(rdram,&ctx);require(ctx.r2==2);pak_service_lookup(0x80060880)(rdram,&ctx);require(ctx.r2==0);
 set_pak_port_connected(1,false);
 bool invalid=false;try{set_pak_port_connected(4,true);}catch(const std::out_of_range&){invalid=true;}require(invalid);
 ctx.r4=queue;ctx.r5=0;pak_service_lookup(0x80060880)(rdram,&ctx);require(ctx.r2==0);require(MEM_BU(0,gpr(0xFFFFFFFF8009C434ull))==0xFA);
 ctx.r4=queue;ctx.r5=buffer;pak_service_lookup(0x80060060)(rdram,&ctx);require(ctx.r2==0&&MEM_BU(0,buffer)==1);
 ctx.r4=queue;ctx.r5=0;ctx.r6=40;ctx.r7=buffer;ctx.r29=gpr(0xFFFFFFFF807FF000ull);MEM_W(16,ctx.r29)=0;
 for(unsigned n=0;n<32;++n)MEM_B(n,buffer)=uint8_t(n*11);
 pak_service_lookup(0x80061780)(rdram,&ctx);require(ctx.r2==0);
 for(unsigned n=0;n<32;++n)MEM_B(n,buffer)=0;
 pak_service_lookup(0x80061590)(rdram,&ctx);require(ctx.r2==0);for(unsigned n=0;n<32;++n)require(MEM_BU(n,buffer)==uint8_t(n*11));
 ctx.r7=0xFFFFFFFF807FFFF0ull;pak_service_lookup(0x80061590)(rdram,&ctx);require(ctx.r2==5);
 ctx.r7=0x180100000ull;pak_service_lookup(0x80061590)(rdram,&ctx);require(ctx.r2==5);
 ctx.r7=buffer;ctx.r5=4;pak_service_lookup(0x80061590)(rdram,&ctx);require(ctx.r2==5);
 set_pak_accessory(0,PakAccessory::Rumble);require(pak_accessory(0)==PakAccessory::Rumble);
 ctx.r5=0;pak_service_lookup(0x80060880)(rdram,&ctx);require(ctx.r2==2);pak_service_lookup(0x80060880)(rdram,&ctx);require(ctx.r2==0);
 shutdown_paks();require(pak_accessory(0)==PakAccessory::None);configure_paks(argv[1]);require(pak_accessory(0)==PakAccessory::Rumble);
 ctx.r4=queue;ctx.r5=0;pak_service_lookup(0x80060880)(rdram,&ctx);require(ctx.r2==0);
 shutdown_paks();return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
''')
   if pal:
    original=source.read_text()
    for old,new in {'80060550':'80060DD0','80061590':'80061E10','80061780':'80062000','80060880':'80061100','80060060':'800608E0','8009C434':'80099A44'}.items():
     original=original.replace(old,new)
    # The other revision's physical-device entrypoints must remain unmapped.
    original=original.replace(' configure_paks(argv[1]);require(pak_accessory(0)==PakAccessory::Controller);', ' require(pak_service_lookup(0x80061590)==nullptr);require(pak_service_lookup(0x80060880)==nullptr);\n configure_paks(argv[1]);require(pak_accessory(0)==PakAccessory::Controller);')
    source.write_text(original)
   exe=folder/'abi' 
   result=subprocess.run(['c++',*(['-DISS2000_PAL_ENGLISH'] if pal else []),'-std=c++20','-Wall','-Wextra','-Werror','-pthread',*(['-Wl,--wrap=fsync'] if sys.platform!='win32' else []),'-I',str(ROOT/'src'),'-I',str(ROOT/'.local/deps/N64Recomp/include'),'-I',str(ROOT/'.local/deps/N64ModernRuntime/thirdparty'),str(source),str(ROOT/'src/runtime/pak_services.cpp'),str(ROOT/'src/runtime/controller_pak.cpp'),'-o',str(exe)],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
   result=subprocess.run([str(exe),str(folder/'saves')],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
   for text in ['{"schemaVersion":1,"ports":["controller"]}', '{"schemaVersion":9,"ports":["none","none","none","none"]}', '{"schemaVersion":1,"schemaVersion":1,"ports":["none","none","none","none"]}', 'original malformed preferences']:
    bad=folder/'invalid-prefs';bad.mkdir(exist_ok=True);path=bad/'controller-paks.json';path.write_text(text)
    result=subprocess.run([str(exe),str(bad),'invalid'],capture_output=True,text=True)
    self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(path.read_text(),text)
    self.assertFalse((bad/'controller-pak-1.mpk').exists())
   if sys.platform!='win32':
    linkdir=folder/'symlink-prefs';linkdir.mkdir();target=folder/'external-prefs.json';target.write_text('preserve external preferences')
    link=linkdir/'controller-paks.json';link.symlink_to(target)
    result=subprocess.run([str(exe),str(linkdir),'invalid'],capture_output=True,text=True)
    self.assertEqual(result.returncode,0,result.stderr);self.assertTrue(link.is_symlink());self.assertEqual(target.read_text(),'preserve external preferences')
    result=subprocess.run([str(exe),str(folder/'sync-failure'),'faildir'],capture_output=True,text=True)
    self.assertEqual(result.returncode,0,result.stderr)
if __name__=='__main__':unittest.main()
