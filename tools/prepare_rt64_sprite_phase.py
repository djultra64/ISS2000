"""Prepare a pinned private RT64 identity-sprite viewport phase derivative.

Original project work: djultra64. Keep original guest geometry, UVs and filters.
"""
import argparse,hashlib,json
from pathlib import Path
SOURCE_SHA256='73870c23b2340611b930b668d52aec9e687fd74b7da310962b7b1ef35dee015d'
HELPERS=r'''
    static bool iss2000_native_sprite_phase(bool regularOrigins, bool tileCopiesUsed, bool upscale2D, bool identityScale, uint32_t cycle, uint32_t filter) {
        return regularOrigins && !tileCopiesUsed && upscale2D && identityScale && (cycle == G_CYC_1CYCLE) && (filter == G_TF_POINT);
    }

    static bool iss2000_high_sprite_scale(int32_t fbWidth, int16_t ds, int16_t dt) {
        // Original640-wide High sprites double geometry and halve derivatives.
        // They are the same identity native texel scale, not scaled/COPY draws.
        return fbWidth == 640 && (ds == 512 || ds == -512) && (dt == 512 || dt == -512);
    }

    static bool iss2000_high_sprite_edge(int32_t fbWidth, int16_t ds, int16_t dt, FixedRect rect) {
        // Original High sprite builders append one-native-pixel right/bottom
        // repair strips to the doubled512-derivative body. Their other axis
        // remains512; admitting arbitrary1024/512 scaled rectangles is unsafe.
        return fbWidth == 640 && ((rect.ulx | rect.uly | rect.lrx | rect.lry) & 3) == 0 &&
            rect.lrx > rect.ulx && rect.lry > rect.uly &&
            ((ds == 1024 && dt == 512 && rect.lrx - rect.ulx == 4) ||
             (ds == 512 && dt == 1024 && rect.lry - rect.uly == 4));
    }

    static bool iss2000_radar_marker_phase(int32_t fbWidth,int16_t ds,int16_t dt,FixedRect rect) {
        const int size=fbWidth==640?64:fbWidth==320?32:0;
        const int step=fbWidth==640?496:992;
        return size && ds==step && dt==step && rect.lrx-rect.ulx==size && rect.lry-rect.uly==size &&
            ((rect.ulx|rect.uly|rect.lrx|rect.lry)&3)==0;
    }

    static RenderViewport iss2000_interpolate_sprite_viewport(RenderViewport previous, RenderViewport current, float weight) {
        if (weight == 1.0f) return current;
        if (weight == 0.0f) return previous;
        return RenderViewport(previous.x + (current.x - previous.x) * weight, previous.y + (current.y - previous.y) * weight,
            previous.width + (current.width - previous.width) * weight, previous.height + (current.height - previous.height) * weight);
    }

    static bool iss2000_intro_canvas_phase(bool upscale2D, uint32_t cycle, uint32_t filter, uint8_t aspect, int16_t ds, int16_t dt, int32_t x0, int32_t y0, int32_t x1, int32_t y1, uint16_t leftOrigin, uint16_t rightOrigin) {
        if (!upscale2D || cycle != G_CYC_1CYCLE || filter != G_TF_POINT || aspect != G_EX_ASPECT_ADJUST || ds || dt || y0 || y1 != 960) return false;
        return (x0 == -4 && x1 == 0 && leftOrigin == G_EX_ORIGIN_LEFT && rightOrigin == G_EX_ORIGIN_NONE) ||
            (x0 == 1280 && x1 == 1284 && leftOrigin == G_EX_ORIGIN_NONE && rightOrigin == G_EX_ORIGIN_RIGHT);
    }

    static RenderViewport iss2000_sprite_viewport_rect(FixedRect rect, hlslpp::float2 resScale, int32_t fbWidth, float aspectRatioScale, float extOriginPercentage, float horizontalMisalignment, uint16_t leftOrigin, uint16_t rightOrigin, bool nativePhase, bool introCanvas = false) {
        if ((!nativePhase && !introCanvas) || (!introCanvas && ((leftOrigin != G_EX_ORIGIN_NONE) || (rightOrigin != G_EX_ORIGIN_NONE)))) {
            return convertViewportRect(rect, resScale, fbWidth, aspectRatioScale, extOriginPercentage, horizontalMisalignment, leftOrigin, rightOrigin);
        }
        // Keep the same native UV slope across independently tiled sprites.
        // Rounding8px and16px pieces independently changes their texel phase.
        // Regular origins use the same framebuffer center in the original;
        // their offsets do not depend on horizontalMisalignment/extOrigin.
        auto origin = [=](uint16_t value) {
            return value < G_EX_ORIGIN_NONE ? ((fbWidth * value) / G_EX_ORIGIN_RIGHT) * extOriginPercentage + (fbWidth / 2) * (1.0f - extOriginPercentage) : float(fbWidth) / 2;
        };
        const float leftCenter = origin(leftOrigin), rightCenter = origin(rightOrigin);
        const float left = (leftCenter + (rect.left(true) - leftCenter) * aspectRatioScale) * resScale.x;
        const float right = (rightCenter + (rect.right(true) - rightCenter) * aspectRatioScale) * resScale.x;
        const float top = rect.top(true) * resScale.y;
        const float bottom = rect.bottom(true) * resScale.y;
        return RenderViewport(left, top, right - left, bottom - top);
    }
'''
OLD='                            RenderViewport viewportRect = convertViewportRect(call.callDesc.rect, p.resolutionScale, p.fbWidth, invRatioScale, extOriginPercentage, horizontalMisalignment, call.callDesc.rectLeftOrigin, call.callDesc.rectRightOrigin);'
NEW='''                            const bool nativeSpritePhase = iss2000_native_sprite_phase(regularOrigins, tileCopiesUsed, call.shaderDesc.flags.upscale2D, (call.callDesc.identityRectScale() || iss2000_high_sprite_scale(p.fbWidth, call.callDesc.rectDsdx, call.callDesc.rectDtdy) || iss2000_high_sprite_edge(p.fbWidth, call.callDesc.rectDsdx, call.callDesc.rectDtdy, call.callDesc.rect) || iss2000_radar_marker_phase(p.fbWidth, call.callDesc.rectDsdx, call.callDesc.rectDtdy, call.callDesc.rect)), call.callDesc.otherMode.cycleType(), call.callDesc.otherMode.textFilt());
                            const bool introCanvasPhase = iss2000_intro_canvas_phase(call.shaderDesc.flags.upscale2D, call.callDesc.otherMode.cycleType(), call.callDesc.otherMode.textFilt(), call.callDesc.rectAspect, call.callDesc.rectDsdx, call.callDesc.rectDtdy, call.callDesc.rect.ulx, call.callDesc.rect.uly, call.callDesc.rect.lrx, call.callDesc.rect.lry, call.callDesc.rectLeftOrigin, call.callDesc.rectRightOrigin);
                            RenderViewport viewportRect = iss2000_sprite_viewport_rect(call.callDesc.rect, p.resolutionScale, p.fbWidth, invRatioScale, extOriginPercentage, horizontalMisalignment, call.callDesc.rectLeftOrigin, call.callDesc.rectRightOrigin, nativeSpritePhase, introCanvasPhase);
                            iss2000::MenuRectPrevious previousMenuRect;
                            if (iss2000::menu_rect_previous(p.curWorkload, call.callDesc.callIndex, previousMenuRect)) {
                                FixedRect previousRect = call.callDesc.rect;
                                previousRect.ulx = previousMenuRect.rect[0]; previousRect.uly = previousMenuRect.rect[1];
                                previousRect.lrx = previousMenuRect.rect[2]; previousRect.lry = previousMenuRect.rect[3];
                                const RenderViewport previousViewport = iss2000_sprite_viewport_rect(previousRect, p.resolutionScale, p.fbWidth, invRatioScale, extOriginPercentage, horizontalMisalignment, call.callDesc.rectLeftOrigin, call.callDesc.rectRightOrigin, nativeSpritePhase, introCanvasPhase);
                                viewportRect = iss2000_interpolate_sprite_viewport(previousViewport, viewportRect, previousMenuRect.weight);
                            }'''
