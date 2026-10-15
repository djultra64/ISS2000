"""Prepare a privately generated PAL VI adapter from pinned upstream source.

Does not edit the upstream checkout. Original project work: djultra64.
"""
import argparse
import hashlib
import json
from pathlib import Path

SOURCE_SHA256='6e97f155ae149a191128c9e941735a4e9948056787b39a8f67c26581866fac05'
REPLACEMENTS={
    'regs.VI_STATUS_REG = next_state->control;': 'regs.VI_STATUS_REG = next_state->control;\n            iss2000_record_vi_framebuffer(regs.VI_ORIGIN_REG, regs.VI_WIDTH_REG, regs.VI_STATUS_REG, uint32_t(framebuffer));',
    '    int retrace_count = 1;': '    int retrace_count = 1;\n    iss2000::ViScaleState scale;',
    'uint32_t yScale = field_regs->yScale;': 'uint32_t yScale = next_state->scale.y_register(field_regs->yScale);',
    'regs.VI_X_SCALE_REG = common_regs->xScale; // TODO implement osViSetXScale':
        'regs.VI_X_SCALE_REG = next_state->scale.x_register(common_regs->xScale);',
    'next_state->mode = mode;': 'next_state->mode = mode;\n    next_state->scale.reset();',
    '''extern "C" void osViSetXScale(float scale) {
    if (scale != 1.0f) {
        assert(false);
    }
}''': '''extern "C" void osViSetXScale(float scale) {
    std::lock_guard lock{ events_context.message_mutex };
    events_context.vi.get_next_state()->scale.set_x(scale);
}''',
    '''extern "C" void osViSetYScale(float scale) {
    if (scale != 1.0f) {
        assert(false);
    }
}''': '''extern "C" void osViSetYScale(float scale) {
    std::lock_guard lock{ events_context.message_mutex };
    events_context.vi.get_next_state()->scale.set_y(scale);
}''',
    '(total_vis * 1000000us) / (60 * ultramodern::get_speed_multiplier())':
        'iss2000::pal_video_timing.deadline(total_vis, ultramodern::get_speed_multiplier())',
    '(time_now * (60 * ultramodern::get_speed_multiplier()) / 1000ms) + 1':
        'iss2000::pal_video_timing.elapsed_vis(time_now, ultramodern::get_speed_multiplier())',
}

def prepare(source:Path,output:Path)->dict:
    original=source.read_bytes()
    if hashlib.sha256(original).hexdigest()!=SOURCE_SHA256:
        raise ValueError('Pinned runtime events source digest mismatch')
    text=original.decode()
    for old,new in REPLACEMENTS.items():
        if text.count(old)!=1:raise ValueError('Pinned runtime VI expression is not unique')
        text=text.replace(old,new)
    generated=('#include "runtime/video_timing.hpp"\n#include "runtime/vi_scale.hpp"\n#include "runtime/vi_framebuffer.hpp"\n'+text).encode()
    receipt=dict(source_sha256=SOURCE_SHA256,generated_sha256=hashlib.sha256(generated).hexdigest(),
                 vi_hz=50,status='PAL VI scheduling and original next-state X/Y scaling; presentation rate is independent')
    files={'events.cpp':generated,'receipt.json':(json.dumps(receipt,indent=2)+'\n').encode()}
    if output.exists():
        if output.is_symlink() or any(not (output/name).is_file() or (output/name).is_symlink() or (output/name).read_bytes()!=value for name,value in files.items()):
            raise ValueError('Refusing to modify existing timing adaptation output')
        return receipt
    if any(parent.is_symlink() for parent in output.absolute().parents):
        raise ValueError('Timing output parent paths must not contain symlinks')
    output.mkdir(parents=True,exist_ok=False)
    for name,value in files.items():
        with (output/name).open('xb') as target:target.write(value)
    return receipt

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(prepare(args.source,args.output),indent=2))

if __name__=='__main__':main()
