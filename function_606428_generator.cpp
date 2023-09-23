#include <tiramisu/tiramisu.h>
#include <tiramisu/auto_scheduler/evaluator.h>
#include <tiramisu/auto_scheduler/search_method.h>
#include "function663824_wrapper.h"
using namespace tiramisu;
int main(int argc, char **argv)
{
    tiramisu::init("function663824");
    var i0("i0", 0, 32), i1("i1", 0, 32), i2("i2", 0, 64), i3("i3", 0, 128);
    input icomp00("icomp00", {i1, i2, i3}, p_float64);
    input input01("input01", {i0, i1}, p_float64);
    computation comp00("comp00", {i0, i1, i2, i3}, p_float64);
    comp00.set_expression(icomp00(i1, i2, i3) + input01(i0, i1));
    buffer buf00("buf00", {32, 64, 128}, p_float64, a_output);
    buffer buf01("buf01", {32, 32}, p_float64, a_input);
    icomp00.store_in(&buf00);
    input01.store_in(&buf01);
    comp00.store_in(&buf00, {i1, i2, i3});
    tiramisu::codegen({&buf00, &buf01}, "function663824.o");
    return 0;
}