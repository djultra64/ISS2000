"""Original project work: djultra64. Private source adaptation boundaries."""
from pathlib import Path
import tempfile,unittest
from tools.prepare_render_evidence import prepare,SOURCE_HASHES
ROOT=Path(__file__).resolve().parents[1]
SOURCES=ROOT/'.local/deps/rt64/src/hle'
@unittest.skipUnless(SOURCES.is_dir(),'Pinned private RT64 source required')
class RenderEvidenceSourceTests(unittest.TestCase):
 def test_exact_pinned_sources_emit_only_observers_and_preserve_target_clamp(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'out';receipt=prepare(SOURCES,out)
   self.assertEqual(len(receipt['sources']),2)
   workload=(out/'rt64_workload_queue.cpp').read_text();present=(out/'rt64_present_queue.cpp').read_text()
   self.assertIn('workloadConfig.targetRate = ext.sharedResources->swapChainRate;',workload)
   self.assertEqual(workload.count('iss2000_render_evidence_frame('),1)
   self.assertEqual(present.count('iss2000_render_evidence_present('),1)
   self.assertLess(workload.index('threadRenderFrame(curFrame, prevFrame'),workload.index('iss2000_render_evidence_frame('))
   self.assertLess(present.index('ext.swapChain->present(swapChainIndex'),present.index('iss2000_render_evidence_present('))
   self.assertEqual(prepare(SOURCES,out),receipt)
   (out/'rt64_present_queue.cpp').write_text('changed')
   with self.assertRaises(ValueError):prepare(SOURCES,out)
 def test_changed_dependency_or_symlink_output_is_rejected_before_output(self):
  with tempfile.TemporaryDirectory() as d:
   folder=Path(d);src=folder/'src';src.mkdir()
   for name in SOURCE_HASHES:(src/name).write_bytes((SOURCES/name).read_bytes())
   (src/'rt64_workload_queue.cpp').write_bytes((src/'rt64_workload_queue.cpp').read_bytes()+b'\n')
   with self.assertRaises(ValueError):prepare(src,folder/'out')
   self.assertFalse((folder/'out').exists())
   (folder/'link').symlink_to(SOURCES,target_is_directory=True)
   with self.assertRaises(ValueError):prepare(SOURCES,folder/'link'/'out')
