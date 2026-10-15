// Original project work: djultra64.
#include "prompt_encoded.hpp"
#include "rom_image.hpp"
#include <algorithm>
#include <cstring>
#include <memory>
#include <mutex>
#include <optional>
#include <stdexcept>
#include <utility>
namespace iss2000 {
namespace {
std::optional<uint32_t> offset(uint64_t value,uint32_t size){
    const uint32_t lo=uint32_t(value),hi=uint32_t(value>>32);
    if(hi && (hi!=0xFFFFFFFFu || !(lo&0x80000000u)))return {};
    if((lo&0xE0000000u)!=0x80000000u && (lo&0xE0000000u)!=0xA0000000u)return {};
    const uint32_t physical=lo&0x1FFFFFFFu;
    if(physical>=0x800000 || size>0x800000-physical)return {};
    return physical;
}
uint32_t word(std::span<const uint8_t> ram,uint32_t p){uint32_t value;std::memcpy(&value,ram.data()+p,4);return value;}
std::vector<uint8_t> read(std::span<const uint8_t> ram,uint32_t p,uint32_t size){
    std::vector<uint8_t> result(size);
    for(uint32_t n=0;n<size;++n)result[n]=ram[(p+n)^3u];
    return result;
}
void write(std::span<uint8_t> ram,uint32_t p,const std::vector<uint8_t>& data){
    for(size_t n=0;n<data.size();++n)ram[(p+uint32_t(n))^3u]=data[n];
}
std::optional<std::vector<uint8_t>> encode(std::string_view text){
    // Original PAL font asset0D: space00,0..9=01..0A,A..Z=0B..24,
    // a..z=25..3E,period3F. Never emit original control/extended glyph bytes.
    std::vector<uint8_t> result;
    for(unsigned char c:text){
        if(c==' '||c=='-')result.push_back(0);
        else if(c>='0'&&c<='9')result.push_back(uint8_t(c-'0'+1));
        else if(c>='A'&&c<='Z')result.push_back(uint8_t(c-'A'+0x0B));
        else if(c>='a'&&c<='z')result.push_back(uint8_t(c-'a'+0x25));
        else if(c=='.')result.push_back(0x3F);
        else return {};
    }
    return result;
}
std::string name(std::string_view physical){
    if(physical=="+")return "Plus";
    if(physical=="-")return "Minus";
    return std::string(physical);
}
}
EncodedPromptLayout pal_en_encoded_prompt_layout(){
    // Exact whole-message hashes from original PAL data, not inferred US offsets.
    // All source extents terminate at the original FF11; editable ranges contain
    // letters/spaces only. No original asset bytes are embedded here.
    return {{
        {0x1EEF18,114,"7b7805919bd1bb1df64d63d80d47ca48a2262033fe7ce2c214bde56a95d865b0",{{80,30,0,"Press "," to proceed."}}},
        {0x1EEF8C,116,"4f9d9f404a5cd92b6b57ac25b1ac863e1299888d5f828150ef91c6bd4c4910d1",{{82,30,0,"Press "," to proceed."}}},
        {0x1F2304,78,"093e503c0ae212b0a895b90d47d8c46e47981bfef030179be1973461dc9e2512",{{51,23,2,"Press ","."}}},
        {0x1F23BC,37,"a14bdb78a497f5e528a5f05db791da611ff26fe06b0b7e7ec341fa1103432352",{{0,15,2,"Use ",""}}},
        // Data-only PAL overlay: ROM514950 -> guest802DD400. Source pointers
        // are original table entries5147FC/514828/514830; no alignment padding
        // preceding those actual targets is part of the guarded message.
        {0x2DD8C0,86,"83b627ece320dade69ad01d2b8fb420edd363ef8e747b6e2fe2213e382888bac",{{52,30,0,"Press "," to proceed."}}},
        {0x2DDB2C,69,"8d057ca0a914891920b0ec232acfead532118e40c0a1c45bcd81c98e744f7af0",{{35,30,0,"Press "," to proceed."}}},
        {0x2DDB74,68,"1bf17b202b95be48ce49fd8273856b7bfcb903aafa8a1966711fcafddc1ce71d",{{34,30,0,"Press "," to proceed."}}}
    }};
}
EncodedPromptGuard::EncodedPromptGuard(EncodedPromptLayout layout):layout_(std::move(layout)),cache_(layout_.messages.size()){
    if(layout_.messages.empty()||layout_.messages.size()>64)throw std::invalid_argument("Invalid encoded prompt layout");
    for(size_t i=0;i<layout_.messages.size();++i){
        const auto& message=layout_.messages[i];
        if(message.source_offset>=0x800000 || message.byte_count<2 || message.byte_count>1024 ||
           message.byte_count>0x800000-message.source_offset || message.original_sha256.size()!=64 ||
           message.original_sha256.find_first_not_of("0123456789abcdef")!=std::string::npos || message.edits.empty())
            throw std::invalid_argument("Invalid encoded prompt message extent/hash");
        for(size_t j=0;j<i;++j)
            if(layout_.messages[j].source_offset==message.source_offset)
                throw std::invalid_argument("Ambiguous encoded prompt source");
        std::vector<bool> edited(message.byte_count);
        for(const auto& edit:message.edits){
            if(!edit.capacity || edit.offset>message.byte_count || edit.capacity>message.byte_count-edit.offset ||
               edit.prompt_index>=3 || !encode(edit.prefix) || !encode(edit.suffix))
                throw std::invalid_argument("Invalid encoded prompt edit");
            for(uint32_t n=edit.offset;n<edit.offset+edit.capacity;++n){
                if(edited[n])throw std::invalid_argument("Overlapping encoded prompt edits");
                edited[n]=true;
            }
        }
    }
}
bool EncodedPromptGuard::prepare(std::span<uint8_t> ram,uint64_t text_object,const std::array<std::string_view,3>& names){
    if(ram.size()!=0x800000)return false;
    const auto object=offset(text_object,0x24);
    if(!object || *object%4 || ram[(*object+5)^3]!=0)return false;
    const auto source=offset(word(ram,*object+0x14),1);
    if(!source)return false;
    if(memory_!=ram.data()){memory_=ram.data();cache_=std::vector<Cache>(layout_.messages.size());}
    for(size_t i=0;i<layout_.messages.size();++i){
        const auto& message=layout_.messages[i];
        if(message.source_offset!=*source)continue;
        auto& cache=cache_[i];
        const auto current=read(ram,*source,message.byte_count);
        const bool ours=cache.valid && current==cache.applied;
        if(!ours){
            if(rom_detail::sha256_hex(current)!=message.original_sha256){cache.valid=false;return false;}
            // Verified controls remain at their original offsets. A malformed
            // profile must not gain ownership of a control byte, even by hash.
            if(current[current.size()-2]!=0xFF || current.back()!=0x11)return false;
            std::vector<bool> protected_bytes(current.size());
            for(size_t n=0;n<current.size();++n){
                if(current[n]<0xF5)continue;
                protected_bytes[n]=true;
                if(n+1<current.size())protected_bytes[++n]=true;
            }
            for(const auto& edit:message.edits)
                for(uint32_t n=edit.offset;n<edit.offset+edit.capacity;++n)
                    if(protected_bytes[n])return false;
            cache.original=current;cache.valid=true;
        }
        auto desired=cache.original;
        for(const auto& edit:message.edits){
            const auto physical=name(names[edit.prompt_index]);
            const std::string instruction=physical=="Unbound"?"Control unbound":edit.prefix+physical+edit.suffix;
            auto encoded=physical.empty()?std::optional<std::vector<uint8_t>>{}:encode(instruction);
            if(!encoded || encoded->size()>edit.capacity){
                if(ours)write(ram,*source,cache.original);
                cache.valid=false;return false;
            }
            std::fill_n(desired.begin()+edit.offset,edit.capacity,0);
            std::copy(encoded->begin(),encoded->end(),desired.begin()+edit.offset);
        }
        cache.applied=desired;write(ram,*source,desired);return true;
    }
    return false;
}
namespace {
std::mutex encoded_mutex;
std::unique_ptr<EncodedPromptGuard> encoded_guard;
}
void configure_encoded_menu_prompts(const EncodedPromptLayout& layout){
    auto candidate=std::make_unique<EncodedPromptGuard>(layout);
    std::lock_guard lock(encoded_mutex);
    if(encoded_guard)throw std::logic_error("Encoded menu prompts are already configured");
    encoded_guard=std::move(candidate);
}
bool prepare_encoded_menu_prompt(std::span<uint8_t> ram,uint64_t object,const std::array<std::string_view,3>& names){
    std::lock_guard lock(encoded_mutex);return encoded_guard && encoded_guard->prepare(ram,object,names);
}
}
