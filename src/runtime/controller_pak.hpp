// Original project work: djultra64.
#pragma once
#include <array>
#include <cstdint>
#include <filesystem>
#include <memory>
#include <string>
namespace iss2000 {
using PakImage=std::array<uint8_t,32768>;
using PakBlock=std::array<uint8_t,32>;
enum class PakAccessory { None,Rumble,Controller };
// Canonical N64 byte order. Filesystem layout/checksums derive from ISS2000's
// original InitPak, ID checksum and inode functions; existing images are untouched.
PakImage formatted_controller_pak(const std::array<uint8_t,24>& identity);
class ControllerPakStore {
    struct State;
    std::unique_ptr<State> state_;
public:
    explicit ControllerPakStore(const std::filesystem::path& saves_directory);
    ~ControllerPakStore();
    ControllerPakStore(const ControllerPakStore&)=delete;
    ControllerPakStore& operator=(const ControllerPakStore&)=delete;
    void set_accessory(unsigned port,PakAccessory accessory);
    PakAccessory accessory(unsigned port) const;
    // SDK return codes: 0 success,1 no pak,2 changed pak,4 I/O,5 invalid,11 device.
    int status(unsigned port);
    uint8_t plugged_mask() const;
    int read_block(unsigned port,uint16_t block,PakBlock& output);
    int write_block(unsigned port,uint16_t block,const PakBlock& input,bool force);
    // Called around the real SDK file-write function. Low-level blocks remain
    // visible to that thread; successful return requires one durable publish.
    int begin_file_write(unsigned port);
    int finish_file_write(unsigned port,bool commit);
    std::filesystem::path image_path(unsigned port) const;
    std::string last_error() const;
};
}
