// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vbambu_testbench.h for the primary calling header

#include "verilated.h"
#include "verilated_dpi.h"

#include "Vbambu_testbench__Syms.h"
#include "Vbambu_testbench___024root.h"

#ifdef VL_DEBUG
VL_ATTR_COLD void Vbambu_testbench___024root___dump_triggers__stl(Vbambu_testbench___024root* vlSelf);
#endif  // VL_DEBUG

VL_ATTR_COLD void Vbambu_testbench___024root___eval_triggers__stl(Vbambu_testbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbambu_testbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbambu_testbench___024root___eval_triggers__stl\n"); );
    // Body
    vlSelf->__VstlTriggered.at(0U) = (0U == vlSelf->__VstlIterCount);
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vbambu_testbench___024root___dump_triggers__stl(vlSelf);
    }
#endif
}
