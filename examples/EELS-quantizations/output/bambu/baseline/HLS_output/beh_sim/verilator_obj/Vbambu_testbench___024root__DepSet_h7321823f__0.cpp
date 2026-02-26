// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vbambu_testbench.h for the primary calling header

#include "verilated.h"
#include "verilated_dpi.h"

#include "Vbambu_testbench__Syms.h"
#include "Vbambu_testbench___024root.h"

extern "C" unsigned int m_next(unsigned int state);

VL_INLINE_OPT void Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__SystemFSM__DOT__m_next_TOP(IData/*31:0*/ state, IData/*31:0*/ &m_next__Vfuncrtn) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__SystemFSM__DOT__m_next_TOP\n"); );
    // Body
    unsigned int state__Vcvt;
    for (size_t state__Vidx = 0; state__Vidx < 1; ++state__Vidx) state__Vcvt = state;
    unsigned int m_next__Vfuncrtn__Vcvt;
    m_next__Vfuncrtn__Vcvt = m_next(state__Vcvt);
    m_next__Vfuncrtn = m_next__Vfuncrtn__Vcvt;
}

extern "C" int m_fini();

VL_INLINE_OPT void Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__SystemFSM__DOT__m_fini_TOP(IData/*31:0*/ &m_fini__Vfuncrtn) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__SystemFSM__DOT__m_fini_TOP\n"); );
    // Body
    int m_fini__Vfuncrtn__Vcvt;
    m_fini__Vfuncrtn__Vcvt = m_fini();
    m_fini__Vfuncrtn = m_fini__Vfuncrtn__Vcvt;
}

extern "C" int m_read(unsigned char id, svLogicVecVal* data, unsigned short bitsize, unsigned int addr, unsigned char shift);

VL_INLINE_OPT void Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__m_read_TOP(CData/*7:0*/ id, VlWide<128>/*4095:0*/ &data, SData/*15:0*/ bitsize, IData/*31:0*/ addr, CData/*7:0*/ shift, IData/*31:0*/ &m_read__Vfuncrtn) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__m_read_TOP\n"); );
    // Body
    unsigned char id__Vcvt;
    for (size_t id__Vidx = 0; id__Vidx < 1; ++id__Vidx) id__Vcvt = id;
    svLogicVecVal data__Vcvt[128];
    unsigned short bitsize__Vcvt;
    for (size_t bitsize__Vidx = 0; bitsize__Vidx < 1; ++bitsize__Vidx) bitsize__Vcvt = bitsize;
    unsigned int addr__Vcvt;
    for (size_t addr__Vidx = 0; addr__Vidx < 1; ++addr__Vidx) addr__Vcvt = addr;
    unsigned char shift__Vcvt;
    for (size_t shift__Vidx = 0; shift__Vidx < 1; ++shift__Vidx) shift__Vcvt = shift;
    int m_read__Vfuncrtn__Vcvt;
    m_read__Vfuncrtn__Vcvt = m_read(id__Vcvt, data__Vcvt, bitsize__Vcvt, addr__Vcvt, shift__Vcvt);
    VL_SET_W_SVLV(4096,data,data__Vcvt + 0);
m_read__Vfuncrtn = m_read__Vfuncrtn__Vcvt;
}

extern "C" int m_write(unsigned char id, const svLogicVecVal* data, unsigned short bitsize, unsigned int addr, unsigned char shift);

VL_INLINE_OPT void Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__m_write_TOP(CData/*7:0*/ id, VlWide<128>/*4095:0*/ data, SData/*15:0*/ bitsize, IData/*31:0*/ addr, CData/*7:0*/ shift, IData/*31:0*/ &m_write__Vfuncrtn) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__m_write_TOP\n"); );
    // Body
    unsigned char id__Vcvt;
    for (size_t id__Vidx = 0; id__Vidx < 1; ++id__Vidx) id__Vcvt = id;
    svLogicVecVal data__Vcvt[128];
    for (size_t data__Vidx = 0; data__Vidx < 1; ++data__Vidx) VL_SET_SVLV_W(4096, data__Vcvt + 128 * data__Vidx, data);
    unsigned short bitsize__Vcvt;
    for (size_t bitsize__Vidx = 0; bitsize__Vidx < 1; ++bitsize__Vidx) bitsize__Vcvt = bitsize;
    unsigned int addr__Vcvt;
    for (size_t addr__Vidx = 0; addr__Vidx < 1; ++addr__Vidx) addr__Vcvt = addr;
    unsigned char shift__Vcvt;
    for (size_t shift__Vidx = 0; shift__Vidx < 1; ++shift__Vidx) shift__Vcvt = shift;
    int m_write__Vfuncrtn__Vcvt;
    m_write__Vfuncrtn__Vcvt = m_write(id__Vcvt, data__Vcvt, bitsize__Vcvt, addr__Vcvt, shift__Vcvt);
    m_write__Vfuncrtn = m_write__Vfuncrtn__Vcvt;
}

