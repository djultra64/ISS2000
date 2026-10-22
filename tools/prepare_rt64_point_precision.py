"""Pinned private POINT-sprite precision derivative. Original work: djultra64."""
import argparse, hashlib, json
from pathlib import Path
SOURCE_SHA256='927ca2d1c748862f683b3d6115bc97a56cc2ff343474a641046a64788fecef3a'
OLD='        uvCoord = round(uvCoord * LowPrecision) / LowPrecision;'
NEW='''        // Enlarged POINT rectangles must keep floor(UV) invariant. Rounding
        // U31.996 to32 reads another atlas column at fractional PAL scales.
        // Keep hardware rounding for the original grid and all other draws.
        const bool precisePointSprite = renderFlagRect(renderFlags) && renderFlagUpscale2D(renderFlags) &&
            !renderFlagLinearFiltering(renderFlags) && otherMode.textFilt() == G_TF_POINT &&
            otherMode.cycleType() == G_CYC_1CYCLE &&
            abs(ddxUV.x) > 0.0f && abs(ddxUV.x) < 1.0f &&
            abs(ddyUV.y) > 0.0f && abs(ddyUV.y) < 1.0f;
        uvCoord = precisePointSprite ? floor(uvCoord * LowPrecision) / LowPrecision :
            round(uvCoord * LowPrecision) / LowPrecision;'''
def derive(raw:bytes)->bytes:
 if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA256:raise ValueError('Pinned RT64 texture sampler digest mismatch')
 text=raw.decode()
 if text.count(OLD)!=1:raise ValueError('POINT interpolation boundary is not unique')
 return text.replace(OLD,NEW).encode()

PINS={
 'shaders/TextureSampler.hlsli':SOURCE_SHA256,
 'shaders/RasterPS.hlsl':'957b283411550457573421015580f84ca750c68a050981dbc1a4fe2634507820',
 'render/rt64_raster_shader.cpp':'5e5de4bbd8a22192e857c277bae5af033b8606a6464aa73863d2efe0fd0a0d4d',
}
def prepare(source:Path,output:Path)->dict:
 if output.is_symlink() or any(p.is_symlink()for p in output.absolute().parents):
  raise ValueError('POINT shader output paths must not contain symlinks')
 original={name:(source/name).read_bytes()for name in PINS}
 if any(hashlib.sha256(original[name]).hexdigest()!=digest for name,digest in PINS.items()):
  raise ValueError('Pinned POINT shader integration source digest mismatch')
 files={'shaders/TextureSampler.hlsli':derive(original['shaders/TextureSampler.hlsli']),
        'shaders/RasterPS.hlsl':original['shaders/RasterPS.hlsl'],
        'rt64_raster_shader.cpp':original['render/rt64_raster_shader.cpp']}
 receipt=dict(schema=1,attribution='djultra64',source_sha256=PINS,
  generated_sha256={name:hashlib.sha256(data).hexdigest()for name,data in files.items()},
  behavior='Preserve floor(UV) for magnified one-cycle POINT rectangles; rebuild all fragment permutations and their consumer with matching array lengths.')
 files['receipt.json']=(json.dumps(receipt,indent=2)+'\n').encode()
 if output.exists():
  if not output.is_dir() or any(not(output/name).is_file() or (output/name).is_symlink() or (output/name).read_bytes()!=data for name,data in files.items()):
   raise ValueError('Refusing to overwrite changed private POINT shader sources')
  return receipt
 output.mkdir(parents=True,exist_ok=False)
 for name,data in files.items():
  p=output/name;p.parent.mkdir(parents=True,exist_ok=True)
  with p.open('xb')as f:f.write(data)
 return receipt
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
 print(json.dumps(prepare(args.source,args.output),indent=2))
