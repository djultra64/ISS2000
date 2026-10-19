// Original project work: djultra64.
#include "pal_real_names.hpp"
#include "rom_image.hpp"
#include <algorithm>
namespace iss2000 {
std::optional<PalPlayerName> encode_pal_player_name(std::string_view text){
 if(text.empty()||text.size()>8||text.find_first_not_of(' ')==std::string_view::npos)return {};
 PalPlayerName out{};
 for(std::size_t i=0;i<text.size();++i){const char c=text[i];
  if(c==' ')out[i]=0;
  else if(c>='0'&&c<='9')out[i]=1+c-'0';
  else if(c>='A'&&c<='Z')out[i]=0x0B+c-'A';
  else if(c>='a'&&c<='z')out[i]=0x25+c-'a';
  else if(c=='.')out[i]=0x3F;
  else return {};
 }
 return out;
}
bool PalRealNames::configure(std::span<const uint8_t> rom,std::span<const std::string_view> names){
 ready_=false;
 if(rom.size()!=0x1000000||names.size()!=names_.size()||rom_detail::sha256_hex(rom)!="6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf")return false;
 decltype(names_) encoded{};
 for(std::size_t i=0;i<names.size();++i){auto name=encode_pal_player_name(names[i]);if(!name)return false;encoded[i]=*name;}
 names_=encoded;ready_=true;return true;
}
std::size_t PalRealNames::apply(std::span<uint8_t> ram,uint32_t offset,uint32_t guest,uint32_t size)const{
 constexpr uint32_t table_rom=0x2F1290,table_ram=0x1BFC40,record_size=56,table_size=106*22*record_size;
 const uint32_t physical=guest&0x1FFFFFFF;
 const uint32_t segment=guest&0xE0000000;
 if(!ready_||ram.size()!=0x800000||!size||(segment!=0x80000000&&segment!=0xA0000000)||physical>=ram.size()||size>ram.size()-physical||offset>=0x1000000||size>0x1000000-offset)return 0;
 if(int64_t(offset)-table_rom!=int64_t(physical)-table_ram)return 0;
 const uint32_t begin=std::max(offset,table_rom),end=std::min(offset+size,table_rom+table_size);
 if(begin>=end)return 0;
 std::size_t written=0;
 const uint32_t first=(begin-table_rom)/record_size,last=(end-1-table_rom)/record_size;
 for(uint32_t i=first;i<=last;++i){
  const uint32_t name=table_rom+i*record_size+24;
  for(uint32_t a=std::max(begin,name);a<std::min(end,name+8);++a){ram[(physical+a-offset)^3]=names_[i][a-name];++written;}
 }
 return written;
}
}
