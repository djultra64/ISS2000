// Original project work: djultra64.
#pragma once
#include <cstdint>
namespace iss2000 {
// Main-thread window requests are separate from renderer configuration snapshots.
// Success only requests an asynchronous transition: actual flags acknowledge it.
class WindowModeSync {
 bool initialized_{},requested_{};
 uint64_t attempted_at_{};
 bool attempted_{};
public:
 enum class Result { Satisfied,Pending,Failed };
 template<class Request> Result update(bool requested,bool actual,uint64_t now_ms,Request request){
  if(!initialized_||requested!=requested_){initialized_=true;requested_=requested;attempted_=false;}
  if(actual==requested){attempted_=false;return Result::Satisfied;}
  if(attempted_&&now_ms-attempted_at_<1000)return Result::Pending;
  attempted_=true;attempted_at_=now_ms;
  return request(requested)?Result::Pending:Result::Failed;
 }
};
}
