"""Prepare a pinned private RT64 shader-only 2D bilinear option.

Original project work: djultra64. The dependency checkout stays read-only.
"""
import argparse,hashlib,json
from pathlib import Path
SOURCE_SHA256="98464b469c2bdf7bb13e17bb204d41476250a23d82bba332a020e7962279ebc8"
ANCHOR="                    // Submit the shader to the cache so compilation can start right away."
FILTER='''                    bool spriteFramebufferCopy = false;
                    for (uint32_t t = 0; t < callDesc.tileCount; ++t) {
                        spriteFramebufferCopy |= workload.drawData.callTiles[callDesc.tileIndex + t].tileCopyUsed;
                    }
                    if (iss2000::filter_2d_call(filter2D, flags.rect, callDesc.otherMode.cycleType(), callDesc.tileCount, spriteFramebufferCopy)) {
                        // RT64's shader sampler uses four-tap linear filtering
                        // even for original POINT sprites when this flag is set.
                        // Preserve callDesc so viewport phase/UVs remain exact.
                        flags.linearFiltering = true;
                        if (!flags.dynamicTiles && callDesc.tileCount <= 2) {
                            // Clamp only nonrepeating source axes. A POINT sprite
                            // often uses WRAP despite ending exactly at a tile
                            // edge; linear taps must not read a neighboring atlas
                            // cell. Genuine repeated/mirrored ranges stay intact.
                            auto spriteModes = [&](uint32_t index, bool horizontal) {
                                const auto &tile = workload.drawData.rdpTiles[callDesc.tileIndex + index];
                                const auto &sample = workload.drawData.callTiles[callDesc.tileIndex + index];
                                const float shift = horizontal ? tile.shifts : tile.shiftt;
                                const float low = (horizontal ? sample.minTexcoord.x : sample.minTexcoord.y) * shift;
                                const float high = (horizontal ? sample.maxTexcoord.x : sample.maxTexcoord.y) * shift;
                                const float ul = (horizontal ? tile.uls : tile.ult) / 4.0f;
                                const float lr = (horizontal ? tile.lrs : tile.lrt) / 4.0f + 1.0f;
                                const uint32_t mode = horizontal ? tile.cms : tile.cmt;
                                return mode | ((low >= ul && high <= lr) ? G_TX_CLAMP : 0);
                            };
                            flags.cms0 = spriteModes(0, true); flags.cmt0 = spriteModes(0, false);
                            const uint32_t second = callDesc.tileCount > 1 ? 1 : 0;
                            flags.cms1 = spriteModes(second, true); flags.cmt1 = spriteModes(second, false);
                            flags.nativeSampler0 = flags.nativeSampler1 = NATIVE_SAMPLER_NONE;
                        }
                        if (callDesc.otherMode.textFilt() == G_TF_POINT) {
                            // POINT addresses texel corners. Smooth sampling is
                            // centered on texels; keep each hosted rectangle's
                            // six private vertices at the same half-texel phase.
                            const uint32_t first = meshDesc.rawVertexStart * 2;
                            const uint32_t end = first + callDesc.triangleCount * 6;
                            for (uint32_t uv = first; uv < end; ++uv) workload.drawData.triTcFloats[uv] -= 0.5f;
                        }
                    }

'''
def derive(raw:bytes)->bytes:
 if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA256:raise ValueError("Pinned RT64 state source digest mismatch")
 text=raw.decode();config="        const UserConfiguration::Upscale2D upscale2D = ext.userConfig->upscale2D;"
 if text.count(ANCHOR)!=1 or text.count(config)!=1:raise ValueError("Reviewed RT64 shader boundary is not unique")
 return ('#include "runtime/filter_2d.hpp"\n'+text.replace(config,config+'\n        const bool filter2D = iss2000_filter_2d_enabled();').replace(ANCHOR,FILTER+ANCHOR)).encode()
def prepare(source:Path,output:Path)->dict:
 if output.is_symlink() or any(p.is_symlink() for p in output.absolute().parents):raise ValueError("2D filter output paths must not contain symlinks")
 generated=derive(source.read_bytes());receipt=dict(schema=1,attribution="djultra64",source_sha256=SOURCE_SHA256,generated_sha256=hashlib.sha256(generated).hexdigest(),behavior="Optional rectangle-only centered linear shader sampling; copy/fill, framebuffer-copy and 3D draws retain original filtering. Original draw descriptors and viewport phase remain unchanged; POINT sprites receive a hosted half-texel center adjustment before upload.")
 files={"rt64_state.cpp":generated,"receipt.json":(json.dumps(receipt,indent=2)+"\n").encode()}
 if output.exists():
  if any(not(output/n).is_file() or(output/n).is_symlink() or(output/n).read_bytes()!=v for n,v in files.items()):raise ValueError("Refusing to overwrite changed private 2D filter output")
  return receipt
 output.mkdir(parents=True,exist_ok=False)
 for n,v in files.items():
  with(output/n).open("xb")as f:f.write(v)
 return receipt
if __name__=="__main__":
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--source",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args();print(json.dumps(prepare(a.source,a.output),indent=2))
