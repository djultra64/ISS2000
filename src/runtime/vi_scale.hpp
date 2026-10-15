// Original project work: djultra64.
#pragma once
#include <cmath>
#include <cstdint>
#include <stdexcept>
namespace iss2000 {
// Original PAL setters: both multiply the mode scale; preserve field offsets.
class ViScaleState {
 bool x_updated_{},y_updated_{};
 float x_{};
 float y_{};
 static void validate(float value){
  if(!std::isfinite(value)||value<0||value>16)throw std::invalid_argument("Invalid VI scale factor");
 }
public:
 void reset(){x_updated_=y_updated_=false;}
 void set_x(float value){validate(value);x_=value;x_updated_=true;}
 void set_y(float value){validate(value);y_=value;y_updated_=true;}
 uint32_t x_register(uint32_t mode)const{return x_updated_?(uint32_t(x_*float(mode&0xFFFu))&0xFFFu)|(mode&~0xFFFu):mode;}
 uint32_t y_register(uint32_t mode)const{return y_updated_?uint32_t(float(mode&0xFFFu)*y_)|(mode&~0xFFFu):mode;}
};
}
