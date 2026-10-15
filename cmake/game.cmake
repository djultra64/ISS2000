# Original project work: djultra64.
# Dependencies are built separately from pinned source under private .local/.
set(ISS2000_ROM_REVISION "iss2000-pal-en-de-rev0" CACHE STRING "Exact ROM revision compiled into this game")
set_property(CACHE ISS2000_ROM_REVISION PROPERTY STRINGS iss2000-us-rev0 iss2000-pal-en-de-rev0)
if(ISS2000_ROM_REVISION STREQUAL "iss2000-pal-en-de-rev0")
  set(ISS2000_DEFAULT_CPU "${CMAKE_SOURCE_DIR}/.local/pal-map-bound-01/functions")
  set(ISS2000_DEFAULT_METADATA "${CMAKE_SOURCE_DIR}/.local/pal-native-metadata-02")
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
      --output "${CMAKE_CURRENT_BINARY_DIR}/pal-runtime-timing-v3"
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
  src/game_main.cpp src/platform.cpp src/renderer.cpp src/runtime/native_game.cpp src/runtime/rom_image.cpp src/runtime/ntsc_match_clock.cpp src/runtime/debug_console.cpp src/runtime/graphics_settings.cpp src/runtime/input_preferences.cpp src/runtime/test_controller.cpp src/runtime/controller_pak.cpp src/runtime/pak_services.cpp src/runtime/settings_dialog.cpp src/runtime/prompt_textures.cpp src/runtime/prompt_text.cpp src/runtime/prompt_encoded.cpp src/runtime/widescreen_culling.cpp src/runtime/transform_tracker.cpp src/runtime/transform_runtime.cpp src/runtime/graphics_task_bank.cpp src/runtime/rt64_transform_bridge.cpp
  tests/test_platform_prompts.cpp
  "${ISS2000_NATIVE_METADATA}/native_metadata.cpp" "${ISS2000_NATIVE_METADATA}/native_bindings.cpp" "${ISS2000_NATIVE_METADATA}/native_retained.cpp"
  "${ISS2000_AUDIO_GENERATED}" $<TARGET_OBJECTS:iss2000_original>)
add_dependencies(iss2000 iss2000_verify_native_inputs)
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
  set(ISS2000_PAL_TIMING "${CMAKE_CURRENT_BINARY_DIR}/pal-runtime-timing-v3")
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

endif()
option(ISS2000_ENABLE_RENDER_EVIDENCE "Enable private RT64 render evidence instrumentation" OFF)
if(ISS2000_ENABLE_RENDER_EVIDENCE)
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
    "${ISS2000_RENDER_EVIDENCE_OUTPUT}/rt64_workload_queue.cpp"
    "${ISS2000_RENDER_EVIDENCE_OUTPUT}/rt64_present_queue.cpp")
  target_sources(iss2000 PRIVATE ${ISS2000_RENDER_EVIDENCE_SOURCES})
  set_source_files_properties(${ISS2000_RENDER_EVIDENCE_SOURCES}
    PROPERTIES COMPILE_DEFINITIONS "HLSL_CPU;FFX_GCC")
endif()
target_link_libraries(iss2000 PRIVATE SDL2::SDL2 Threads::Threads ${CMAKE_DL_LIBS})
if(WIN32)
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
set_source_files_properties(src/renderer.cpp src/runtime/rt64_transform_bridge.cpp PROPERTIES COMPILE_DEFINITIONS "HLSL_CPU;FFX_GCC")

option(ISS2000_ENABLE_INPUT_TESTING "Enable app-only virtual controller test fixture" OFF)
if(ISS2000_ENABLE_INPUT_TESTING)
  target_compile_definitions(iss2000 PRIVATE ISS2000_ENABLE_INPUT_TESTING)
endif()
