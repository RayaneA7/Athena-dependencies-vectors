#include <tiramisu/tiramisu.h>
#include <tiramisu/auto_scheduler/evaluator.h>
#include <tiramisu/auto_scheduler/search_method.h>
// #include "function_gemver_MINI_wrapper.h"

using namespace tiramisu;

int main(int argc, char **argv)
{
    tiramisu::init("test_expansion");

    // Algorithm
    tiramisu::constant N("N", tiramisu::expr((int32_t)10));
    tiramisu::var i("i", 1, N - 1), j("j", 1, N - 1);

    tiramisu::var i1("i1"), j1("j1");
    tiramisu::var i2("i2"), j2("j2");

    tiramisu::input A("A", {i, j}, p_uint8);

    tiramisu::computation result("result", {i, j}, A(i - 1, j - 1) + A(i - 1, j) + A(i - 1, j));

    tiramisu::computation addition("addition", {i, j}, A(i, j) + 1);

    tiramisu::computation addition2("addition2", {i, j}, addition(i, j) + 2);

    // the order must be defined
    // result & addition must be fused in the innermost loop level
    result.then(addition, j).then(addition2, j);

    tiramisu::buffer buff_A("buff_A", {N, N}, tiramisu::p_uint8, a_input);

    tiramisu::buffer buff_A2("buff_A2", {}, tiramisu::p_uint8, a_temporary);
    A.store_in(&buff_A);
    result.store_in(&buff_A);
    // tmp buffer to expand
    addition.store_in(&buff_A2, {});
    addition2.store_in(&buff_A);

    tiramisu::codegen({&buff_A}, "test_expansion.o");

    return 0;
}
