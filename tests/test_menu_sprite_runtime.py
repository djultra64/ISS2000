"""Original project work: djultra64. Genuine sprite producer and immutablequeuedmetadata."""
from pathlib import Path
import json,struct,shutil,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
CODE=r'''#include "recomp.h"
#include "runtime/menu_sprite_runtime.hpp"
#include "runtime/pal_radar_interpolation.hpp"
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <set>
#include <thread>
#include <string_view>
DECLS
using namespace iss2000;using Bytes=std::vector<uint8_t>;
extern "C" recomp_func_t*get_function(int32_t a){switch(uint32_t(a)){LOOKUP default:std::abort();}}
extern "C" void do_break(uint32_t){std::abort();}extern "C" void switch_error(const char*,uint32_t,uint32_t){std::abort();}
uint32_t word(const Bytes&r,uint32_t a){uint32_t v;memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
void put(Bytes&r,uint32_t a,uint32_t v){memcpy(r.data()+(a&0x7fffff),&v,4);}
Bytes load(const char*p){FILE*f=fopen(p,"rb");assert(f);fseek(f,0,SEEK_END);size_t n=ftell(f);rewind(f);Bytes b(n);assert(fread(b.data(),1,n,f)==n);fclose(f);return b;}
int main(int argc,char**argv){assert(argc==4);auto rom=load(argv[1]),r=load(argv[2]);assert(configure_menu_sprite_runtime(rom));auto wrong=rom;wrong[0]^=1;assert(!configure_menu_sprite_runtime(wrong));
 recomp_context c{};c.r29=int32_t(0x800a4000);c.f_odd=&c.f0.u32h;const unsigned object=0x8013c92c,head=word(r,0x800a4aa4)+8;
 TransformTaskFingerprint task{.data_ptr=head,.ucode=0x80069ad0,.ucode_data=0x80099ef0,.data_size=0x100};
 auto draw=[&](){put(r,0x8009e0c8,head);begin_menu_sprite_frame(r);auto observation=observe_menu_sprite_before(r,object);assert(observation.valid);auto context=c;context.f_odd=&context.f0.u32h;context.r4=int32_t(object);func_80041B50_resident(r.data(),&context);observe_menu_sprite_after(r,observation);submit_menu_sprite_metadata(1,task);};
 observe_menu_sprite_initialization(object);draw();auto first=consume_menu_sprite_metadata(task);assert(first&&first->commands.size()==2);auto ids=first->commands;auto values=[](const auto&commands){std::set<uint32_t>out;for(auto [pc,id]:commands)out.insert(id);return out;};
 // A real original sprite moves and fades: command identity remainsstable.
 put(r,object+0x20,word(r,object+0x20)+0x40000);r[((object+0x11)&0x7fffff)^3]=96;draw();bool fade=false;for(auto pc=head;pc<word(r,0x8009e0c8);pc+=8)if(word(r,pc)>>24==0xfa)fade|=(word(r,pc+4)&255)==96;assert(fade);auto second=consume_menu_sprite_metadata(task);assert(second&&values(second->commands)==values(ids)&&second->sequence>first->sequence);
 // BB8 rotates the original Gfx bank after frameentry. Producer captures
 // must follow the current bank, not reject all alternate-frame rectangles.
 begin_menu_sprite_frame(r);auto alternate=word(r,0x800a4aa4)==0x800d0320?0x800e0380u:0x800d0320u;put(r,0x800a4aa4,alternate);put(r,0x8009e0c8,alternate+8);auto rotated=observe_menu_sprite_before(r,object);auto rc=c;rc.f_odd=&rc.f0.u32h;rc.r4=int32_t(object);func_80041B50_resident(r.data(),&rc);observe_menu_sprite_after(r,rotated);auto rotatedTask=task;rotatedTask.data_ptr=alternate+8;submit_menu_sprite_metadata(1,rotatedTask);assert(consume_menu_sprite_metadata(rotatedTask)->commands.size()==2);put(r,0x800a4aa4,head-8);
 // Genuine completed yellow SelectTeams leaves A4AA4=0. The host frame
 // observer runs before originalBB8/2A10 acquires its next task bank. A released
 // owner at frameentry must defer until the first actual original sprite draw.
 put(r,0x800a4aa4,0);put(r,0x8009e0c8,head);begin_menu_sprite_frame(r);assert(!observe_menu_sprite_before(r,object).valid);
 put(r,0x800a4aa4,head-8);auto acquired=observe_menu_sprite_before(r,object);assert(acquired.valid);auto ac=c;ac.f_odd=&ac.f0.u32h;ac.r4=int32_t(object);func_80041B50_resident(r.data(),&ac);observe_menu_sprite_after(r,acquired);submit_menu_sprite_metadata(1,task);assert(consume_menu_sprite_metadata(task)->commands.size()==2);
 // A foreign nonzero frameowner cannot gain authority later in that frame.
 put(r,0x800a4aa4,0x80001000);begin_menu_sprite_frame(r);put(r,0x800a4aa4,head-8);assert(!observe_menu_sprite_before(r,object).valid);
 // Queued metadata owns its identity across later object reuse andscenecuts.
 draw();observe_menu_sprite_initialization(object);draw();auto old=consume_menu_sprite_metadata(task),fresh=consume_menu_sprite_metadata(task);assert(old&&fresh&&values(old->commands)==values(ids)&&values(fresh->commands)!=values(ids)&&first->commands==ids);
 draw();notify_menu_sprite_discontinuity();draw();old=consume_menu_sprite_metadata(task);fresh=consume_menu_sprite_metadata(task);assert(old&&fresh&&old->epoch!=fresh->epoch&&old->commands!=fresh->commands);
 // Stale observations cannot leak across frame boundaries. Unknown/nongraphics
 // submissions and a fingerprint mismatch cannot reuse last frame'smetadata.
 put(r,0x8009e0c8,head);begin_menu_sprite_frame(r);auto stale=observe_menu_sprite_before(r,object);begin_menu_sprite_frame(r);observe_menu_sprite_after(r,stale);submit_menu_sprite_metadata(1,task);assert(consume_menu_sprite_metadata(task)->commands.empty());
 begin_menu_sprite_frame(r);assert(!observe_menu_sprite_before(r,0x80001000).valid);submit_menu_sprite_metadata(2,task);draw();assert(consume_menu_sprite_metadata(task)->commands.size()==2);
 // The original font path emits directE4 rectangles, bypassing41B50.
 // Capture its complete originalclosure, retaining pool lifetime and textstyle.
 const uint32_t text=0x8013c9a4,source=0x807f1000;for(unsigned i=0;i<0x24;++i)r[((text+i)&0x7fffff)^3]=0;r[((text+4)&0x7fffff)^3]=2;put(r,text+0x14,source);put(r,text+0xc,0x00000050);put(r,text+0x10,0x00400000);put(r,text+0x20,0x0000ffff);r[(source&0x7fffff)^3]=0x0b;r[((source+1)&0x7fffff)^3]=0x0c;r[((source+2)&0x7fffff)^3]=0xff;r[((source+3)&0x7fffff)^3]=0x11;
 auto font=[&](){put(r,0x8009e0c8,head);begin_menu_sprite_frame(r);auto observation=observe_menu_text_before(r,text);assert(observation.valid);auto context=c;context.f_odd=&context.f0.u32h;context.r4=int32_t(text);func_80048660_resident(r.data(),&context);observe_menu_sprite_after(r,observation);submit_menu_sprite_metadata(1,task);auto result=consume_menu_sprite_metadata(task);assert(result&&result->commands.size()==2);return values(result->commands);};
 observe_menu_sprite_initialization(text);auto fontIds=font();put(r,text+0xc,0x00000054);assert(font()==fontIds);observe_menu_sprite_initialization(text);assert(font()!=fontIds);
 put(r,0x8009e0c8,head);begin_menu_sprite_frame(r);memcpy(r.data()+0xa3800,r.data()+(text&0x7fffff),0x24);assert(!observe_menu_text_before(r,0x800a3800).valid);
 {MenuSpriteSemanticScope page(0x464f4e5450414745ULL);auto o=observe_menu_text_before(r,0x800a3800);assert(o.valid);auto context=c;context.f_odd=&context.f0.u32h;context.r4=int32_t(0x800a3800);func_80048660_resident(r.data(),&context);observe_menu_sprite_after(r,o);}submit_menu_sprite_metadata(1,task);assert(consume_menu_sprite_metadata(task)->commands.size()==2);

 // Reused temporarystackobjects require explicit semantic scope, not guesses.
 put(r,0x8009e0c8,head);begin_menu_sprite_frame(r);assert(!observe_menu_sprite_before(r,0x800a3800).valid);
 {MenuSpriteSemanticScope scope(0x504353455454494eULL);memcpy(r.data()+0xa3800,r.data()+(object&0x7fffff),0x3c);auto observation=observe_menu_sprite_before(r,0x800a3800);assert(observation.valid);auto context=c;context.f_odd=&context.f0.u32h;context.r4=int32_t(0x800a3800);func_80041B50_resident(r.data(),&context);observe_menu_sprite_after(r,observation);}submit_menu_sprite_metadata(1,task);assert(consume_menu_sprite_metadata(task)->commands.size()==2);
 // Private radar ownership shares FIFO IDs without weakening main-arena bounds.
 const uint32_t radar=0x802b4408;
 auto radarDraw=[&](uint64_t generation,bool reachable,bool submit=true){
  put(r,0x800a4aa4,head-8);put(r,0x8009e0c8,head);begin_menu_sprite_frame(r);
  retire_menu_radar_bank(radar);
  put(r,head,reachable?0xde000000:0xdf000000);put(r,head+4,reachable?radar:0);put(r,head+8,0xdf000000);put(r,head+12,0);
  put(r,radar,0xe4004040);put(r,radar+4,0);put(r,radar+8,0xe1000000);put(r,radar+12,0);put(r,radar+16,0xf1000000);put(r,radar+20,0x04000400);put(r,radar+24,0xdf000000);put(r,radar+28,0);
  PalRadarCapture capture;assert(capture.begin(r,{11,0x80145624,1,1},0,radar));assert(capture.emit(r,radar,radar+24,{12,0x801456bc,generation,1},1));assert(capture.finish(r,radar+32));
  observe_menu_radar(r,capture);if(submit)submit_menu_sprite_metadata(1,task,r);
 };
 radarDraw(1,true);auto ra=consume_menu_sprite_metadata(task,r);assert(ra->commands.size()==1);
 radarDraw(1,true);auto rb=consume_menu_sprite_metadata(task,r);assert(ra->commands==rb->commands);
 radarDraw(2,true);auto rcapture=consume_menu_sprite_metadata(task,r);assert(ra->commands!=rcapture->commands);
 radarDraw(2,true,false);put(r,0x800a4aa4,0);begin_menu_sprite_frame(r);submit_menu_sprite_metadata(1,task,r);assert(consume_menu_sprite_metadata(task,r)->commands.size()==1);
 radarDraw(2,true,false);put(r,0x800a4aa4,0);begin_menu_sprite_frame(r);retire_menu_radar_bank(radar);submit_menu_sprite_metadata(1,task,r);assert(consume_menu_sprite_metadata(task,r)->commands.empty());
 radarDraw(2,false);assert(consume_menu_sprite_metadata(task,r)->commands.empty());
 radarDraw(2,true);put(r,radar+12,7);assert(consume_menu_sprite_metadata(task,r)->commands.empty());
 radarDraw(2,true);retire_menu_radar_bank(radar);assert(consume_menu_sprite_metadata(task,r)->commands.empty());
 // Upstream implicit per-thread streams do not guarantee cross-producerFIFO,
 // even when two producers use the exact same task fingerprint.
 if(std::string_view(argv[3])=="missing"){assert(!consume_menu_sprite_metadata(task));}else{draw();if(std::string_view(argv[3])=="mismatch"){auto foreign=task;foreign.data_size+=8;assert(!consume_menu_sprite_metadata(foreign));}else if(std::string_view(argv[3])=="overflow"){for(unsigned n=0;n<64;++n)submit_menu_sprite_metadata(1,task);}else{std::thread foreignProducer([&]{submit_menu_sprite_metadata(1,task);});foreignProducer.join();}}assert(!consume_menu_sprite_metadata(task));begin_menu_sprite_frame(r);submit_menu_sprite_metadata(1,task);assert(!consume_menu_sprite_metadata(task));
}
'''
TEAM_FLASH_CODE=r'''#include "recomp.h"
#include "runtime/menu_sprite_runtime.hpp"
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <set>
DECLS
using namespace iss2000;using Bytes=std::vector<uint8_t>;
extern "C" recomp_func_t*get_function(int32_t a){switch(uint32_t(a)){LOOKUP default:std::abort();}}
extern "C" void do_break(uint32_t){std::abort();}extern "C" void switch_error(const char*,uint32_t,uint32_t){std::abort();}
uint32_t word(const Bytes&r,uint32_t a){uint32_t v;memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
void put(Bytes&r,uint32_t a,uint32_t v){memcpy(r.data()+(a&0x7fffff),&v,4);}
Bytes load(const char*p){FILE*f=fopen(p,"rb");assert(f);fseek(f,0,SEEK_END);size_t n=ftell(f);rewind(f);Bytes b(n);assert(fread(b.data(),1,n,f)==n);fclose(f);return b;}
int main(int argc,char**argv){assert(argc==4);auto rom=load(argv[1]),r=load(argv[2]);assert(configure_menu_sprite_runtime(rom));
 constexpr uint32_t object=0x8013CE54;const auto head=word(r,0x800A4AA4)+8;observe_menu_sprite_initialization(object);
 TransformTaskFingerprint task{.data_ptr=head,.ucode=0x80069ad0,.ucode_data=0x80099ef0,.data_size=0x100};
 std::shared_ptr<const MenuSpriteTaskSnapshot> previous;
 for(unsigned frame=0;frame<3;++frame){const uint8_t alpha=frame?96:80;r[((object+0x11)&0x7fffff)^3]=alpha;put(r,0x8009E0C8,head);
  auto expected=r;recomp_context c{};c.r29=int32_t(0x800A4000);c.f_odd=&c.f0.u32h;c.r4=int32_t(object);func_80041B50_resident(expected.data(),&c);
  begin_menu_sprite_frame(r);const auto observation=observe_menu_sprite_before(r,object);assert(observation.valid);
  c={};c.r29=int32_t(0x800A4000);c.f_odd=&c.f0.u32h;c.r4=int32_t(object);func_80041B50_resident(r.data(),&c);observe_menu_sprite_after(r,observation);
  assert(r==expected&&"Flash observer must preserve ALL original RAM");submit_menu_sprite_metadata(1,task);auto snapshot=consume_menu_sprite_metadata(task);assert(snapshot&&!snapshot->commands.empty());
  unsigned rectangles=0,colors=0;for(auto pc=head;pc<word(r,0x8009E0C8);pc+=8){const auto op=word(r,pc);if(op>>24==0xE4){++rectangles;assert(snapshot->commands.contains(pc&0x7fffff));}if(op>>24==0xFA){++colors;assert((word(r,pc+4)&255)==alpha);}}
  assert(rectangles==snapshot->commands.size()&&rectangles==30&&colors);
  if(previous){std::set<uint32_t>now_ids,previous_ids;for(const auto&[pc,id]:snapshot->commands)now_ids.insert(id);for(const auto&[pc,id]:previous->commands)previous_ids.insert(id);assert(now_ids==previous_ids&&snapshot->sequence==previous->sequence+1&&snapshot->epoch==previous->epoch);}
  previous=snapshot;
 }
}
'''
BANK_CODE=r'''#include "recomp.h"
#include "runtime/menu_sprite_runtime.hpp"
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <set>
DECLS
using namespace iss2000;using Bytes=std::vector<uint8_t>;
extern "C" recomp_func_t*get_function(int32_t a){switch(uint32_t(a)){LOOKUP default:std::abort();}}
extern "C" void do_break(uint32_t){std::abort();}extern "C" void switch_error(const char*,uint32_t,uint32_t){std::abort();}
uint32_t word(const Bytes&r,uint32_t a){uint32_t v;memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
void put(Bytes&r,uint32_t a,uint32_t v){memcpy(r.data()+(a&0x7fffff),&v,4);}
Bytes load(const char*p){FILE*f=fopen(p,"rb");assert(f);fseek(f,0,SEEK_END);size_t n=ftell(f);rewind(f);Bytes b(n);assert(fread(b.data(),1,n,f)==n);fclose(f);return b;}
int main(int argc,char**argv){assert(argc==4);auto rom=load(argv[1]),r=load(argv[2]);assert(configure_menu_sprite_runtime(rom));
 constexpr uint32_t A=0x800d0320,B=0x800e0380,object=0x8013c92c;
 auto task=[](uint32_t bank){return TransformTaskFingerprint{.data_ptr=bank+8,.ucode=0x80069ad0,.ucode_data=0x80099ef0,.data_size=0x100};};
 auto ids=[](const auto&commands){std::set<uint32_t>out;for(auto [pc,id]:commands)out.insert(id);return out;};
 auto begin=[&](uint32_t bank){put(r,0x800a4aa4,bank);put(r,0x8009e0c8,bank+8);auto before=r;begin_menu_sprite_frame(r);assert(r==before);};
 auto draw=[&](uint32_t bank){begin(bank);auto expected=r;recomp_context c{};c.r29=int32_t(0x800a4000);c.f_odd=&c.f0.u32h;c.r4=int32_t(object);func_80041B50_resident(expected.data(),&c);
  auto o=observe_menu_sprite_before(r,object);assert(o.valid);c={};c.r29=int32_t(0x800a4000);c.f_odd=&c.f0.u32h;c.r4=int32_t(object);func_80041B50_resident(r.data(),&c);observe_menu_sprite_after(r,o);assert(r==expected&&"Arena observer must preserve ALL original RAM");
  std::set<uint32_t>pcs;for(auto pc=bank+8;pc<word(r,0x8009e0c8);pc+=8)if(word(r,pc)>>24==0xe4)pcs.insert(pc&0x7fffff);assert(pcs.size()==2);return pcs;};
 auto submit=[&](uint32_t bank){auto before=r;auto t=task(bank);submit_menu_sprite_metadata(1,t);auto s=consume_menu_sprite_metadata(t);assert(s&&r==before);return s;};
 observe_menu_sprite_initialization(object);
 // The real scheduler submits A only after BB8 has drawn B. Retain the A
 // producer frame, rather than publishing B's PCs or silently empty metadata.
 auto apcs=draw(A);auto bpcs=draw(B);auto a=submit(A);
 assert(a->commands.size()==2&&"Delayed original task must retain its own arena metadata");for(auto [pc,id]:a->commands)assert(apcs.contains(pc)&&id);
 auto b=submit(B);assert(b->commands.size()==2&&a->sequence+1==b->sequence&&a->epoch==b->epoch&&ids(a->commands)==ids(b->commands));for(auto [pc,id]:b->commands)assert(bpcs.contains(pc));
 const auto original=a->commands;assert(submit(A)->commands.empty()&&submit(B)->commands.empty()&&a->commands==original);
 // Both opposite-bank directions keep source sequence and object lifetime.
 apcs=draw(A);observe_menu_sprite_initialization(object);bpcs=draw(B);a=submit(A);b=submit(B);assert(a->commands.size()==2&&b->commands.size()==2&&ids(a->commands)!=ids(b->commands));
 bpcs=draw(B);apcs=draw(A);b=submit(B);a=submit(A);assert(b->commands.size()==2&&a->commands.size()==2&&b->sequence+1==a->sequence&&ids(a->commands)==ids(b->commands));
 // Drawing into a reused arena retires its old owner even when no eligible
 // sprite follows. An arena from more than one producer frame ago is stale.
 draw(A);draw(B);begin(A);assert(submit(A)->commands.empty());
 draw(A);draw(B);draw(B);assert(submit(A)->commands.empty()&&submit(B)->commands.size()==2);
 // Same-arena immediate submission still works; unsupported microcode cannot
 // consume a retained owner and later replay it under a different fingerprint.
 draw(A);assert(submit(A)->commands.size()==2);draw(A);draw(B);auto foreign=task(A);foreign.ucode+=8;submit_menu_sprite_metadata(1,foreign);assert(consume_menu_sprite_metadata(foreign)->commands.empty());assert(submit(A)->commands.empty());
 // A cut retires both unsubmitted arenas without mutating alreadyqueued copies.
 draw(A);draw(B);auto t=task(A);submit_menu_sprite_metadata(1,t);notify_menu_sprite_discontinuity();auto queued=consume_menu_sprite_metadata(t);assert(queued&&queued->commands.size()==2);assert(submit(B)->commands.empty()&&queued->commands.size()==2);
 draw(A);assert(submit(A)->commands.size()==2);
}
'''
FIELD_CODE=r'''#include "recomp.h"
#include "runtime/menu_sprite_runtime.hpp"
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <set>
#include <array>
DECLS
using namespace iss2000;using Bytes=std::vector<uint8_t>;
extern "C" recomp_func_t*get_function(int32_t a){switch(uint32_t(a)){LOOKUP default:std::abort();}}
extern "C" void do_break(uint32_t){std::abort();}extern "C" void switch_error(const char*,uint32_t,uint32_t){std::abort();}
uint32_t word(const Bytes&r,uint32_t a){uint32_t v;memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
void put(Bytes&r,uint32_t a,uint32_t v){memcpy(r.data()+(a&0x7fffff),&v,4);}
uint8_t byte(const Bytes&r,uint32_t a){return r[(a&0x7fffff)^3];}
void sb(Bytes&r,uint32_t a,uint8_t v){r[(a&0x7fffff)^3]=v;}
Bytes load(const char*p){FILE*f=fopen(p,"rb");assert(f);fseek(f,0,SEEK_END);size_t n=ftell(f);rewind(f);Bytes b(n);assert(fread(b.data(),1,n,f)==n);fclose(f);return b;}
int main(int argc,char**argv){assert(argc==4);auto rom=load(argv[1]),r=load(argv[2]);assert(configure_menu_sprite_runtime(rom));
 assert(byte(r,0x8013b446)==6&&byte(r,0x8013b44c)==4&&!byte(r,0x8013b452)&&!byte(r,0x8013b42a));
 constexpr uint32_t object=0x8013c4b8,bank=0x800d0320;assert(word(r,object+0x14)==0x80076f70&&word(r,object+0x30)==0x8026182c);
 TransformTaskFingerprint task{.data_ptr=bank+8,.ucode=0x80069ad0,.ucode_data=0x80099ef0,.data_size=0x100};
 auto ids=[](const auto&commands){std::set<uint32_t>out;for(auto [pc,id]:commands)out.insert(id);return out;};
 struct Captured{std::shared_ptr<const MenuSpriteTaskSnapshot>snapshot;std::array<uint32_t,2>rect;};
 auto draw=[&](){put(r,0x800a4aa4,bank);put(r,0x8009e0c8,bank+8);auto pristine=r;begin_menu_sprite_frame(r);assert(r==pristine);
  auto o=observe_menu_sprite_before(r,object);assert(o.valid&&"Live original field HUD uses the shared sprite producer");
  auto expected=r;recomp_context c{};c.r29=int32_t(0x800a4000);c.f_odd=&c.f0.u32h;c.r4=int32_t(object);func_80041B50_resident(expected.data(),&c);
  c={};c.r29=int32_t(0x800a4000);c.f_odd=&c.f0.u32h;c.r4=int32_t(object);func_80041B50_resident(r.data(),&c);observe_menu_sprite_after(r,o);assert(r==expected&&"HUD observer preserves ALL original RAM");
  submit_menu_sprite_metadata(1,task);auto snapshot=consume_menu_sprite_metadata(task);if(!snapshot||snapshot->commands.empty()){for(auto pc=bank+8;pc<word(r,0x8009e0c8);pc+=8)std::fprintf(stderr,"%08x %08x %08x\n",pc,word(r,pc),word(r,pc+4));}assert(snapshot&&!snapshot->commands.empty()&&r==expected);std::array<uint32_t,2>rect{};unsigned n=0;
  for(auto pc=bank+8;pc<word(r,0x8009e0c8);pc+=8)if(word(r,pc)>>24==0xe4){assert(snapshot->commands.contains(pc&0x7fffff));if(!n)rect={word(r,pc),word(r,pc+4)};++n;}assert(n==snapshot->commands.size());
  assert(!observe_menu_sprite_before(r,0x800a3800).valid);return Captured{snapshot,rect};};
 observe_menu_sprite_initialization(object);auto first=draw();put(r,object+0x20,word(r,object+0x20)+0x40000);sb(r,object+0x11,96);auto moved=draw();
 assert(first.rect!=moved.rect&&ids(first.snapshot->commands)==ids(moved.snapshot->commands)&&first.snapshot->epoch==moved.snapshot->epoch&&first.snapshot->sequence+1==moved.snapshot->sequence);
 // Pause, resume and an explicit same-scene cut retire identities. Neither
 // causes a stale field owner to match the next original UI frame.
 sb(r,0x8013b452,1);auto paused=draw();assert(paused.snapshot->epoch!=moved.snapshot->epoch&&ids(paused.snapshot->commands)!=ids(moved.snapshot->commands));
 sb(r,0x8013b452,0);auto resumed=draw();assert(resumed.snapshot->epoch!=paused.snapshot->epoch);notify_menu_sprite_discontinuity();auto cut=draw();assert(cut.snapshot->epoch!=resumed.snapshot->epoch&&ids(cut.snapshot->commands)!=ids(resumed.snapshot->commands));
 // A different genuine HUD component's descriptor/segments changes material
 // identity even at the same position. Reinitialization changes lifetime too.
 put(r,object+0x14,word(r,0x8013c47c+0x14));put(r,object+0x30,word(r,0x8013c47c+0x30));auto material=draw();assert(ids(material.snapshot->commands)!=ids(cut.snapshot->commands));observe_menu_sprite_initialization(object);auto reused=draw();assert(ids(reused.snapshot->commands)!=ids(material.snapshot->commands));
 sb(r,0x8013b44c,7);auto scene=draw();assert(scene.snapshot->epoch!=reused.snapshot->epoch&&ids(scene.snapshot->commands)!=ids(reused.snapshot->commands));
}
'''
TEXT_POOL_CODE=r'''#include "recomp.h"
#include "runtime/menu_sprite_runtime.hpp"
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <set>
DECLS
using namespace iss2000;using Bytes=std::vector<uint8_t>;
extern "C" recomp_func_t*get_function(int32_t a){switch(uint32_t(a)){LOOKUP default:std::abort();}}
extern "C" void do_break(uint32_t){std::abort();}extern "C" void switch_error(const char*,uint32_t,uint32_t){std::abort();}
uint32_t word(const Bytes&r,uint32_t a){uint32_t v;memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
void put(Bytes&r,uint32_t a,uint32_t v){memcpy(r.data()+(a&0x7fffff),&v,4);}
Bytes load(const char*p){FILE*f=fopen(p,"rb");assert(f);fseek(f,0,SEEK_END);size_t n=ftell(f);rewind(f);Bytes b(n);assert(fread(b.data(),1,n,f)==n);fclose(f);return b;}
int main(int argc,char**argv){assert(argc==4);auto rom=load(argv[1]),r=load(argv[2]);assert(configure_menu_sprite_runtime(rom));constexpr uint32_t text=0x801650dc,bank=0x800d0320;
 auto context=[](){recomp_context c{};c.r29=int32_t(0x800a4000);return c;};
 auto ids=[](const auto&commands){std::set<uint32_t>out;for(auto [pc,id]:commands)out.insert(id);return out;};
 // Actual name updater selects the original roster string, character metrics,
 // position and style. Repeating a logical update does not reinitialize text.
 auto update=[&](unsigned player){auto c=context();c.r4=int32_t(text);c.r5=0;c.r6=player;c.r7=64;c.f_odd=&c.f0.u32h;put(r,uint32_t(c.r29)+0x10,210);put(r,uint32_t(c.r29)+0x14,11);func_8002CC18_resident(r.data(),&c);};
 auto draw=[&](){put(r,0x800a4aa4,bank);put(r,0x8009e0c8,bank+8);auto pristine=r;begin_menu_sprite_frame(r);assert(r==pristine);auto o=observe_menu_text_before(r,text);assert(o.valid&&"Original80-record text pool needs global font ownership");
  auto expected=r;auto c=context();c.f_odd=&c.f0.u32h;c.r4=int32_t(text);func_80048660_resident(expected.data(),&c);c=context();c.f_odd=&c.f0.u32h;c.r4=int32_t(text);func_80048660_resident(r.data(),&c);observe_menu_sprite_after(r,o);assert(r==expected&&"Native font observer preserves ALL original RAM");
  TransformTaskFingerprint task{.data_ptr=bank+8,.ucode=0x80069ad0,.ucode_data=0x80099ef0,.data_size=0x100};submit_menu_sprite_metadata(1,task);auto snapshot=consume_menu_sprite_metadata(task);if(!snapshot||snapshot->commands.empty()){std::fprintf(stderr,"font source %08x flags %08x head %08x\n",word(r,text+0x14),word(r,text+0x20),word(r,0x8009e0c8));for(auto pc=bank+8;pc<word(r,0x8009e0c8);pc+=8)std::fprintf(stderr,"%08x %08x %08x\n",pc,word(r,pc),word(r,pc+4));}assert(snapshot&&!snapshot->commands.empty()&&r==expected);unsigned n=0;for(auto pc=bank+8;pc<word(r,0x8009e0c8);pc+=8)if(word(r,pc)>>24==0xe4){assert(snapshot->commands.contains(pc&0x7fffff));++n;}assert(n==snapshot->commands.size());return snapshot;};
 auto original=draw();put(r,text+0xc,word(r,text+0xc)+4);auto moved=draw();assert(ids(moved->commands)==ids(original->commands));
 update(0);auto player0=draw();auto source=word(r,text+0x14);update(0);auto repeated=draw();assert(ids(player0->commands)==ids(repeated->commands));update(1);assert(word(r,text+0x14)!=source);auto player1=draw();assert(ids(player0->commands)!=ids(player1->commands));
 // Exact generic reset defines a fresh text allocation; observing it cannot
 // change original record/RAM values, and restoring the same name is new life.
 auto before=r,expected=r;auto c=context();c.f_odd=&c.f0.u32h;c.r4=int32_t(text);func_80048528_resident(expected.data(),&c);c=context();c.f_odd=&c.f0.u32h;c.r4=int32_t(text);func_80048528_resident(r.data(),&c);observe_menu_text_initialization(text);assert(r==expected);memcpy(r.data()+(text&0x7fffff),before.data()+(text&0x7fffff),0x28);auto reused=draw();assert(ids(reused->commands)!=ids(player1->commands));
 // Neighboring globals and unaligned addresses are never text owners.
 put(r,0x8009e0c8,bank+8);begin_menu_sprite_frame(r);assert(!observe_menu_text_before(r,text+4).valid&&!observe_menu_text_before(r,0x80165d5c).valid&&!observe_menu_text_before(r,0x800a3800).valid);
 // Both ends of the actual bounded80-record pool use the same font path.
 memcpy(r.data()+0x165d34,r.data()+(text&0x7fffff),0x28);auto last=observe_menu_text_before(r,0x80165d34);assert(last.valid);
}
'''
class MenuSpriteRuntimeTests(unittest.TestCase):
 def test_actual_player_names_use_original80_record_text_lifetimes(self):
  self._genuine_sprite_fixture(False,False,False,True)
 def test_unpaused_field_hud_uses_shared_identity_with_motion_material_and_scene_cuts(self):
  self._genuine_sprite_fixture(False,False,True)
 def test_original_sprites_survive_delayed_opposite_arena_submission(self):
  self._genuine_sprite_fixture(False,True)
 def test_genuine_sprite_lifetimes_cuts_and_immutable_task_fifo(self):
  self._genuine_sprite_fixture(False)
 def test_select_teams_flash_has_stable_observed_rectangles_during_original_alpha_changes(self):
  self._genuine_sprite_fixture(True)
 def _genuine_sprite_fixture(self,team_flash,task_banks=False,field_hud=False,text_pool=False):
  self.assertTrue((ROOT/'src/runtime/menu_sprite_runtime.cpp').is_file(),'Missing original Controller renderer')
  g=ROOT/'.local/pal-map-bound-01/functions';h=ROOT/'.local/deps/N64Recomp/include';rom=ROOT/'.local/inputs/pal-en-de/rom.z64';snapshot=ROOT/('.local/pal-acceptance/field09.rdram' if text_pool else '.local/training-timing-01/free-training-low.rdram' if field_hud else '.local/hidden-test-01/team16-completed.rdram' if team_flash else '.local/ui-redesign-01/controller49-completed.rdram');mb=ROOT/'.local/runtime-deps-build/librecomp/miniz';rt64=ROOT/'.local/deps/rt64'
  if not shutil.which('c++')or not all(p.is_file()for p in [rom,snapshot,h/'recomp.h',mb/'libminiz.a']):self.skipTest('Original private PAL CPU/compiler fixtures required')
  image=rom.read_bytes();sections=json.loads((g.parent/'section-analysis.json').read_text());functions={f['vram']:(s,f)for s in sections for f in s['functions']};pending=[0x80008a54,0x80007c2c,0x80041b50,0x80048660]+([0x80048528,0x8002cc18] if text_pool else []);seen=set()
  while pending:
   pc=pending.pop()
   if pc in seen:continue
   seen.add(pc);s,f=functions[pc];a=s['rom']+pc-s['vram']
   for op in struct.unpack_from('>'+str(f['size']//4)+'I',image,a):
    if op>>26==3:pending.append(0x80000000|((op&0x3ffffff)<<2))
  native=(ROOT/'src/runtime/native_game.cpp').read_text();start=native.index('bool original_controller_screen(');opening=native.index('{',start);end=opening+1;depth=1
  while depth:
   depth+=(native[end]=='{')-(native[end]=='}');end+=1
  native_owner=native[start:end]
  paths={pc:next(g.glob(f'func_{pc:08X}_*.c'))for pc in seen};code=(TEXT_POOL_CODE if text_pool else FIELD_CODE if field_hud else BANK_CODE if task_banks else TEAM_FLASH_CODE if team_flash else CODE).replace('DECLS','\n'.join(f'extern "C" void {p.stem}(uint8_t*,recomp_context*);'for p in paths.values())).replace('LOOKUP','\n'.join(f'case 0x{pc:08X}:return {p.stem};'for pc,p in paths.items()))
  code=code.replace('NATIVE_OWNER',native_owner)
  r=bytearray(snapshot.read_bytes())
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);(p/'test.cpp').write_text(code);(p/'original.c').write_text('\n'.join('#include '+json.dumps(str(v))for v in paths.values()));(p/'base.rdram').write_bytes(r)
   (p/'controller.rdram').write_bytes(r)
   q=subprocess.run(['cc','-O1','-fno-strict-aliasing','-I'+str(h),'-c',str(p/'original.c'),'-o',str(p/'original.o')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
   inc=['src','.local/deps/N64Recomp/include','.local/deps/N64ModernRuntime/librecomp/include','.local/deps/N64ModernRuntime/ultramodern/include','.local/deps/N64ModernRuntime/thirdparty','.local/deps/N64ModernRuntime/thirdparty/concurrentqueue']
   q=subprocess.run(['c++','-std=c++20','-O1','-pthread',*['-I'+str(ROOT/x)for x in inc],'-I/home/linuxbrew/.linuxbrew/include/SDL2','-I'+str(rt64/'include'),'-I'+str(rt64/'src/contrib'),'-I'+str(ROOT/'.local/deps/N64ModernRuntime/thirdparty/miniz'),'-I'+str(mb),str(p/'test.cpp'),str(p/'original.o'),*[str(ROOT/'src/runtime'/x)for x in ['menu_sprite_runtime.cpp','pal_radar_interpolation.cpp','graphics_task_bank.cpp','rom_image.cpp']],str(mb/'libminiz.a'),'-o',str(p/'test')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
   for mode in (['textpool'] if text_pool else ['field'] if field_hud else ['banks'] if task_banks else ['flash'] if team_flash else ['mismatch','producer','missing','overflow']):
    q=subprocess.run([str(p/'test'),str(rom),str(p/'base.rdram'),mode],capture_output=True,text=True,timeout=30);self.assertEqual(q.returncode,0,mode+': '+q.stderr)
if __name__=='__main__':unittest.main()
