// Original project work: djultra64.
#include "platform.hpp"
using namespace iss2000::platform;
// The same logical action must follow its physical position across controller
// families. These contracts protect Nintendo's two swapped face-button pairs.
static_assert(face_label(Family::Xbox,0)=="A");
static_assert(face_label(Family::Nintendo,0)=="B");
static_assert(face_label(Family::Xbox,1)=="B");
static_assert(face_label(Family::Nintendo,1)=="A");
static_assert(face_label(Family::Xbox,2)=="X");
static_assert(face_label(Family::Nintendo,2)=="Y");
static_assert(face_label(Family::Xbox,3)=="Y");
static_assert(face_label(Family::Nintendo,3)=="X");
static_assert(face_label(Family::PlayStation,0)=="Cross");
static_assert(face_label(Family::PlayStation,1)=="Circle");
static_assert(face_label(Family::PlayStation,2)=="Square");
static_assert(face_label(Family::PlayStation,3)=="Triangle");
static_assert(face_label(Family::Xbox,4)=="Unbound");
