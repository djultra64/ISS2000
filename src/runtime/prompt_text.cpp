// Original project work: djultra64.
#include "prompt_text.hpp"
#include <mutex>
#include <memory>
#include <stdexcept>
#include <optional>
#include <string>
namespace iss2000 {
namespace prompt_detail {
namespace {
std::optional<std::array<uint8_t,12>> text(std::string_view name){
    // Original80003A54 skips spaces, otherwise indexes the original glyph table
    // by ASCII-0x30. Literal plus/minus would index before that table.
    if(name=="+")name="PLUS";
    if(name=="-")name="MINUS";
    std::string label;
    for(unsigned char c:name){
        if(c>='a'&&c<='z')c=uint8_t(c-'a'+'A');
        if(c=='-')c=' ';
        if(!((c>='A'&&c<='Z')||(c>='0'&&c<='9')||c==' '))return {};
        label+=char(c);
    }
    if(label.empty()||label.size()>11||label.front()==' '||label.back()==' ')return {};
    if(label.size()<=5)label="PRESS "+label;
    std::array<uint8_t,12> bytes{};
    for(size_t n=0;n<label.size();++n)bytes[n]=uint8_t(label[n]);
    return bytes;
}
}
TitleTextGuard::TitleTextGuard(const TitlePromptLayout& layout):layout_(layout){
    if(layout.text_offset>0x800000-12 || !layout.original[0] || layout.original.back()!=0)
        throw std::invalid_argument("Invalid title prompt layout");
}
bool TitleTextGuard::prepare(uint8_t* ram,uint64_t slot,uint64_t source,std::string_view physical_name){
    const uint64_t expected=0x80000000ull+layout_.text_offset;
    if(!ram||slot!=layout_.registration_slot ||
       (source!=expected && source!=(0xFFFFFFFF00000000ull|expected)))return false;
    const auto location=layout_.text_offset;
    const auto& original=layout_.original;
    if(memory_!=ram){memory_=ram;owned_=false;}
    std::array<uint8_t,12> current{};
    for(uint32_t n=0;n<12;++n)current[n]=ram[(location+n)^3u];
    if(current!=original&&(!owned_||current!=applied_)){owned_=false;return false;}
    const auto desired=text(physical_name);
    const auto& bytes=desired?*desired:original;
    for(uint32_t n=0;n<12;++n)ram[(location+n)^3u]=bytes[n];
    applied_=bytes;owned_=bool(desired);
    return bool(desired);
}
}
namespace {
std::mutex title_mutex;
std::unique_ptr<prompt_detail::TitleTextGuard> title_guard;
}
void configure_title_prompt(const TitlePromptLayout& layout){
    auto candidate=std::make_unique<prompt_detail::TitleTextGuard>(layout);
    std::lock_guard lock(title_mutex);
    if(title_guard)throw std::logic_error("Title prompt is already configured");
    title_guard=std::move(candidate);
}
bool prepare_title_prompt(uint8_t* ram,uint64_t slot,uint64_t source,std::string_view physical_name){
    std::lock_guard lock(title_mutex);
    return title_guard && title_guard->prepare(ram,slot,source,physical_name);
}
}