extern "C" int m_state(unsigned char id, int data);

VL_INLINE_OPT void Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__m_state_TOP(CData/*7:0*/ id, IData/*31:0*/ data, IData/*31:0*/ &m_state__Vfuncrtn) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__m_state_TOP\n"); );
    // Body
    unsigned char id__Vcvt;
    for (size_t id__Vidx = 0; id__Vidx < 1; ++id__Vidx) id__Vcvt = id;
    int data__Vcvt;
    for (size_t data__Vidx = 0; data__Vidx < 1; ++data__Vidx) data__Vcvt = data;
    int m_state__Vfuncrtn__Vcvt;
    m_state__Vfuncrtn__Vcvt = m_state(id__Vcvt, data__Vcvt);
    m_state__Vfuncrtn = m_state__Vfuncrtn__Vcvt;
}

VL_INLINE_OPT void Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__if_default_P0__DOT__m_utils__DOT__m_read_TOP(CData/*7:0*/ id, VlWide<128>/*4095:0*/ &data, SData/*15:0*/ bitsize, IData/*31:0*/ addr, CData/*7:0*/ shift, IData/*31:0*/ &m_read__Vfuncrtn) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__if_default_P0__DOT__m_utils__DOT__m_read_TOP\n"); );
    // Body
    unsigned char id__Vcvt;
    for (size_t id__Vidx = 0; id__Vidx < 1; ++id__Vidx) id__Vcvt = id;
    svLogicVecVal data__Vcvt[128];
    unsigned short bitsize__Vcvt;
    for (size_t bitsize__Vidx = 0; bitsize__Vidx < 1; ++bitsize__Vidx) bitsize__Vcvt = bitsize;
    unsigned int addr__Vcvt;
    for (size_t addr__Vidx = 0; addr__Vidx < 1; ++addr__Vidx) addr__Vcvt = addr;
    unsigned char shift__Vcvt;
    for (size_t shift__Vidx = 0; shift__Vidx < 1; ++shift__Vidx) shift__Vcvt = shift;
    int m_read__Vfuncrtn__Vcvt;
    m_read__Vfuncrtn__Vcvt = m_read(id__Vcvt, data__Vcvt, bitsize__Vcvt, addr__Vcvt, shift__Vcvt);
    VL_SET_W_SVLV(4096,data,data__Vcvt + 0);
m_read__Vfuncrtn = m_read__Vfuncrtn__Vcvt;
}

VL_INLINE_OPT void Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__if_default_P0__DOT__m_utils__DOT__m_write_TOP(CData/*7:0*/ id, VlWide<128>/*4095:0*/ data, SData/*15:0*/ bitsize, IData/*31:0*/ addr, CData/*7:0*/ shift, IData/*31:0*/ &m_write__Vfuncrtn) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__if_default_P0__DOT__m_utils__DOT__m_write_TOP\n"); );
    // Body
    unsigned char id__Vcvt;
    for (size_t id__Vidx = 0; id__Vidx < 1; ++id__Vidx) id__Vcvt = id;
    svLogicVecVal data__Vcvt[128];
    for (size_t data__Vidx = 0; data__Vidx < 1; ++data__Vidx) VL_SET_SVLV_W(4096, data__Vcvt + 128 * data__Vidx, data);
    unsigned short bitsize__Vcvt;
    for (size_t bitsize__Vidx = 0; bitsize__Vidx < 1; ++bitsize__Vidx) bitsize__Vcvt = bitsize;
    unsigned int addr__Vcvt;
    for (size_t addr__Vidx = 0; addr__Vidx < 1; ++addr__Vidx) addr__Vcvt = addr;
    unsigned char shift__Vcvt;
    for (size_t shift__Vidx = 0; shift__Vidx < 1; ++shift__Vidx) shift__Vcvt = shift;
    int m_write__Vfuncrtn__Vcvt;
    m_write__Vfuncrtn__Vcvt = m_write(id__Vcvt, data__Vcvt, bitsize__Vcvt, addr__Vcvt, shift__Vcvt);
    m_write__Vfuncrtn = m_write__Vfuncrtn__Vcvt;
}

