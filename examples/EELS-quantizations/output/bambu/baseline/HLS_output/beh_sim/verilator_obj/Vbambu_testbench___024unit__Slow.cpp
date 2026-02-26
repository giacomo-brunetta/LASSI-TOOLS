// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vbambu_testbench.h for the primary calling header

#include "verilated.h"
#include "verilated_dpi.h"

#include "Vbambu_testbench__Syms.h"
#include "Vbambu_testbench___024unit.h"

void Vbambu_testbench___024unit___ctor_var_reset(Vbambu_testbench___024unit* vlSelf);

Vbambu_testbench___024unit::Vbambu_testbench___024unit(Vbambu_testbench__Syms* symsp, const char* v__name)
    : VerilatedModule{v__name}
    , vlSymsp{symsp}
 {
    // Reset structure values
    Vbambu_testbench___024unit___ctor_var_reset(this);
}

void Vbambu_testbench___024unit::__Vconfigure(bool first) {
    if (false && first) {}  // Prevent unused
}

Vbambu_testbench___024unit::~Vbambu_testbench___024unit() {
}
