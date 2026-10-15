// Original project work: djultra64.
#pragma once
#include <array>
#include <cstdint>

namespace iss2000 {
// Nintendo SDK osAiGetLength/Status/SetNextBuffer: current DMA length,
// two descriptors, FIFO_FULL when both are occupied. No PCM data lives here.
// https://ultra64.ca/files/documentation/online-manuals/man-v5-1/n64man/os/osAiGetLength.htm
class AudioFifo {
    std::array<uint32_t,2> frames_{};
    unsigned slots_{};
public:
    bool submit(uint32_t bytes) {
        if((bytes&7u) || bytes>262144u)return false;
        if(bytes==0)return true;
        if(slots_==2)return false;
        frames_[slots_++]=bytes/4;
        return true;
    }
    void consume(uint64_t frames) {
        while(slots_ && frames) {
            if(frames<frames_[0]) {frames_[0]-=uint32_t(frames);break;}
            frames-=frames_[0];
            frames_[0]=frames_[1];frames_[1]=0;--slots_;
        }
    }
    uint32_t length() const {return slots_?(frames_[0]*4)&~7u:0;}
    uint32_t status() const {return slots_?(0x40000000u|(slots_==2?0x80000000u:0)):0;}
};
// Convert real output-device stereo frames to source stereo frames without
// accumulating a rounding error at every SDL consumption observation.
class AudioFrameClock {
    uint64_t remainder_{};
public:
    uint64_t consume(uint64_t output_frames,uint32_t frequency) {
        uint64_t scaled=output_frames*frequency+remainder_;
        remainder_=scaled%48000;
        return scaled/48000;
    }
};
inline bool valid_audio_buffer(uint32_t address,uint32_t bytes) {
    if(address>=0x00800000u && (address&0xE0000000u)!=0x80000000u && (address&0xE0000000u)!=0xA0000000u)return false;
    uint32_t physical=address&0x1FFFFFFFu;
    return !(address&7u) && !(bytes&7u) && bytes<=262144u && physical<=0x800000u && bytes<=0x800000u-physical;
}
}
