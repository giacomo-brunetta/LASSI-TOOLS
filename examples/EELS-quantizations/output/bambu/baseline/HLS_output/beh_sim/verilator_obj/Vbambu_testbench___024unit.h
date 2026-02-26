// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vbambu_testbench.h for the primary calling header

#ifndef VERILATED_VBAMBU_TESTBENCH___024UNIT_H_
#define VERILATED_VBAMBU_TESTBENCH___024UNIT_H_  // guard

#include "verilated.h"

class Vbambu_testbench__Syms;

class Vbambu_testbench___024unit final : public VerilatedModule {
  public:

    // INTERNAL VARIABLES
    Vbambu_testbench__Syms* const vlSymsp;

    // CONSTRUCTORS
    Vbambu_testbench___024unit(Vbambu_testbench__Syms* symsp, const char* v__name);
    ~Vbambu_testbench___024unit();
    VL_UNCOPYABLE(Vbambu_testbench___024unit);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
} VL_ATTR_ALIGNED(VL_CACHE_LINE_BYTES);


#endif  // guard
