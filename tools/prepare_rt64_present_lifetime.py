"""Pin RT64 presentation targets through the final GPU fence without editing dependencies.

Original project work: djultra64. Compose the exact production/evidence present
source from its immutable pinned upstream bytes; do not edit generated output.
"""
import argparse,hashlib,json
from pathlib import Path
try:from tools.prepare_render_evidence import PRESENT_ANCHOR,PRESENT_OBSERVER
except ModuleNotFoundError:from prepare_render_evidence import PRESENT_ANCHOR,PRESENT_OBSERVER
SOURCE_SHA256='90df4e9c97136fa9662ee003393ad657fcb3e58cade6a24052012cf54a124c90'
INCLUDE='#include "runtime/render_target_lifetime.hpp"\n#include <cstdio>\n#include <cstdlib>\n'
EVIDENCE_INCLUDE='#include "runtime/render_evidence_api.hpp"\n'
PRESENT_ANCHOR_SCOPE='    void PresentQueue::threadPresent(const Present &present, bool &swapChainValid) {\n'
PRESENT_PIN='''        // Only threadPresent is pinned: its caller has already waited for the
        // first workload frame. Extra-frame generation never acquires this pin.
        iss2000::RenderTargetPresentationScope targetLifetime(ext.sharedResources);
'''
FALLBACK_ANCHOR = """            else {
                uint32_t fbAddress = present.screenVI.fbAddress();
"""
FALLBACK_GUARDED = """            // A retained descriptor may outlive its GPU target after config
            // cleanup. Use only this queued VI's validated original image.
            const uint32_t fallbackSize = present.screenVI.fbSiz();
            const uint32_t fallbackPixelBytes = fallbackSize == G_IM_SIZ_16b ? 2u : fallbackSize == G_IM_SIZ_32b ? 4u : 0u;
            const uint64_t fallbackPixels = uint64_t(fbSize.x) * uint64_t(fbSize.y);
            const bool fallbackStorageValid = fallbackPixelBytes != 0 &&
                fallbackPixels <= 0x800000u / fallbackPixelBytes &&
                present.storage.size() >= fallbackPixels * fallbackPixelBytes;
            if ((colorTarget == nullptr) && fallbackStorageValid) {
                framesToPresent = 1;
                const char *fallbackEvidence = std::getenv("ISS2000_RENDER_EVIDENCE");
                if (fallbackEvidence && *fallbackEvidence) {
                    std::fprintf(stderr, "[RenderFallback] reason=%s address=%08x bytes=%zu\\n",
                        (presentFb && viFb) ? "empty_target" : "missing_framebuffer",
                        present.screenVI.fbAddress(), present.storage.size());
                }
                uint32_t fbAddress = present.screenVI.fbAddress();
"""
FALLBACK_LOCK_ANCHOR = """                lockedWorkloadMutex = true;
                ext.sharedResources->workloadMutex.lock();

                RenderTargetKey colorTargetKey(fbAddress, scratchFb.width, scratchFb.siz, Framebuffer::Type::Color);
"""
FALLBACK_LOCK_GUARDED = """                if (!lockedWorkloadMutex) {
                    lockedWorkloadMutex = true;
                    ext.sharedResources->workloadMutex.lock();
                }

                RenderTargetKey colorTargetKey(fbAddress, scratchFb.width, scratchFb.siz, Framebuffer::Type::Color);
"""
def derive(raw:bytes,evidence:bool=False)->bytes:
 if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA256:raise ValueError('Pinned RT64 present source digest mismatch')
 text=raw.decode()
 if text.count(PRESENT_ANCHOR_SCOPE)!=1 or text.count(PRESENT_ANCHOR)!=1:raise ValueError('Reviewed RT64 presentation lifetime boundary is not unique')
 text=INCLUDE+text.replace(PRESENT_ANCHOR_SCOPE,PRESENT_ANCHOR_SCOPE+PRESENT_PIN)
 if text.count(FALLBACK_ANCHOR)!=1 or text.count(FALLBACK_LOCK_ANCHOR)!=1:raise ValueError('Reviewed original-image fallback boundary is not unique')
 text=text.replace(FALLBACK_ANCHOR,FALLBACK_GUARDED).replace(FALLBACK_LOCK_ANCHOR,FALLBACK_LOCK_GUARDED)
 if evidence:text=EVIDENCE_INCLUDE+text.replace(PRESENT_ANCHOR,PRESENT_OBSERVER+PRESENT_ANCHOR)
 return text.encode()
def prepare(source:Path,output:Path,evidence:bool=False)->dict:
 if output.is_symlink()or any(p.is_symlink()for p in output.absolute().parents):raise ValueError('Present derivative output paths must not contain symlinks')
 generated=derive(source.read_bytes(),evidence)
 receipt=dict(schema=2,attribution='djultra64',source_sha256=SOURCE_SHA256,generated_sha256=hashlib.sha256(generated).hexdigest(),evidence=evidence,behavior='Pin existing RT64 render targets for a complete presentation through all original GPU fences; preserve original interpolation production, submission and presentation ordering. Missing or empty visible-VI targets use validated event-owned original pixels as one frame; invisible VI remains untouched.')
 files={'rt64_present_queue.cpp':generated,'receipt.json':(json.dumps(receipt,indent=2)+'\n').encode()}
 if output.exists():
  if any(not(output/n).is_file()or(output/n).is_symlink()or(output/n).read_bytes()!=raw for n,raw in files.items()):raise ValueError('Refusing to overwrite changed private present derivative output')
  return receipt
 output.mkdir(parents=True,exist_ok=False)
 for n,raw in files.items():
  with(output/n).open('xb')as f:f.write(raw)
 return receipt
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--evidence',action='store_true');a=p.parse_args();print(json.dumps(prepare(a.source,a.output,a.evidence),indent=2))
