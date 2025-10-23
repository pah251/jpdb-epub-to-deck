#include <pybind11/pybind11.h>

int add(int a, int b)
{
    return a + b;
}

PYBIND11_MODULE(my_cpp_module, m)
{
    m.doc() = "A simple C++ module for Python";

    m.def("add", &add, "A function to add 2 numbers but really quickly");
}