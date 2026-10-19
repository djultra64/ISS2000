"""Original work: djultra64. Execute pinned RT64 raw-TMEM content hashing."""
from pathlib import Path
import shutil, subprocess, tempfile, unittest
ROOT=Path(__file__).resolve().parents[1]
class RawTMEMIdentityTests(unittest.TestCase):
 def test_actual_upload_hash_covers_texels_palette_range_and_owned_copy(self):
  path=ROOT/'.local/deps/rt64/src/hle/rt64_rdp_tmem.cpp'
  if not path.is_file()or not shutil.which('c++'):self.skipTest('Pinned RT64 checkout and C++ compiler required')
  source=path.read_text();begin=source.index('    uint64_t TextureManager::uploadTMEM(');end=source.index('    uint64_t TextureManager::uploadTexture(',begin)
  function=source[begin:end]
  fixture=r'''#define XXH_INLINE_ALL
#include "xxHash/xxh3.h"
#include <array>
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <unordered_set>
#include <vector>
namespace RT64 {
constexpr unsigned RDP_TMEM_BYTES=4096;
struct LoadTile{};
struct RDP{uint64_t TMEM[512]{};};
struct State{RDP*rdp;std::filesystem::path dumpingTexturesDirectory;};
struct TextureCache{
 std::vector<std::array<uint8_t,4096>>uploads;
 void queueGPUUploadTMEM(uint64_t,uint64_t,const uint8_t*bytes,unsigned size,uint16_t,uint16_t,unsigned,LoadTile,bool decoded){assert(size==4096&&!decoded);std::array<uint8_t,4096>copy;memcpy(copy.data(),bytes,size);uploads.push_back(copy);}
};
struct TextureManager{
 std::unordered_set<uint64_t>hashSet;
 uint64_t uploadTMEM(State*,const LoadTile&,TextureCache*,uint64_t,uint16_t,uint16_t,uint16_t,uint16_t,uint32_t);
 void dumpTexture(uint64_t,State*,const LoadTile&,uint16_t,uint16_t,uint32_t){assert(false);}
};
FUNCTION
}
int main(){using namespace RT64;RDP rdp;State s{&rdp,{}};TextureManager manager;TextureCache cache;auto*bytes=reinterpret_cast<uint8_t*>(rdp.TMEM);
 for(unsigned i=0;i<4096;++i)bytes[i]=uint8_t(i*13+7);
 auto hash=[&](uint64_t frame=1,uint16_t offset=0,uint16_t size=4096){return manager.uploadTMEM(&s,{},&cache,frame,offset,size,320,240,2);};
 const auto first=hash();assert(first&&cache.uploads.size()==1);const auto owned=cache.uploads[0];assert(hash(99)==first&&cache.uploads.size()==1);
 // Raw hashing covers all texel banks and the entire upper-half TLUT, including
 // palette entries outside the immediate visible cell. Never trust pointer IDs.
 for(unsigned offset:{0u,127u,2047u,2048u,3072u,4095u}){bytes[offset]^=0x80;const auto changed=hash();assert(changed&&changed!=first);bytes[offset]^=0x80;assert(hash()==first);assert(cache.uploads[0]==owned);}
 assert(hash(1,0,2048)!=first&&hash(1,2048,2048)!=hash(1,0,2048));
 // Uploads own their byte copy; later mutable producer TMEM cannot alter it.
 memset(bytes,0,4096);assert(cache.uploads[0]==owned&&hash()!=first);
}
'''.replace('FUNCTION',function)
  with tempfile.TemporaryDirectory()as directory:
   p=Path(directory);(p/'probe.cpp').write_text(fixture)
   built=subprocess.run(['c++','-std=c++20','-O1','-Wall','-Wextra','-Werror','-I'+str(ROOT/'.local/deps/rt64/src/contrib'),str(p/'probe.cpp'),'-o',str(p/'probe')],capture_output=True,text=True)
   self.assertEqual(built.returncode,0,built.stderr)
   result=subprocess.run([str(p/'probe')],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
 def test_actual_copy_fallback_retains_non_content_id_and_dimensions(self):
  path=ROOT/'.local/deps/rt64/src/hle/rt64_state.cpp'
  if not path.is_file()or not shutil.which('c++'):self.skipTest('Pinned RT64 checkout and C++ compiler required')
  source=path.read_text()
  start=source.index('            if (callTile.tileCopyUsed) {',source.index('// Invalidate the use of the tile copy'))
  end=source.index('            // Determine if the use of raw TMEM',start)
  fallback=source[start:end]
  start=source.index('            if (!callTile.tileCopyUsed) {',source.index('auto uploadTile ='))
  end=source.index('            else if (callTile.reinterpretTile)',start)
  upload=source[start:end]
  fixture=r'''#include <cassert>
#include <cstdint>
constexpr unsigned RDP_TMEM_BYTES=4096;
struct LoadTile{};
struct Tile{LoadTile loadTile;uint64_t tmemHashOrID=0xfeed1234;bool tileCopyUsed=true,rawTMEM=true;uint16_t tileCopyWidth=8,tileCopyHeight=8,sampleWidth=16,sampleHeight=16;uint32_t tlut=2;};
struct Workload{uint64_t submissionFrame=3;};
struct Manager{
 unsigned empty{},raw{},decoded{};
 template<class...T>void uploadEmpty(T...){++empty;}
 template<class...T>uint64_t uploadTMEM(T...){++raw;return 0xabcd5678;}
 template<class...T>uint64_t uploadTexture(T...){++decoded;return 0x11112222;}
};
struct State{Manager textureManager;struct{void*textureCache=nullptr;}ext;
 void upload(Tile&callTile,Workload&workload){UPLOAD}
};
void originalFallback(Tile&callTile){struct{int x=16,y=16;}maxTexcoord;FALLBACK}
int main(){Tile tile;originalFallback(tile);
 // Execute actual pinned branches: insufficient copy clears only its flag.
 // The retained hash-shaped value is a framebuffer ID, and uploadEmpty owns no
 // new image content. Both retained dimensions must disqualify interpolation.
 assert(!tile.tileCopyUsed&&tile.rawTMEM&&tile.tileCopyWidth==8&&tile.tileCopyHeight==8&&tile.tmemHashOrID==0xfeed1234);
 State state;Workload workload;state.upload(tile,workload);
 assert(state.textureManager.empty==1&&!state.textureManager.raw&&!state.textureManager.decoded&&tile.tmemHashOrID==0xfeed1234);
 // Genuine fresh raw storage has no copy dimensions and acquires its own hash.
 tile.tmemHashOrID=0;tile.tileCopyWidth=tile.tileCopyHeight=0;state.upload(tile,workload);
 assert(state.textureManager.raw==1&&tile.tmemHashOrID==0xabcd5678);
}
'''.replace('FALLBACK',fallback).replace('UPLOAD',upload)
  with tempfile.TemporaryDirectory()as directory:
   p=Path(directory);(p/'probe.cpp').write_text(fixture)
   built=subprocess.run(['c++','-std=c++20','-O1','-Wall','-Wextra','-Werror',str(p/'probe.cpp'),'-o',str(p/'probe')],capture_output=True,text=True)
   self.assertEqual(built.returncode,0,built.stderr)
   result=subprocess.run([str(p/'probe')],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
