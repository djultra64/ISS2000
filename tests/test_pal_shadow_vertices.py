"""Original project work: djultra64. Original shadow identity/task boundary tests."""
from pathlib import Path
import shutil,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class PalShadowMetadataTests(unittest.TestCase):
 def test_actual_original_objects_generations_cuts_banks_fifo_and_foreign_cases(self):
  snap=ROOT/'.local/training-timing-01/free-training-high43-completed.rdram'
  if not shutil.which('c++')or not snap.is_file():self.skipTest('Private original High frame required')
  code=r'''#include "runtime/pal_shadow_vertices.hpp"
#include <vector>
#include <cstring>
#include <cstdio>
#include <cassert>
#include <thread>
using namespace iss2000;using Bytes=std::vector<uint8_t>;
uint32_t w(const Bytes&r,uint32_t a){uint32_t v;memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
void put(Bytes&r,uint32_t a,uint32_t v){memcpy(r.data()+(a&0x7fffff),&v,4);}
void byte(Bytes&r,uint32_t a,uint8_t v){r[(a&0x7fffff)^3]=v;}
constexpr uint32_t obj=0x8014E964;
void frame(PalShadowVertices&t,Bytes&r,unsigned bank=0){put(r,0x8009DED0,bank);put(r,0x800B1A48,0x800A7848+bank*0x5100);put(r,0x800B1A4C,0x800AC948+bank*0x5100);put(r,obj+0x5c,w(r,w(r,obj+0x80))+bank*640);t.begin_frame(r);}
TransformTaskFingerprint task(const Bytes&r){return {0x800D0328,0x80069AD0,0x80099EF0,w(r,0x8009E0C8)-0x800D0328};}
int main(int argc,char**argv){assert(argc==2);Bytes base(0x800000);auto*f=fopen(argv[1],"rb");assert(f&&fread(base.data(),1,base.size(),f)==base.size());fclose(f);auto r=base;
 PalShadowVertices t;t.allocation(obj);assert(!t.capture(r,obj));frame(t,r);auto untouched=r;assert(t.capture(r,obj));assert(r==untouched);
 auto fp=task(r);t.submit(r,1,fp);auto first=t.consume(fp);assert(first&&first->tags.size()==1&&first->bank==0&&first->scene==0x604);
 const auto tag=first->tags[0];assert(tag.object==obj&&tag.generation==1&&tag.first_id>=PalShadowIdFirst&&tag.second_id<=PalShadowIdLast&&tag.first_id!=tag.second_id);
 assert(first->lookup(tag.vertices,28,0)==tag.first_id&&first->lookup(tag.vertices+448,12,0)==tag.second_id);
 assert(!first->lookup(tag.vertices,12,0)&&!first->lookup(tag.vertices+16,28,0)&&!first->lookup(tag.vertices,28,1));
 frame(t,r);assert(t.capture(r,obj));t.submit(r,1,fp);auto next=t.consume(fp);assert(next&&next->tags[0].first_id==tag.first_id);
 t.invalidate();assert(!t.capture(r,obj));frame(t,r);assert(t.capture(r,obj));t.submit(r,1,fp);auto cut=t.consume(fp);assert(cut&&cut->epoch!=first->epoch&&cut->tags[0].first_id!=tag.first_id);
 assert(first->tags[0].first_id==tag.first_id); // already submitted task retains its immutable lifetime.
 t.release(obj);assert(!t.capture(r,obj));t.allocation(obj);assert(t.capture(r,obj));t.submit(r,1,fp);auto reused=t.consume(fp);assert(reused->tags[0].generation==2&&reused->tags[0].first_id!=cut->tags[0].first_id);
 // The opposite original shadowbuffer can be captured only into its own task bank.
 frame(t,r,1);assert(t.capture(r,obj));auto originalTask=fp;fp.data_ptr=0x80001000;fp.data_size=16;put(r,0x80001000,0xDA380007);put(r,0x80001004,0x800C1B00);put(r,0x80001008,0xDF000000);put(r,0x8000100C,0);
 t.submit(r,1,fp);auto bank1=t.consume(fp);assert(bank1&&bank1->bank==1&&bank1->tags[0].vertices==tag.vertices+640&&bank1->tags[0].first_id==reused->tags[0].first_id);
 // Replay reuses the same pose stream. Continuous playback retains IDs;
 // a seek, invalid cursor or foreign phase must never interpolate across cuts.
 auto replay=base;PalShadowVertices playback;playback.allocation(obj);
 auto cursor=[&](unsigned v){uint16_t h=v;memcpy(replay.data()+(0x12ddf0^2),&h,2);};
 byte(replay,0x8012de27,3);cursor(0);frame(playback,replay);assert(playback.capture(replay,obj));playback.submit(replay,1,originalTask);auto rp=playback.consume(originalTask);assert(rp&&rp->tags.size()==1);auto rid=rp->tags[0].first_id;
 cursor(1);frame(playback,replay);assert(playback.capture(replay,obj));playback.submit(replay,1,originalTask);assert(playback.consume(originalTask)->tags[0].first_id==rid);
 cursor(9);frame(playback,replay);assert(playback.capture(replay,obj));playback.submit(replay,1,originalTask);assert(playback.consume(originalTask)->tags[0].first_id!=rid);
 cursor(68);frame(playback,replay);assert(!playback.capture(replay,obj));byte(replay,0x8012de27,2);cursor(0);frame(playback,replay);assert(!playback.capture(replay,obj));
 // Unknownnear topology, spans, owners and stale task objects never produce a tag.
 for(int bad=0;bad<10;++bad){auto b=base;PalShadowVertices x;x.allocation(obj);frame(x,b);
  if(bad==0)put(b,obj+0x7c,0x8003749c);if(bad==1)put(b,obj+0x24,0x80083C70);if(bad==2)put(b,obj+0x80,0x800A7214);
  if(bad==3)put(b,obj+0x5c,w(b,obj+0x5c)+640);if(bad==4)put(b,0x80083B00,0x0101B038);if(bad==5)put(b,obj+0x50,obj+0x130);
  if(bad==6)put(b,obj+0x28,0);if(bad==7)byte(b,0x8013B452,1);if(bad==8)x.release(obj);if(bad==9)put(b,0x800A7210,0x807FFFF8);
  auto old=b;assert(!x.capture(b,obj));assert(b==old);}
 // Fresh frame resets stale captures, language/microcode foreign cases are paired empty entries.
 r=base;PalShadowVertices empty;empty.allocation(obj);frame(empty,r);assert(empty.capture(r,obj));frame(empty,r);empty.submit(r,1,originalTask);auto e=empty.consume(originalTask);assert(e&&e->tags.empty());
 auto wrong=originalTask;wrong.ucode=0;empty.submit(r,1,wrong);assert(!empty.consume(wrong));assert(empty.capture(r,obj));empty.submit(r,1,originalTask);assert(empty.consume(originalTask)->tags.size()==1);
 // A mismatched FIFO consumer quarantines instead of searching/reusing a root.
 empty.submit(r,1,originalTask);wrong=originalTask;wrong.data_size++;assert(!empty.consume(wrong));empty.submit(r,1,originalTask);assert(!empty.consume(originalTask));
 PalShadowVertices parallel;parallel.allocation(obj);frame(parallel,r);assert(parallel.capture(r,obj));parallel.submit(r,1,originalTask);std::thread other([&]{parallel.submit(r,1,originalTask);});other.join();assert(!parallel.consume(originalTask));
 // A release/reallocation after publication cannot rewrite that queued task.
 PalShadowVertices queued;queued.allocation(obj);frame(queued,r);assert(queued.capture(r,obj));queued.submit(r,1,originalTask);queued.release(obj);queued.allocation(obj);auto retained=queued.consume(originalTask);assert(retained&&retained->tags[0].generation==1);
 configure_pal_shadow_vertices(false);observe_pal_shadow_allocation(obj);observe_pal_shadow_frame(r);observe_pal_shadow_vertices(r,obj);submit_pal_shadow_metadata(r,1,originalTask);assert(!consume_pal_shadow_metadata(originalTask));
}
'''
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);(p/'test.cpp').write_text(code);cmd=['c++','-std=c++20','-O2','-pthread','-I'+str(ROOT/'src'),str(p/'test.cpp'),str(ROOT/'src/runtime/pal_shadow_vertices.cpp'),str(ROOT/'src/runtime/graphics_task_bank.cpp'),'-o',str(p/'test')]
   q=subprocess.run(cmd,capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
   q=subprocess.run([str(p/'test'),str(snap)],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
