"""Original project work: djultra64. Host metadata tests; no guest execution."""
from pathlib import Path
import subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class TransformTrackerTests(unittest.TestCase):
 def test_identity_bounds_recursive_capture_and_immutable_task_snapshots(self):
  source=r'''#include "runtime/transform_tracker.hpp"
#include <cassert>
#include <stdexcept>
#include <thread>
using namespace iss2000;
template<class F> void rejects(F f){bool rejected=false;try{f();}catch(const std::exception&){rejected=true;}assert(rejected);}
int main(){
 TransformTracker t(us_transform_layout(),2); t.begin_scene(6*256+4);
 auto a=t.allocate(0x80148104),b=t.allocate(0xFFFFFFFFA014819CULL);
 assert(t.lookup_record(a.record)->generation==a.generation);assert(!t.lookup_record(0x80001000));
 assert(a.id<TransformModelIdLimit&&b.id<TransformModelIdLimit);assert(a.record==0x80148104&&b.record==0x8014819C&&a.id!=b.id&&a.id&&a.id!=0xFFFFFFFF);
 rejects([&]{t.allocate(0x80148108);});rejects([&]{t.allocate(0x123480148104ULL);});rejects([&]{t.allocate(0x148104);});
 auto child=t.allocate(0x80152A3C+899*0x60);assert(child.id!=a.id);
 rejects([&]{t.allocate(0x80152A3C+900*0x60);});
 rejects([&]{t.begin_frame(2,0x800AA128,0x800AF228);});
 rejects([&]{t.begin_frame(0,0x800AA168,0x800AF228);});
 auto f=t.begin_frame(0,0x800AA128,0x800AF228);
 // Recursive children can advance the cursor by more than one matrix.
 assert(t.capture_matrix({f,0xA0148104,0x80000000,0,0xAA128,0xAA128,0xAA1E8,0x80400000,TransformMatrixBuilder::Conditional252F8}));
 assert(t.capture_matrix({f,0x8014819C,0x80000000,0,0x800AA168,0x800AA168,0x800AA1A8,0x80400000,TransformMatrixBuilder::Conditional252F8}));
 assert(!t.capture_matrix({f,child.record,0,0,0xAA1A8,0xAA1A8,0xAA1E8,0x80400000,TransformMatrixBuilder::Conditional252F8}));
 assert(!t.capture_matrix({f,child.record,0x80000000,0,0xAF228,0xAF228,0xAF268,0x80400000,TransformMatrixBuilder::Conditional252F8}));
 assert(!t.capture_matrix({f,child.record,0x80000000,0,0xAA1A9,0xAA1A9,0xAA1E8,0x80400000,TransformMatrixBuilder::Conditional252F8}));
 auto token=t.publish_task(f,0xFFFFFFFF800D2C08ULL);auto snapshot=t.consume_task(token.sequence,0xD2C08);
 assert(snapshot->root==0xD2C08&&snapshot->lookup(0x800AA128)->id==a.id);
 assert(snapshot->lookup(0xA00AA168)->id==b.id&&!snapshot->lookup(0xAA1A8));
 rejects([&]{t.consume_task(token.sequence,0xD2C08);});
 t.release(0x80148104);assert(!t.lookup_record(0x80148104));auto releasedToken=t.publish_task(f,0xD2C08);assert(!t.consume_task(releasedToken.sequence,0xD2C08)->lookup(0xAA128));auto again=t.allocate(0x80148104);assert(again.id!=a.id&&again.generation>a.generation);
 auto f1=t.begin_frame(1,0x800AF228,0x800B4328);
 assert(t.capture_matrix({f1,again.record,0x80000000,0xAA128,0xAF228,0xAF228,0xAF268,0x80400000,TransformMatrixBuilder::Conditional252F8}));
 assert(t.capture_matrix({f1,b.record,0x80000000,0xAA168,0xAF268,0xAF268,0xAF2A8,0x80400000,TransformMatrixBuilder::Conditional252F8}));
 auto token1=t.publish_task(f1,0x800D2C08);auto token2=t.publish_task(f1,0x800D2C08);
 rejects([&]{t.publish_task(f1,0x800E2C68);});
 rejects([&]{t.consume_task(token1.sequence,0x800E2C68);});
 auto latest=t.consume_task(token2.sequence,0x800D2C08);
 assert(latest->lookup(0xAF228)->id==again.id&&latest->lookup(0xAF268)->id==b.id);
 auto first=t.consume_task(token1.sequence,0x800D2C08);assert(first->sequence!=latest->sequence);
 assert(snapshot->lookup(0xAA128)->id==a.id); // old task survives free/reuse
 auto f2=t.begin_frame(0,0xAA128,0xAF228);
 assert(t.capture_matrix({f2,b.record,0x80000000,0xAA168,0xAA168,0xAA168,0xAA1A8,0x80400000,TransformMatrixBuilder::Conditional252F8}));
 assert(!t.capture_matrix({f2,b.record,0x80000800,0xAA168,0xAA168,0xAA168,0xAA1E8,0x80400000,TransformMatrixBuilder::Conditional252F8}));

 assert(!t.capture_matrix({f2,b.record,0x80000000,0xAA168,0xAA168,0xAA168,0xAA1A8,0x80000000,TransformMatrixBuilder::Conditional252F8})); // stale unchanged
 assert(t.capture_matrix({f2,again.record,0x80000000,0xAF228,0xAA128,0xAA128,0xAA168,0x80400000,TransformMatrixBuilder::Conditional252F8}));
 assert(t.capture_matrix({f2,child.record,0x80000000,0,0xAA128,0xAA128,0xAA168,0x80400000,TransformMatrixBuilder::Conditional252F8})); // collision => neither guessed
 auto collision=t.publish_task(f2,0xD2C08);assert(!t.consume_task(collision.sequence,0xD2C08)->lookup(0xAA128));
 t.begin_scene(6*256+7);
 rejects([&]{t.publish_task(f2,0xD2C08);});
 auto f3=t.begin_frame(0,0xAA128,0xAF228);
 assert(t.capture_matrix({f3,again.record,0x80000000,0,0xAA128,0xAA128,0xAA168,0x80400000,TransformMatrixBuilder::Conditional252F8}));
 auto cut=t.publish_task(f3,0xD2C08);auto cutSnapshot=t.consume_task(cut.sequence,0xD2C08);
 assert(cutSnapshot->lookup(0xAA128)->id!=again.id&&cutSnapshot->scene_epoch>snapshot->scene_epoch);
 // Immutable snapshots can be safely read by graphics worker after CPU state changes.
 std::thread reader([snapshot,a]{for(int i=0;i<10000;i++)assert(snapshot->lookup(0xAA128)->id==a.id);});
 t.release(again.record);reader.join();
 assert(!t.release(again.record));
 TransformTracker startup(us_transform_layout());auto early=startup.allocate(0x80148104);startup.begin_scene(0x604);
 auto sf=startup.begin_frame(0,0xAA128,0xAF228);
 assert(startup.capture_matrix({sf,early.record,0x80000000,0,0xAA128,0xAA128,0xAA168,0x80400000,TransformMatrixBuilder::Unconditional25710}));
 auto st=startup.publish_task(sf,0xD2C08);assert(startup.consume_task(st.sequence,0xD2C08)->lookup(0xAA128)->id==early.id);
 startup.begin_scene(0x607);auto sf2=startup.begin_frame(0,0xAA128,0xAF228);
 assert(startup.capture_matrix({sf2,early.record,0x80000000,0xAA128,0xAA128,0xAA128,0xAA168,0x80400000,TransformMatrixBuilder::Unconditional25710}));
 auto st2=startup.publish_task(sf2,0xD2C08);assert(startup.consume_task(st2.sequence,0xD2C08)->lookup(0xAA128)->id!=early.id);

}
'''
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'test.cpp').write_text(source)
   subprocess.run(['c++','-std=c++20','-pthread','-I'+str(ROOT/'src'),str(p/'test.cpp'),str(ROOT/'src/runtime/transform_tracker.cpp'),'-o',str(p/'test')],check=True,capture_output=True)
   subprocess.run([str(p/'test')],check=True,capture_output=True)

 def test_graphics_submission_fifo_fingerprint_quarantine_and_scene_ids(self):
  source=r'''#include "runtime/transform_tracker.hpp"
#include <cassert>
#include <thread>
using namespace iss2000;
int main(){
 TransformTracker t(us_transform_layout()); t.begin_scene(0x604);auto a=t.allocate(0x80148104);
 auto f=t.begin_frame(0,0xAA128,0xAF228);
 assert(t.capture_matrix({f,a.record,0x80000000,0,0xAA128,0xAA128,0xAA168,0x80400000,TransformMatrixBuilder::Conditional252F8}));
 TransformTaskFingerprint fp{.data_ptr=0x800D2C08,.ucode=0x80069250,.ucode_data=0x8009C8E0,.data_size=0x200};
 auto first=t.submit_task(1,fp,f);assert(first);
 assert(!t.submit_task(2,{},f)); // audio never consumes a graphics metadata slot
 auto empty=t.submit_task(1,fp);assert(empty&&empty->sequence!=first->sequence);
 t.release(a.record);t.begin_scene(0x607);
 auto old=t.consume_submission(fp);assert(old&&old->sequence==first->sequence&&old->scene_token==0x604);
 assert(old->lookup(0xAA128)->id==a.id&&old->camera_id(0)&&old->camera_id(1));
 assert(old->camera_id(0)!=old->camera_id(1)&&old->camera_id(0)!=a.id&&!old->camera_id(2));
 auto blank=t.consume_submission(fp);assert(blank&&blank->sequence==empty->sequence&&!blank->lookup(0xAA128)&&!blank->camera_id(0));
 auto menuFrame=t.begin_frame(0,0xAA128,0xAF228);auto menu=t.submit_task(1,fp,menuFrame);auto changed=t.consume_submission(fp);
 assert(changed->scene_token==0x607&&changed->camera_id(0)!=old->camera_id(0));
 // A reused root with any differing fingerprint component never borrows maps.
 for(int field=0;field<4;++field){
   t.reset_submissions();t.submit_task(1,fp);
   auto wrong=fp;
   if(field==0)wrong.data_ptr+=8;if(field==1)wrong.ucode+=8;
   if(field==2)wrong.ucode_data+=8;if(field==3)wrong.data_size+=8;
   assert(!t.consume_submission(wrong)&&!t.submissions_synchronized());
   assert(!t.submit_task(1,fp));assert(!t.consume_submission(fp));
 }
 t.reset_submissions();assert(t.submissions_synchronized());
 auto token=t.submit_task(1,fp);auto alias=fp;alias.data_ptr=0xD2C08;alias.ucode=0xA0069250;alias.ucode_data=0xFFFFFFFF8009C8E0ULL;
 assert(t.consume_submission(alias)->sequence==token->sequence);
 assert(!t.consume_submission(fp)&&!t.submissions_synchronized()); // missing event failclosed
 t.reset_submissions();t.submit_task(1,fp);
 std::thread audio([&]{assert(!t.submit_task(2,{}));});audio.join();assert(t.submissions_synchronized());
 std::thread anotherGraphicsProducer([&]{assert(!t.submit_task(1,fp));});anotherGraphicsProducer.join();
 assert(!t.submissions_synchronized()&&!t.consume_submission(fp));
 assert(old->lookup(0xAA128)->id==a.id); // no subsequent mutation reaches old frame
}
'''
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'test.cpp').write_text(source)
   subprocess.run(['c++','-std=c++20','-pthread','-I'+str(ROOT/'src'),str(p/'test.cpp'),str(ROOT/'src/runtime/transform_tracker.cpp'),'-o',str(p/'test')],check=True,capture_output=True)
   subprocess.run([str(p/'test')],check=True,capture_output=True)

 def test_first_quarantine_diagnostic_is_gated_and_keeps_fingerprint_evidence(self):
  # A missing report, altered fingerprint or repeated reporting loses the first cause.
  import json,os
  source=r'''#include "runtime/transform_tracker.hpp"
#include <cassert>
#include <string>
#include <thread>
using namespace iss2000;
int main(int argc,char** argv){
 assert(argc==2);std::string mode=argv[1];TransformTracker t(us_transform_layout());t.begin_scene(0x604);
 TransformTaskFingerprint fp{0x800D2C08,0x80069250,0x8009C8E0,0x200};
 if(mode!="empty")t.submit_task(1,fp);
 auto wrong=fp;wrong.data_size=0x208;
 if(mode=="thread"){std::thread worker([&]{assert(!t.submit_task(1,wrong));});worker.join();}
 else if(mode=="invalid"){wrong.data_ptr=0x90000000;assert(!t.consume_submission(wrong));}
 else if(mode=="missing"){t.consume_task(1,fp.data_ptr);assert(!t.consume_submission(fp));}
 else assert(!t.consume_submission(mode=="empty"?fp:wrong));
 assert(!t.submissions_synchronized());
 t.invalidate_scene();for(int n=0;n<3;++n){assert(!t.submit_task(1,fp));assert(!t.consume_submission(fp));}
}
'''
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'test.cpp').write_text(source)
   subprocess.run(['c++','-std=c++20','-pthread','-I'+str(ROOT/'src'),str(p/'test.cpp'),str(ROOT/'src/runtime/transform_tracker.cpp'),'-o',str(p/'test')],check=True,capture_output=True)
   env=os.environ.copy();env.pop('ISS2000_RENDER_EVIDENCE',None)
   for gate in (None,'','unused-evidence-path'):
    if gate is not None:env['ISS2000_RENDER_EVIDENCE']=gate
    for mode,reason in [('mismatch','fingerprint_mismatch'),('thread','producer_changed'),('empty','empty_queue'),('invalid','invalid_fingerprint'),('missing','missing_snapshot')]:
     with self.subTest(gate=gate,mode=mode):
      result=subprocess.run([str(p/'test'),mode],env=env,text=True,capture_output=True,check=True)
      if not gate:self.assertEqual(result.stderr,'');continue
      lines=result.stderr.splitlines();self.assertEqual(len(lines),1)
      report=json.loads(lines[0]);self.assertEqual(report['event'],'transform_quarantine');self.assertEqual(report['reason'],reason)
      self.assertEqual(report['scene'],0x604);self.assertEqual(report['epoch'],1)
      self.assertEqual(report['producer_changed'],mode=='thread')
      self.assertEqual(report['queued'],0 if mode=='empty' else 1)
      self.assertEqual(report['pending'],0 if mode in ('empty','missing') else 1)
      self.assertEqual(report['head_sequence'],0 if mode=='empty' else 1)
      expected={'data_ptr':0xD2C08,'ucode':0x69250,'ucode_data':0x9C8E0,'data_size':0x200}
      self.assertEqual(report['expected'],None if mode=='empty' else expected)
      self.assertEqual(report['observed'],{'data_ptr':0x90000000 if mode=='invalid' else 0x800D2C08,'ucode':0x80069250,'ucode_data':0x8009C8E0,'data_size':0x200 if mode in ('empty','missing') else 0x208})
