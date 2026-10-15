// Original project work: djultra64.
#pragma once
#include "controller_pak.hpp"
#include "recomp.h"
namespace iss2000 {
void configure_paks(const std::filesystem::path& saves_directory);
void shutdown_paks();
PakAccessory pak_accessory(int port);
void set_pak_port_connected(unsigned port,bool connected);
void set_pak_accessory(unsigned port,PakAccessory accessory);
recomp_func_t* pak_service_lookup(uint32_t address);
std::string pak_storage_error();
}
