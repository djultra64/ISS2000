// Original project work: djultra64.
#pragma once
#include "controller_pak.hpp"
#include "recomp.h"
namespace iss2000 {
// Automatic native mode supplies storage to each connected player; legacy manual
// selection remains available only to the low-level diagnostic API.
void configure_paks(const std::filesystem::path& saves_directory,bool automatic=false);
void shutdown_paks();
PakAccessory pak_accessory(int port);
void set_pak_port_connected(unsigned port,bool connected);
void set_pak_accessory(unsigned port,PakAccessory accessory);
recomp_func_t* pak_service_lookup(uint32_t address);
std::string pak_storage_error();
// Preserve the genuine SDK filesystem implementation and publish its complete
// file-write operation only after its actual success; failures roll back.
void run_pak_file_write(uint8_t*,recomp_context*,recomp_func_t* original);
}
