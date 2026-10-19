// Original project work: djultra64.
#pragma once
#include <cstdint>
#include <mutex>
namespace iss2000 {
struct MainExitInput {bool north{},accept{},cancel{},left{},right{},any{},focused{};uint64_t device{};};
struct MainExitResult {bool suppress{},quit{};};
struct MainExitView {bool available{},open{},yes{};};
class MainExitMenu {
    mutable std::mutex mutex_;
    bool available_{},open_{},yes_{},armed_{},drain_{};
    uint64_t device_{};
    unsigned previous_{};
public:
    void publish(bool available){std::lock_guard lock(mutex_);
        if(available_==available)return;
        available_=available;armed_=false;previous_=0;
        if(!available){drain_|=open_;open_=yes_=false;}
    }
    MainExitView view()const{std::lock_guard lock(mutex_);return {available_,open_,yes_};}
    MainExitResult input(const MainExitInput&i){std::lock_guard lock(mutex_);
        if(!i.focused||device_!=i.device){device_=i.device;armed_=false;previous_=0;yes_=false;}
        if(i.focused&&!i.any){armed_=true;drain_=false;previous_=0;}
        MainExitResult out{open_||drain_,false};
        if(!available_||!i.focused||!armed_)return out;
        const unsigned held=unsigned(i.north)|unsigned(i.accept)<<1|unsigned(i.cancel)<<2|unsigned(i.left)<<3|unsigned(i.right)<<4;
        const auto pressed=held&~previous_;previous_=held;
        if(!open_){if(pressed&1){open_=true;yes_=false;armed_=false;out.suppress=true;}return out;}
        if(pressed&4){open_=yes_=false;armed_=false;drain_=true;return out;}
        if(pressed&8)yes_=false;
        else if(pressed&16)yes_=true;
        else if(pressed&2){out.quit=yes_;open_=yes_=false;armed_=false;drain_=true;}
        return out;
    }
};
inline MainExitMenu& main_exit_menu(){static MainExitMenu menu;return menu;}
}
