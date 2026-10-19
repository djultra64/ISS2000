"""Original project work: djultra64. Pinned real queue scope/fence ordering, no game run."""
from pathlib import Path
import hashlib,importlib.util,json,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class MenuQueueDerivativeTests(unittest.TestCase):
 def test_real_queue_scope_original_gpu_fence_and_evidence_composition(self):
  path=ROOT/'tools/prepare_rt64_menu_interpolation.py';self.assertTrue(path.is_file(),'No queue adapter generator')
  spec=importlib.util.spec_from_file_location('menu_generator',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  src=ROOT/'.local/deps/rt64/src/hle/rt64_workload_queue.cpp'
  if not src.is_file():self.skipTest('Pinned RT64 source required')
  raw=src.read_bytes()
  for evidence in [False,True]:
   out=m.derive(raw,evidence).decode();loop=out.index('for (uint32_t w = 0; w < curFrame.workloads.size(); w++)');body=out[loop:out.index('void WorkloadQueue::threadAdvanceWorkloadId',loop)]
   positions=[body.index(x)for x in ['MenuRectRenderScope menuInterpolation','bufferUploaders.clear();','menuInterpolation.uploader()','framebufferRenderer->addFramebuffer','framebufferRenderer->recordSetup','framebufferRenderer->waitForUploaders();','ext.workloadGraphicsWorker->execute();','ext.workloadGraphicsWorker->wait();']]
   self.assertEqual(positions,sorted(positions));self.assertEqual(out.count('MenuRectRenderScope menuInterpolation'),1);self.assertEqual(out.count('iss2000_render_evidence_frame('),int(evidence))
   cleanup=out.index('void WorkloadQueue::threadConfigurationUpdate(')
   positions=[out.index(x,cleanup)for x in ['std::unique_lock configurationLock','configurationLock.unlock();','targetCleanup.emplace(ext.sharedResources);','configurationLock.lock();','const bool sizeChanged','ext.sharedResources->interpolatedColorTargets.clear();']]
   self.assertEqual(positions,sorted(positions))
   self.assertEqual(out.count('targetCleanup.emplace(ext.sharedResources);'),1)
   self.assertNotIn(m.CLEANUP_WAIT,out);self.assertIn(m.CLEANUP_RETIRE,out)
   self.assertLess(out.index(m.CLEANUP_RETIRE),out.index('ext.sharedResources->interpolatedColorTargets.clear();'))
   # Undo exactly our additions, including the lifetime cleanup prolog:
   # every remaining scheduling/VI/GPU-call byte must remain original.
   restored=out.replace(m.INCLUDE,'').replace(m.SCOPE,'').replace(m.UPLOAD,'').replace(m.CLEANUP_PROLOG+'        const bool sizeChanged = ext.sharedResources->swapChainSizeChanged;',m.CLEANUP_ANCHOR).replace(m.CLEANUP_RETIRE,m.CLEANUP_WAIT).replace(m.TARGET_GROWTH_LOCKED,m.TARGET_GROWTH_ANCHOR)
   if evidence:restored=restored.replace(m.EVIDENCE_INCLUDE,'').replace(m.WORKLOAD_OBSERVER,'')
   self.assertEqual(restored.encode(),raw)
   with tempfile.TemporaryDirectory()as d:
    p=Path(d)/'output';a=m.prepare(src,p,evidence);self.assertEqual(a,m.prepare(src,p,evidence));self.assertEqual(a['generated_sha256'],hashlib.sha256((p/src.name).read_bytes()).hexdigest());self.assertNotIn(b'\r',(p/src.name).read_bytes());(p/src.name).write_bytes(b'changed')
    with self.assertRaises(ValueError):m.prepare(src,p,evidence)
  with self.assertRaises(ValueError):m.derive(raw+b'\n',False)
