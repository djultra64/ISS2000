"""Generate private, hash-pinned RT64 render/present observers without editing dependencies.

Original project work: djultra64. Does not change rendering cadence or its display cap.
"""
import argparse,hashlib,json
from pathlib import Path
SOURCE_HASHES={
 'rt64_workload_queue.cpp':'6e53030e8899c42347b51e67879fcb9679ad487ac067c192612c432d85bca4a4',
 'rt64_present_queue.cpp':'90df4e9c97136fa9662ee003393ad657fcb3e58cade6a24052012cf54a124c90',
}
WORKLOAD_ANCHOR='''                    // Add total time the frame took to render.
'''
WORKLOAD_OBSERVER='''                    // Project-private opt-in evidence after the real GPU frame completed.
                    if (iss2000_render_evidence_enabled()) {
                        std::scoped_lock<std::mutex> evidenceTargets(ext.sharedResources->workloadMutex);
                        std::scoped_lock<std::mutex> evidenceWorker(workerMutex);
                        RenderTarget *evidenceTarget = overrideTarget;
                        if ((evidenceTarget == nullptr) && !interpolationTargetKey.isEmpty()) {
                            evidenceTarget = &ext.sharedResources->renderTargetManager.get(interpolationTargetKey);
                        }
                        iss2000_render_evidence_frame(ext.workloadGraphicsWorker, evidenceTarget,
                            workload.workloadId, workload.presentId, frame, displayFrames,
                            curFrameWeight, prevFrameWeight, workloadConfig.targetRate,
                            workload.viOriginalRate, prevFrame.matched);
                    }

'''
PRESENT_ANCHOR='''                presentProfiler.logAndRestart();'''
PRESENT_OBSERVER='''                if (iss2000_render_evidence_enabled()) {
                    iss2000_render_evidence_present(present.presentId, i, framesToPresent,
                        targetRate, viOriginalRate, swapChainValid);
                }
'''
def prepare(source:Path,output:Path)->dict:
 if output.is_symlink() or any(p.is_symlink() for p in output.absolute().parents):
  raise ValueError('Evidence output paths must not contain symlinks')
 generated={};records={}
 for name,digest in SOURCE_HASHES.items():
  raw=(source/name).read_bytes()
  if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError('Pinned RT64 source digest mismatch: '+name)
  text=raw.decode();anchor=WORKLOAD_ANCHOR if name=='rt64_workload_queue.cpp' else PRESENT_ANCHOR
  addition=WORKLOAD_OBSERVER if name=='rt64_workload_queue.cpp' else PRESENT_OBSERVER
  if text.count(anchor)!=1:raise ValueError('RT64 evidence insertion boundary is not unique')
  text='#include "runtime/render_evidence_api.hpp"\n'+text.replace(anchor,addition+anchor)
  generated[name]=text.encode();records[name]=dict(source_sha256=digest,generated_sha256=hashlib.sha256(generated[name]).hexdigest())
 receipt=dict(schema_version=1,sources=records,behavior='Opt-in evidence only; original render/present scheduling and display-rate clamp preserved')
 generated['receipt.json']=(json.dumps(receipt,indent=2)+'\n').encode()
 if output.exists():
  if any(not (output/n).is_file() or (output/n).is_symlink() or (output/n).read_bytes()!=raw for n,raw in generated.items()):
   raise ValueError('Refusing to overwrite changed private RT64 evidence output')
  return receipt
 output.mkdir(parents=True,exist_ok=False)
 for name,raw in generated.items():
  with (output/name).open('xb') as target:target.write(raw)
 return receipt

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
 args=parser.parse_args();print(json.dumps(prepare(args.source,args.output),indent=2))
if __name__=='__main__':main()
