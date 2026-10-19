"""Original work: djultra64. Readback bounds on actual render-target dimensions."""
from pathlib import Path
import subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class RenderEvidenceRegionTests(unittest.TestCase):
 def test_radar_center_and_full_regions_are_bounded_and_distinct(self):
  source=(ROOT/'src/renderer.cpp').read_text()
  self.assertIn('struct EvidenceRegion',source)
  body=source[source.index('struct EvidenceRegion'):source.index('struct Log {')]
  test=r'''
int main(){
 auto radar=evidence_region(1920,1080,false,true);assert(radar.x==768&&radar.y==810&&radar.width==384&&radar.height==270);
 auto center=evidence_region(1920,1080,true,false);assert(center.x==832&&center.y==412&&center.width==256&&center.height==256);
 auto full=evidence_region(1920,1080,false,false);assert(full.x==0&&full.y==0&&full.width==1920&&full.height==1080);
 for(unsigned w:{0u,1u,17u,1280u,1920u,3840u})for(unsigned h:{0u,1u,17u,720u,1080u,1121u,2160u})for(bool radar:{false,true})for(bool small:{false,true}){auto r=evidence_region(w,h,small,radar);assert(r.x+r.width<=w&&r.y+r.height<=h);if(w&&h)assert(r.width&&r.height);}
}
'''
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);(p/'test.cpp').write_text('#include <algorithm>\n#include <cstdint>\n#include <cassert>\n#define small char\n'+body+'\n#undef small\n'+test)
   q=subprocess.run(['c++','-std=c++20',str(p/'test.cpp'),'-o',str(p/'test')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
   q=subprocess.run([str(p/'test')],capture_output=True,text=True);self.assertEqual(q.returncode,0,q.stderr)
