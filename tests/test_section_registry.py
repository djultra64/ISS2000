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
    r.add({"old",0x1000,0x80100000,0x100,0x80,{{0,a},{0x40,old_only}}});
    r.add({"new",0x2000,0x80100000,0x100,0x40,{{0,b}}});
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
    try { r.add({"bad",0x6000,0x80101000,0x100,0x40,{{0x44,a}}}); } catch (const std::invalid_argument&) {rejected=true;}
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
