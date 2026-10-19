"""Original project work: djultra64. Immutable production/evidence lifetime derivative."""
from pathlib import Path
import hashlib,importlib.util,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class PresentLifetimeDerivativeTests(unittest.TestCase):
 def test_exact_original_present_fences_and_evidence_composition(self):
  path=ROOT/'tools/prepare_rt64_present_lifetime.py';self.assertTrue(path.is_file())
  spec=importlib.util.spec_from_file_location('present_generator',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  src=ROOT/'.local/deps/rt64/src/hle/rt64_present_queue.cpp'
  if not src.is_file():self.skipTest('Pinned original RT64 source required')
  raw=src.read_bytes()
  for evidence in[False,True]:
   out=m.derive(raw,evidence).decode();begin=out.index(m.PRESENT_ANCHOR_SCOPE);end=out.index('    void PresentQueue::skipInterpolation()',begin);body=out[begin:end]
   positions=[body.index(x)for x in ['RenderTargetPresentationScope targetLifetime','configurationLock(ext.sharedResources->configurationMutex)','InterpolatedFrameCounters &frameCounters','fbManager.find(','colorTarget->resolveTarget(','ext.presentGraphicsWorker->wait();']]
   self.assertEqual(positions,sorted(positions));self.assertEqual(out.count('RenderTargetPresentationScope targetLifetime'),1)
   loop=out[out.index('    void PresentQueue::threadLoop()'):];self.assertLess(loop.index('waitForWorkloadId(present.workloadId);'),loop.index('threadPresent(present, swapChainValid);'))
   restored=out.replace(m.INCLUDE,'').replace(m.PRESENT_PIN,'').replace(m.FALLBACK_GUARDED,m.FALLBACK_ANCHOR).replace(m.FALLBACK_LOCK_GUARDED,m.FALLBACK_LOCK_ANCHOR)
   if evidence:restored=restored.replace(m.EVIDENCE_INCLUDE,'').replace(m.PRESENT_OBSERVER,'')
   self.assertEqual(restored.encode(),raw)
   with tempfile.TemporaryDirectory()as d:
    p=Path(d)/'generated';receipt=m.prepare(src,p,evidence);self.assertEqual(receipt,m.prepare(src,p,evidence));self.assertEqual(receipt['generated_sha256'],hashlib.sha256((p/src.name).read_bytes()).hexdigest());(p/src.name).write_text('changed')
    with self.assertRaises(ValueError):m.prepare(src,p,evidence)
  with self.assertRaises(ValueError):m.derive(raw+b'\n')
if __name__=='__main__':unittest.main()
