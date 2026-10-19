# Original project work: djultra64.
# Dependencies are built separately from pinned source under private .local/.
set(ISS2000_ROM_REVISION "iss2000-pal-en-de-rev0" CACHE STRING "Exact ROM revision compiled into this game")
set_property(CACHE ISS2000_ROM_REVISION PROPERTY STRINGS iss2000-us-rev0 iss2000-pal-en-de-rev0)
if(ISS2000_ROM_REVISION STREQUAL "iss2000-pal-en-de-rev0")
  set(ISS2000_DEFAULT_CPU "${CMAKE_SOURCE_DIR}/.local/pal-map-bound-01/functions")
  set(ISS2000_DEFAULT_METADATA "${CMAKE_SOURCE_DIR}/.local/pal-native-metadata-04")
elseif(ISS2000_ROM_REVISION STREQUAL "iss2000-us-rev0")
  set(ISS2000_DEFAULT_CPU "${CMAKE_SOURCE_DIR}/.local/runtime-map-04/functions")
  set(ISS2000_DEFAULT_METADATA "${CMAKE_SOURCE_DIR}/.local/native-metadata-09")
else()
  message(FATAL_ERROR "Unsupported native ROM revision: ${ISS2000_ROM_REVISION}")
endif()
set(ISS2000_RUNTIME_SOURCE "${CMAKE_SOURCE_DIR}/.local/deps/N64ModernRuntime" CACHE PATH "Pinned runtime")
set(ISS2000_RT64_SOURCE "${CMAKE_SOURCE_DIR}/.local/deps/rt64" CACHE PATH "Pinned RT64")
set(ISS2000_RUNTIME_BUILD "${CMAKE_SOURCE_DIR}/.local/runtime-deps-build" CACHE PATH "Runtime dependency build")
set(ISS2000_RT64_BUILD "${CMAKE_SOURCE_DIR}/.local/rt64-build" CACHE PATH "RT64 dependency build")
set(ISS2000_GAME_GENERATED "${ISS2000_DEFAULT_CPU}" CACHE PATH "Private generated CPU code")
set(ISS2000_NATIVE_METADATA "${ISS2000_DEFAULT_METADATA}" CACHE PATH "Verified native service/section metadata")
set(ISS2000_AUDIO_GENERATED "${CMAKE_SOURCE_DIR}/.local/runtime-research-rsp/audio.cpp" CACHE FILEPATH "Original generated audio RSP")
find_package(SDL2 CONFIG REQUIRED)
find_package(Threads REQUIRED)
file(GLOB ISS2000_CPU_SOURCES CONFIGURE_DEPENDS "${ISS2000_GAME_GENERATED}/*.c")
if(NOT ISS2000_CPU_SOURCES OR NOT EXISTS "${ISS2000_NATIVE_METADATA}/native_metadata.cpp")
  message(FATAL_ERROR "Generate and verify private CPU code and native metadata before building")
endif()
# A PAL importer must never be linked to a US map or retained SDK body.
file(READ "${CMAKE_SOURCE_DIR}/config/roms/${ISS2000_ROM_REVISION}.json" ISS2000_REVISION_JSON)
string(JSON ISS2000_EXPECTED_DIGEST GET "${ISS2000_REVISION_JSON}" sha256)
file(READ "${ISS2000_NATIVE_METADATA}/receipt.json" ISS2000_METADATA_JSON)
get_filename_component(ISS2000_MAP_DIRECTORY "${ISS2000_GAME_GENERATED}" DIRECTORY)
file(READ "${ISS2000_MAP_DIRECTORY}/summary.json" ISS2000_MAP_JSON)
foreach(identity_json ISS2000_METADATA_JSON ISS2000_MAP_JSON)
  string(JSON input_digest GET "${${identity_json}}" rom_sha256)
  if(NOT input_digest STREQUAL ISS2000_EXPECTED_DIGEST)
    message(FATAL_ERROR "Native map/metadata ROM identity does not match ${ISS2000_ROM_REVISION}")
  endif()
endforeach()
file(SHA256 "${ISS2000_MAP_DIRECTORY}/section-analysis.json" ISS2000_SECTION_DIGEST)
string(JSON ISS2000_METADATA_SECTION_DIGEST GET "${ISS2000_METADATA_JSON}" section_analysis_sha256)
if(NOT ISS2000_SECTION_DIGEST STREQUAL ISS2000_METADATA_SECTION_DIGEST)
  message(FATAL_ERROR "Native metadata does not describe the selected CPU section map")
endif()
foreach(generated_file native_metadata.cpp native_bindings.cpp native_retained.cpp)
  file(SHA256 "${ISS2000_NATIVE_METADATA}/${generated_file}" actual_digest)
  string(JSON expected_digest GET "${ISS2000_METADATA_JSON}" generated_files "${generated_file}")
  if(NOT actual_digest STREQUAL expected_digest)
    message(FATAL_ERROR "Native metadata source changed after verification: ${generated_file}")
  endif()
