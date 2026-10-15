// Original project work: djultra64.
#pragma once
#include <span>
#include <cstdint>
#include <cstring>
#include <stdexcept>
namespace iss2000 {
inline void set_boot_tv_type(std::span<uint8_t> ram,uint32_t tv_type){
 if(ram.size()<0x304||tv_type>2)throw std::invalid_argument("Invalid IPL television identity");
 // Aligned guest words are native-endian in the runtime's word-swapped RDRAM.
 std::memcpy(ram.data()+0x300,&tv_type,sizeof(tv_type));
}
}