VL_INLINE_OPT void Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__if_default_P1__DOT__m_utils__DOT__m_read_TOP(CData/*7:0*/ id, VlWide<128>/*4095:0*/ &data, SData/*15:0*/ bitsize, IData/*31:0*/ addr, CData/*7:0*/ shift, IData/*31:0*/ &m_read__Vfuncrtn) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__if_default_P1__DOT__m_utils__DOT__m_read_TOP\n"); );
    // Body
    unsigned char id__Vcvt;
    for (size_t id__Vidx = 0; id__Vidx < 1; ++id__Vidx) id__Vcvt = id;
    svLogicVecVal data__Vcvt[128];
    unsigned short bitsize__Vcvt;
    for (size_t bitsize__Vidx = 0; bitsize__Vidx < 1; ++bitsize__Vidx) bitsize__Vcvt = bitsize;
    unsigned int addr__Vcvt;
    for (size_t addr__Vidx = 0; addr__Vidx < 1; ++addr__Vidx) addr__Vcvt = addr;
    unsigned char shift__Vcvt;
    for (size_t shift__Vidx = 0; shift__Vidx < 1; ++shift__Vidx) shift__Vcvt = shift;
    int m_read__Vfuncrtn__Vcvt;
    m_read__Vfuncrtn__Vcvt = m_read(id__Vcvt, data__Vcvt, bitsize__Vcvt, addr__Vcvt, shift__Vcvt);
    VL_SET_W_SVLV(4096,data,data__Vcvt + 0);
m_read__Vfuncrtn = m_read__Vfuncrtn__Vcvt;
}

VL_INLINE_OPT void Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__if_default_P1__DOT__m_utils__DOT__m_write_TOP(CData/*7:0*/ id, VlWide<128>/*4095:0*/ data, SData/*15:0*/ bitsize, IData/*31:0*/ addr, CData/*7:0*/ shift, IData/*31:0*/ &m_write__Vfuncrtn) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__if_default_P1__DOT__m_utils__DOT__m_write_TOP\n"); );
    // Body
    unsigned char id__Vcvt;
    for (size_t id__Vidx = 0; id__Vidx < 1; ++id__Vidx) id__Vcvt = id;
    svLogicVecVal data__Vcvt[128];
    for (size_t data__Vidx = 0; data__Vidx < 1; ++data__Vidx) VL_SET_SVLV_W(4096, data__Vcvt + 128 * data__Vidx, data);
    unsigned short bitsize__Vcvt;
    for (size_t bitsize__Vidx = 0; bitsize__Vidx < 1; ++bitsize__Vidx) bitsize__Vcvt = bitsize;
    unsigned int addr__Vcvt;
    for (size_t addr__Vidx = 0; addr__Vidx < 1; ++addr__Vidx) addr__Vcvt = addr;
    unsigned char shift__Vcvt;
    for (size_t shift__Vidx = 0; shift__Vidx < 1; ++shift__Vidx) shift__Vcvt = shift;
    int m_write__Vfuncrtn__Vcvt;
    m_write__Vfuncrtn__Vcvt = m_write(id__Vcvt, data__Vcvt, bitsize__Vcvt, addr__Vcvt, shift__Vcvt);
    m_write__Vfuncrtn = m_write__Vfuncrtn__Vcvt;
}

