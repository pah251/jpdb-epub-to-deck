cmake_minimum_required(VERSION 4.2.0)

project(EpubAnalizer)

add_subdirectory(extern/pybind11)

pybind11_add_module(my_cpp_module main.cpp)