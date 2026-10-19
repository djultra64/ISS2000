// Original project work: djultra64.
#pragma once
#include "transform_tracker.hpp"
#include <span>
#include <vector>
namespace iss2000 {
struct PalRadarCommand {uint32_t pc{};TransformTag actor{};uint32_t role{};};
// Immutable completed private-list observation. Never changes original RAM.
class PalRadarCapture {
 bool active_{},sealed_{};uint32_t begin_{};TransformTag owner_{};
 std::vector<PalRadarCommand> commands_;std::vector<uint8_t> bytes_;
public:
 bool begin(std::span<const uint8_t>,TransformTag owner,unsigned bank,uint32_t begin);
 bool emit(std::span<const uint8_t>,uint32_t begin,uint32_t end,TransformTag actor,uint32_t role);
 bool finish(std::span<const uint8_t>,uint32_t end);
 bool reachable(std::span<const uint8_t>,uint64_t parent_root)const;
 bool unchanged(std::span<const uint8_t>)const;
 uint32_t begin_address()const{return begin_;}
 const TransformTag& owner()const{return owner_;}
 const std::vector<PalRadarCommand>& commands()const{return commands_;}
};
}
