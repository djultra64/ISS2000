"""Exercise executable lifetimes, fragmented DMA and stale target rejection."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class SectionRegistryTests(unittest.TestCase):
    def test_overlay_alias_and_fragmented_dma_lifetimes(self):
        program = r'''
#include "runtime/section_registry.hpp"
#include <cassert>
#include <cstdint>
void a() {} void old_only() {} void b() {}
int main() {
    iss2000::SectionRegistry<void(*)()> r;
    r.add({"old",0x1000,0x80100000,0x100,0x80,{{0,a,8},{0x40,old_only,0x10}}});
    r.add({"new",0x2000,0x80100000,0x100,0x40,{{0,b,0x10}}});
    assert(r.find(0x80100000)==nullptr);
    r.dma_completed(0x1000,0x80100000,0x100);
    assert(r.find(0x80100000)==a && r.find(0x80100040)==old_only);
    r.dma_completed(0x2000,0x80100000,0x80);
    assert(r.find(0x80100000)==nullptr && r.find(0x80100040)==nullptr);
    r.dma_completed(0x2080,0x80100080,0x80);
    assert(r.find(0x80100000)==b && r.find(0x80100040)==nullptr);
    bool copied=false,completed=false;
    r.transfer(0x1000,0x80100000,0x100,[&]{copied=true;},[&]{
        assert(copied && r.find(0x80100000)==a);completed=true;
    });
    assert(completed);
    r.dma_completed(0x2000,0x80100000,0x100);
    // A texture DMA into data does not erase the still-valid code mapping.
    r.dma_completed(0x4000,0x80100080,0x10);
    assert(r.find(0x80100000)==b);
    // An unrelated ROM write over code invalidates native targets immediately.
    r.dma_completed(0x5000,0x80100000,4);
    assert(r.find(0x80100000)==nullptr);
    bool rejected=false;
    try { r.dma_completed(0x6000,0x807FFFF0,0x20); } catch (const std::invalid_argument&) {rejected=true;}
    assert(rejected);
    // Invalid metadata cannot insert host targets outside guest code.
    rejected=false;
    try { r.add({"bad",0x6000,0x80101000,0x100,0x40,{{0x44,a,4}}}); } catch (const std::invalid_argument&) {rejected=true;}
    assert(rejected);
}
'''
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'registry.cpp';exe=Path(tmp)/'registry'
            source.write_text(program)
            built=subprocess.run(['c++','-std=c++20','-I',str(ROOT/'src'),str(source),'-o',str(exe)],capture_output=True,text=True)
            self.assertEqual(built.returncode,0,built.stderr)
            result=subprocess.run([str(exe)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)

    def test_real_career_tail_survives_original_head_overlay_replacement(self):
        program = r'''#include "runtime/section_registry.hpp"
#include <cassert>
void head() {} void tail() {}
int main(){
 iss2000::SectionRegistry<void(*)()> r;
 r.add({"Career516CE0",0x516CE0,0x801EF060,0xC440,0xAD50,
        {{0x1000,head,0x20},{0xAC80,tail,0x38}}});
 r.dma_completed(0x516CE0,0x801EF060,0xC440);
 assert(r.find(0x801F9CE0)==tail);
 // These are the exact two original loads whose complete text matches the
 // saved fault memory. The second stops at801F7100, below the surviving tail.
 r.dma_completed(0x29D870,0x801EB960,0x5A30);
 r.dma_completed(0x2AB220,0x801F14C0,0x5C40);
 assert(r.find(0x801F0060)==nullptr);
 assert(r.find(0x801F9CE0)==tail);
}
'''
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'registry.cpp';exe=Path(tmp)/'registry'
            source.write_text(program)
            built=subprocess.run(['c++','-std=c++20','-I',str(ROOT/'src'),str(source),'-o',str(exe)],capture_output=True,text=True)
            self.assertEqual(built.returncode,0,built.stderr)
            result=subprocess.run([str(exe)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)

    def test_complete_function_span_and_initial_full_load_are_required(self):
        program = r'''
#include "runtime/section_registry.hpp"
#include <cassert>
#include <string>
#include <vector>
void a() {} void b() {} void tail() {} void alias() {}
int main(){
 using Registry=iss2000::SectionRegistry<void(*)()>;
 Registry r;
 r.add({"original",0x1000,0x80100000,0x100,0x80,
        {{0,a,0x20},{0x40,b,0x20},{0x70,tail,0x10}}});
 r.add({"alias",0x2000,0x80100000,0x100,0x40,{{0,alias,0x20}}});
 // The complete b body alone is insufficient before the original overlay's
 // first complete load; filling all section bytes later enables its targets.
 r.dma_completed(0x1040,0x80100040,0x20);
 assert(r.find(0x80100040)==nullptr && r.active_names().empty());
 r.dma_completed(0x1000,0x80100000,0x40);
 assert(r.find(0x80100000)==nullptr);
 r.dma_completed(0x1060,0x80100060,0xA0);
 assert(r.find(0x80100000)==a&&r.find(0x80100040)==b&&r.find(0x80100070)==tail);
 // A one-byte overwrite at the final instruction invalidates the whole a
 // body, even though its entrypoint bytes and all other functions survive.
 r.dma_completed(0x301F,0x8010001F,1);
 assert(r.find(0x80100000)==nullptr&&r.find(0x80100040)==b);
 r.dma_completed(0x101F,0x8010001F,1);
 assert(r.find(0x80100000)==a);
 // One foreign write crosses function/gap/function boundaries. Exact original
 // fragments restore each complete body independently, in reverse order.
 r.dma_completed(0x4000,0x8010001C,0x28);
 assert(r.find(0x80100000)==nullptr&&r.find(0x80100040)==nullptr&&r.find(0x80100070)==tail);
 r.dma_completed(0x1042,0x80100042,2);
 assert(r.find(0x80100040)==nullptr);
 r.dma_completed(0x1040,0x80100040,2);
 assert(r.find(0x80100040)==b&&r.find(0x80100000)==nullptr);
 r.dma_completed(0x101C,0x8010001C,4);
 assert(r.find(0x80100000)==a);
 // Replacing data after the initial full load preserves intact code and does
 // not require restoring the original data bytes to restore a code fragment.
 r.dma_completed(0x5000,0x80100090,0x10);
 r.dma_completed(0x5010,0x80100010,4);
 assert(r.find(0x80100000)==nullptr&&r.find(0x80100070)==tail);
 r.dma_completed(0x1010,0x80100010,4);
 assert(r.find(0x80100000)==a);
 // Correct alias code is still gated until its first complete section load.
 // Its written bytes invalidate old originals; its untouched old tail survives.
 r.dma_completed(0x2000,0x80100000,0x40);
 assert(r.find(0x80100000)==nullptr&&r.find(0x80100070)==tail);
 r.dma_completed(0x2040,0x80100040,0xC0);
 assert(r.find(0x80100000)==alias&&r.find(0x80100040)==nullptr&&r.find(0x80100070)==nullptr);
 assert(r.active_names()==std::vector<std::string>{"alias"});
 // The registry independently rejects absent, non-instruction-aligned and
 // out-of-text function spans; it cannot silently accept old two-field data.
 for(unsigned size:{0u,3u,0x84u}){
  bool rejected=false;
  try {Registry bad;bad.add({"bad",0x1000,0x80100000,0x100,0x80,{{0,a,size}}});}
  catch(const std::invalid_argument&){rejected=true;}
  assert(rejected);
 }
}
'''
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'registry.cpp';exe=Path(tmp)/'registry'
            source.write_text(program)
            built=subprocess.run(['c++','-std=c++20','-Wall','-Wextra','-Werror','-I',str(ROOT/'src'),str(source),'-o',str(exe)],capture_output=True,text=True)
            self.assertEqual(built.returncode,0,built.stderr)
            result=subprocess.run([str(exe)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)


    def test_folded_jump_table_bytes_share_the_native_target_lifetime(self):
        program = r'''#include "runtime/section_registry.hpp"
#include <cassert>
void a(){} void b(){}
int main(){
 using R=iss2000::SectionRegistry<void(*)()>;R r;
 r.add({"original",0x1000,0x80100000,0x100,0x80,
        {{0,a,0x20,{{0x90,0xA0}}},{0x40,b,0x20}}});
 r.dma_completed(0x1000,0x80100000,0x100);
 assert(r.find(0x80100000)==a);
 // Foreign table byte invalidates only the function whose compiled switch uses it.
 r.dma_completed(0x5000,0x80100097,2);
 assert(r.find(0x80100000)==nullptr&&r.find(0x80100040)==b);
 r.dma_completed(0x1097,0x80100097,1);
 assert(r.find(0x80100000)==nullptr);
 r.dma_completed(0x1098,0x80100098,1);
 assert(r.find(0x80100000)==a);
 r.dma_completed(0x6000,0x801000A0,0x10);
 assert(r.find(0x80100000)==a);
 for(auto span:{std::pair<unsigned,unsigned>{0x90,0x104},{0x91,0x98},{0x98,0x98}}){
  bool rejected=false;try{R bad;bad.add({"bad",0x1000,0x80100000,0x100,0x80,{{0,a,4,{span}}}});}
  catch(const std::invalid_argument&){rejected=true;}assert(rejected);
 }
 R only;only.add({"only",0x1000,0x80100000,0x100,0x80,{{0,a,0x20,{{0x90,0xA0}}}}});
 only.dma_completed(0x1000,0x80100000,0x100);
 only.dma_completed(0x5000,0x80100090,4);
 assert(only.active_names().empty());
}
'''
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'registry.cpp';exe=Path(tmp)/'registry'
            source.write_text(program)
            built=subprocess.run(['c++','-std=c++20','-I',str(ROOT/'src'),str(source),'-o',str(exe)],capture_output=True,text=True)
            self.assertEqual(built.returncode,0,built.stderr)
            result=subprocess.run([str(exe)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)


    def test_original_zero_fill_invalidates_only_written_coverage(self):
        program=r'''#include "runtime/section_registry.hpp"
#include <cassert>
void a(){}void b(){}
int main(){
 using R=iss2000::SectionRegistry<void(*)()>;R r;
 r.add({"original",0x1000,0x80100000,0x100,0x80,{{0,a,0x20,{{0x90,0xA0}}},{0x40,b,0x20}}});
 r.dma_completed(0x1000,0x80100000,0x100);
 // Byte-aligned clear reaches the final code byte, preserving other entries.
 r.invalidate_ram_range(0x8010001F,1);
 assert(r.find(0x80100000)==nullptr&&r.find(0x80100040)==b);
 r.dma_completed(0x101F,0x8010001F,1);
 assert(r.find(0x80100000)==a);
 // Clearing a folded-table byte also disables its dependent native function.
 r.invalidate_ram_range(0x80100097,1);
 assert(r.find(0x80100000)==nullptr&&r.find(0x80100040)==b);
 r.dma_completed(0x1097,0x80100097,1);
 r.invalidate_ram_range(0x80100080,1);
 assert(r.find(0x80100000)==a);
 r.invalidate_ram_range(0,0); // Original zero-fill writes nothing at size0.
 r.invalidate_ram_range(0x8010001F,0);
 assert(r.find(0x80100000)==a);
 for(auto span:{std::pair<unsigned,unsigned>{0x807FFFFF,2},{0x7FFFFFFF,1},{0xFFFFFFFF,1}}){
  bool rejected=false;try{r.invalidate_ram_range(span.first,span.second);}
  catch(const std::invalid_argument&){rejected=true;}assert(rejected);
 }
 r.add({"alias",0x2000,0x80100000,0x100,0x80,{{0,b,0x20}}});
 r.dma_completed(0x2000,0x80100000,0x100);
 r.invalidate_ram_range(0x80100010,1);
 assert(r.find(0x80100000)==nullptr);
 // Clearing never establishes original coverage or a first full section load.
 R fresh;fresh.add({"fresh",0x1000,0x80100000,0x100,0x80,{{0,a,0x20}}});
 fresh.invalidate_ram_range(0x80100000,0x100);assert(fresh.find(0x80100000)==nullptr);
}
'''
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'registry.cpp';exe=Path(tmp)/'registry';source.write_text(program)
            built=subprocess.run(['c++','-std=c++20','-Wall','-Wextra','-Werror','-I',str(ROOT/'src'),str(source),'-o',str(exe)],capture_output=True,text=True)
            self.assertEqual(built.returncode,0,built.stderr)
            result=subprocess.run([str(exe)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
