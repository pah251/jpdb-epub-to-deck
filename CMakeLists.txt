# 1. Set the minimum version of CMake required
cmake_minimum_required(VERSION 4.2.0)

# 2. Define the project name
project(EpubAnalyzer)

# --- Find pybind11 ---
add_subdirectory(extern/pybind11)

# --- Find MeCab ---
# 1. Define a "cache" variable for MECAB_ROOT.
#    The user *must* set this on the command line (e.g., -DMECAB_ROOT=...).
set(MECAB_ROOT "" CACHE PATH "Root directory of your MeCab installation (e.g., C:/Program Files/MeCab)")

# 2. Check if the variable is still empty (meaning the user forgot to set it).
if(NOT MECAB_ROOT)
    message(FATAL_ERROR "MeCab not found. Set the MECAB_ROOT variable. \nUse the -D command: cmake -DMECAB_ROOT=\"C:/Program Files/MeCab\" ..")
endif()

# 3. Now that we have MECAB_ROOT, find the files.
find_path(
  MECAB_INCLUDE_DIR mecab.h
  HINTS "${MECAB_ROOT}/sdk" "${MECAB_ROOT}/include")

find_library(
  MECAB_LIBRARY libmecab
  HINTS "${MECAB_ROOT}/sdk" "${MECAB_ROOT}/lib")

# 4. Check if we *actually* found the files in that path
if(MECAB_INCLUDE_DIR AND MECAB_LIBRARY)
  message(STATUS "Found MeCab headers: ${MECAB_INCLUDE_DIR}")
  message(STATUS "Found MeCab library: ${MECAB_LIBRARY}")
  
  # Add the include path (for #include <mecab.h>)
  include_directories(${MECAB_INCLUDE_DIR})
else()
  message(FATAL_ERROR "Could not find mecab.h or libmecab.lib in the provided MECAB_ROOT: ${MECAB_ROOT}")
endif()

# --- Build Our Module ---
pybind11_add_module(my_cpp_module main.cpp)

# 7. Link our module to the MeCab library
target_link_libraries(my_cpp_module PRIVATE ${MECAB_LIBRARY})