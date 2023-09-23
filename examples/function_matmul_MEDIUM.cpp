#include <tiramisu/tiramisu.h>
#include <tiramisu/auto_scheduler/evaluator.h>
#include <tiramisu/auto_scheduler/search_method.h>
// #include "function_matmul_MEDIUM_wrapper.h"

using namespace tiramisu;

int main(int argc, char **argv)
{
    tiramisu::init("function_matmul_MEDIUM");

    // -------------------------------------------------------
    // Layer I
    // -------------------------------------------------------
    var i00("i00", 0, 192), i01("i01", 0, 256), i02("i02", 0, 320);
    // inputs
    input input00("input00", {i00, i02}, p_int32);
    input input01("input01", {i02, i01}, p_int32);

    // Computations
    computation comp02("comp02", {i00, i01, i02}, p_int32);
    comp02.set_expression(comp02(i00, i01, i02) + input00(i00, i02) * input01(i02, i01));

    // -------------------------------------------------------
    // Layer III
    // -------------------------------------------------------
    // Input Buffers
    buffer buf02("buf02", {192, 256}, p_int32, a_output);
    buffer buf00("buf00", {192, 320}, p_int32, a_input);
    buffer buf01("buf01", {320, 256}, p_int32, a_input);

    comp02.store_in(&buf02, {i00, i01});
    input00.store_in(&buf00);
    input01.store_in(&buf01);
    // -------------------------------------------------------
    // Code Generation
    // -------------------------------------------------------

    tiramisu::codegen({&buf02, &buf00, &buf01}, "function_matmul_MEDIUM.o");

    return 0;
}