VL_INLINE_OPT void Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__if_default_P2__DOT__m_utils__DOT__m_read_TOP(CData/*7:0*/ id, VlWide<128>/*4095:0*/ &data, SData/*15:0*/ bitsize, IData/*31:0*/ addr, CData/*7:0*/ shift, IData/*31:0*/ &m_read__Vfuncrtn) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__if_default_P2__DOT__m_utils__DOT__m_read_TOP\n"); );
    // Body
    unsigned char id__Vcvt;
    for (size_t id__Vidx = 0; id__Vidx < 1; ++id__Vidx) id__Vcvt = id;
    svLogicVecVal data__Vcvt[128];
    unsigned short bitsize__Vcvt;
    for (size_t bitsize__Vidx = 0; bitsize__Vidx < 1; ++bitsize__Vidx) bitsize__Vcvt = bitsize;
    unsigned int addr__Vcvt;
    for (size_t addr__Vidx = 0; addr__Vidx < 1; ++addr__Vidx) addr__Vcvt = addr;
    unsigned char shift__Vcvt;
    for (size_t shift__Vidx = 0; shift__Vidx < 1; ++shift__Vidx) shift__Vcvt = shift;
    int m_read__Vfuncrtn__Vcvt;
    m_read__Vfuncrtn__Vcvt = m_read(id__Vcvt, data__Vcvt, bitsize__Vcvt, addr__Vcvt, shift__Vcvt);
    VL_SET_W_SVLV(4096,data,data__Vcvt + 0);
m_read__Vfuncrtn = m_read__Vfuncrtn__Vcvt;
}

VL_INLINE_OPT void Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__if_default_P2__DOT__m_utils__DOT__m_write_TOP(CData/*7:0*/ id, VlWide<128>/*4095:0*/ data, SData/*15:0*/ bitsize, IData/*31:0*/ addr, CData/*7:0*/ shift, IData/*31:0*/ &m_write__Vfuncrtn) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__if_default_P2__DOT__m_utils__DOT__m_write_TOP\n"); );
    // Body
    unsigned char id__Vcvt;
    for (size_t id__Vidx = 0; id__Vidx < 1; ++id__Vidx) id__Vcvt = id;
    svLogicVecVal data__Vcvt[128];
    for (size_t data__Vidx = 0; data__Vidx < 1; ++data__Vidx) VL_SET_SVLV_W(4096, data__Vcvt + 128 * data__Vidx, data);
    unsigned short bitsize__Vcvt;
    for (size_t bitsize__Vidx = 0; bitsize__Vidx < 1; ++bitsize__Vidx) bitsize__Vcvt = bitsize;
    unsigned int addr__Vcvt;
    for (size_t addr__Vidx = 0; addr__Vidx < 1; ++addr__Vidx) addr__Vcvt = addr;
    unsigned char shift__Vcvt;
    for (size_t shift__Vidx = 0; shift__Vidx < 1; ++shift__Vidx) shift__Vcvt = shift;
    int m_write__Vfuncrtn__Vcvt;
    m_write__Vfuncrtn__Vcvt = m_write(id__Vcvt, data__Vcvt, bitsize__Vcvt, addr__Vcvt, shift__Vcvt);
    m_write__Vfuncrtn = m_write__Vfuncrtn__Vcvt;
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vbambu_testbench___024root___dump_triggers__act(Vbambu_testbench___024root* vlSelf);
#endif  // VL_DEBUG

void Vbambu_testbench___024root___eval_triggers__act(Vbambu_testbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbambu_testbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbambu_testbench___024root___eval_triggers__act\n"); );
    // Body
    vlSelf->__VactTriggered.at(0U) = ((IData)(vlSelf->clock) 
                                      & (~ (IData)(vlSelf->__Vtrigrprev__TOP__clock)));
    vlSelf->__VactTriggered.at(1U) = (((~ (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__rst)) 
                                       & (IData)(vlSelf->__Vtrigrprev__TOP__bambu_testbench__DOT__system__DOT__SystemFSM__DOT__rst)) 
                                      | ((IData)(vlSelf->clock) 
                                         & (~ (IData)(vlSelf->__Vtrigrprev__TOP__clock))));
    vlSelf->__VactTriggered.at(2U) = ((~ (IData)(vlSelf->clock)) 
                                      & (IData)(vlSelf->__Vtrigrprev__TOP__clock));
    vlSelf->__Vtrigrprev__TOP__clock = vlSelf->clock;
    vlSelf->__Vtrigrprev__TOP__bambu_testbench__DOT__system__DOT__SystemFSM__DOT__rst 
        = vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__rst;
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vbambu_testbench___024root___dump_triggers__act(vlSelf);
    }
#endif
}
