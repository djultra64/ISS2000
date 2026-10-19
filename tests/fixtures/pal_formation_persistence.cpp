// Original regression work: djultra64. Original PAL callback and worker execute;
// SDK probe/write and task scheduling are explicit simulated boundaries.
#include "recomp.h"
#include <vector>
#include <cassert>
#include <cstdio>
#include <cstdlib>
extern "C" void func_802A3464_overlay_3e83d0_8029eea0(uint8_t*,recomp_context*);
extern "C" void func_802A3720_overlay_3e83d0_8029eea0(uint8_t*,recomp_context*);
unsigned ram_save,disk_prepare,probe_calls,write_calls;uint32_t scheduled;int probe_result,write_result;
void noop(uint8_t*,recomp_context*){}
void probe(uint8_t*,recomp_context*c){++probe_calls;c->r2=probe_result;}
void ram(uint8_t*,recomp_context*){++ram_save;}
void disk(uint8_t*,recomp_context*){++disk_prepare;}
void write(uint8_t*,recomp_context*c){++write_calls;c->r2=write_result;}
void schedule(uint8_t*,recomp_context*c){scheduled=uint32_t(c->r4);}
recomp_func_t*get_function(int32_t a){switch(uint32_t(a)){
case 0x801B7D90:case 0x802A6E04:case 0x801ADA4C:case 0x802A6C58:return noop;
case 0x803C949C:return probe;
case 0x802A6CD4:return ram;
case 0x802A6C6C:return disk;
case 0x80019A64:return write;
case 0x801B3E84:return schedule;
default:std::fprintf(stderr,"unexpected %08x\n",unsigned(a));std::abort();}}
void switch_error(const char*,uint32_t,uint32_t){std::abort();}
struct Result {unsigned ram,disk,probe;uint32_t callback;unsigned state;bool operator==(const Result&)const=default;};
Result run(unsigned port,unsigned selection,int status){
 std::vector<uint8_t> m(0x800000);auto*rdram=m.data();
 MEM_B(0,0xffffffff8012de51ull)=3;MEM_B(0,0xffffffff8012de7eull)=port;
 MEM_B(port,0xffffffff8012e62bull)=selection;
 recomp_context c{};c.r29=0xffffffff800a4000ull;
 ram_save=disk_prepare=probe_calls=write_calls=scheduled=0;probe_result=status;
 func_802A3464_overlay_3e83d0_8029eea0(rdram,&c);
 assert(MEM_BU(port,0xffffffff8012e62bull)==selection);
 return {ram_save,disk_prepare,probe_calls,scheduled,MEM_BU(0,0xffffffff8012de51ull)};
}
int main(){
 for(unsigned port=0;port<2;++port)for(int status=0;status<9;++status){
  auto expected=run(port,1,status);assert(expected.probe==1);assert(expected.ram==0);
  for(unsigned selection=0;selection<3;++selection){auto actual=run(port,selection,status);
   if(!(actual==expected)){std::fprintf(stderr,"Save incorrectly skips original storage route: port=%u selection=%u probe=%d ram=%u disk=%u\n",port,selection,status,actual.ram,actual.disk);return 1;}
  }
 }
 // Outside the two logical selection ports, keep the original branch.
 for(unsigned port: {2u,3u})for(unsigned choice=0;choice<3;++choice){
  auto result=run(port,choice,0);
  assert(result.probe==unsigned(choice==1));
  assert(result.ram==unsigned(choice!=1));
 }
 for(unsigned port=0;port<2;++port)for(int error: {0,1,4,9}){
  std::vector<uint8_t> m(0x800000);auto*rdram=m.data();MEM_B(0,0xffffffff8012de7eull)=port;
  recomp_context c{};c.r29=0xffffffff800a4000ull;write_calls=0;write_result=error;
  func_802A3720_overlay_3e83d0_8029eea0(rdram,&c);
  assert(write_calls==1);assert(MEM_BU(0,0xffffffff8012de51ull)==(error?7:6));
 }
 std::puts("54 storage-route cases and 8 original write-result cases passed");
}
