# Original project work: djultra64.
# Rebuild private shader variants; leave pinned RT64 sources/archives intact.
set(ISS2000_POINT_SOURCE "${CMAKE_CURRENT_BINARY_DIR}/rt64-point-source-v1")
set(ISS2000_POINT_BLOBS "${CMAKE_CURRENT_BINARY_DIR}/rt64-point-blobs-v1")
set(ISS2000_POINT_COMMAND "${Python3_EXECUTABLE}" -m tools.prepare_rt64_point_precision
  --source "${ISS2000_RT64_SOURCE}/src" --output "${ISS2000_POINT_SOURCE}")
execute_process(COMMAND ${ISS2000_POINT_COMMAND} WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
  RESULT_VARIABLE point_result OUTPUT_QUIET)
if(NOT point_result EQUAL 0)
  message(FATAL_ERROR "Could not prepare pinned POINT sprite precision sources")
endif()
add_custom_target(iss2000_verify_point_precision COMMAND ${ISS2000_POINT_COMMAND}
  WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}" VERBATIM)
set(ISS2000_POINT_TOOL "${ISS2000_RT64_BUILD}/src/tools/file_to_c/file_to_c${CMAKE_EXECUTABLE_SUFFIX}")
if(NOT EXISTS "${ISS2000_POINT_TOOL}")
  message(FATAL_ERROR "Build the pinned RT64 file_to_c tool before the game")
endif()
if(WIN32)
  set(ISS2000_POINT_DXC "${ISS2000_RT64_SOURCE}/src/contrib/dxc/bin/x64/dxc.exe")
else()
  set(ISS2000_POINT_DXC "${CMAKE_COMMAND}" -E env
    "LD_LIBRARY_PATH=${ISS2000_RT64_SOURCE}/src/contrib/dxc/lib/x64"
    "${ISS2000_RT64_SOURCE}/src/contrib/dxc/bin/x64/dxc-linux")
endif()
file(GLOB_RECURSE ISS2000_POINT_HEADERS CONFIGURE_DEPENDS
  "${ISS2000_RT64_SOURCE}/src/shaders/*.hlsli" "${ISS2000_RT64_SOURCE}/src/shared/*.h")
set(ISS2000_POINT_OUTPUTS)
function(iss2000_point_shader name format)
  set(base "${ISS2000_POINT_BLOBS}/shaders/${name}.hlsl")
  set(options "-I${ISS2000_RT64_SOURCE}/src" "-I${ISS2000_RT64_SOURCE}/src/shaders")
  if(format STREQUAL "spirv")
    list(APPEND options -spirv -fspv-target-env=vulkan1.0 -fvk-use-dx-layout -E PSMain -T ps_6_3)
    set(binary "${base}.spv")
    set(symbol "${name}BlobSPIRV")
  else()
    list(APPEND options -Wno-ignored-attributes)
    if(name MATCHES "Library")
      list(APPEND options -D LIBRARY -T lib_6_3)
    else()
      list(APPEND options -E PSMain -T ps_6_3)
    endif()
    set(binary "${base}.dxil")
    set(symbol "${name}BlobDXIL")
  endif()
  foreach(define IN LISTS ARGN)
    list(APPEND options -D "${define}")
  endforeach()
  add_custom_command(OUTPUT "${base}.${format}.c" "${base}.${format}.h"
    COMMAND "${CMAKE_COMMAND}" -E make_directory "${ISS2000_POINT_BLOBS}/shaders"
    COMMAND ${ISS2000_POINT_DXC} ${options} "${ISS2000_POINT_SOURCE}/shaders/RasterPS.hlsl" /Fo "${binary}"
    COMMAND "${ISS2000_POINT_TOOL}" "${binary}" "${symbol}" "${base}.${format}.c" "${base}.${format}.h"
    DEPENDS "${ISS2000_POINT_SOURCE}/shaders/RasterPS.hlsl"
      "${ISS2000_POINT_SOURCE}/shaders/TextureSampler.hlsli" ${ISS2000_POINT_HEADERS}
      "${ISS2000_POINT_TOOL}" VERBATIM)
  target_sources(iss2000 PRIVATE "${base}.${format}.c")
  set(ISS2000_POINT_OUTPUTS ${ISS2000_POINT_OUTPUTS} "${base}.${format}.c" "${base}.${format}.h" PARENT_SCOPE)
endfunction()
iss2000_point_shader(RasterPSDynamic spirv DYNAMIC_RENDER_PARAMS)
iss2000_point_shader(RasterPSDynamicMS spirv DYNAMIC_RENDER_PARAMS MULTISAMPLING)
iss2000_point_shader(RasterPSSpecConstant spirv SPEC_CONSTANT_RENDER_PARAMS)
iss2000_point_shader(RasterPSSpecConstantMS spirv SPEC_CONSTANT_RENDER_PARAMS MULTISAMPLING)
iss2000_point_shader(RasterPSSpecConstantFlat spirv SPEC_CONSTANT_RENDER_PARAMS VERTEX_FLAT_COLOR)
iss2000_point_shader(RasterPSSpecConstantFlatMS spirv SPEC_CONSTANT_RENDER_PARAMS VERTEX_FLAT_COLOR MULTISAMPLING)
if(WIN32)
  iss2000_point_shader(RasterPSDynamic dxil DYNAMIC_RENDER_PARAMS)
  iss2000_point_shader(RasterPSDynamicMS dxil DYNAMIC_RENDER_PARAMS MULTISAMPLING)
  iss2000_point_shader(RasterPSLibrary dxil)
  iss2000_point_shader(RasterPSLibraryMS dxil MULTISAMPLING)
endif()
add_custom_target(iss2000_point_blobs DEPENDS ${ISS2000_POINT_OUTPUTS})
add_dependencies(iss2000_point_blobs iss2000_verify_point_precision)
add_dependencies(iss2000 iss2000_point_blobs)
# The consumer must see the new array lengths as well as the new bytes.
# Otherwise std::size truncates SPIR-V before re-spirv parses it.
target_include_directories(iss2000 BEFORE PRIVATE "${ISS2000_POINT_BLOBS}" "${ISS2000_RT64_BUILD}/src")
target_sources(iss2000 PRIVATE "${ISS2000_POINT_SOURCE}/rt64_raster_shader.cpp")
set_source_files_properties("${ISS2000_POINT_SOURCE}/rt64_raster_shader.cpp"
  PROPERTIES COMPILE_DEFINITIONS "HLSL_CPU;FFX_GCC")
if(MSVC)
  set_property(SOURCE "${ISS2000_POINT_SOURCE}/rt64_raster_shader.cpp" APPEND PROPERTY COMPILE_OPTIONS /std:c++17)
else()
  set_property(SOURCE "${ISS2000_POINT_SOURCE}/rt64_raster_shader.cpp" APPEND PROPERTY COMPILE_OPTIONS -std=c++17)
endif()