def derive(source:bytes)->bytes:
 if hashlib.sha256(source).hexdigest()!=SOURCE_SHA256:raise ValueError('Pinned RT64 framebuffer renderer source digest mismatch')
 text=source.decode();boundary='    hlslpp::float3 viewPositionFrom('
 if text.count(boundary)!=1 or text.count(OLD)!=1:raise ValueError('Reviewed RT64 rectangle boundary is not unique')
 return ('#include \"runtime/menu_sprite_render.hpp\"\n'+text.replace(boundary,HELPERS+'\n'+boundary).replace(OLD,NEW)).encode()
def prepare(source:Path,output:Path)->dict:
 if output.is_symlink() or any(p.is_symlink()for p in output.absolute().parents):raise ValueError('Sprite phase output paths must not contain symlinks')
 generated=derive(source.read_bytes());receipt=dict(schema=1,attribution='djultra64',source_sha256=SOURCE_SHA256,generated_sha256=hashlib.sha256(generated).hexdigest(),guard='Normal-origin upscaled identity POINT rectangles, original640-wide512-derivative High equivalents and exact one-native-pixel mixed-derivative edge repair strips; exact constant-UV full-height intro side canvases; adjacent owned menu rectangle matches',change='Keep fractional viewport edges and original UV derivatives for a consistent original native texel phase. All other viewport calls unchanged.')
 files={'rt64_framebuffer_renderer.cpp':generated,'receipt.json':(json.dumps(receipt,indent=2)+'\n').encode()}
 if output.exists():
  if any(not(output/n).is_file()or(output/n).is_symlink()or(output/n).read_bytes()!=v for n,v in files.items()):raise ValueError('Refusing to overwrite changed private RT64 sprite phase output')
  return receipt
 output.mkdir(parents=True,exist_ok=False)
 for n,v in files.items():
  with(output/n).open('xb')as f:f.write(v)
 return receipt
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(prepare(a.source,a.output),indent=2))
