"""Original project work: djultra64. Log analysis unit fixtures, not rendered evidence."""
import unittest
from tools.analyze_render_evidence import analyze
class RenderEvidenceAnalysisTests(unittest.TestCase):
 def test_distinct_pixel_hash_and_fractional_weight_required_within_same_workload(self):
  def frame(workload,weight,digest,matched=True):return dict(event='render',workload=workload,weight=weight,pixel_sha256=digest,capture='gpu_readback',matched=matched,target_hz=60,time_us=100)
  samples=[dict(event='display',detected_hz=60,requested_hz=120),
   frame(1,.5,'a'*64),frame(1,1.,'b'*64),
   frame(2,.5,'a'*64),frame(2,1.,'a'*64),
   frame(3,.5,'a'*64),frame(4,1.,'b'*64),
   frame(5,.5,'a'*64,False),frame(5,1.,'b'*64,False)]
  result=analyze(samples)
  self.assertEqual(result['distinct_fractional_gpu_workloads'],[1])
  self.assertEqual(result['effective_render_rates_hz'],[60])
  self.assertEqual(result['requested_rates_hz'],[120])
  self.assertFalse(result['physical_120hz_proven'])
 def test_no_hash_or_present_success_never_becomes_proof(self):
  result=analyze([dict(event='render',workload=1,weight=.5,matched=True,target_hz=120,pixel_sha256='',capture='not_requested'),dict(event='present',success=False,time_us=100)])
  self.assertEqual(result['distinct_fractional_gpu_workloads'],[])
  self.assertEqual(result['successful_present_calls'],0)
  self.assertFalse(result['physical_120hz_proven'])
