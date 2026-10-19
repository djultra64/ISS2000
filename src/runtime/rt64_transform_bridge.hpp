// Original project work: djultra64.
#pragma once
#include "transform_tracker.hpp"
#include <memory>
namespace RT64 { struct State; struct GBI; }
namespace iss2000 {
struct TransformSelection {
    enum class Kind { Ignore, Inherit, Camera, Model };
    Kind kind=Kind::Ignore;
    uint32_t id=0;
    bool vertices=false;
};
// Addresses here are already resolved through the active RSP segment table.
// This policy does not read or write guest memory or execute game code.
inline TransformSelection select_rt64_transform(const TransformTaskSnapshot* snapshot,bool allow,
    uint32_t physical,bool projection,bool load,bool perspective){
    using Kind=TransformSelection::Kind;
    if(!allow || !snapshot)return {};
    if(!projection && load){
        if(auto tag=snapshot->lookup(physical)){
            if(snapshot->model_scope)for(const auto& cloth:snapshot->model_scope->vertex_models)
                if(cloth.record&&cloth.id&&tag->record==cloth.record)return {Kind::Model,cloth.id,true};
            return {Kind::Model,tag->id};
        }
        return {};
    }
    // Camera and multiply inheritance retain the proven field policy. Unknown
    // static/orthographic matrices elsewhere never acquire an inferred group.
    if(!perspective || (snapshot->scene_token&0xFFFF)!=snapshot->layout.interpolation_scene_token)return {};
    if(projection){
        unsigned slot=0;
        const auto& layout=snapshot->layout;
        if(load){if(physical!=layout.perspective_matrices[0] && physical!=layout.perspective_matrices[1])return {};}
        else if(physical==layout.view_matrices[1][0] || physical==layout.view_matrices[1][1])slot=1;
        else if(physical!=layout.view_matrices[0][0] && physical!=layout.view_matrices[0][1])return {};
        const auto id=snapshot->camera_id(slot);
        return id?TransformSelection{Kind::Camera,id}:TransformSelection{};
    }
    if(auto tag=snapshot->lookup(physical))return {Kind::Model,tag->id};
    return load?TransformSelection{}:TransformSelection{Kind::Inherit,0};
}
struct TransformBridgeStats {
    uint64_t matrix_calls{},model_groups{},camera_groups{},inherited_groups{},ignored_groups{};
};
// Scoped, synchronous F3DEX2 callback installation. Construct after loadUCodeGBI
// and keep alive only around processDisplayLists. RT64 State/GBI must outlive it;
// the caller must serialize display-list processing for a given State/GBI.
// Unsupported or already-owned maps are left untouched (installed()==false).
class RT64TransformBridge {
    struct Impl;
    std::unique_ptr<Impl> impl_;
public:
    RT64TransformBridge(RT64::State*,RT64::GBI*,std::shared_ptr<const TransformTaskSnapshot>,bool allow);
    ~RT64TransformBridge();
    RT64TransformBridge(const RT64TransformBridge&)=delete;
    RT64TransformBridge& operator=(const RT64TransformBridge&)=delete;
    bool installed()const noexcept;
    TransformBridgeStats stats()const noexcept;
};
}
