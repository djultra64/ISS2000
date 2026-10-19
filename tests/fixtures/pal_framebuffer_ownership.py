"""Original scheduler CPU reproduction, not a complete game. Work: djultra64."""
from pathlib import Path
import subprocess,tempfile,os
root=Path(os.environ['ISS_FB_ROOT'])
functions=['8001E054','8001DA94','8001DA34','8001DAE4','8001DB30','8001D480']
code=r'''#include "recomp.h"
#include <vector>
#include <cassert>
#include <cstdio>
#include <cstdlib>
'''+''.join('extern "C" void func_'+a+'_resident(uint8_t*,recomp_context*);\n'for a in functions)+r'''
uint32_t current,next;
void getcurrent(uint8_t*,recomp_context*c){c->r2=(int32_t)current;}
void swap(uint8_t*,recomp_context*c){next=uint32_t(c->r4);}
recomp_func_t*get_function(int32_t a){switch(uint32_t(a)){
case 0x8001da94:return func_8001DA94_resident;
case 0x8001da34:return func_8001DA34_resident;
case 0x8001dae4:return func_8001DAE4_resident;
case 0x8005eae0:return getcurrent;
case 0x8005f1a0:return swap;
default:std::fprintf(stderr,"unexpected %08x\n",unsigned(a));std::abort();}}
void switch_error(const char*,uint32_t,uint32_t){std::abort();}
int main(){
 // Low-to-High reconfiguration retains a displayed address outside the new
 // pool. Three native completions can arrive before the next VI adopts A.
 // The original three-entry ring then wraps to read==write and loses all work.
 {
 std::vector<uint8_t> m(0x800000);auto*rdram=m.data();recomp_context c{};c.r29=int32_t(0x800a4000);
 uint32_t fb[]={0x80500000,0x805aa000,0x80654000};current=next=0x8032d000;
 MEM_W(0,0xffffffff80077630ull)=current;MEM_W(0,0xffffffff8009dea0ull)=3;
 MEM_W(0,0xffffffff8009defcull)=MEM_W(0,0xffffffff8009df9cull)=0x8012dce0;
 MEM_W(0,0xffffffff800e0328ull)=0x800a49f0;MEM_W(0,0xffffffff800f0388ull)=0x800a4a48;
 for(unsigned i=0;i<3;++i)MEM_W(i*8,0xffffffff801a07b8ull)=fb[i];
 unsigned completed=0,blocked=0;
 for(unsigned turn=0;turn<120&&completed<10;++turn){
  auto old=m;func_8001D480_resident(rdram,&c);assert(m==old);const auto slot=uint32_t(c.r2);
  if(slot){MEM_W(0,int32_t(slot))=1;MEM_W(0,0xffffffff800a49fcull)=MEM_W(4,int32_t(slot));c.r4=int32_t(0x800a49f0);func_8001E054_resident(rdram,&c);++completed;
   if(completed==1)func_8001DB30_resident(rdram,&c); // Requests A; hardware is still Low.
  }else ++blocked;
  if(completed>=3||!slot){current=next;func_8001DB30_resident(rdram,&c);}
 }
 const bool equal=MEM_W(0,0xffffffff8009defcull)==MEM_W(0,0xffffffff8009df9cull);
 std::printf("foreign_current_burst completed=%u blocked=%u ring_equal=%u current=%08x\n",completed,blocked,equal,current);
 if(std::getenv("ISS_FB_DERIVATIVE"))assert(completed==10&&blocked>0);
 else assert(completed==3&&equal&&current==fb[0]);
 }
 // Exhaust every pool size, busy mask and current identity; allocation must not write guest RAM.
 for(int count=0;count<=3;count++)for(unsigned mask=0;mask<8;mask++)for(int shown=0;shown<4;shown++){
  std::vector<uint8_t> m(0x800000);auto*rdram=m.data();recomp_context c{};
  MEM_W(0,0xffffffff8009dea0ull)=count;
  MEM_W(0,0xffffffff80077630ull)=0x80500000+shown*0xa0000;
  uint32_t expected=0;
  for(int i=0;i<3;i++){
   MEM_W(i*8,0xffffffff801a07b4ull)=(mask>>i)&1;
   MEM_W(i*8,0xffffffff801a07b8ull)=0x80500000+i*0xa0000;
   if(i<count&&!expected&&!((mask>>i)&1)&&(!std::getenv("ISS_FB_DERIVATIVE")||i!=shown))expected=0x801a07b4+i*8;
  }
  if(std::getenv("ISS_FB_DERIVATIVE")&&count==3&&shown==3&&__builtin_popcount(mask)>=2)expected=0;
  auto before=m;func_8001D480_resident(rdram,&c);assert(uint32_t(c.r2)==expected);assert(m==before);
 }
 for(int pool_count:{2,3})for(bool same:{false,true}){
 std::vector<uint8_t> m(0x800000);auto*rdram=m.data();recomp_context c{};c.r29=int32_t(0x800a4000);
 uint32_t fb[]={0x80500000,0x805aa000,0x80654000};
 current=next=same?fb[0]:fb[1];
 // Reconfiguration clears all busy flags, retaining cached current and an empty ring.
 MEM_W(0,0xffffffff80077630ull)=current;
 MEM_W(0,0xffffffff8009defcull)=0x8012dce0;
 MEM_W(0,0xffffffff8009df9cull)=0x8012dce0;
 MEM_W(0,0xffffffff8009dea0ull)=pool_count;
 MEM_W(0,0xffffffff800e0328ull)=0x800a49f0;
 MEM_W(0,0xffffffff800f0388ull)=0x800a4a48;
 for(int i=0;i<3;i++){MEM_W(i*8,0xffffffff801a07b8ull)=fb[i];MEM_W(i*4,0xffffffff8012dce0ull)=fb[i];}
 int completed=0;
 for(int i=0;i<10;i++){
  func_8001D480_resident(rdram,&c);uint32_t slot=c.r2;
  if(!slot)break;
  // Scheduler ownership boundary: successful allocation marks the slot busy.
  MEM_W(0,int32_t(slot))=1;MEM_W(0,0xffffffff800a49fcull)=MEM_W(4,int32_t(slot));
  c.r4=int32_t(0x800a49f0);func_8001E054_resident(rdram,&c);completed++;
  for(int tick=0;tick<4;tick++){current=next;func_8001DB30_resident(rdram,&c);}
 }
 unsigned busy=0;for(int i=0;i<3;i++)busy+=MEM_W(i*8,0xffffffff801a07b4ull)!=0;
 bool ring_equal=MEM_W(0,0xffffffff8009defcull)==MEM_W(0,0xffffffff8009df9cull);
 std::printf("same_current_first=%u completed=%d busy=%u ring_equal=%u current=%08x pool=%d\n",same,completed,busy,ring_equal,current,pool_count);
 if(same && !std::getenv("ISS_FB_DERIVATIVE")){assert(completed==pool_count);assert(busy==unsigned(pool_count));assert(ring_equal==(pool_count==3));assert(current==fb[0]);}
 else {assert(completed==10);assert(busy==1);}
}}
'''
with tempfile.TemporaryDirectory(prefix='iss-fb-repro-')as tmp:
 p=Path(tmp);(p/'test.cpp').write_text(code);inc='-I'+str(root/'.local/deps/N64Recomp/include');objs=[]
 for a in functions:
  obj=p/(a+'.o');objs.append(str(obj))
  source=root/'.local/pal-map-bound-01/functions'/('func_'+a+'_resident.c')
  if a=='8001D480' and os.getenv('ISS_FB_DERIVATIVE'):
   source=Path(os.environ['ISS_FB_DERIVATIVE']);args=['c++','-std=c++20']
  else:args=['cc','-std=c17']
  subprocess.run([*args,'-O1',inc,'-c',str(source),'-o',str(obj)],check=True)
 subprocess.run(['c++','-std=c++20','-O1',inc,str(p/'test.cpp'),*objs,'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