endforeach()
if(ISS2000_ROM_REVISION STREQUAL "iss2000-pal-en-de-rev0")
  find_package(Python3 REQUIRED COMPONENTS Interpreter)
  set(ISS2000_RENDER_PATCH_MANIFEST "${CMAKE_SOURCE_DIR}/config/recomp/${ISS2000_ROM_REVISION}/render-patches.json")
  set(ISS2000_RENDER_PATCH_OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/pal-render-sources")
  execute_process(COMMAND "${Python3_EXECUTABLE}" -m tools.prepare_render_sources
    --generated "${ISS2000_GAME_GENERATED}" --manifest "${ISS2000_RENDER_PATCH_MANIFEST}"
    --output "${ISS2000_RENDER_PATCH_OUTPUT}"
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" RESULT_VARIABLE render_patch_result)
  if(NOT render_patch_result EQUAL 0)
    message(FATAL_ERROR "Could not prepare reviewed PAL render consumers")
  endif()
  file(READ "${ISS2000_RENDER_PATCH_MANIFEST}" render_patch_json)
  string(JSON patch_count LENGTH "${render_patch_json}" patches)
  math(EXPR patch_last "${patch_count}-1")
  foreach(index RANGE 0 ${patch_last})
    string(JSON filename GET "${render_patch_json}" patches ${index} source)
    list(REMOVE_ITEM ISS2000_CPU_SOURCES "${ISS2000_GAME_GENERATED}/${filename}")
    list(APPEND ISS2000_CPU_SOURCES "${ISS2000_RENDER_PATCH_OUTPUT}/${filename}")
  endforeach()
endif()
find_package(Python3 REQUIRED COMPONENTS Interpreter)
if(ISS2000_ROM_REVISION STREQUAL "iss2000-pal-en-de-rev0")
  set(ISS2000_RUNTIME_MANIFEST "${CMAKE_SOURCE_DIR}/config/recomp/${ISS2000_ROM_REVISION}/runtime-symbols.json")
else()
  set(ISS2000_RUNTIME_MANIFEST "${CMAKE_SOURCE_DIR}/config/recomp/runtime-symbols.json")
endif()
set(ISS2000_VERIFY_COMMAND "${Python3_EXECUTABLE}" -m tools.verify_native_build
  --revision "${ISS2000_ROM_REVISION}" --generated "${ISS2000_GAME_GENERATED}"
  --metadata "${ISS2000_NATIVE_METADATA}" --runtime-symbols "${ISS2000_RUNTIME_MANIFEST}"
  --audio "${ISS2000_AUDIO_GENERATED}")
if(ISS2000_ROM_REVISION STREQUAL "iss2000-pal-en-de-rev0")
  add_custom_target(iss2000_verify_native_inputs
    COMMAND ${ISS2000_VERIFY_COMMAND}
    COMMAND "${Python3_EXECUTABLE}" -m tools.prepare_render_sources
      --generated "${ISS2000_GAME_GENERATED}" --manifest "${ISS2000_RENDER_PATCH_MANIFEST}"
      --output "${ISS2000_RENDER_PATCH_OUTPUT}"
    COMMAND "${Python3_EXECUTABLE}" -m tools.prepare_runtime_timing
      --source "${ISS2000_RUNTIME_SOURCE}/ultramodern/src/events.cpp"
      --output "${CMAKE_CURRENT_BINARY_DIR}/pal-runtime-timing-v4"
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" VERBATIM)
else()
  add_custom_target(iss2000_verify_native_inputs COMMAND ${ISS2000_VERIFY_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" VERBATIM)
endif()
add_library(iss2000_original OBJECT ${ISS2000_CPU_SOURCES})
add_dependencies(iss2000_original iss2000_verify_native_inputs)
set_target_properties(iss2000_original PROPERTIES UNITY_BUILD ON UNITY_BUILD_BATCH_SIZE 100)
target_include_directories(iss2000_original PRIVATE "${ISS2000_N64RECOMP_SOURCE}/include")
if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(iss2000_original PRIVATE -O1 -fexceptions -fno-strict-aliasing)
endif()
add_executable(iss2000
  src/game_main.cpp src/platform.cpp src/renderer.cpp src/runtime/native_game.cpp src/runtime/rom_image.cpp src/runtime/ntsc_match_clock.cpp src/runtime/debug_console.cpp src/runtime/graphics_settings.cpp src/runtime/input_preferences.cpp src/runtime/test_controller.cpp src/runtime/controller_pak.cpp src/runtime/pak_services.cpp src/runtime/prompt_textures.cpp src/runtime/prompt_text.cpp src/runtime/prompt_encoded.cpp src/runtime/prompt_title_model.cpp src/runtime/widescreen_culling.cpp src/runtime/transform_tracker.cpp src/runtime/transform_runtime.cpp src/runtime/graphics_task_bank.cpp src/runtime/rt64_transform_bridge.cpp
  tests/test_platform_prompts.cpp
  "${ISS2000_NATIVE_METADATA}/native_metadata.cpp" "${ISS2000_NATIVE_METADATA}/native_bindings.cpp" "${ISS2000_NATIVE_METADATA}/native_retained.cpp"
  "${ISS2000_AUDIO_GENERATED}" $<TARGET_OBJECTS:iss2000_original>)
add_dependencies(iss2000 iss2000_verify_native_inputs)
target_sources(iss2000 PRIVATE src/runtime/game_controls_menu.cpp src/runtime/game_settings_menu.cpp src/runtime/settings_persistence.cpp src/runtime/controller_schemes.cpp src/runtime/football_controller_editor.cpp src/runtime/pal_main_select.cpp src/runtime/pal_controller_screen.cpp src/runtime/pal_football_input.cpp src/runtime/pal_menu_audio.cpp src/runtime/menu_sprite_runtime.cpp src/runtime/pal_radar_interpolation.cpp src/runtime/menu_sprite_bridge.cpp src/runtime/menu_sprite_render.cpp src/runtime/menu_sprite_match.cpp src/runtime/pal_projected_shadow.cpp src/runtime/pal_shadow_vertices.cpp src/runtime/rt64_shadow_bridge.cpp src/runtime/pal_menu_avatar.cpp src/runtime/pal_team_saved_data.cpp src/runtime/prompt_sprite_draw.cpp src/runtime/render_target_lifetime.cpp)
target_include_directories(iss2000 PRIVATE
  "${CMAKE_SOURCE_DIR}/src" "${ISS2000_N64RECOMP_SOURCE}/include"
  "${ISS2000_RUNTIME_SOURCE}/librecomp/include" "${ISS2000_RUNTIME_SOURCE}/ultramodern/include"
  "${ISS2000_RUNTIME_SOURCE}/thirdparty" "${ISS2000_RUNTIME_SOURCE}/thirdparty/concurrentqueue"
  "${ISS2000_RUNTIME_SOURCE}/thirdparty/miniz" "${ISS2000_RUNTIME_BUILD}/librecomp/miniz"
  "${ISS2000_RT64_SOURCE}/src" "${ISS2000_RT64_SOURCE}/src/hle"
  "${ISS2000_RT64_SOURCE}/src/contrib/plume"
  "${ISS2000_RT64_SOURCE}/src/contrib/plume/contrib/VulkanMemoryAllocator/include"
  "${ISS2000_RT64_SOURCE}/src/contrib/plume/contrib/volk"
  "${ISS2000_RT64_SOURCE}/src/contrib/plume/contrib/Vulkan-Headers/include"
  "${ISS2000_RT64_SOURCE}/src/contrib/hlslpp/include" "${ISS2000_RT64_SOURCE}/src/contrib"
  "${ISS2000_RT64_SOURCE}/src/contrib/nativefiledialog-extended/src/include")
if(UNIX AND NOT APPLE)
  target_include_directories(iss2000 SYSTEM PRIVATE "/home/linuxbrew/.linuxbrew/opt/xorgproto/include")
  target_compile_definitions(iss2000 PRIVATE RT64_SDL_WINDOW_VULKAN PLUME_SDL_VULKAN_ENABLED)
endif()
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(iss2000 PRIVATE -msse4.1 -fno-strict-aliasing)
endif()
file(GLOB_RECURSE ISS2000_RUNTIME_ARCHIVES "${ISS2000_RUNTIME_BUILD}/*.a" "${ISS2000_RUNTIME_BUILD}/*.lib")
file(GLOB_RECURSE ISS2000_RT64_ARCHIVES "${ISS2000_RT64_BUILD}/*.a" "${ISS2000_RT64_BUILD}/*.lib")
if(NOT ISS2000_RUNTIME_ARCHIVES OR NOT ISS2000_RT64_ARCHIVES)
  message(FATAL_ERROR "Build pinned runtime and RT64 archives first")
endif()
include("${CMAKE_CURRENT_LIST_DIR}/runtime_lookup_bridge.cmake")
iss2000_configure_runtime_lookup(iss2000 "${ISS2000_RUNTIME_BUILD}")
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang" AND NOT APPLE
    AND NOT CMAKE_CXX_COMPILER_FRONTEND_VARIANT STREQUAL "MSVC")
  target_link_libraries(iss2000 PRIVATE -Wl,--start-group ${ISS2000_RUNTIME_ARCHIVES} ${ISS2000_RT64_ARCHIVES} -Wl,--end-group)
else()
  target_link_libraries(iss2000 PRIVATE ${ISS2000_RUNTIME_ARCHIVES} ${ISS2000_RT64_ARCHIVES})
endif()
if(ISS2000_ROM_REVISION STREQUAL "iss2000-pal-en-de-rev0")
  target_compile_definitions(iss2000 PRIVATE ISS2000_PAL_ENGLISH)
  find_package(Python3 REQUIRED COMPONENTS Interpreter)
  set(ISS2000_PAL_TIMING "${CMAKE_CURRENT_BINARY_DIR}/pal-runtime-timing-v4")
  execute_process(COMMAND "${Python3_EXECUTABLE}" -m tools.prepare_runtime_timing
    --source "${ISS2000_RUNTIME_SOURCE}/ultramodern/src/events.cpp"
    --output "${ISS2000_PAL_TIMING}"
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" RESULT_VARIABLE timing_result)
  if(NOT timing_result EQUAL 0)
    message(FATAL_ERROR "Could not prepare the pinned PAL VI adapter")
  endif()
  # Defining every event symbol in this object prevents events.cpp.o from the
  # upstream static archive from being extracted; pinned checkout stays pristine.
  target_sources(iss2000 PRIVATE "${ISS2000_PAL_TIMING}/events.cpp")
  set(ISS2000_PAL_ROM "${CMAKE_SOURCE_DIR}/.local/inputs/pal-en-de/rom.z64" CACHE FILEPATH "Private exact PAL ROM used to verify original rendering source generation")
  set(ISS2000_PAL_NATIVE_PACE "${CMAKE_CURRENT_BINARY_DIR}/pal-native-pace-v2")
  set(ISS2000_PAL_NATIVE_PACE_COMMAND "${Python3_EXECUTABLE}" -m tools.prepare_pal_native_pace
    --rom "${ISS2000_PAL_ROM}" --source "${ISS2000_GAME_GENERATED}/func_80000C30_resident.c"
    --output "${ISS2000_PAL_NATIVE_PACE}")
  execute_process(COMMAND ${ISS2000_PAL_NATIVE_PACE_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" RESULT_VARIABLE pal_native_pace_result)
  if(NOT pal_native_pace_result EQUAL 0)
    message(FATAL_ERROR "Could not prepare the pinned PAL native simulation pace")
  endif()
  add_custom_target(iss2000_verify_pal_native_pace COMMAND ${ISS2000_PAL_NATIVE_PACE_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" VERBATIM)
  add_dependencies(iss2000 iss2000_verify_pal_native_pace)
  target_sources(iss2000 PRIVATE "${ISS2000_PAL_NATIVE_PACE}/pal_native_frame_pace.cpp")
  set(ISS2000_PAL_HIGH_SPRITES "${CMAKE_CURRENT_BINARY_DIR}/pal-high-sprites-v1")
  set(ISS2000_PAL_HIGH_SPRITES_COMMAND "${Python3_EXECUTABLE}" -m tools.prepare_pal_high_sprites
    --rom "${ISS2000_PAL_ROM}" --source "${ISS2000_GAME_GENERATED}/func_807AA008_overlay_515890_807aa000.c"
    --output "${ISS2000_PAL_HIGH_SPRITES}")
  execute_process(COMMAND ${ISS2000_PAL_HIGH_SPRITES_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" RESULT_VARIABLE pal_high_sprites_result)
  if(NOT pal_high_sprites_result EQUAL 0)
    message(FATAL_ERROR "Could not prepare the pinned PAL High sprite sampling")
  endif()
  add_custom_target(iss2000_verify_pal_high_sprites COMMAND ${ISS2000_PAL_HIGH_SPRITES_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" VERBATIM)
  add_dependencies(iss2000 iss2000_verify_pal_high_sprites)
  target_sources(iss2000 PRIVATE "${ISS2000_PAL_HIGH_SPRITES}/pal_high_sprite_edges.cpp")
  set(ISS2000_PAL_RADAR "${CMAKE_CURRENT_BINARY_DIR}/pal-radar-interpolation-v1")
  set(ISS2000_PAL_RADAR_COMMAND "${Python3_EXECUTABLE}" -m tools.prepare_pal_radar_interpolation
    --rom "${ISS2000_PAL_ROM}" --source "${ISS2000_GAME_GENERATED}/func_802A5290_overlay_376010_802a4380.c"
    --output "${ISS2000_PAL_RADAR}")
  execute_process(COMMAND ${ISS2000_PAL_RADAR_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" RESULT_VARIABLE pal_radar_result)
  if(NOT pal_radar_result EQUAL 0)
    message(FATAL_ERROR "Could not prepare the pinned PAL radar metadata")
  endif()
  add_custom_target(iss2000_verify_pal_radar COMMAND ${ISS2000_PAL_RADAR_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" VERBATIM)
  add_dependencies(iss2000 iss2000_verify_pal_radar)
  target_sources(iss2000 PRIVATE "${ISS2000_PAL_RADAR}/pal_radar_callback.cpp")
  set(ISS2000_PAL_FIXED_HIGH "${CMAKE_CURRENT_BINARY_DIR}/pal-fixed-high-v3")
  set(ISS2000_PAL_FIXED_HIGH_COMMAND "${Python3_EXECUTABLE}" -m tools.prepare_pal_fixed_high
    --rom "${ISS2000_PAL_ROM}" --source "${ISS2000_GAME_GENERATED}/func_80008C30_resident.c"
    --output "${ISS2000_PAL_FIXED_HIGH}")
  execute_process(COMMAND ${ISS2000_PAL_FIXED_HIGH_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" RESULT_VARIABLE pal_fixed_high_result)
  if(NOT pal_fixed_high_result EQUAL 0)
    message(FATAL_ERROR "Could not prepare the pinned PAL fixed High preference")
  endif()
  add_custom_target(iss2000_verify_pal_fixed_high COMMAND ${ISS2000_PAL_FIXED_HIGH_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" VERBATIM)
  add_dependencies(iss2000 iss2000_verify_pal_fixed_high)
  target_sources(iss2000 PRIVATE src/runtime/pal_options_skin.cpp src/runtime/pal_options_row_font.cpp src/runtime/pal_options_entry.cpp "${ISS2000_PAL_FIXED_HIGH}/pal_fixed_high_initializer.cpp")
  set(ISS2000_PAL_FRAMEBUFFER_OWNERSHIP "${CMAKE_CURRENT_BINARY_DIR}/pal-framebuffer-ownership-v2")
  set(ISS2000_PAL_FRAMEBUFFER_OWNERSHIP_COMMAND "${Python3_EXECUTABLE}" -m tools.prepare_pal_framebuffer_ownership
    --rom "${ISS2000_PAL_ROM}" --source "${ISS2000_GAME_GENERATED}/func_8001D480_resident.c"
    --output "${ISS2000_PAL_FRAMEBUFFER_OWNERSHIP}")
  execute_process(COMMAND ${ISS2000_PAL_FRAMEBUFFER_OWNERSHIP_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" RESULT_VARIABLE pal_framebuffer_ownership_result)
  if(NOT pal_framebuffer_ownership_result EQUAL 0)
    message(FATAL_ERROR "Could not prepare the pinned PAL framebuffer ownership correction")
  endif()
  add_custom_target(iss2000_verify_pal_framebuffer_ownership COMMAND ${ISS2000_PAL_FRAMEBUFFER_OWNERSHIP_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" VERBATIM)
  add_dependencies(iss2000 iss2000_verify_pal_framebuffer_ownership)
  target_sources(iss2000 PRIVATE "${ISS2000_PAL_FRAMEBUFFER_OWNERSHIP}/pal_framebuffer_allocator.cpp")
  set(ISS2000_PAL_DETAIL "${CMAKE_CURRENT_BINARY_DIR}/pal-max-detail-v1")
  set(ISS2000_PAL_DETAIL_COMMAND "${Python3_EXECUTABLE}" -m tools.prepare_pal_max_detail
    --rom "${ISS2000_PAL_ROM}"
    --models-source "${ISS2000_GAME_GENERATED}/func_800300D0_resident.c"
    --shadows-source "${ISS2000_GAME_GENERATED}/func_80037498_resident.c"
    --output "${ISS2000_PAL_DETAIL}")
  execute_process(COMMAND ${ISS2000_PAL_DETAIL_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" RESULT_VARIABLE pal_detail_result)
  if(NOT pal_detail_result EQUAL 0)
    message(FATAL_ERROR "Could not prepare the pinned PAL maximum-detail model and shadow sources")
  endif()
  add_custom_target(iss2000_verify_pal_detail COMMAND ${ISS2000_PAL_DETAIL_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" VERBATIM)
  add_dependencies(iss2000 iss2000_verify_pal_detail)
  target_sources(iss2000 PRIVATE "${ISS2000_PAL_DETAIL}/pal_max_detail_models.cpp"
    "${ISS2000_PAL_DETAIL}/pal_max_detail_shadows.cpp")
  set(ISS2000_PAL_RUMBLE_UI "${CMAKE_CURRENT_BINARY_DIR}/pal-rumble-ui-v1")
  set(ISS2000_PAL_EXPANSION_UI "${CMAKE_CURRENT_BINARY_DIR}/pal-expansion-ui-v1")
  set(ISS2000_PAL_EXPANSION_UI_COMMAND "${Python3_EXECUTABLE}" -m tools.prepare_pal_expansion_ui
    --rom "${ISS2000_PAL_ROM}"
    --source "${ISS2000_GAME_GENERATED}/func_802B1FDC_overlay_481680_802b1070.c"
    --output "${ISS2000_PAL_EXPANSION_UI}")
  execute_process(COMMAND ${ISS2000_PAL_EXPANSION_UI_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" RESULT_VARIABLE pal_expansion_ui_result)
  if(NOT pal_expansion_ui_result EQUAL 0)
    message(FATAL_ERROR "Could not prepare the pinned PAL Expansion Pak notice continuation")
  endif()
  add_custom_target(iss2000_verify_pal_expansion_ui COMMAND ${ISS2000_PAL_EXPANSION_UI_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" VERBATIM)
  add_dependencies(iss2000 iss2000_verify_pal_expansion_ui)
  target_sources(iss2000 PRIVATE "${ISS2000_PAL_EXPANSION_UI}/pal_skip_expansion_notice.cpp")
  set(ISS2000_PAL_AUTO_STORAGE_UI "${CMAKE_CURRENT_BINARY_DIR}/pal-auto-storage-ui-v6")
  set(ISS2000_PAL_AUTO_STORAGE_UI_COMMAND "${Python3_EXECUTABLE}" -m tools.prepare_pal_auto_storage_ui
    --rom "${ISS2000_PAL_ROM}"
    --source "${ISS2000_GAME_GENERATED}/func_802B1CC8_overlay_481680_802b1070.c"
    --output "${ISS2000_PAL_AUTO_STORAGE_UI}")
  execute_process(COMMAND ${ISS2000_PAL_AUTO_STORAGE_UI_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" RESULT_VARIABLE pal_auto_storage_ui_result)
  if(NOT pal_auto_storage_ui_result EQUAL 0)
    message(FATAL_ERROR "Could not prepare the pinned PAL Expansion Pak notice continuation")
  endif()
  add_custom_target(iss2000_verify_pal_auto_storage_ui COMMAND ${ISS2000_PAL_AUTO_STORAGE_UI_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" VERBATIM)
  add_dependencies(iss2000 iss2000_verify_pal_auto_storage_ui)
  target_sources(iss2000 PRIVATE "${ISS2000_PAL_AUTO_STORAGE_UI}/pal_automatic_storage_ui.cpp")
  set(ISS2000_PAL_STORAGE_TEXT "${CMAKE_CURRENT_BINARY_DIR}/pal-storage-text-v2")
  set(ISS2000_PAL_STORAGE_TEXT_COMMAND "${Python3_EXECUTABLE}" -m tools.prepare_pal_storage_text
    --rom "${ISS2000_PAL_ROM}" --output "${ISS2000_PAL_STORAGE_TEXT}")
  execute_process(COMMAND ${ISS2000_PAL_STORAGE_TEXT_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" RESULT_VARIABLE pal_storage_text_result)
  if(NOT pal_storage_text_result EQUAL 0)
    message(FATAL_ERROR "Could not prepare the pinned PAL save wording")
  endif()
  add_custom_target(iss2000_verify_pal_storage_text COMMAND ${ISS2000_PAL_STORAGE_TEXT_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" VERBATIM)
  add_dependencies(iss2000 iss2000_verify_pal_storage_text)
  target_sources(iss2000 PRIVATE "${ISS2000_PAL_STORAGE_TEXT}/pal_storage_text.cpp")
  set(ISS2000_PAL_RUMBLE_UI_COMMAND "${Python3_EXECUTABLE}" -m tools.prepare_pal_rumble_ui
    --rom "${ISS2000_PAL_ROM}" --generated "${ISS2000_GAME_GENERATED}"
    --output "${ISS2000_PAL_RUMBLE_UI}")
  execute_process(COMMAND ${ISS2000_PAL_RUMBLE_UI_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" RESULT_VARIABLE pal_rumble_ui_result)
  if(NOT pal_rumble_ui_result EQUAL 0)
    message(FATAL_ERROR "Could not prepare the pinned PAL Rumble notice continuations")
  endif()
  add_custom_target(iss2000_verify_pal_rumble_ui COMMAND ${ISS2000_PAL_RUMBLE_UI_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" VERBATIM)
  add_dependencies(iss2000 iss2000_verify_pal_rumble_ui)
  foreach(pal_rumble_ui_entry IN ITEMS 802B5574 802BA770 802BE1B8 802C6D34 803D2F34)
    target_sources(iss2000 PRIVATE "${ISS2000_PAL_RUMBLE_UI}/pal_rumble_ui_${pal_rumble_ui_entry}.cpp")
  endforeach()
  set(ISS2000_PAL_SKY "${CMAKE_CURRENT_BINARY_DIR}/pal-wide-sky-v1")
  set(ISS2000_PAL_SKY_COMMAND "${Python3_EXECUTABLE}" -m tools.prepare_pal_sky
    --rom "${ISS2000_PAL_ROM}" --source "${ISS2000_GAME_GENERATED}/func_80035CC0_resident.c"
    --output "${ISS2000_PAL_SKY}")
  execute_process(COMMAND ${ISS2000_PAL_SKY_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" RESULT_VARIABLE pal_sky_result)
  if(NOT pal_sky_result EQUAL 0)
    message(FATAL_ERROR "Could not prepare the pinned PAL widescreen sky")
  endif()
  add_custom_target(iss2000_verify_pal_sky COMMAND ${ISS2000_PAL_SKY_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" VERBATIM)
  add_dependencies(iss2000 iss2000_verify_pal_sky)
  target_sources(iss2000 PRIVATE src/runtime/pal_sky_widescreen.cpp src/runtime/pal_hud_widescreen.cpp src/runtime/pal_background_widescreen.cpp "${ISS2000_PAL_SKY}/pal_wide_sky.cpp")
  set(ISS2000_PAL_VI "${CMAKE_CURRENT_BINARY_DIR}/pal-rt64-vi-v1")
  set(ISS2000_PAL_VI_COMMAND "${Python3_EXECUTABLE}" -m tools.prepare_rt64_vi
    --source "${ISS2000_RT64_SOURCE}/src/hle/rt64_vi.cpp" --output "${ISS2000_PAL_VI}")
  execute_process(COMMAND ${ISS2000_PAL_VI_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" RESULT_VARIABLE pal_vi_result)
  if(NOT pal_vi_result EQUAL 0)
    message(FATAL_ERROR "Could not prepare the pinned PAL framebuffer identity adapter")
  endif()
  add_custom_target(iss2000_verify_pal_vi COMMAND ${ISS2000_PAL_VI_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" VERBATIM)
  add_dependencies(iss2000 iss2000_verify_pal_vi)
  target_sources(iss2000 PRIVATE src/runtime/vi_framebuffer.cpp "${ISS2000_PAL_VI}/rt64_vi.cpp")
  set_source_files_properties("${ISS2000_PAL_VI}/rt64_vi.cpp"
    PROPERTIES COMPILE_DEFINITIONS "HLSL_CPU;FFX_GCC")

  set(ISS2000_PAL_FORMATION_PERSISTENCE "${CMAKE_CURRENT_BINARY_DIR}/pal-formation-persistence-v1")
  set(ISS2000_PAL_FORMATION_PERSISTENCE_COMMAND "${Python3_EXECUTABLE}" -m tools.prepare_pal_formation_persistence
    --rom "${ISS2000_PAL_ROM}" --source "${ISS2000_GAME_GENERATED}/func_802A3464_overlay_3e83d0_8029eea0.c"
    --output "${ISS2000_PAL_FORMATION_PERSISTENCE}")
  execute_process(COMMAND ${ISS2000_PAL_FORMATION_PERSISTENCE_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" RESULT_VARIABLE pal_formation_persistence_result)
  if(NOT pal_formation_persistence_result EQUAL 0)
    message(FATAL_ERROR "Could not prepare the pinned PAL formation persistence correction")
  endif()
  add_custom_target(iss2000_verify_pal_formation_persistence COMMAND ${ISS2000_PAL_FORMATION_PERSISTENCE_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" VERBATIM)
  add_dependencies(iss2000 iss2000_verify_pal_formation_persistence)
  target_sources(iss2000 PRIVATE "${ISS2000_PAL_FORMATION_PERSISTENCE}/pal_formation_save.cpp")

  add_custom_target(iss2000_verify_real_names
    COMMAND "${Python3_EXECUTABLE}" -m tools.generate_pal_real_names --check
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" VERBATIM)
  add_dependencies(iss2000 iss2000_verify_real_names)
  target_sources(iss2000 PRIVATE src/runtime/pal_real_names.cpp src/runtime/pal_real_names_data.cpp)

  set(ISS2000_FILTER_2D "${CMAKE_CURRENT_BINARY_DIR}/rt64-filter-2d-v3")
  set(ISS2000_FILTER_2D_COMMAND "${Python3_EXECUTABLE}" -m tools.prepare_rt64_filter_2d
    --source "${ISS2000_RT64_SOURCE}/src/hle/rt64_state.cpp" --output "${ISS2000_FILTER_2D}")
  execute_process(COMMAND ${ISS2000_FILTER_2D_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" RESULT_VARIABLE filter_2d_result)
  if(NOT filter_2d_result EQUAL 0)
    message(FATAL_ERROR "Could not prepare the pinned 2D shader filtering option")
  endif()
  add_custom_target(iss2000_verify_filter_2d COMMAND ${ISS2000_FILTER_2D_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" VERBATIM)
  add_dependencies(iss2000 iss2000_verify_filter_2d)
  target_sources(iss2000 PRIVATE "${ISS2000_FILTER_2D}/rt64_state.cpp")
  target_include_directories(iss2000 PRIVATE "${ISS2000_RT64_SOURCE}/src/contrib/imgui")
  set_source_files_properties("${ISS2000_FILTER_2D}/rt64_state.cpp"
    PROPERTIES COMPILE_DEFINITIONS "HLSL_CPU;FFX_GCC")
  # Pinned upstream State uses the pre-C++20 filesystem u8string interface.
  if(MSVC)
    set_property(SOURCE "${ISS2000_FILTER_2D}/rt64_state.cpp" APPEND PROPERTY COMPILE_OPTIONS /std:c++17)
  else()
    set_property(SOURCE "${ISS2000_FILTER_2D}/rt64_state.cpp" APPEND PROPERTY COMPILE_OPTIONS -std=c++17)
  endif()

  set(ISS2000_SPRITE_PHASE "${CMAKE_CURRENT_BINARY_DIR}/rt64-sprite-phase-v5")
  set(ISS2000_SPRITE_PHASE_COMMAND "${Python3_EXECUTABLE}" -m tools.prepare_rt64_sprite_phase
    --source "${ISS2000_RT64_SOURCE}/src/render/rt64_framebuffer_renderer.cpp"
    --output "${ISS2000_SPRITE_PHASE}")
  execute_process(COMMAND ${ISS2000_SPRITE_PHASE_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" RESULT_VARIABLE sprite_phase_result)
  if(NOT sprite_phase_result EQUAL 0)
    message(FATAL_ERROR "Could not prepare the pinned sprite viewport alignment")
  endif()
  add_custom_target(iss2000_verify_sprite_phase COMMAND ${ISS2000_SPRITE_PHASE_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" VERBATIM)
  add_dependencies(iss2000 iss2000_verify_sprite_phase)
  # Defining this complete source keeps the original archive object unextracted.
  # The pinned dependency checkout is read-only.
  target_sources(iss2000 PRIVATE "${ISS2000_SPRITE_PHASE}/rt64_framebuffer_renderer.cpp")
  target_include_directories(iss2000 PRIVATE "${ISS2000_RT64_SOURCE}/src/render")
  set_source_files_properties("${ISS2000_SPRITE_PHASE}/rt64_framebuffer_renderer.cpp"
    PROPERTIES COMPILE_DEFINITIONS "HLSL_CPU;FFX_GCC")


endif()
option(ISS2000_ENABLE_RENDER_EVIDENCE "Enable private RT64 render evidence instrumentation" OFF)
if(ISS2000_ROM_REVISION STREQUAL "iss2000-pal-en-de-rev0")
  set(ISS2000_MENU_QUEUE "${CMAKE_CURRENT_BINARY_DIR}/rt64-menu-interpolation-v4")
  set(ISS2000_MENU_QUEUE_COMMAND "${Python3_EXECUTABLE}" -m tools.prepare_rt64_menu_interpolation
    --source "${ISS2000_RT64_SOURCE}/src/hle/rt64_workload_queue.cpp")
  if(ISS2000_ENABLE_RENDER_EVIDENCE)
    string(APPEND ISS2000_MENU_QUEUE "-evidence")
    list(APPEND ISS2000_MENU_QUEUE_COMMAND --evidence)
  endif()
  list(APPEND ISS2000_MENU_QUEUE_COMMAND --output "${ISS2000_MENU_QUEUE}")
  execute_process(COMMAND ${ISS2000_MENU_QUEUE_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" RESULT_VARIABLE menu_queue_result)
  if(NOT menu_queue_result EQUAL 0)
    message(FATAL_ERROR "Could not prepare pinned menu rectangle interpolation")
  endif()
  add_custom_target(iss2000_verify_menu_queue COMMAND ${ISS2000_MENU_QUEUE_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" VERBATIM)
  add_dependencies(iss2000 iss2000_verify_menu_queue)
  target_sources(iss2000 PRIVATE "${ISS2000_MENU_QUEUE}/rt64_workload_queue.cpp")
  set_source_files_properties("${ISS2000_MENU_QUEUE}/rt64_workload_queue.cpp"
    PROPERTIES COMPILE_DEFINITIONS "HLSL_CPU;FFX_GCC")
  set(ISS2000_PRESENT_LIFETIME "${CMAKE_CURRENT_BINARY_DIR}/rt64-present-lifetime-v2")
  set(ISS2000_PRESENT_LIFETIME_COMMAND "${Python3_EXECUTABLE}" -m tools.prepare_rt64_present_lifetime
    --source "${ISS2000_RT64_SOURCE}/src/hle/rt64_present_queue.cpp")
  if(ISS2000_ENABLE_RENDER_EVIDENCE)
    string(APPEND ISS2000_PRESENT_LIFETIME "-evidence")
    list(APPEND ISS2000_PRESENT_LIFETIME_COMMAND --evidence)
  endif()
  list(APPEND ISS2000_PRESENT_LIFETIME_COMMAND --output "${ISS2000_PRESENT_LIFETIME}")
  execute_process(COMMAND ${ISS2000_PRESENT_LIFETIME_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" RESULT_VARIABLE present_lifetime_result)
  if(NOT present_lifetime_result EQUAL 0)
    message(FATAL_ERROR "Could not prepare pinned presentation target lifetime")
  endif()
  add_custom_target(iss2000_verify_present_lifetime COMMAND ${ISS2000_PRESENT_LIFETIME_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" VERBATIM)
  add_dependencies(iss2000 iss2000_verify_present_lifetime)
  target_sources(iss2000 PRIVATE "${ISS2000_PRESENT_LIFETIME}/rt64_present_queue.cpp")
  set_source_files_properties("${ISS2000_PRESENT_LIFETIME}/rt64_present_queue.cpp"
    PROPERTIES COMPILE_DEFINITIONS "HLSL_CPU;FFX_GCC")
endif()
if(ISS2000_ENABLE_RENDER_EVIDENCE AND NOT ISS2000_ROM_REVISION STREQUAL "iss2000-pal-en-de-rev0")
  set(ISS2000_RENDER_EVIDENCE_OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/rt64-render-evidence")
  set(ISS2000_RENDER_EVIDENCE_COMMAND "${Python3_EXECUTABLE}" -m tools.prepare_render_evidence
    --source "${ISS2000_RT64_SOURCE}/src/hle" --output "${ISS2000_RENDER_EVIDENCE_OUTPUT}")
  execute_process(COMMAND ${ISS2000_RENDER_EVIDENCE_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" RESULT_VARIABLE render_evidence_result)
  if(NOT render_evidence_result EQUAL 0)
    message(FATAL_ERROR "Could not prepare pinned RT64 render evidence sources")
  endif()
  add_custom_target(iss2000_verify_render_evidence
    COMMAND ${ISS2000_RENDER_EVIDENCE_COMMAND}
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" VERBATIM)
  add_dependencies(iss2000 iss2000_verify_render_evidence)
  set(ISS2000_RENDER_EVIDENCE_SOURCES
    "${ISS2000_RENDER_EVIDENCE_OUTPUT}/rt64_present_queue.cpp")
  if(NOT ISS2000_ROM_REVISION STREQUAL "iss2000-pal-en-de-rev0")
    list(APPEND ISS2000_RENDER_EVIDENCE_SOURCES "${ISS2000_RENDER_EVIDENCE_OUTPUT}/rt64_workload_queue.cpp")
  endif()
  target_sources(iss2000 PRIVATE ${ISS2000_RENDER_EVIDENCE_SOURCES})
  set_source_files_properties(${ISS2000_RENDER_EVIDENCE_SOURCES}
    PROPERTIES COMPILE_DEFINITIONS "HLSL_CPU;FFX_GCC")
endif()
target_link_libraries(iss2000 PRIVATE SDL2::SDL2 Threads::Threads ${CMAKE_DL_LIBS})
if(WIN32)
  # Keep the SDL_MAIN_HANDLED main entry without opening a separate console.
  set_target_properties(iss2000 PROPERTIES WIN32_EXECUTABLE TRUE)
  target_link_options(iss2000 PRIVATE /ENTRY:mainCRTStartup)
  target_compile_definitions(iss2000 PRIVATE NOMINMAX)
  target_include_directories(iss2000 PRIVATE "${ISS2000_RT64_SOURCE}/src/contrib/dxc/inc")
  # Upstream targets are linked here as private static archives, so their
  # Windows SDK/import-library dependencies must be preserved explicitly.
  set(ISS2000_DXC_IMPORT "${ISS2000_RT64_SOURCE}/src/contrib/dxc/lib/x64/dxcompiler.lib")
  if(NOT EXISTS "${ISS2000_DXC_IMPORT}")
    message(FATAL_ERROR "Pinned Windows DXC import library is missing")
  endif()
  # RT64: delayimp/D3D12/DXGI/Shcore/DXC. Native dialogs use COM/shell GUIDs;
  # the checked HWND owner query uses user32.
  target_link_libraries(iss2000 PRIVATE delayimp D3D12 DXGI Shcore
    ole32 shell32 uuid user32 "${ISS2000_DXC_IMPORT}")
endif()
if(UNIX AND NOT APPLE)
  find_library(ISS2000_DBUS_LIBRARY NAMES dbus-1 HINTS /home/linuxbrew/.linuxbrew/lib REQUIRED)
  target_link_libraries(iss2000 PRIVATE "${ISS2000_DBUS_LIBRARY}")
endif()
set_source_files_properties(src/renderer.cpp src/runtime/rt64_transform_bridge.cpp src/runtime/menu_sprite_bridge.cpp src/runtime/menu_sprite_render.cpp src/runtime/rt64_shadow_bridge.cpp PROPERTIES COMPILE_DEFINITIONS "HLSL_CPU;FFX_GCC")

option(ISS2000_ENABLE_INPUT_TESTING "Enable app-only virtual controller test fixture" OFF)
if(ISS2000_ENABLE_INPUT_TESTING)
  target_compile_definitions(iss2000 PRIVATE ISS2000_ENABLE_INPUT_TESTING)
endif()
