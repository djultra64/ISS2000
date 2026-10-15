// Original project work: djultra64.
#pragma once
#include "controller_pak.hpp"
namespace iss2000 {
constexpr int motor_init_result(int result,PakAccessory accessory) {
    // The upstream callback cannot represent Controller Pak and reports no-pak.
    // Translate only that result; disconnected-controller and other errors win.
    return result==1 && accessory==PakAccessory::Controller?11:result;
}
}
