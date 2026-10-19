"""Original project work: djultra64. Genuine PAL preparation-avatar CPU chain."""
from pathlib import Path
import hashlib,json,re,shutil,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class PalMenuAvatarTests(unittest.TestCase):
 def test_genuine_matrix_and_draw_producers_tag_allocator_owned_limbs_and_title_in_both_banks(self):
  self._genuine_matrix_chain(ROOT/'.local/ui-redesign-01/training-prep49-completed.rdram')
 def test_select_teams_owns_both_genuine_nineteen_limb_rigs_in_both_banks(self):
  self._genuine_matrix_chain(ROOT/'.local/hidden-test-01/team16-completed.rdram', select_teams=True)
 def test_training_single_team_selection_has_its_own_exact_original_overlay_owner(self):
  self._genuine_matrix_chain(ROOT/'.local/select-teams-54-before/yellow.rdram',single_teams=True)
 def test_genuine_model_producers_are_not_gated_by_menu_scene_or_exact_scheduler_owner(self):
  self._genuine_matrix_chain(ROOT/'.local/ui-redesign-01/training-prep49-completed.rdram',global_scene=True)
 def _genuine_matrix_chain(self,snapshot,select_teams=False,single_teams=False,global_scene=False):
  folder=ROOT/'.local/pal-map-bound-01/functions';rom=ROOT/'.local/inputs/pal-en-de/rom.z64'
  if not shutil.which('c++')or not snapshot.is_file()or not rom.is_file():self.skipTest('Private PAL CPU output and completed Training preparation required')
  self.assertEqual(hashlib.sha256(rom.read_bytes()).hexdigest(),'6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf')
  paths={};pending=[0x80031E74,0x8002B30C,0x80002824,0x8002B9B4]+([0x80039A88] if select_teams else [])
  while pending:
   a=pending.pop()
   if a in paths:continue
   candidates=list(folder.glob(f'func_{a:08X}_*.c'))+list((ROOT/'.local/pal-map-01/functions').glob(f'func_{a:08X}_*.c'))
   if not candidates:continue # Unexecuted privileged/cache/error branches remain fatal below.
   p=candidates[0];s=p.read_text();paths[a]=p;pending += [int(x,16)for x in re.findall(r'LOOKUP_FUNC\(0x([0-9A-Fa-f]+)\)',s)]
  code=r'''
#include "recomp.h"
#include "runtime/transform_runtime.hpp"
#include "runtime/pal_menu_avatar.hpp"
#include "runtime/pal_game_layout.hpp"
#include "runtime/rt64_transform_bridge.hpp"
#include <vector>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cassert>
ORIGINALS
using namespace iss2000;using Bytes=std::vector<uint8_t>;
TransformRuntime*observer=nullptr;unsigned captures=0;
void arena(uint8_t*r,recomp_context*c){func_80025910_resident(r,c);if(observer)observer->observe_frame({r,0x800000});}
void model(uint8_t*r,recomp_context*c,bool child){auto before=observer?observer->observe_matrix_before({r,0x800000},c->r4,child?TransformMatrixBuilder::Unconditional25710:TransformMatrixBuilder::Conditional252F8):MatrixBuildObservation{};
 if(child)func_80025D70_resident(r,c);else func_80025958_resident(r,c);
 if(observer){observer->observe_matrix_after({r,0x800000},before);++captures;}}
void root_model(uint8_t*r,recomp_context*c){model(r,c,false);}void child_model(uint8_t*r,recomp_context*c){model(r,c,true);}
extern "C" void switch_error(const char*f,uint32_t p,uint32_t t){fprintf(stderr,"Original invalid switch %s %08x %08x\n",f,p,t);abort();}
extern "C" void do_break(uint32_t p){fprintf(stderr,"Original BREAK %08x\n",p);abort();}
extern "C" recomp_func_t*get_function(int32_t p){switch(uint32_t(p)){DISPATCH default:fprintf(stderr,"Unexpected original target %08x\n",uint32_t(p));abort();}}
uint32_t w(const Bytes&r,uint32_t a){uint32_t v;memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
void put(Bytes&r,uint32_t a,uint32_t v){memcpy(r.data()+(a&0x7fffff),&v,4);}
Bytes load(const char*p){Bytes r(0x800000);auto*f=fopen(p,"rb");assert(f&&fread(r.data(),1,r.size(),f)==r.size());fclose(f);return r;}
void original_frame(Bytes&r){recomp_context c{};c.r29=int32_t(0x800A4200);c.f_odd=&c.f0.u32h;ANIMATION_UPDATE WAVE_UPDATE func_8002B30C_resident(r.data(),&c);
 // Same genuine main task base as80002A10; leave original framebuffer/Gfxbank distinct from modelbank.
 put(r,0x800A4AA4,0x800D0320);put(r,0x8009E0C8,0x800D0328);func_80002824_resident(r.data(),&c);c.r4=0;c.r5=128;func_8002B9B4_resident(r.data(),&c);
 auto end=w(r,0x8009E0C8);assert(end<0x800E0328);put(r,end,0xDF000000);put(r,end+4,0);}
int main(int argc,char**argv){assert(argc==2);auto r=load(argv[1]);TransformRuntime rt(verified_pal_transform_layout());
 GLOBAL_SCENE
 SELECT_GUARDS
 const auto initial_bank=w(r,0x8009DED0);
 std::array<uint32_t,38>rig{};const unsigned count=RIG_COUNT;for(unsigned i=0;i<count;++i){rig[i]=w(r,0x801A07CC+(i/19)*0x100+4*(i%19));rt.observe_allocation(rig[i]);} OTHER_ALLOCATION FLAG_ALLOCATION
 // Start from the actual bank0 completed frame; genuine2B30C toggles1 then0.
 std::array<uint32_t,2>previous_flag_ids{};std::array<uint32_t,38>previous_ids{};std::array<std::array<uint8_t,64>,38>previous_matrices{};std::shared_ptr<const TransformTaskSnapshot> retained;
 for(unsigned frame=0;frame<4;++frame){if(frame==2)rt.invalidate_scene();if(frame==3){rt.observe_release(rig[0]);rt.observe_allocation(rig[0]);}auto expected=r;observer=nullptr;original_frame(expected);observer=&rt;original_frame(r);assert(r==expected&&"Host observers must leave ALL guest RAM identical");
  const auto bank=w(r,0x8009DED0);assert(bank==(initial_bank^((frame+1)%2)));assert(captures>=19);
  TransformTaskFingerprint task{0x800D0328,0x80069AD0,0x80099EF0,w(r,0x8009E0C8)-0x800D0328+8};
  const auto unchanged=r;rt.submit_metadata(r,1,task);auto s=rt.consume_metadata(task);assert(r==unchanged&&s&&s->bank==bank);
  assert(bool(s->model_scope)==EXPECT_SCOPE);std::array<unsigned,2> moved{};unsigned index=0;for(unsigned n=0;n<count;++n){const auto object=rig[n];const auto matrix=w(r,object+0x18+bank*4)&0x7fffff;auto tag=s->lookup(matrix);assert(tag&&tag->record==object);if(frame==1)assert(tag->id==previous_ids[index]);if(frame==2)assert(tag->id!=previous_ids[index]);if(frame==3)assert((tag->id!=previous_ids[index])==(index==0));previous_ids[index]=tag->id;if(frame&&memcmp(previous_matrices[index].data(),r.data()+matrix,64))++moved[index/19];memcpy(previous_matrices[index++].data(),r.data()+matrix,64);
   auto selection=select_rt64_transform(s.get(),true,matrix,false,true,true);assert(selection.kind==TransformSelection::Kind::Model&&selection.id==tag->id&&"Verified menu avatar must interpolate every original limb");assert(select_rt64_transform(s.get(),true,matrix,false,false,true).kind==TransformSelection::Kind::Ignore);}
  if(frame==1&&VERIFY_MOVED)for(unsigned rig=0;rig<count/19;++rig)assert(moved[rig]&&"Real original animation must change each avatar rig, not just rebuild static metadata");
  FLAG_ASSERTIONS
  // The genuine Training title is separate. Teams state1 is another avatar.
  OTHER_ASSERTION const auto other=OTHER_MATRIX;
  for(bool load:{false,true}){auto known=s->lookup(other);assert(select_rt64_transform(s.get(),true,other,false,load,true).kind==(load&&known?TransformSelection::Kind::Model:TransformSelection::Kind::Ignore));assert(select_rt64_transform(s.get(),true,0x1234,false,load,true).kind==TransformSelection::Kind::Ignore);}
  if(auto known=s->lookup(other))assert(select_rt64_transform(s.get(),true,other,false,true,false).id==known->id&&"Genuine title matrix must interpolate under orthographic projection too");
  FLAG_CUTS
  if(frame==1)retained=s;if(frame==3){assert(retained&&retained->scene_epoch<s->scene_epoch);assert(bool(retained->model_scope)==EXPECT_SCOPE);if(retained->model_scope)for(unsigned n=0;n<count;++n)assert(retained->model_scope->records[n]==rig[n]);}
  if(frame==3&&count==38){rt.observe_release(rig[19]);rt.observe_allocation(rig[19]);rt.submit_metadata(r,1,task);auto stale=rt.consume_metadata(task);assert(stale&&!stale->model_scope&&"Second-rig allocation reuse needs a fresh genuine matrix too");assert(bool(retained->model_scope)==EXPECT_SCOPE);}
  if(frame==3){rt.observe_release(rig[0]);rt.observe_allocation(rig[0]);rt.submit_metadata(r,1,task);auto stale=rt.consume_metadata(task);assert(stale&&!stale->model_scope&&"A reused allocation without a fresh matrix cannot authorize old menu tags");assert(bool(retained->model_scope)==EXPECT_SCOPE);}
  for(auto address:{0xC1AC0u,0xC1B00u,0xCC388u,0xCC3C8u})for(bool load:{false,true})assert(select_rt64_transform(s.get(),true,address,true,load,true).kind==TransformSelection::Kind::Ignore);
 }
}
'''
  guards=r'''const auto proof=verified_pal_menu_avatar(r);assert(proof&&proof->models.scene==0x607);
 assert(proof->models.records.size()>=38&&"Both original avatar rigs must fit the published scope");
 for(unsigned n=0;n<38;++n)assert(proof->models.records[n]==w(r,0x801A07CC+(n/19)*0x100+(n%19)*4));
 const auto task=w(r,0x800A4AA4)+8;const auto submitted_bank=pal_menu_avatar_task_bank(r,task,*proof);assert(submitted_bank);
 assert(proof->models.record_count==38);
 uint32_t second_load=0;for(auto pc=task;pc<w(r,0x8009E0C8);pc+=8)
  if(w(r,pc)==0xDA380003&&(w(r,pc+4)&0x7fffff)==proof->matrices[19][*submitted_bank])second_load=pc;
 assert(second_load);
 for(unsigned fault=0;fault<2;++fault){auto bad=r;
  put(bad,second_load+4,fault?0x801A3F00:0x80000000+proof->matrices[19][1-*submitted_bank]);
  const auto before=bad;assert(!pal_menu_avatar_task_bank(bad,task,*proof)&&bad==before);
 }
 {auto one=r;put(one,0x801A08CC,0);const auto before=one;auto single=verified_pal_menu_avatar(one);
  assert(single&&single->models.record_count==19&&one==before);
  for(unsigned n=19;n<38;++n)assert(!single->models.records[n]);
 }
 assert(proof->models.vertex_models[0].record&&proof->models.vertex_models[1].record);
 for(unsigned fault=0;fault<4;++fault){auto bad=r;const auto vertices=w(r,0x800BD9D8),display=w(r,0x800BD9E0);
  if(fault==0)put(bad,display+16,0);if(fault==1)bad[((vertices+8)&0x7fffff)^3]^=1;
  if(fault==2)bad[(vertices&0x7fffff)^3]^=1;if(fault==3)put(bad,0x802ACD78,w(r,0x801A07CC));
  const auto unchanged=bad;auto rejected=verified_pal_menu_avatar(bad);assert(bad==unchanged&&rejected&&rejected->models.records==proof->models.records);
  assert(!rejected->models.vertex_models[0].record&&"Foreign flag mesh/rig never gains vertex interpolation");
 }
 uint32_t owner_node=0;for(auto node=w(r,0x80077390);node;node=w(r,node))if(w(r,node+12)==0x802A0C48)owner_node=node;
 assert(owner_node);
 // A stale Select Teams overlay must not authorize its flag roots after the
 // active owner has changed to genuine Training preparation.
 {auto switched=r;const auto training=load(TRAINING_FIXTURE);
  for(unsigned n=0;n<15;++n)put(switched,0x802BDA2C+n*4,w(training,0x802BDA2C+n*4));
  put(switched,owner_node+12,0x802BDA2C);const auto before=switched;auto fresh=verified_pal_menu_avatar(switched);
  assert(fresh&&fresh->models.record_count==19&&switched==before&&!fresh->models.vertex_models[0].record&&!fresh->models.vertex_models[1].record);
  for(unsigned n=19;n<38;++n)assert(!fresh->models.records[n]);
 }
 for(unsigned fault=0;fault<10;++fault){auto bad=r;
  if(fault==0)put(bad,0x802A0C48,0); // Exact foreign/changed overlay rejects.
  if(fault==1)put(bad,owner_node+12,0); // Inactive Select Teams owner rejects.
  if(fault==2)put(bad,owner_node,owner_node); // Cyclic scheduler rejects.
  if(fault==3)put(bad,w(r,0x801A07CC)+0x84,0); // Rig owner must be reciprocal.
  if(fault==4)put(bad,0x801A07D0,w(r,0x801A07CC)); // Duplicate joint rejects.
  if(fault==5)put(bad,proof->models.records[1]+0x44,0x8014FCFC); // Foreign title cannot join rig.
  if(fault==6)put(bad,w(r,0x801A08CC)+0x84,0x801A07CC);
  if(fault==7)put(bad,0x801A08D0,0);
  if(fault==8)put(bad,w(r,0x801A08D0)+0x44,w(r,0x801A07CC));
  if(fault==9)put(bad,0x801A08D0,w(r,0x801A07D0));
  const auto unchanged=bad;assert(!verified_pal_menu_avatar(bad)&&bad==unchanged);
 }
'''
  code=code.replace('GLOBAL_SCENE','r[0x13B44C^3]=6;put(r,0x802BDA2C,0);' if global_scene else '').replace('EXPECT_SCOPE','false' if global_scene else 'true')
  code=code.replace('SELECT_GUARDS',guards if select_teams else '''const auto proof=verified_pal_menu_avatar(r);assert(proof&&proof->models.record_count==19&&\"Yellow single-team Select Teams must own its genuine avatar\");
 assert(pal_menu_avatar_task_bank(r,0x800E0388,*proof)==0&&\"Captured actual host-adapted yellow task must authorize the genuine rig\");
 uint32_t owner=0;for(auto p=w(r,0x80077390);p;p=w(r,p))if(w(r,p+12)==0x802A8434)owner=p;assert(owner);
 for(unsigned fault=0;fault<3;++fault){auto bad=r;if(fault==0)put(bad,0x802A8434,0);if(fault==1)put(bad,owner+12,0);if(fault==2)put(bad,w(r,0x801A07CC)+0x84,0);const auto before=bad;assert(!verified_pal_menu_avatar(bad)&&bad==before);}
''' if single_teams else '').replace('TRAINING_FIXTURE',json.dumps(str(ROOT/'.local/ui-redesign-01/training-prep49-completed.rdram')))
  if select_teams:
   code=code.replace('assert(bank==(initial_bank^((frame+1)%2)));','assert(bank==frame%2);')
  code=code.replace('ANIMATION_UPDATE','func_80031E74_resident(r.data(),&c);' if select_teams else '').replace('VERIFY_MOVED','true' if select_teams else 'false')
  code=code.replace('WAVE_UPDATE','const auto wind_before=r;func_80039A88_resident(r.data(),&c);const auto cloth=w(r,0x800BD9D8)&0x7fffff;assert(memcmp(r.data()+cloth,wind_before.data()+cloth,30*16)!=0);' if select_teams else '')
  code=code.replace('FLAG_ALLOCATION','for(unsigned i=0;i<2;++i)rt.observe_allocation(w(r,0x802ACD78+i*4));' if select_teams else '')
  code=code.replace('FLAG_CUTS',r'''if(frame==1){
   const auto flag=w(r,0x802ACD78),otherflag=w(r,0x802ACD7C),texture=w(r,flag+0x5C),matrix=w(r,flag+0x18+bank*4)&0x7fffff,othermatrix=w(r,otherflag+0x18+bank*4)&0x7fffff;
   const auto before=select_rt64_transform(s.get(),true,matrix,false,true,true),otherbefore=select_rt64_transform(s.get(),true,othermatrix,false,true,true);
   r[(texture&0x7fffff)^3]^=1;const auto unchanged=r;rt.submit_metadata(r,1,task);auto changed=rt.consume_metadata(task);assert(r==unchanged&&changed&&changed->model_scope);
   assert(select_rt64_transform(changed.get(),true,matrix,false,true,true).id!=before.id&&"A changed team flag texture must cut its vertex group identity");
   assert(select_rt64_transform(changed.get(),true,othermatrix,false,true,true).id==otherbefore.id);
   assert(select_rt64_transform(s.get(),true,matrix,false,true,true).id==before.id&&"Queued previous identity remains immutable");
   r[(texture&0x7fffff)^3]^=1;
  }
  if(frame==3){const auto flag=w(r,0x802ACD78),matrix=w(r,flag+0x18+bank*4)&0x7fffff;rt.observe_release(flag);rt.observe_allocation(flag);rt.submit_metadata(r,1,task);auto stale=rt.consume_metadata(task);
   assert(stale&&stale->model_scope&&select_rt64_transform(stale.get(),true,matrix,false,true,true).kind==TransformSelection::Kind::Ignore&&"A flag reallocation without fresh matrix cannot reuse old metadata");
  }
''' if select_teams else '')
  code=code.replace('FLAG_ASSERTIONS' ,r'''for(unsigned i=0;i<2;++i){const auto flag=w(r,0x802ACD78+i*4),matrix=w(r,flag+0x18+bank*4)&0x7fffff;assert(s->lookup(matrix));
   auto chosen=select_rt64_transform(s.get(),true,matrix,false,true,true);assert(chosen.kind==TransformSelection::Kind::Model&&chosen.vertices&&"Verified Select Teams cloth must have a stable model/vertex interpolation group");
   if(frame==1)assert(chosen.id==previous_flag_ids[i]);if(frame==2)assert(chosen.id!=previous_flag_ids[i]);previous_flag_ids[i]=chosen.id;
   bool submitted=false;for(auto pc=0x800D0328u;pc<w(r,0x8009E0C8);pc+=8)submitted|=w(r,pc)==0xDA380003&&(w(r,pc+4)&0x7fffff)==matrix;assert(submitted&&"Each flag owns an actual original MODEL LOAD");}
''' if select_teams else '')
  code=code.replace('RIG_COUNT','38' if select_teams else '19').replace('OTHER_ALLOCATION','' if select_teams else 'rt.observe_allocation(0x8014FEC4);').replace('OTHER_ASSERTION','' if select_teams else 'assert(s->lookup(w(r,0x8014FEC4+0x18+bank*4)&0x7fffff));').replace('OTHER_MATRIX','0x1234' if select_teams else 'w(r,0x8014FEC4+0x18+bank*4)&0x7fffff')
  code=code.replace('ORIGINALS','extern \"C\" void func_8002EB64_resident(uint8_t*,recomp_context*);\n'+'\n'.join('#include '+json.dumps(str(p))for a,p in paths.items()if a!=0x8002EB64)).replace('DISPATCH','\n'.join(f'case 0x{a:08X}:return '+({0x80025910:'arena',0x80025958:'root_model',0x80025D70:'child_model'}.get(a,p.stem))+';'for a,p in paths.items()))
  with tempfile.TemporaryDirectory()as d:
   d=Path(d);(d/'test.cpp').write_text(code)
   q=subprocess.run(['cc','-O1','-I'+str(ROOT/'.local/deps/N64Recomp/include'),'-c',str(paths[0x8002EB64]),'-o',str(d/'geometry.o')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
   q=subprocess.run(['c++','-std=c++20','-O1','-pthread','-I'+str(ROOT/'src'),'-I'+str(ROOT/'.local/deps/N64Recomp/include'),str(d/'test.cpp'),str(d/'geometry.o'),*[str(ROOT/'src/runtime'/n)for n in ('transform_runtime.cpp','transform_tracker.cpp','graphics_task_bank.cpp','pal_menu_avatar.cpp')],'-o',str(d/'test')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
   q=subprocess.run([str(d/'test'),str(snapshot)],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
 def test_completed_screen_owner_task_bank_and_foreign_guards_are_read_only(self):
  snapshots=[ROOT/'.local/ui-redesign-01'/name for name in ('training-prep49-completed.rdram','controller49-completed.rdram','select-training49-completed.rdram')]
  if not shutil.which('c++')or not all(p.is_file()for p in snapshots):self.skipTest('Private completed original PAL menus required')
  code=r'''#include "runtime/pal_menu_avatar.hpp"
#include <vector>
#include <cstdio>
#include <cassert>
#include <cstring>
using namespace iss2000;using Bytes=std::vector<uint8_t>;
uint32_t w(const Bytes&r,uint32_t a){uint32_t v;memcpy(&v,r.data()+(a&0x7fffff),4);return v;}
void put(Bytes&r,uint32_t a,uint32_t v){memcpy(r.data()+(a&0x7fffff),&v,4);}
void byte(Bytes&r,uint32_t a,uint8_t v){r[(a&0x7fffff)^3]=v;}
Bytes load(const char*p){Bytes r(0x800000);auto*f=fopen(p,"rb");assert(f&&fread(r.data(),1,r.size(),f)==r.size());fclose(f);return r;}
int main(int argc,char**argv){assert(argc==4);auto base=load(argv[1]);const auto proof=verified_pal_menu_avatar(base);assert(proof&&proof->models.scene==0x607);
 assert(!verified_pal_menu_avatar(load(argv[2]))&&!verified_pal_menu_avatar(load(argv[3])));
 auto task=w(base,0x800A4AA4)+8;assert(task==0x800E0388);auto original=base;
 assert(pal_menu_avatar_task_bank(base,task,*proof)==0);assert(pal_menu_avatar_task_bank(base,uint64_t(int64_t(int32_t(task))),*proof)==0);assert(base==original);
 // Actual completed frame has Gfxbank1 but modelbank0. Neither bankglobal can authorize a task.
 put(base,0x8009DED0,1);assert(pal_menu_avatar_task_bank(base,task,*proof)==0);base=original;
 assert(!pal_menu_avatar_task_bank(base,0x12345678800E0388ull,*proof));assert(!pal_menu_avatar_task_bank(base,0x807FFFFC,*proof));
 uint32_t root_load=0,ucode=0;for(auto p=task;p<w(base,0x8009E0C8);p+=8){if(w(base,p)==0xDA380003&&(w(base,p+4)&0x7fffff)==proof->matrices[0][0])root_load=p;if(w(base,p)==0xDD0007FF)ucode=p;}
 assert(root_load&&ucode);
 for(unsigned bad=0;bad<6;++bad){auto r=original;
  if(bad==0)put(r,root_load+4,0x80000000+proof->matrices[0][1]); // Mixed19-limb banks reject.
  if(bad==1)put(r,root_load+4,0x801A3F00); // Missing any owned joint rejects.
  if(bad==2)put(r,ucode+4,0x80069AD8); // Unknown microcode switch rejects.
  if(bad==3){put(r,task,0xDE000000);put(r,task+4,task);} // Cyclic list bounded.
  if(bad==4){put(r,task,0x04000000);put(r,task+4,task);} // Conditional branch cannot be guessed.
  if(bad==5){put(r,task,0xDF000000);put(r,task+4,0);} // Early return without19 ownedLOADs rejects.
  auto before=r;assert(!pal_menu_avatar_task_bank(r,task,*proof));assert(r==before);
 }
 const auto root=proof->models.records[0],limb=proof->models.records[1];
 for(unsigned bad=0;bad<15;++bad){auto r=original;
  if(bad==0)put(r,0x8009E02C,0);if(bad==1)byte(r,0x8013B446,5);if(bad==2)byte(r,0x8013B44C,4);
  if(bad==3)byte(r,0x8013B452,1);if(bad==4)byte(r,0x8013B42A,1);if(bad==5)put(r,0x8013B42C,0x02800220);
  if(bad==6)put(r,0x802BDA2C,0);if(bad==7)put(r,0x801E75E0+12,0);if(bad==8)put(r,0x801E75E0,0x801E75E0);
  if(bad==9)put(r,0x801A07CC+4,root);if(bad==10)put(r,limb+0x28,0);if(bad==11)put(r,root+0x84,0);
  if(bad==12)put(r,root+0x48,0);if(bad==13)put(r,limb+0x44,0x8014FEC4);if(bad==14)put(r,limb+0x1C,w(r,limb+0x1C)+8);
  auto before=r;assert(!verified_pal_menu_avatar(r));assert(r==before);
 }
 assert(!verified_pal_menu_avatar(std::span<const uint8_t>(base.data(),128)));
}
'''
  with tempfile.TemporaryDirectory()as d:
   d=Path(d);(d/'test.cpp').write_text(code);q=subprocess.run(['c++','-std=c++20','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I'+str(ROOT/'src'),str(d/'test.cpp'),str(ROOT/'src/runtime/pal_menu_avatar.cpp'),'-o',str(d/'test')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
   q=subprocess.run([str(d/'test'),*map(str,snapshots)],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)

if __name__=='__main__':unittest.main()
