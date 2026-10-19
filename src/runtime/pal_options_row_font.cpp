// Original project work: djultra64.
#include "pal_options_row_font.hpp"
#include "rom_image.hpp"
#include <array>
namespace iss2000 {namespace {
struct Part {unsigned offset,stride,x,y,width;bool capital_f=false;};
// All slices retain the original 16-pixel row and original palette indices.
// P/C: original Create Player; Setting: original Game Setting;
// final s: original Resolution. Five transparent columns separate PC/Settings.
constexpr std::array pc{
    Part{0x700,96,48,16,12},Part{0x700,96,0,16,10},Part{0,0,0,0,5},
    Part{0,112,42,16,49},Part{0xD00,128,18,16,7}};
constexpr std::array setting{Part{0,112,42,16,49}};
constexpr std::array game_setting{Part{0,112,0,16,42},Part{0,112,42,16,70}};
constexpr std::array create_player{
    Part{0x700,96,0,16,10},Part{0x700,96,10,16,38},
    Part{0x700,96,48,16,12},Part{0x700,96,60,16,36}};
constexpr std::array resolution{
    Part{0xD00,128,0,16,18},Part{0xD00,128,18,16,7},
    Part{0xD00,128,25,16,103}};
constexpr std::array go_back{Part{0,112,0,0,56}};
constexpr std::array player{Part{0x700,96,48,16,48}};
// A bounded selection of source columns from the SAME
// original Options asset. There is no inferred alphabet or drawn replacement.
// Per-word antialias variants remain authored. Lowercase v is the right
// diagonal pair of the original w in New; p is from player. F combines
// E upper strokes with P lower stem, explicitly marked below.
struct Letter {char letter;Part source;};
constexpr std::array letters{
    Letter{'F',{0x2800,128,0,0,12,true}},
    Letter{'g',{0,112,82,16,9}},
    Letter{'p',{0x2000,64,20,48,9}},
    Letter{'v',{0x2000,64,24,0,6}},
    Letter{'P',{0x700,96,48,16,12}},Letter{'C',{0x700,96,0,16,10}},
    Letter{'S',{0,112,42,16,9}},Letter{'R',{0xD00,128,0,16,11}},
    Letter{'G',{0,112,0,0,11}},Letter{'a',{0x700,96,25,16,8}},
    Letter{'b',{0,112,24,0,8}},Letter{'c',{0,112,40,0,7}},
    Letter{'e',{0x700,96,17,16,8}},Letter{'i',{0,112,71,16,3}},
    Letter{'l',{0xD00,128,33,16,3}},Letter{'m',{0,112,18,16,11}},
    Letter{'n',{0,112,74,16,8}},Letter{'o',{0xD00,128,25,16,8}},
    Letter{'r',{0x700,96,10,16,7}},Letter{'s',{0xD00,128,18,16,7}},
    Letter{'t',{0x700,96,33,16,6}},Letter{'u',{0xD00,128,36,16,7}},
    Letter{'y',{0x700,96,72,16,7}},Letter{'k',{0,112,47,0,8}}};
std::optional<std::vector<Part>> body(std::string_view text){
    // Natural labels avoid letters absent from this original row-face source.
    if(text=="Graphics")text="Picture";
    else if(text=="Save")text="Save options";
    else if(text=="Aspect")text="Screen ratio";
    else if(text=="Frame rate")text="Rate";
    else if(text=="Vibration")text="Rumble";
    else if(text=="Controller type")text="Controller";
    if(text!="Filtering"&&text!="Picture"&&text!="Controls"&&text!="Store"&&text!="Cancel"&&
       text!="Save options"&&text!="Framerate limit"&&text!="Screen ratio"&&text!="Rate"&&text!="Screen"&&text!="Rumble"&&text!="Controller")return {};
    std::vector<Part> out;
    for(char c:text){
        if(c==' '){out.push_back({0,0,0,0,5});continue;}
        bool found=false;
        for(const auto& letter:letters)if(letter.letter==c){out.push_back(letter.source);found=true;break;}
        if(!found)return {};
    }
    return out;
}
}
std::optional<PalOptionsRowBitmap> pal_options_row_bitmap(
    std::span<const uint8_t> asset,std::string_view text){
    std::span<const Part> parts;
    std::optional<std::vector<Part>> assembled;
    if(text=="PC Settings")parts=pc;
    else if(text=="Setting")parts=setting;
    else if(text=="Game Setting")parts=game_setting;
    else if(text=="Create Player")parts=create_player;
    else if(text=="Resolution")parts=resolution;
    else if(text=="Go back"||text=="Back")parts=go_back;
    else if(text=="Player")parts=player;
    else {assembled=body(text);if(!assembled)return {};parts=*assembled;}
    if(asset.size()!=0x2C00 || rom_detail::sha256_hex(asset)!=
       "5dbf56dd71d5c280fc0fad104003a23898312e4fd9468a76fd023db8d221a3e8")return {};
    PalOptionsRowBitmap out;out.pixels.resize(out.width*out.height/2);unsigned at=0;
    for(const auto& part:parts){
        if(part.width>out.width-at)return {};
        if(part.stride)for(unsigned y=0;y<out.height;++y)for(unsigned x=0;x<part.width;++x){
            const unsigned source=(part.y+y)*part.stride+part.x+x;
            if(part.offset+source/2>=asset.size())return {};
            const auto packed=asset[part.offset+source/2];
            unsigned pixel=source&1?packed&15:packed>>4;
            // F shares E's authored top and middle strokes. Below the middle
            // stroke, retain P's straight italic stem and its antialias edge;
            // neither missing letter nor another face is silently substituted.
            if(part.capital_f&&y>=8){
                const unsigned stem=(16+y)*96+48+x;
                const auto p=asset[0x700+stem/2];pixel=x<6?(stem&1?p&15:p>>4):0;
            }
            const unsigned destination=y*out.width+at+x;
            out.pixels[destination/2]|=uint8_t(pixel<<(destination&1?0:4));
        }
        at+=part.width;
    }
    out.advance=uint16_t(at);return out;
}
}
