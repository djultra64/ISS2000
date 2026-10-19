"""Prepare the pinned private menu rectangle render scope; existing RT64 GPU/frame ordering is retained.

Original project work: djultra64.
"""
import argparse,hashlib,json
from pathlib import Path
try:from tools.prepare_render_evidence import WORKLOAD_ANCHOR,WORKLOAD_OBSERVER
except ModuleNotFoundError:from prepare_render_evidence import WORKLOAD_ANCHOR,WORKLOAD_OBSERVER
SOURCE_SHA256='6e53030e8899c42347b51e67879fcb9679ad487ac067c192612c432d85bca4a4'
INCLUDE='#include "runtime/menu_sprite_render.hpp"\n#include "runtime/render_target_lifetime.hpp"\n#include <optional>\n'
EVIDENCE_INCLUDE='#include "runtime/render_evidence_api.hpp"\n'
SCOPE='            iss2000::MenuRectRenderScope menuInterpolation(this, &workload, &curFrame, &prevFrame, curFrameWeight, ext.workloadGraphicsWorker);\n'
UPLOAD='            if (auto *menuUploader = menuInterpolation.uploader()) bufferUploaders.emplace_back(menuUploader);\n'
CLEANUP_ANCHOR='        const std::scoped_lock lock(ext.sharedResources->configurationMutex);\n        const bool sizeChanged = ext.sharedResources->swapChainSizeChanged;'
CLEANUP_PROLOG='        std::unique_lock configurationLock(ext.sharedResources->configurationMutex);\n        std::optional<iss2000::RenderTargetCleanupScope> targetCleanup;\n        if (ext.sharedResources->fbConfigChanged || ext.sharedResources->swapChainSizeChanged) {\n            // Do not wait for presentation while holding configurationMutex:\n            // the inspector/presentation may need it before releasing its pin.\n            configurationLock.unlock();\n            targetCleanup.emplace(ext.sharedResources);\n            configurationLock.lock();\n        }\n'
CLEANUP_WAIT='            {\n                // Wait until the other queue has stopped using the interpolated color targets.\n                std::unique_lock<std::mutex> interpolatedLock(ext.sharedResources->interpolatedMutex);\n                InterpolatedFrameCounters &curFrameCounters = ext.sharedResources->interpolatedFrames[ext.sharedResources->interpolatedFramesIndex];\n                ext.sharedResources->interpolatedCondition.wait(interpolatedLock, [&]() {\n                    return curFrameCounters.presented >= curFrameCounters.available;\n                });\n            }'
CLEANUP_RETIRE='            {\n                // All active presentations have finished their original GPU\n                // fences before this exclusive lifetime scope was acquired.\n                // Retire both old counter generations with the targets. A queued\n                // later VI must use the normal single-frame/RDRAM fallback,\n                // rather than indexing a vector that this cleanup just cleared.\n                std::scoped_lock<std::mutex> interpolatedLock(ext.sharedResources->interpolatedMutex);\n                for (auto &counters : ext.sharedResources->interpolatedFrames) {\n                    counters = {};\n                    counters.count = 1;\n                }\n            }'
TARGET_GROWTH_ANCHOR='                if ((requiredFrames > 0) && (interpolatedTargets.size() < requiredFrames)) {\n                    uint32_t previousSize = uint32_t(interpolatedTargets.size());\n                    interpolatedTargets.resize(requiredFrames);\n                    for (uint32_t i = previousSize; i < requiredFrames; i++) {\n                        interpolatedTargets[i] = std::make_unique<RenderTarget>(interpolationTargetKey.address, Framebuffer::Type::Color, RenderMultisampling(), usesHDR);\n                    }\n                }\n'
TARGET_GROWTH_LOCKED='                {\n                    // Present indexes this vector under interpolatedMutex. Keep\n                    // growth/reallocation under the same mutex, but release it\n                    // before waiting for older targets or producing GPU frames.\n                    std::scoped_lock<std::mutex> targetVectorLock(ext.sharedResources->interpolatedMutex);\n                    if ((requiredFrames > 0) && (interpolatedTargets.size() < requiredFrames)) {\n                        uint32_t previousSize = uint32_t(interpolatedTargets.size());\n                        interpolatedTargets.resize(requiredFrames);\n                        for (uint32_t i = previousSize; i < requiredFrames; i++) {\n                            interpolatedTargets[i] = std::make_unique<RenderTarget>(interpolationTargetKey.address, Framebuffer::Type::Color, RenderMultisampling(), usesHDR);\n                        }\n                    }\n                }\n'
def derive(raw:bytes,evidence:bool=False)->bytes:
 if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA256:raise ValueError('Pinned RT64 workload source digest mismatch')
 text=raw.decode();a='            Workload &workload = workloads[curFrame.workloads[w]];\n';b='            bufferUploaders.clear();\n'
 if text.count(a)!=1 or text.count(b)!=1 or text.count(WORKLOAD_ANCHOR)!=1 or text.count(CLEANUP_ANCHOR)!=1 or text.count(CLEANUP_WAIT)!=1 or text.count(TARGET_GROWTH_ANCHOR)!=1:raise ValueError('Reviewed RT64 queue boundary is not unique')
 text=text.replace(CLEANUP_WAIT,CLEANUP_RETIRE).replace(TARGET_GROWTH_ANCHOR,TARGET_GROWTH_LOCKED)
 text=INCLUDE+text.replace(a,a+SCOPE).replace(b,b+UPLOAD).replace(CLEANUP_ANCHOR,CLEANUP_PROLOG+"        const bool sizeChanged = ext.sharedResources->swapChainSizeChanged;")
 if evidence:text=EVIDENCE_INCLUDE+text.replace(WORKLOAD_ANCHOR,WORKLOAD_OBSERVER+WORKLOAD_ANCHOR)
 return text.encode('utf-8')
def prepare(source:Path,output:Path,evidence:bool=False)->dict:
 if output.is_symlink()or any(p.is_symlink()for p in output.absolute().parents):raise ValueError('Menu derivative output paths must not contain symlinks')
 generated=derive(source.read_bytes(),evidence);receipt=dict(schema=4,attribution='djultra64',source_sha256=SOURCE_SHA256,generated_sha256=hashlib.sha256(generated).hexdigest(),evidence=evidence,behavior='Per-fractional-render immutable menu colors and matched rectangle scope. Original submission, simulation, VI, GPU execute and fence ordering retained. Destructive configuration cleanup waits for presentation lifetime pins after releasing configurationMutex; both obsolete interpolated counter generations retire with their targets; ordinary workloads remain unblocked. Target-vector growth shares the presentation lookup mutex and releases it before any target-consumption wait or GPU work.')
 files={'rt64_workload_queue.cpp':generated,'receipt.json':(json.dumps(receipt,indent=2)+'\n').encode('utf-8')}
 if output.exists():
  if any(not(output/n).is_file()or(output/n).is_symlink()or(output/n).read_bytes()!=raw for n,raw in files.items()):raise ValueError('Refusing to overwrite changed private menu derivative output')
  return receipt
 output.mkdir(parents=True,exist_ok=False)
 for n,raw in files.items():
  with(output/n).open('xb')as f:f.write(raw)
 return receipt
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--evidence',action='store_true');a=p.parse_args();print(json.dumps(prepare(a.source,a.output,a.evidence),indent=2))
