// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vbambu_testbench.h for the primary calling header

#include "verilated.h"
#include "verilated_dpi.h"

#include "Vbambu_testbench___024root.h"

void Vbambu_testbench___024root___eval_act(Vbambu_testbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbambu_testbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbambu_testbench___024root___eval_act\n"); );
}

void Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__if_default_P0__DOT__m_utils__DOT__m_read_TOP(CData/*7:0*/ id, VlWide<128>/*4095:0*/ &data, SData/*15:0*/ bitsize, IData/*31:0*/ addr, CData/*7:0*/ shift, IData/*31:0*/ &m_read__Vfuncrtn);
void Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__if_default_P2__DOT__m_utils__DOT__m_read_TOP(CData/*7:0*/ id, VlWide<128>/*4095:0*/ &data, SData/*15:0*/ bitsize, IData/*31:0*/ addr, CData/*7:0*/ shift, IData/*31:0*/ &m_read__Vfuncrtn);
void Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__SystemFSM__DOT__m_fini_TOP(IData/*31:0*/ &m_fini__Vfuncrtn);
void Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__SystemFSM__DOT__m_next_TOP(IData/*31:0*/ state, IData/*31:0*/ &m_next__Vfuncrtn);
void Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__m_read_TOP(CData/*7:0*/ id, VlWide<128>/*4095:0*/ &data, SData/*15:0*/ bitsize, IData/*31:0*/ addr, CData/*7:0*/ shift, IData/*31:0*/ &m_read__Vfuncrtn);
void Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__if_default_P1__DOT__m_utils__DOT__m_read_TOP(CData/*7:0*/ id, VlWide<128>/*4095:0*/ &data, SData/*15:0*/ bitsize, IData/*31:0*/ addr, CData/*7:0*/ shift, IData/*31:0*/ &m_read__Vfuncrtn);

VL_INLINE_OPT void Vbambu_testbench___024root___nba_sequent__TOP__0(Vbambu_testbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbambu_testbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbambu_testbench___024root___nba_sequent__TOP__0\n"); );
    // Init
    IData/*31:0*/ __Vfunc_bambu_testbench__DOT__system__DOT__SystemFSM__DOT__m_fini__0__Vfuncout;
    __Vfunc_bambu_testbench__DOT__system__DOT__SystemFSM__DOT__m_fini__0__Vfuncout = 0;
    IData/*31:0*/ __Vfunc_bambu_testbench__DOT__system__DOT__SystemFSM__DOT__m_fini__1__Vfuncout;
    __Vfunc_bambu_testbench__DOT__system__DOT__SystemFSM__DOT__m_fini__1__Vfuncout = 0;
    IData/*31:0*/ __Vfunc_bambu_testbench__DOT__system__DOT__SystemFSM__DOT__m_next__2__Vfuncout;
    __Vfunc_bambu_testbench__DOT__system__DOT__SystemFSM__DOT__m_next__2__Vfuncout = 0;
    IData/*31:0*/ __Vfunc_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__read_a__3__Vfuncout;
    __Vfunc_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__read_a__3__Vfuncout = 0;
    IData/*31:0*/ __Vfunc_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__read_a__3__addr;
    __Vfunc_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__read_a__3__addr = 0;
    VlWide<128>/*4095:0*/ __Vfunc_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__read_a__3___data;
    VL_ZERO_W(4096, __Vfunc_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__read_a__3___data);
    IData/*31:0*/ __Vtask_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__m_read__4__Vfuncout;
    __Vtask_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__m_read__4__Vfuncout = 0;
    VlWide<128>/*4095:0*/ __Vtask_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__m_read__4__data;
    VL_ZERO_W(4096, __Vtask_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__m_read__4__data);
    IData/*31:0*/ __Vfunc_bambu_testbench__DOT__system__DOT__if_default_P0__DOT__m_utils__DOT__read__11__Vfuncout;
    __Vfunc_bambu_testbench__DOT__system__DOT__if_default_P0__DOT__m_utils__DOT__read__11__Vfuncout = 0;
    VlWide<128>/*4095:0*/ __Vfunc_bambu_testbench__DOT__system__DOT__if_default_P0__DOT__m_utils__DOT__read__11___data;
    VL_ZERO_W(4096, __Vfunc_bambu_testbench__DOT__system__DOT__if_default_P0__DOT__m_utils__DOT__read__11___data);
    IData/*31:0*/ __Vtask_bambu_testbench__DOT__system__DOT__if_default_P0__DOT__m_utils__DOT__m_read__12__Vfuncout;
    __Vtask_bambu_testbench__DOT__system__DOT__if_default_P0__DOT__m_utils__DOT__m_read__12__Vfuncout = 0;
    VlWide<128>/*4095:0*/ __Vtask_bambu_testbench__DOT__system__DOT__if_default_P0__DOT__m_utils__DOT__m_read__12__data;
    VL_ZERO_W(4096, __Vtask_bambu_testbench__DOT__system__DOT__if_default_P0__DOT__m_utils__DOT__m_read__12__data);
    IData/*31:0*/ __Vfunc_bambu_testbench__DOT__system__DOT__if_default_P1__DOT__m_utils__DOT__read__13__Vfuncout;
    __Vfunc_bambu_testbench__DOT__system__DOT__if_default_P1__DOT__m_utils__DOT__read__13__Vfuncout = 0;
    VlWide<128>/*4095:0*/ __Vfunc_bambu_testbench__DOT__system__DOT__if_default_P1__DOT__m_utils__DOT__read__13___data;
    VL_ZERO_W(4096, __Vfunc_bambu_testbench__DOT__system__DOT__if_default_P1__DOT__m_utils__DOT__read__13___data);
    IData/*31:0*/ __Vtask_bambu_testbench__DOT__system__DOT__if_default_P1__DOT__m_utils__DOT__m_read__14__Vfuncout;
    __Vtask_bambu_testbench__DOT__system__DOT__if_default_P1__DOT__m_utils__DOT__m_read__14__Vfuncout = 0;
    VlWide<128>/*4095:0*/ __Vtask_bambu_testbench__DOT__system__DOT__if_default_P1__DOT__m_utils__DOT__m_read__14__data;
    VL_ZERO_W(4096, __Vtask_bambu_testbench__DOT__system__DOT__if_default_P1__DOT__m_utils__DOT__m_read__14__data);
    IData/*31:0*/ __Vfunc_bambu_testbench__DOT__system__DOT__if_default_P2__DOT__m_utils__DOT__read__15__Vfuncout;
    __Vfunc_bambu_testbench__DOT__system__DOT__if_default_P2__DOT__m_utils__DOT__read__15__Vfuncout = 0;
    VlWide<128>/*4095:0*/ __Vfunc_bambu_testbench__DOT__system__DOT__if_default_P2__DOT__m_utils__DOT__read__15___data;
    VL_ZERO_W(4096, __Vfunc_bambu_testbench__DOT__system__DOT__if_default_P2__DOT__m_utils__DOT__read__15___data);
    IData/*31:0*/ __Vtask_bambu_testbench__DOT__system__DOT__if_default_P2__DOT__m_utils__DOT__m_read__16__Vfuncout;
    __Vtask_bambu_testbench__DOT__system__DOT__if_default_P2__DOT__m_utils__DOT__m_read__16__Vfuncout = 0;
    VlWide<128>/*4095:0*/ __Vtask_bambu_testbench__DOT__system__DOT__if_default_P2__DOT__m_utils__DOT__m_read__16__data;
    VL_ZERO_W(4096, __Vtask_bambu_testbench__DOT__system__DOT__if_default_P2__DOT__m_utils__DOT__m_read__16__data);
    VlWide<3>/*95:0*/ __Vtemp_hb1848f04__0;
    VlWide<3>/*95:0*/ __Vtemp_hb1848f04__1;
    VlWide<3>/*95:0*/ __Vtemp_hb1848f04__2;
    VlWide<3>/*95:0*/ __Vtemp_hb1848f04__3;
    VlWide<3>/*95:0*/ __Vtemp_hb1848f04__4;
    // Body
    if (VL_UNLIKELY((((~ (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT____VdfgTmp_hca893bdf__0)) 
                      & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__fuselector_BMEMORY_CTRLN_83_i0_STORE)) 
                     & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__fuselector_BMEMORY_CTRLN_83_i0_LOAD)))) {
        VL_WRITEF("ERROR - Mout_we_ram and Mout_oe_ram both enabled on channel 0!\n");
        VL_FINISH_MT("HLS_output/simulation/bambu_testbench.v", 817, "");
    }
    vlSelf->__Vdly__bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_14__DOT__reg_out1 
        = vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_14__DOT__reg_out1;
    vlSelf->__Vdly__bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_14__DOT__reg_out1 
        = (1U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_9__DOT__reg_out1 
                 >> 0x1aU));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_27__DOT__reg_out1 
        = (1U & (IData)((0xffffffffffffULL & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_ui_mult_expr_FU_32_32_32_0_109_i0_fu_forward_kernel_500073_510825 
                                              >> 0x2fU))));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_28__DOT__reg_out1 
        = (1U & ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_UUdata_converter_FU_38_i0_fu_forward_kernel_500073_510858) 
                 >> 9U));
    vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__start 
        = vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__start_next;
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_33__DOT__reg_out1 
        = (1U & (IData)((0x8000000000000000ULL >> (
                                                   (0x20U 
                                                    & ((IData)(
                                                               (0x1ffffffffULL 
                                                                & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_113_i1_fu_forward_kernel_500073_510909 
                                                                   >> 0x1eU))) 
                                                       << 5U)) 
                                                   | ((0x10U 
                                                       & ((IData)(
                                                                  (0x1ffffffffULL 
                                                                   & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_113_i1_fu_forward_kernel_500073_510909 
                                                                      >> 0x1dU))) 
                                                          << 4U)) 
                                                      | ((8U 
                                                          & ((IData)(
                                                                     (0x1ffffffffULL 
                                                                      & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_113_i1_fu_forward_kernel_500073_510909 
                                                                         >> 0x1aU))) 
                                                             << 3U)) 
                                                         | ((4U 
                                                             & ((IData)(
                                                                        (0x1ffffffffULL 
                                                                         & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_113_i1_fu_forward_kernel_500073_510909 
                                                                            >> 0x19U))) 
                                                                << 2U)) 
                                                            | ((2U 
                                                                & ((IData)(
                                                                           (0x1ffffffffULL 
                                                                            & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_113_i1_fu_forward_kernel_500073_510909 
                                                                               >> 0x18U))) 
                                                                   << 1U)) 
                                                               | (1U 
                                                                  & (IData)(
                                                                            (0x1ffffffffULL 
                                                                             & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_113_i1_fu_forward_kernel_500073_510909 
                                                                                >> 0x17U))))))))))));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_32__DOT__reg_out1 
        = (1U & (IData)((0x1ffffffffULL & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_113_i1_fu_forward_kernel_500073_510909 
                                           >> 0x1cU))));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_31__DOT__reg_out1 
        = (1U & (IData)((0x1ffffffffULL & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_113_i1_fu_forward_kernel_500073_510909 
                                           >> 0x1bU))));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_30__DOT__reg_out1 
        = (1U & (IData)((vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_113_i1_fu_forward_kernel_500073_510909 
                         >> 0x1fU)));
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_24) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_24__DOT__reg_out1 
            = vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_lut_expr_FU_68_i0_fu_forward_kernel_500073_511134;
    }
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_26__DOT__reg_out1 
        = (1U & (IData)((0xffffffffffffULL & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_ui_mult_expr_FU_32_32_32_0_109_i0_fu_forward_kernel_500073_510825 
                                              >> 0x2fU))));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_25__DOT__reg_out1 
        = vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_ui_mult_expr_FU_32_32_32_0_109_i0_fu_forward_kernel_500073_510825;
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_23) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_23__DOT__reg_out1 
            = (1U & (0x10fU >> (IData)(vlSelf->__VdfgTmp_h6e163198__0)));
    }
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_34__DOT__reg_out1 
        = (1U & (0xa800U >> ((8U & ((IData)((0x1ffffffffULL 
                                             & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_113_i1_fu_forward_kernel_500073_510909 
                                                >> 0x20U))) 
                                    << 3U)) | (IData)(vlSelf->__VdfgTmp_hcdb08d50__0))));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_27__DOT__reg_out1 
        = (0x7ffffffffffULL & ((QData)((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_ior_concat_expr_FU_166_i0_fu___05F_float_adde8m23b_127nih_501195_501585)) 
                               << 0x10U));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_26__DOT__reg_out1 
        = vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_ior_concat_expr_FU_166_i0_fu___05F_float_adde8m23b_127nih_501195_501585;
    vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__rst_count 
        = vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__rst_count_next;
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_16__DOT__reg_out1 
        = vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_lut_expr_FU_57_i0_fu_forward_kernel_500073_511100;
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_0__DOT__reg_out1 
        = (0x7ffffffU & ((0x3ffffffU & ((0x3ffffffU 
                                         & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_ior_expr_FU_0_32_32_168_i0_fu___05F_float_adde8m23b_127nih_501195_501465 
                                            << 2U)) 
                                        >> (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_ior_expr_FU_8_8_8_177_i0_fu___05F_float_adde8m23b_127nih_501195_501506))) 
                         ^ (- (IData)((1U & (IData)(
                                                    VL_SHIFTRS_QQI(64,64,6, 
                                                                   (VL_EXTENDS_QI(64,2, 
                                                                                (1U 
                                                                                & (0xb0ba1f4U 
                                                                                >> (IData)(vlSelf->__VdfgTmp_h648d1a24__0)))) 
                                                                    << 0x3fU), 0x3fU)))))));
    vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state 
        = vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next;
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_1) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_1__DOT__reg_out1 
            = vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_ui_pointer_plus_expr_FU_32_32_32_115_i2_fu_forward_kernel_500073_500127;
    }
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_17__DOT__reg_out1 
        = (1U & (0xe0fU >> (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_lut_expr_FU_64_i0_fu_forward_kernel_500073_511121) 
                             << 3U) | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_lut_expr_FU_57_i0_fu_forward_kernel_500073_511100) 
                                        << 2U) | (IData)(vlSelf->__VdfgTmp_h34d5e52a__0)))));
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_21) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_21__DOT__reg_out1 
            = vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_47_i0_fu___05F_float_adde8m23b_127nih_501195_510578;
    }
    vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__1__KET____DOT__Rready = 0U;
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_22) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_22__DOT__reg_out1 
            = (1U & (0xbU >> (IData)(vlSelf->__VdfgTmp_h4ab71bb9__0)));
    }
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_19) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_19__DOT__reg_out1 
            = vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_45_i0_fu___05F_float_adde8m23b_127nih_501195_510572;
    }
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_18) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_18__DOT__reg_out1 
            = vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_44_i0_fu___05F_float_adde8m23b_127nih_501195_510569;
    }
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_17) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_17__DOT__reg_out1 
            = vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_43_i0_fu___05F_float_adde8m23b_127nih_501195_510566;
    }
    vlSelf->bambu_testbench__DOT__system__DOT__if_default_P0__DOT__val 
        = vlSelf->bambu_testbench__DOT__system__DOT__sig_P0;
    vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__1__KET____DOT__queue_counter 
        = ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__rst)
            ? (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__1__KET____DOT__queue_counter_next)
            : 0U);
    if (vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__setup) {
        Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__if_default_P0__DOT__m_utils__DOT__m_read_TOP(0U, __Vtask_bambu_testbench__DOT__system__DOT__if_default_P0__DOT__m_utils__DOT__m_read__12__data, 0x20U, 0U, 0U, __Vtask_bambu_testbench__DOT__system__DOT__if_default_P0__DOT__m_utils__DOT__m_read__12__Vfuncout);
        VL_ASSIGN_W(4096,__Vfunc_bambu_testbench__DOT__system__DOT__if_default_P0__DOT__m_utils__DOT__read__11___data, __Vtask_bambu_testbench__DOT__system__DOT__if_default_P0__DOT__m_utils__DOT__m_read__12__data);
        __Vfunc_bambu_testbench__DOT__system__DOT__if_default_P0__DOT__m_utils__DOT__read__11__Vfuncout 
            = __Vfunc_bambu_testbench__DOT__system__DOT__if_default_P0__DOT__m_utils__DOT__read__11___data[0U];
        vlSelf->bambu_testbench__DOT__system__DOT__if_default_P0__DOT__val 
            = __Vfunc_bambu_testbench__DOT__system__DOT__if_default_P0__DOT__m_utils__DOT__read__11__Vfuncout;
    }
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_59__DOT__reg_out1 
        = (1U & (0xfffe0000U >> ((0x10U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_lshift_expr_FU_64_64_64_195_i0_fu___05F_float_adde8m23b_127nih_501195_501802 
                                           << 2U)) 
                                 | ((8U & vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_lshift_expr_FU_64_64_64_195_i0_fu___05F_float_adde8m23b_127nih_501195_501802) 
                                    | ((4U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_lshift_expr_FU_64_64_64_195_i0_fu___05F_float_adde8m23b_127nih_501195_501802 
                                              << 1U)) 
                                       | ((2U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_lshift_expr_FU_64_64_64_195_i0_fu___05F_float_adde8m23b_127nih_501195_501802 
                                                 << 1U)) 
                                          | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_28__DOT__reg_out1)))))));
    vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__1__KET____DOT__Wready_reg 
        = vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__1__KET____DOT__Wready;
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_53__DOT__reg_out1 
        = (1U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i2_fu___05F_float_adde8m23b_127nih_501195_503543 
                 >> 0xaU));
    vlSelf->bambu_testbench__DOT__system__DOT__if_default_P2__DOT__val 
        = vlSelf->bambu_testbench__DOT__system__DOT__sig_P2;
    if (vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__setup) {
        Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__if_default_P2__DOT__m_utils__DOT__m_read_TOP(2U, __Vtask_bambu_testbench__DOT__system__DOT__if_default_P2__DOT__m_utils__DOT__m_read__16__data, 0x20U, 0U, 0U, __Vtask_bambu_testbench__DOT__system__DOT__if_default_P2__DOT__m_utils__DOT__m_read__16__Vfuncout);
        VL_ASSIGN_W(4096,__Vfunc_bambu_testbench__DOT__system__DOT__if_default_P2__DOT__m_utils__DOT__read__15___data, __Vtask_bambu_testbench__DOT__system__DOT__if_default_P2__DOT__m_utils__DOT__m_read__16__data);
        __Vfunc_bambu_testbench__DOT__system__DOT__if_default_P2__DOT__m_utils__DOT__read__15__Vfuncout 
            = __Vfunc_bambu_testbench__DOT__system__DOT__if_default_P2__DOT__m_utils__DOT__read__15___data[0U];
        vlSelf->bambu_testbench__DOT__system__DOT__if_default_P2__DOT__val 
            = __Vfunc_bambu_testbench__DOT__system__DOT__if_default_P2__DOT__m_utils__DOT__read__15__Vfuncout;
    }
    vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_succ 
        = vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_succ_next;
    if ((0x40U & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next))) {
        if ((1U & (~ ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next) 
                      >> 5U)))) {
            if ((1U & (~ ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next) 
                          >> 4U)))) {
                if ((1U & (~ ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next) 
                              >> 3U)))) {
                    if ((1U & (~ ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next) 
                                  >> 2U)))) {
                        if ((1U & (~ ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next) 
                                      >> 1U)))) {
                            if (VL_UNLIKELY((1U & (~ (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next))))) {
                                vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__unnamedblk6__DOT__curr_time 
                                    = VL_TIME_UNITED_Q(1);
                                __Vtemp_hb1848f04__0[0U] = 0x2e747874U;
                                __Vtemp_hb1848f04__0[1U] = 0x756c7473U;
                                __Vtemp_hb1848f04__0[2U] = 0x726573U;
                                vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__unnamedblk6__DOT__res_file = VL_FOPEN_NN(
                                                                                VL_CVT_PACK_STR_NW(3, __Vtemp_hb1848f04__0)
                                                                                , 
                                                                                std::string{"a"});
                                VL_FWRITEF(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__unnamedblk6__DOT__res_file,"%0#,",
                                           64,vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__unnamedblk6__DOT__curr_time);
                                VL_FCLOSE_I(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__unnamedblk6__DOT__res_file); vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__unnamedblk6__DOT__res_file = 0;
                            }
                        }
                    }
                }
            }
        }
    } else if ((0x20U & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next))) {
        if ((1U & (~ ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next) 
                      >> 4U)))) {
            if ((1U & (~ ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next) 
                          >> 3U)))) {
                if ((1U & (~ ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next) 
                              >> 2U)))) {
                    if ((1U & (~ ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next) 
                                  >> 1U)))) {
                        if (VL_UNLIKELY((1U & (~ (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next))))) {
                            Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__SystemFSM__DOT__m_fini_TOP(__Vfunc_bambu_testbench__DOT__system__DOT__SystemFSM__DOT__m_fini__0__Vfuncout);
                            __Vtemp_hb1848f04__1[0U] = 0x2e747874U;
                            __Vtemp_hb1848f04__1[1U] = 0x756c7473U;
                            __Vtemp_hb1848f04__1[2U] = 0x726573U;
                            vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__unnamedblk8__DOT__res_file = VL_FOPEN_NN(
                                                                                VL_CVT_PACK_STR_NW(3, __Vtemp_hb1848f04__1)
                                                                                , 
                                                                                std::string{"a"});
                            VL_FWRITEF(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__unnamedblk8__DOT__res_file,"\nA\n");
                            VL_WRITEF("Sim: Testbench aborted\n");
                            VL_FCLOSE_I(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__unnamedblk8__DOT__res_file); vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__unnamedblk8__DOT__res_file = 0;
                            VL_FINISH_MT("HLS_output/simulation/bambu_testbench.v", 315, "");
                        }
                    }
                }
            }
        }
    } else if ((1U & (~ ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next) 
                         >> 4U)))) {
        if ((8U & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next))) {
            if ((1U & (~ ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next) 
                          >> 2U)))) {
                if ((1U & (~ ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next) 
                              >> 1U)))) {
                    if (VL_UNLIKELY((1U & (~ (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next))))) {
                        Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__SystemFSM__DOT__m_fini_TOP(__Vfunc_bambu_testbench__DOT__system__DOT__SystemFSM__DOT__m_fini__1__Vfuncout);
                        vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__unnamedblk7__DOT__r 
                            = __Vfunc_bambu_testbench__DOT__system__DOT__SystemFSM__DOT__m_fini__1__Vfuncout;
                        __Vtemp_hb1848f04__2[0U] = 0x2e747874U;
                        __Vtemp_hb1848f04__2[1U] = 0x756c7473U;
                        __Vtemp_hb1848f04__2[2U] = 0x726573U;
                        vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__unnamedblk7__DOT__res_file = VL_FOPEN_NN(
                                                                                VL_CVT_PACK_STR_NW(3, __Vtemp_hb1848f04__2)
                                                                                , 
                                                                                std::string{"a"});
                        VL_FWRITEF(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__unnamedblk7__DOT__res_file,"\n%0#\n",
                                   8,(0xffU & (vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__unnamedblk7__DOT__r 
                                               >> 8U)));
                        VL_WRITEF("Sim: Testbench returned: %0#\n",
                                  8,(0xffU & (vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__unnamedblk7__DOT__r 
                                              >> 8U)));
                        VL_FCLOSE_I(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__unnamedblk7__DOT__res_file); vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__unnamedblk7__DOT__res_file = 0;
                        VL_FINISH_MT("HLS_output/simulation/bambu_testbench.v", 305, "");
                    }
                }
            }
        } else if ((4U & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next))) {
            if ((1U & (~ ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next) 
                          >> 1U)))) {
                if ((1U & (~ (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next)))) {
                    vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__unnamedblk4__DOT__curr_cycle 
                        = VL_EXTENDS_QI(64,32, VL_RTOI_I_D(
                                                           (VL_ITOR_D_Q(64, VL_TIME_UNITED_Q(1)) 
                                                            / 2.0)));
                    if (VL_UNLIKELY((vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__unnamedblk4__DOT__curr_cycle 
                                     >= vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__over_time))) {
                        __Vtemp_hb1848f04__3[0U] = 0x2e747874U;
                        __Vtemp_hb1848f04__3[1U] = 0x756c7473U;
                        __Vtemp_hb1848f04__3[2U] = 0x726573U;
                        vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__unnamedblk4__DOT__unnamedblk5__DOT__res_file = VL_FOPEN_NN(
                                                                                VL_CVT_PACK_STR_NW(3, __Vtemp_hb1848f04__3)
                                                                                , 
                                                                                std::string{"a"});
                        VL_FWRITEF(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__unnamedblk4__DOT__unnamedblk5__DOT__res_file,"X");
                        VL_FCLOSE_I(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__unnamedblk4__DOT__unnamedblk5__DOT__res_file); vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__unnamedblk4__DOT__unnamedblk5__DOT__res_file = 0;
                        VL_WRITEF("Sim: Simulation exceeds 200000000 cycles\n");
                        VL_FINISH_MT("HLS_output/simulation/bambu_testbench.v", 282, "");
                    }
                }
            }
        } else if ((2U & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next))) {
            if ((1U & (~ (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next)))) {
                vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__unnamedblk3__DOT__start_time 
                    = VL_RTOIROUND_Q_D((2.0 + VL_ITOR_D_Q(64, VL_TIME_UNITED_Q(1))));
                vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__unnamedblk3__DOT__start_cycle 
                    = VL_EXTENDS_QI(64,32, VL_RTOI_I_D(
                                                       (VL_ITOR_D_Q(64, vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__unnamedblk3__DOT__start_time) 
                                                        / 2.0)));
                if (VL_UNLIKELY(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__setup_next)) {
                    __Vtemp_hb1848f04__4[0U] = 0x2e747874U;
                    __Vtemp_hb1848f04__4[1U] = 0x756c7473U;
                    __Vtemp_hb1848f04__4[2U] = 0x726573U;
                    vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__unnamedblk3__DOT__res_file = VL_FOPEN_NN(
                                                                                VL_CVT_PACK_STR_NW(3, __Vtemp_hb1848f04__4)
                                                                                , 
                                                                                std::string{"a"});
                    VL_FWRITEF(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__unnamedblk3__DOT__res_file,"%0#|",
                               64,vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__unnamedblk3__DOT__start_time);
                    VL_FCLOSE_I(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__unnamedblk3__DOT__res_file); vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__unnamedblk3__DOT__res_file = 0;
                }
                vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__over_time 
                    = (0xbebc200ULL + vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__unnamedblk3__DOT__start_cycle);
            }
        } else if ((1U & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next))) {
            Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__SystemFSM__DOT__m_next_TOP(1U, __Vfunc_bambu_testbench__DOT__system__DOT__SystemFSM__DOT__m_next__2__Vfuncout);
            vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__unnamedblk2__DOT__next_state 
                = __Vfunc_bambu_testbench__DOT__system__DOT__SystemFSM__DOT__m_next__2__Vfuncout;
            vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_succ 
                = (0x7fU & vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__unnamedblk2__DOT__next_state);
        }
    }
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_19__DOT__reg_out1 
        = (0x800000U | (0x7fffffU & vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_15__DOT__reg_out1 
        = (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0 
           >> 0x1fU);
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_14) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_14__DOT__reg_out1 
            = (0x800000U | (0x7fffffU & vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0));
    }
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_13__DOT__reg_out1 
        = (0U != (0x7fffffU & vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_12__DOT__reg_out1 
        = (0U == (0x7fffffU & vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0));
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_8) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_8__DOT__reg_out1 
            = (0x3bfULL > vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_5__DOT__reg_out1);
    }
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_54__DOT__reg_out1 
        = (1U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i2_fu___05F_float_adde8m23b_127nih_501195_503543 
                 >> 0xbU));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_40__DOT__reg_out1 
        = (1U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i2_fu___05F_float_adde8m23b_127nih_501195_503543 
                 >> 3U));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_32__DOT__reg_out1 
        = (1U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i2_fu___05F_float_adde8m23b_127nih_501195_503543 
                 >> 0x13U));
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_8) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_8__DOT__reg_out1 
            = (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_and_expr_FU_32_32_32_162_i1_fu___05F_float_adde8m23b_127nih_501195_501278 
               >> 0x1fU);
    }
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_13) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_13__DOT__reg_out1 
            = (1U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_and_expr_FU_32_32_32_162_i0_fu___05F_float_adde8m23b_127nih_501195_501268 
                     >> 0x1dU));
    }
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_12) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_12__DOT__reg_out1 
            = (1U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_and_expr_FU_32_32_32_162_i0_fu___05F_float_adde8m23b_127nih_501195_501268 
                     >> 0x1cU));
    }
    vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__0__KET____DOT__Wready_reg 
        = vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__0__KET____DOT__Wready;
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_7) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_7__DOT__reg_out1 
            = (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_and_expr_FU_32_32_32_162_i0_fu___05F_float_adde8m23b_127nih_501195_501268 
               >> 0x1fU);
    }
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_55__DOT__reg_out1 
        = (1U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i2_fu___05F_float_adde8m23b_127nih_501195_503543 
                 >> 0xcU));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_41__DOT__reg_out1 
        = (1U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i2_fu___05F_float_adde8m23b_127nih_501195_503543 
                 >> 4U));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_33__DOT__reg_out1 
        = (1U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i2_fu___05F_float_adde8m23b_127nih_501195_503543 
                 >> 0x14U));
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_18) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_18__DOT__reg_out1 
            = (0x3ffU & ((IData)(0x381U) + ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_11__DOT__reg_out1) 
                                            + (0xffU 
                                               & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0 
                                                  >> 0x17U)))));
    }
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_10) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_10__DOT__reg_out1 
            = (1U & (4U >> (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_2__DOT__reg_out1) 
                             << 1U) | (0x3bfULL > vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_5__DOT__reg_out1))));
    }
    vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__0__KET____DOT__Rready = 0U;
    vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__0__KET____DOT__Rdata = 0U;
    if (vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__rst) {
        vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__0__KET____DOT__queue_counter 
            = vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__0__KET____DOT__queue_counter_next;
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Controller_i__DOT___present_state 
            = vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Controller_i__DOT___next_state;
    } else {
        vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__0__KET____DOT__queue_counter = 0U;
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Controller_i__DOT___present_state = 1U;
    }
    if ((((~ (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT____VdfgTmp_hca893bdf__0)) 
          & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__fuselector_BMEMORY_CTRLN_83_i0_LOAD)) 
         & (0x40000000U <= vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__0__KET____DOT__Waddr))) {
        __Vfunc_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__read_a__3__addr 
            = vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__0__KET____DOT__Waddr;
        Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__m_read_TOP(3U, __Vtask_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__m_read__4__data, 0x20U, __Vfunc_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__read_a__3__addr, 0U, __Vtask_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__m_read__4__Vfuncout);
        VL_ASSIGN_W(4096,__Vfunc_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__read_a__3___data, __Vtask_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__m_read__4__data);
        vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__0__KET____DOT__Rready = 1U;
        __Vfunc_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__read_a__3__Vfuncout 
            = __Vfunc_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__read_a__3___data[0U];
        vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__0__KET____DOT__read_channel__DOT__read_channel__DOT__data 
            = __Vfunc_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__read_a__3__Vfuncout;
        vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__0__KET____DOT__Rdata 
            = vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__0__KET____DOT__read_channel__DOT__read_channel__DOT__data;
    }
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state 
        = ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__rst)
            ? (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___next_state)
            : 0x2000U);
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_46__DOT__reg_out1 
        = (1U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i2_fu___05F_float_adde8m23b_127nih_501195_503543 
                 >> 0xdU));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_7__DOT__reg_out1 
        = (vlSelf->bambu_testbench__DOT__system__DOT__if_default_P1__DOT__val 
           + ((((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_5__DOT__reg_out1) 
                + vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_3__DOT__reg_out1) 
               << 6U) | ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_4__DOT__reg_out1) 
                         << 2U)));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_50__DOT__reg_out1 
        = (1U & vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i0_fu___05F_float_adde8m23b_127nih_501195_501582);
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_47__DOT__reg_out1 
        = (1U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i2_fu___05F_float_adde8m23b_127nih_501195_503543 
                 >> 0xeU));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_51__DOT__reg_out1 
        = (1U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i0_fu___05F_float_adde8m23b_127nih_501195_501582 
                 >> 1U));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_48__DOT__reg_out1 
        = (1U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i2_fu___05F_float_adde8m23b_127nih_501195_503543 
                 >> 0xfU));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_52__DOT__reg_out1 
        = (1U & vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i2_fu___05F_float_adde8m23b_127nih_501195_503543);
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_49__DOT__reg_out1 
        = (1U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i2_fu___05F_float_adde8m23b_127nih_501195_503543 
                 >> 0x10U));
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_10) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_10__DOT__reg_out1 
            = (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_35__DOT__reg_out1 
               >> 0x1fU);
    }
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_38__DOT__reg_out1 
        = (1U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i2_fu___05F_float_adde8m23b_127nih_501195_503543 
                 >> 1U));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_30__DOT__reg_out1 
        = (1U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i2_fu___05F_float_adde8m23b_127nih_501195_503543 
                 >> 0x11U));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_56__DOT__reg_out1 
        = (1U & (0x220527U >> ((0x10U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i2_fu___05F_float_adde8m23b_127nih_501195_503543 
                                         >> 0x10U)) 
                               | ((8U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i2_fu___05F_float_adde8m23b_127nih_501195_503543 
                                         >> 1U)) | 
                                  ((4U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i2_fu___05F_float_adde8m23b_127nih_501195_503543 
                                          >> 0x11U)) 
                                   | ((2U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i2_fu___05F_float_adde8m23b_127nih_501195_503543 
                                             >> 2U)) 
                                      | (0U == (0xffffU 
                                                & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_ior_concat_expr_FU_166_i0_fu___05F_float_adde8m23b_127nih_501195_501585 
                                                   >> 0xbU)))))))));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_39__DOT__reg_out1 
        = (1U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i2_fu___05F_float_adde8m23b_127nih_501195_503543 
                 >> 2U));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_31__DOT__reg_out1 
        = (1U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i2_fu___05F_float_adde8m23b_127nih_501195_503543 
                 >> 0x12U));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_42__DOT__reg_out1 
        = (1U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i2_fu___05F_float_adde8m23b_127nih_501195_503543 
                 >> 5U));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_34__DOT__reg_out1 
        = (1U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i2_fu___05F_float_adde8m23b_127nih_501195_503543 
                 >> 0x15U));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_43__DOT__reg_out1 
        = (1U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i2_fu___05F_float_adde8m23b_127nih_501195_503543 
                 >> 6U));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_35__DOT__reg_out1 
        = (1U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i2_fu___05F_float_adde8m23b_127nih_501195_503543 
                 >> 0x16U));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_44__DOT__reg_out1 
        = (1U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i2_fu___05F_float_adde8m23b_127nih_501195_503543 
                 >> 7U));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_36__DOT__reg_out1 
        = (1U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i2_fu___05F_float_adde8m23b_127nih_501195_503543 
                 >> 0x17U));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_45__DOT__reg_out1 
        = (1U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i2_fu___05F_float_adde8m23b_127nih_501195_503543 
                 >> 8U));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_37__DOT__reg_out1 
        = (1U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i2_fu___05F_float_adde8m23b_127nih_501195_503543 
                 >> 0x18U));
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_16) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_16__DOT__reg_out1 
            = (1U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_9__DOT__reg_out1 
                     >> 0x1dU));
    }
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_15) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_15__DOT__reg_out1 
            = (1U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_9__DOT__reg_out1 
                     >> 0x1cU));
    }
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_9) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_9__DOT__reg_out1 
            = (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_9__DOT__reg_out1 
               >> 0x1fU);
    }
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_5__DOT__reg_out1 
        = (0xffffffU & ((0x800000U & ((IData)((0xfffff5f4ffffffffULL 
                                               >> (
                                                   (0x20U 
                                                    & ((IData)(
                                                               (0x8000000000000000ULL 
                                                                >> 
                                                                (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_47_i0_fu___05F_float_adde8m23b_127nih_501195_510578) 
                                                                  << 5U) 
                                                                 | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_46_i0_fu___05F_float_adde8m23b_127nih_501195_510575) 
                                                                     << 4U) 
                                                                    | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_45_i0_fu___05F_float_adde8m23b_127nih_501195_510572) 
                                                                        << 3U) 
                                                                       | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_44_i0_fu___05F_float_adde8m23b_127nih_501195_510569) 
                                                                           << 2U) 
                                                                          | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_43_i0_fu___05F_float_adde8m23b_127nih_501195_510566) 
                                                                              << 1U) 
                                                                             | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_42_i0_fu___05F_float_adde8m23b_127nih_501195_510563)))))))) 
                                                       << 5U)) 
                                                   | ((0x10U 
                                                       & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_and_expr_FU_32_32_32_162_i0_fu___05F_float_adde8m23b_127nih_501195_501268 
                                                          >> 0x18U)) 
                                                      | ((8U 
                                                          & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_9__DOT__reg_out1 
                                                             >> 0x19U)) 
                                                         | (IData)(vlSelf->__VdfgTmp_h4ab71bb9__0)))))) 
                                      << 0x17U)) | 
                        (0x7fffffU & vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_ior_expr_FU_32_32_32_176_i0_fu___05F_float_adde8m23b_127nih_501195_501275)));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_58__DOT__reg_out1 
        = (0x7fffffffU & ((((1U & (IData)((0xffffffff00008000ULL 
                                           >> (IData)(vlSelf->__VdfgTmp_h01c7106c__0))))
                             ? 0U : (0xffU & (((IData)(1U) 
                                               + (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_6__DOT__reg_out1)) 
                                              - (0x1fU 
                                                 & ((((((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_29__DOT__reg_out1) 
                                                        << 4U) 
                                                       | (1U 
                                                          & (0x110fdd0fU 
                                                             >> (IData)(vlSelf->__VdfgTmp_h69898377__0)))) 
                                                      | (0xfU 
                                                         & ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_119_i0_fu___05F_float_adde8m23b_127nih_501195_503708) 
                                                            << 3U))) 
                                                     | (7U 
                                                        & ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_118_i0_fu___05F_float_adde8m23b_127nih_501195_503699) 
                                                           << 2U))) 
                                                    | (3U 
                                                       & ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_117_i0_fu___05F_float_adde8m23b_127nih_501195_503690) 
                                                          << 1U))))))) 
                           << 0x17U) | (0x7fffffU & 
                                        (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_lshift_expr_FU_64_64_64_195_i0_fu___05F_float_adde8m23b_127nih_501195_501802 
                                         >> 3U))));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_ui_lshift_expr_FU_64_64_64_106_i0_fu_forward_kernel_500073_510849 
        = (0x7fffffffffffULL & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_25__DOT__reg_out1 
                                << (1U & (1U >> (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_26__DOT__reg_out1)))));
    vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__start_next 
        = vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__start;
    vlSelf->bambu_testbench__DOT__system__DOT__sig_P0 
        = vlSelf->bambu_testbench__DOT__system__DOT__if_default_P0__DOT__val;
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_28__DOT__reg_out1 
        = (0U != vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_4__DOT__reg_out1);
    vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT____VdfgTmp_h1e9c198a__0 
        = ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__1__KET____DOT__Rready) 
           | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__1__KET____DOT__Wready_reg));
    vlSelf->bambu_testbench__DOT__system__DOT__sig_P2 
        = vlSelf->bambu_testbench__DOT__system__DOT__if_default_P2__DOT__val;
    vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_succ_next 
        = vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_succ;
    vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__rst_count_next 
        = vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__rst_count;
    if ((1U & (~ ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state) 
                  >> 6U)))) {
        if ((1U & (~ ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state) 
                      >> 5U)))) {
            if ((1U & (~ ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state) 
                          >> 4U)))) {
                if ((1U & (~ ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state) 
                              >> 3U)))) {
                    if ((4U & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state))) {
                        if ((1U & (~ ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state) 
                                      >> 1U)))) {
                            if ((1U & (~ (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state)))) {
                                vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__start_next = 0U;
                            }
                        }
                    } else if ((2U & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state))) {
                        if ((1U & (~ (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state)))) {
                            if (VL_GTES_III(32, 1U, vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__rst_count)) {
                                if ((1U != vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__rst_count)) {
                                    vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__start_next = 1U;
                                }
                            }
                        }
                    }
                    if ((1U & (~ ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state) 
                                  >> 2U)))) {
                        if ((2U & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state))) {
                            if ((1U & (~ (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state)))) {
                                if (VL_LTS_III(32, 1U, vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__rst_count)) {
                                    vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__rst_count_next 
                                        = (vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__rst_count 
                                           - (IData)(1U));
                                } else if ((1U == vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__rst_count)) {
                                    vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__rst_count_next = 0U;
                                }
                            }
                        } else if ((1U & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state))) {
                            if ((2U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_succ))) {
                                vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__rst_count_next = 1U;
                            }
                        }
                    }
                }
            }
        }
    }
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_ui_mult_expr_FU_32_32_32_0_109_i0_fu_forward_kernel_500073_510825 
        = (0xffffffffffffULL & ((QData)((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_19__DOT__reg_out1)) 
                                * (QData)((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_14__DOT__reg_out1))));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_UUdata_converter_FU_38_i0_fu_forward_kernel_500073_510858 
        = (0x3ffU & ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_18__DOT__reg_out1) 
                     + (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_27__DOT__reg_out1)));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_11__DOT__reg_out1 
        = (0xffU & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0 
                    >> 0x17U));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT____Vcellinp__fu_forward_kernel_500073_503980__in1 
        = (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_10__DOT__reg_out1) 
            << 1U) | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_8__DOT__reg_out1));
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_2) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_2__DOT__reg_out1 
            = (0xfULL > vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_0__DOT__reg_out1);
    }
    vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT____VdfgTmp_h6ea6f667__0 
        = ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__0__KET____DOT__Rready) 
           | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__0__KET____DOT__Wready_reg));
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_5) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_5__DOT__reg_out1 
            = vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_MUX_168_reg_5_0_0_0;
    }
    vlSelf->bambu_testbench__DOT__system__DOT__if_default_P1__DOT__val 
        = vlSelf->bambu_testbench__DOT__system__DOT__sig_P1;
    if (vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__setup) {
        Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__if_default_P1__DOT__m_utils__DOT__m_read_TOP(1U, __Vtask_bambu_testbench__DOT__system__DOT__if_default_P1__DOT__m_utils__DOT__m_read__14__data, 0x20U, 0U, 0U, __Vtask_bambu_testbench__DOT__system__DOT__if_default_P1__DOT__m_utils__DOT__m_read__14__Vfuncout);
        VL_ASSIGN_W(4096,__Vfunc_bambu_testbench__DOT__system__DOT__if_default_P1__DOT__m_utils__DOT__read__13___data, __Vtask_bambu_testbench__DOT__system__DOT__if_default_P1__DOT__m_utils__DOT__m_read__14__data);
        __Vfunc_bambu_testbench__DOT__system__DOT__if_default_P1__DOT__m_utils__DOT__read__13__Vfuncout 
            = __Vfunc_bambu_testbench__DOT__system__DOT__if_default_P1__DOT__m_utils__DOT__read__13___data[0U];
        vlSelf->bambu_testbench__DOT__system__DOT__if_default_P1__DOT__val 
            = __Vfunc_bambu_testbench__DOT__system__DOT__if_default_P1__DOT__m_utils__DOT__read__13__Vfuncout;
    }
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_3) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_3__DOT__reg_out1 
            = (0x3ffffffU & (IData)((vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_0__DOT__reg_out1 
                                     >> 4U)));
    }
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_4) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_4__DOT__reg_out1 
            = (0xfU & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_0__DOT__reg_out1));
    }
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_8 = 0U;
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_10 = 0U;
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_1 = 0U;
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_14 = 0U;
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_18 = 0U;
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_23 = 0U;
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_24 = 0U;
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__selector_MUX_168_reg_5_0_0_0 = 0U;
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__selector_MUX_136_reg_0_0_0_0 = 0U;
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__selector_MUX_1_BMEMORY_CTRLN_83_i0_1_1_0 = 0U;
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__selector_MUX_1_BMEMORY_CTRLN_83_i0_1_0_1 = 0U;
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__selector_MUX_1_BMEMORY_CTRLN_83_i0_1_0_0 = 0U;
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__fuselector_BMEMORY_CTRLN_83_i0_LOAD = 0U;
    if (((((((((0x2000U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state)) 
               | (0x800U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) 
              | (0x1000U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) 
             | (1U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) 
            | (2U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) 
           | (4U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) 
          | (8U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) 
         | (0x10U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state)))) {
        if ((0x2000U != (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
            if ((0x800U != (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                if ((0x1000U != (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                    if ((1U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_8 = 1U;
                        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_10 = 1U;
                        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__selector_MUX_168_reg_5_0_0_0 = 1U;
                        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__selector_MUX_1_BMEMORY_CTRLN_83_i0_1_0_1 = 1U;
                    }
                    if ((1U != (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                        if ((2U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                            vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_14 = 1U;
                            vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__selector_MUX_1_BMEMORY_CTRLN_83_i0_1_1_0 = 1U;
                            vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__selector_MUX_1_BMEMORY_CTRLN_83_i0_1_0_0 = 1U;
                        }
                        if ((2U != (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                            if ((4U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                                vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_18 = 1U;
                                vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_23 = 1U;
                                vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_24 = 1U;
                            }
                        }
                    }
                }
            }
            if ((0x800U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_1 = 1U;
                vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__selector_MUX_136_reg_0_0_0_0 = 1U;
                vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__fuselector_BMEMORY_CTRLN_83_i0_LOAD = 1U;
            } else if ((0x1000U != (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                if ((1U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__fuselector_BMEMORY_CTRLN_83_i0_LOAD = 1U;
                } else if ((2U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__fuselector_BMEMORY_CTRLN_83_i0_LOAD = 1U;
                }
            }
        }
    } else if ((0x20U != (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
        if ((0x40U != (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
            if ((0x80U != (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                if ((0x100U != (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                    if ((0x200U != (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                        if ((0x400U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                            vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__selector_MUX_1_BMEMORY_CTRLN_83_i0_1_1_0 = 1U;
                        }
                    }
                }
            }
        }
    }
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__selector_IN_UNBOUNDED_forward_kernel_500073_500104 = 0U;
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__fuselector_BMEMORY_CTRLN_83_i0_STORE = 0U;
    if ((1U & (~ ((((((((0x2000U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state)) 
                        | (0x800U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) 
                       | (0x1000U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) 
                      | (1U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) 
                     | (2U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) 
                    | (4U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) 
                   | (8U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) 
                  | (0x10U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state)))))) {
        if ((0x20U != (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
            if ((0x40U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__selector_IN_UNBOUNDED_forward_kernel_500073_500104 = 1U;
            }
            if ((0x40U != (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                if ((0x80U != (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                    if ((0x100U != (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                        if ((0x200U != (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                            if ((0x400U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                                vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__fuselector_BMEMORY_CTRLN_83_i0_STORE = 1U;
                            }
                        }
                    }
                }
            }
        }
    }
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_35) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_35__DOT__reg_out1 
            = ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_22__DOT__reg_out1)
                ? 0xffc00000U : ((1U & (0xccccc8ccU 
                                        >> (IData)(vlSelf->__VdfgTmp_hfa8950b8__0)))
                                  ? ((1U & (0x4000U 
                                            >> (IData)(vlSelf->__VdfgTmp_hfa8950b8__0)))
                                      ? vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_29__DOT__reg_out1
                                      : vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_20__DOT__reg_out1)
                                  : vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_21__DOT__reg_out1));
    }
}

extern const VlUnpacked<CData/*0:0*/, 32> Vbambu_testbench__ConstPool__TABLE_h1826ca45_0;
extern const VlUnpacked<CData/*3:0*/, 32> Vbambu_testbench__ConstPool__TABLE_ha8015fa6_0;

VL_INLINE_OPT void Vbambu_testbench___024root___nba_sequent__TOP__1(Vbambu_testbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbambu_testbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbambu_testbench___024root___nba_sequent__TOP__1\n"); );
    // Init
    CData/*0:0*/ bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_104_i0_fu___05F_float_adde8m23b_127nih_501195_510621;
    bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_104_i0_fu___05F_float_adde8m23b_127nih_501195_510621 = 0;
    CData/*0:0*/ bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_105_i0_fu___05F_float_adde8m23b_127nih_501195_510624;
    bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_105_i0_fu___05F_float_adde8m23b_127nih_501195_510624 = 0;
    CData/*0:0*/ bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_106_i0_fu___05F_float_adde8m23b_127nih_501195_510627;
    bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_106_i0_fu___05F_float_adde8m23b_127nih_501195_510627 = 0;
    CData/*0:0*/ bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_111_i0_fu___05F_float_adde8m23b_127nih_501195_510639;
    bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_111_i0_fu___05F_float_adde8m23b_127nih_501195_510639 = 0;
    QData/*50:0*/ bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_cond_expr_FU_64_64_64_64_181_i1_fu___05F_float_adde8m23b_127nih_501195_501691;
    bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_cond_expr_FU_64_64_64_64_181_i1_fu___05F_float_adde8m23b_127nih_501195_501691 = 0;
    QData/*54:0*/ bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_cond_expr_FU_64_64_64_64_181_i2_fu___05F_float_adde8m23b_127nih_501195_501726;
    bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_cond_expr_FU_64_64_64_64_181_i2_fu___05F_float_adde8m23b_127nih_501195_501726 = 0;
    CData/*7:0*/ bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_minus_expr_FU_8_8_8_201_i0_fu___05F_float_adde8m23b_127nih_501195_501436;
    bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_minus_expr_FU_8_8_8_201_i0_fu___05F_float_adde8m23b_127nih_501195_501436 = 0;
    CData/*4:0*/ __Vtableidx1;
    __Vtableidx1 = 0;
    // Body
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_9) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_9__DOT__reg_out1 
            = vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_6__DOT__reg_out1;
    }
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_6) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_6__DOT__reg_out1 
            = (0xffU & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_ior_expr_FU_32_32_32_176_i0_fu___05F_float_adde8m23b_127nih_501195_501275 
                        >> 0x17U));
    }
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_29__DOT__reg_out1 
        = (0U == (0xffffU & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_ior_concat_expr_FU_166_i0_fu___05F_float_adde8m23b_127nih_501195_501585 
                             >> 0xbU)));
    vlSelf->__VdfgTmp_hcdb08d50__0 = (((0U != (0x7fffffU 
                                               & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_ui_lshift_expr_FU_64_64_64_106_i0_fu_forward_kernel_500073_510849))) 
                                       << 2U) | ((2U 
                                                  & ((IData)(
                                                             (0x7fffffffffffULL 
                                                              & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_ui_lshift_expr_FU_64_64_64_106_i0_fu_forward_kernel_500073_510849 
                                                                 >> 0x18U))) 
                                                     << 1U)) 
                                                 | (1U 
                                                    & (IData)(
                                                              (0x7fffffffffffULL 
                                                               & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_ui_lshift_expr_FU_64_64_64_106_i0_fu_forward_kernel_500073_510849 
                                                                  >> 0x17U))))));
    vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT____VdfgTmp_h3be9c1ef__0 
        = ((0U != (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__1__KET____DOT__queue_counter)) 
           & (3U == ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__1__KET____DOT__queue_counter) 
                     - (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT____VdfgTmp_h1e9c198a__0))));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_2 = 0U;
    vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__1__KET____DOT__queue_counter_next 
        = (3U & ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__1__KET____DOT__queue_counter) 
                 - ((0x7fffffffU & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT____VdfgTmp_h1e9c198a__0)) 
                    | ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT____VdfgTmp_h6ea6f667__0) 
                       >> 1U))));
    vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT____VdfgTmp_h9ddaf863__0 
        = ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__0__KET____DOT__queue_counter) 
           - (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT____VdfgTmp_h6ea6f667__0));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_5 = 0U;
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_3 = 0U;
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_4 = 0U;
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__BMEMORY_CTRLN_83_i0__DOT____VdfgTmp_h9c0114c5__0 
        = ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__fuselector_BMEMORY_CTRLN_83_i0_LOAD) 
           | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__fuselector_BMEMORY_CTRLN_83_i0_STORE));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_35 = 0U;
    if ((1U & (~ ((((((((0x2000U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state)) 
                        | (0x800U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) 
                       | (0x1000U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) 
                      | (1U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) 
                     | (2U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) 
                    | (4U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) 
                   | (8U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) 
                  | (0x10U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state)))))) {
        if ((0x20U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
            vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_35 = 1U;
        }
    }
    vlSelf->__VdfgTmp_hfa8950b8__0 = (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_34__DOT__reg_out1) 
                                       << 4U) | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_24__DOT__reg_out1) 
                                                  << 3U) 
                                                 | ((4U 
                                                     & ((0x1555U 
                                                         >> 
                                                         (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_33__DOT__reg_out1) 
                                                           << 3U) 
                                                          | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_32__DOT__reg_out1) 
                                                              << 2U) 
                                                             | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_31__DOT__reg_out1) 
                                                                 << 1U) 
                                                                | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_30__DOT__reg_out1))))) 
                                                        << 2U)) 
                                                    | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_23__DOT__reg_out1) 
                                                        << 1U) 
                                                       | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_28__DOT__reg_out1)))));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_9 = 0U;
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_4__DOT__reg_out1 
        = (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_ior_expr_FU_0_32_32_168_i0_fu___05F_float_adde8m23b_127nih_501195_501465 
           & (~ (0xffffffU & (((IData)(0x3ffffffU) 
                               << (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_ior_expr_FU_8_8_8_177_i0_fu___05F_float_adde8m23b_127nih_501195_501506)) 
                              >> 2U))));
    vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT____VdfgTmp_hca893bdf__0 
        = ((0U != (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__0__KET____DOT__queue_counter)) 
           & (3U == vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT____VdfgTmp_h9ddaf863__0));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_MUX_168_reg_5_0_0_0 
        = ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__selector_MUX_168_reg_5_0_0_0)
            ? (1ULL + vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_5__DOT__reg_out1)
            : 0ULL);
    vlSelf->bambu_testbench__DOT__system__DOT__sig_P1 
        = vlSelf->bambu_testbench__DOT__system__DOT__if_default_P1__DOT__val;
    vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__setup 
        = vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__setup_next;
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_0) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_0__DOT__reg_out1 
            = vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_MUX_136_reg_0_0_0_0;
    }
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_21) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_21__DOT__reg_out1 
            = (0x7f800000U | ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_UUdata_converter_FU_15_i0_fu_forward_kernel_500073_510747) 
                              << 0x1fU));
    }
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_22) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_22__DOT__reg_out1 
            = (1U & (4U >> (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_lut_expr_FU_68_i0_fu_forward_kernel_500073_511134) 
                             << 1U) | (1U & (0x10fU 
                                             >> (IData)(vlSelf->__VdfgTmp_h6e163198__0))))));
    }
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_29__DOT__reg_out1 
        = ((0x7fffffffU & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_113_i1_fu_forward_kernel_500073_510909)) 
           | vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_20__DOT__reg_out1);
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_6) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_6__DOT__reg_out1 
            = ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__selector_MUX_169_reg_6_0_0_0)
                ? vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0
                : vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_36__DOT__reg_out1);
    }
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_cond_expr_FU_64_64_64_64_181_i0_fu___05F_float_adde8m23b_127nih_501195_501658 
        = ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_29__DOT__reg_out1)
            ? vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_27__DOT__reg_out1
            : (QData)((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_26__DOT__reg_out1)));
    vlSelf->__VdfgTmp_h4631f68b__0 = (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_34__DOT__reg_out1) 
                                       << 2U) | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_42__DOT__reg_out1) 
                                                  << 1U) 
                                                 | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_29__DOT__reg_out1)));
    vlSelf->__VdfgTmp_h1f3e2f54__0 = (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_36__DOT__reg_out1) 
                                       << 2U) | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_44__DOT__reg_out1) 
                                                  << 1U) 
                                                 | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_29__DOT__reg_out1)));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_0 = 0U;
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_21 = 0U;
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_22 = 0U;
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_113_i1_fu_forward_kernel_500073_510909 
        = (0x1ffffffffULL & (((QData)((IData)((0x7fffffU 
                                               & (IData)(
                                                         (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_ui_lshift_expr_FU_64_64_64_106_i0_fu_forward_kernel_500073_510849 
                                                          >> 0x18U))))) 
                              | ((QData)((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_UUdata_converter_FU_38_i0_fu_forward_kernel_500073_510858)) 
                                 << 0x17U)) + (QData)((IData)(
                                                              (1U 
                                                               & (0xa8U 
                                                                  >> (IData)(vlSelf->__VdfgTmp_hcdb08d50__0)))))));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__selector_MUX_169_reg_6_0_0_0 = 0U;
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_6 = 0U;
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0 
        = (vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__0__KET____DOT__Rdata 
           | (0xffU & ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__Sout_Rdata_ram) 
                       & (- (IData)((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__Sout_DataRdy))))));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_119_i0_fu___05F_float_adde8m23b_127nih_501195_503708 
        = (1U & (IData)((0x3fffffffffffffULL & (0x22052700000000ULL 
                                                >> 
                                                ((0x20U 
                                                  & ((IData)(
                                                             (0x3fffffffffffffULL 
                                                              & (0x22052700000000ULL 
                                                                 >> 
                                                                 ((0x20U 
                                                                   & ((IData)(
                                                                              (0x7fffffffffffffULL 
                                                                               & (0x50035300000000ULL 
                                                                                >> 
                                                                                (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_56__DOT__reg_out1) 
                                                                                << 5U) 
                                                                                | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_31__DOT__reg_out1) 
                                                                                << 4U) 
                                                                                | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_39__DOT__reg_out1) 
                                                                                << 3U) 
                                                                                | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_29__DOT__reg_out1) 
                                                                                << 2U) 
                                                                                | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_30__DOT__reg_out1) 
                                                                                << 1U) 
                                                                                | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_38__DOT__reg_out1))))))))) 
                                                                      << 5U)) 
                                                                  | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_37__DOT__reg_out1) 
                                                                      << 4U) 
                                                                     | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_45__DOT__reg_out1) 
                                                                         << 3U) 
                                                                        | (IData)(vlSelf->__VdfgTmp_h1f3e2f54__0))))))) 
                                                     << 5U)) 
                                                 | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_35__DOT__reg_out1) 
                                                     << 4U) 
                                                    | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_43__DOT__reg_out1) 
                                                        << 3U) 
                                                       | (IData)(vlSelf->__VdfgTmp_h4631f68b__0))))))));
    vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__setup_next 
        = vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__setup;
    if ((1U & (~ ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state) 
                  >> 6U)))) {
        if ((1U & (~ ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state) 
                      >> 5U)))) {
            if ((1U & (~ ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state) 
                          >> 4U)))) {
                if ((1U & (~ ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state) 
                              >> 3U)))) {
                    if ((1U & (~ ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state) 
                                  >> 2U)))) {
                        if ((2U & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state))) {
                            if ((1U & (~ (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state)))) {
                                vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__setup_next 
                                    = (VL_LTS_III(32, 1U, vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__rst_count)
                                        ? (0U == vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__rst_count)
                                        : (1U == vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__rst_count));
                            }
                        }
                    }
                }
            }
        }
    }
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_MUX_136_reg_0_0_0_0 
        = ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__selector_MUX_136_reg_0_0_0_0)
            ? (1ULL + vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_0__DOT__reg_out1)
            : 0ULL);
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_ui_pointer_plus_expr_FU_32_32_32_115_i2_fu_forward_kernel_500073_500127 
        = (vlSelf->bambu_testbench__DOT__system__DOT__if_default_P2__DOT__val 
           + ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_0__DOT__reg_out1) 
              << 2U));
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_20) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_20__DOT__reg_out1 
            = ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_UUdata_converter_FU_15_i0_fu_forward_kernel_500073_510747) 
               << 0x1fU);
    }
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_lut_expr_FU_64_i0_fu_forward_kernel_500073_511121 
        = ((0U >= ((0x20U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0 
                             >> 0x19U)) | ((0x10U & 
                                            (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0 
                                             >> 0x19U)) 
                                           | ((8U & 
                                               (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0 
                                                >> 0x19U)) 
                                              | ((4U 
                                                  & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0 
                                                     >> 0x19U)) 
                                                 | ((2U 
                                                     & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0 
                                                        >> 0x19U)) 
                                                    | (1U 
                                                       & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0 
                                                          >> 0x19U))))))))
            ? (1U & (1U >> ((0x20U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0 
                                      >> 0x19U)) | 
                            ((0x10U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0 
                                       >> 0x19U)) | 
                             ((8U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0 
                                     >> 0x19U)) | (
                                                   (4U 
                                                    & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0 
                                                       >> 0x19U)) 
                                                   | ((2U 
                                                       & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0 
                                                          >> 0x19U)) 
                                                      | (1U 
                                                         & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0 
                                                            >> 0x19U)))))))))
            : 0U);
    vlSelf->__VdfgTmp_h34d5e52a__0 = ((2U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0 
                                             >> 0x17U)) 
                                      | (1U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0 
                                               >> 0x17U)));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_36__DOT__reg_out1 
        = (((0x7fffffU & (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_61__DOT__reg_out1)
                            ? 0U : vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i1_fu___05F_float_adde8m23b_127nih_501195_502107) 
                          | vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_1__DOT__reg_out1)) 
            | vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_60__DOT__reg_out1) 
           | (0x7f800000U & ((IData)(((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_3__DOT__reg_out1)
                                       ? 0xffffffffffffffffULL
                                       : (QData)((IData)(
                                                         (0xffU 
                                                          & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i1_fu___05F_float_adde8m23b_127nih_501195_502107 
                                                             >> 0x17U)))))) 
                             << 0x17U)));
    bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_cond_expr_FU_64_64_64_64_181_i1_fu___05F_float_adde8m23b_127nih_501195_501691 
        = (0x7ffffffffffffULL & ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_119_i0_fu___05F_float_adde8m23b_127nih_501195_503708)
                                  ? (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_cond_expr_FU_64_64_64_64_181_i0_fu___05F_float_adde8m23b_127nih_501195_501658 
                                     << 8U) : vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_cond_expr_FU_64_64_64_64_181_i0_fu___05F_float_adde8m23b_127nih_501195_501658));
    bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_104_i0_fu___05F_float_adde8m23b_127nih_501195_510621 
        = (1U & (IData)((0xff55aa00d8d8d8d8ULL >> (
                                                   ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_119_i0_fu___05F_float_adde8m23b_127nih_501195_503708) 
                                                    << 5U) 
                                                   | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_47__DOT__reg_out1) 
                                                       << 4U) 
                                                      | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_50__DOT__reg_out1) 
                                                          << 3U) 
                                                         | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_35__DOT__reg_out1) 
                                                             << 2U) 
                                                            | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_43__DOT__reg_out1) 
                                                                << 1U) 
                                                               | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_29__DOT__reg_out1)))))))));
    bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_105_i0_fu___05F_float_adde8m23b_127nih_501195_510624 
        = (1U & (IData)((0xff55aa00d8d8d8d8ULL >> (
                                                   ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_119_i0_fu___05F_float_adde8m23b_127nih_501195_503708) 
                                                    << 5U) 
                                                   | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_48__DOT__reg_out1) 
                                                       << 4U) 
                                                      | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_51__DOT__reg_out1) 
                                                          << 3U) 
                                                         | (IData)(vlSelf->__VdfgTmp_h1f3e2f54__0)))))));
    bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_106_i0_fu___05F_float_adde8m23b_127nih_501195_510627 
        = (1U & (IData)((0xff55aa00d8d8d8d8ULL >> (
                                                   ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_119_i0_fu___05F_float_adde8m23b_127nih_501195_503708) 
                                                    << 5U) 
                                                   | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_49__DOT__reg_out1) 
                                                       << 4U) 
                                                      | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_52__DOT__reg_out1) 
                                                          << 3U) 
                                                         | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_37__DOT__reg_out1) 
                                                             << 2U) 
                                                            | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_45__DOT__reg_out1) 
                                                                << 1U) 
                                                               | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_29__DOT__reg_out1)))))))));
    vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT____VdfgTmp_h67aab006__0 
        = ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__BMEMORY_CTRLN_83_i0__DOT____VdfgTmp_h9c0114c5__0)
            ? ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__selector_MUX_1_BMEMORY_CTRLN_83_i0_1_1_0)
                ? ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__selector_MUX_1_BMEMORY_CTRLN_83_i0_1_0_0)
                    ? vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_7__DOT__reg_out1
                    : vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_1__DOT__reg_out1)
                : ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__selector_MUX_1_BMEMORY_CTRLN_83_i0_1_0_1)
                    ? (vlSelf->bambu_testbench__DOT__system__DOT__if_default_P0__DOT__val 
                       + ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_5__DOT__reg_out1) 
                          << 2U)) : vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_ui_pointer_plus_expr_FU_32_32_32_115_i2_fu_forward_kernel_500073_500127))
            : 0U);
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_20 = 0U;
    if (((((((((0x2000U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state)) 
               | (0x800U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) 
              | (0x1000U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) 
             | (1U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) 
            | (2U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) 
           | (4U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) 
          | (8U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) 
         | (0x10U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state)))) {
        if ((0x2000U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
            if (vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__start) {
                vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___next_state = 0x800U;
                vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_0 = 1U;
            } else {
                vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___next_state = 0x2000U;
            }
        } else if ((0x800U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
            vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___next_state = 0x1000U;
            vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_0 = 1U;
        } else {
            vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___next_state 
                = ((0x1000U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))
                    ? 1U : ((1U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))
                             ? 2U : ((2U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))
                                      ? 4U : ((4U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))
                                               ? 8U
                                               : ((8U 
                                                   == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))
                                                   ? 0x10U
                                                   : 0x20U)))));
        }
        if ((0x2000U != (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
            if ((0x800U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_2 = 1U;
                vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_3 = 1U;
                vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_4 = 1U;
            }
            if ((0x800U != (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                if ((0x1000U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_5 = 1U;
                    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__selector_MUX_169_reg_6_0_0_0 = 1U;
                    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_6 = 1U;
                } else if ((1U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_5 = 1U;
                }
                if ((0x1000U != (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                    if ((1U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_9 = 1U;
                    }
                    if ((1U != (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                        if ((2U != (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                            if ((4U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                                vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_21 = 1U;
                                vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_22 = 1U;
                                vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_20 = 1U;
                            }
                        }
                    }
                }
            }
        }
    } else {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___next_state 
            = ((0x20U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))
                ? 0x40U : ((0x40U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))
                            ? 0x80U : ((0x80U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))
                                        ? 0x100U : 
                                       ((0x100U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))
                                         ? 0x200U : 
                                        ((0x200U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))
                                          ? 0x400U : 
                                         ((0x400U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))
                                           ? ((1U == 
                                               (1U 
                                                & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT____Vcellinp__fu_forward_kernel_500073_503980__in1)))
                                               ? 1U
                                               : ((2U 
                                                   == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT____Vcellinp__fu_forward_kernel_500073_503980__in1))
                                                   ? 0x800U
                                                   : 0x4000U))
                                           : 0x2000U))))));
        if ((0x20U != (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
            if ((0x40U != (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                if ((0x80U != (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                    if ((0x100U != (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                        if ((0x200U != (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                            if ((0x400U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                                vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_6 = 1U;
                                if ((1U != (1U & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT____Vcellinp__fu_forward_kernel_500073_503980__in1)))) {
                                    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__wrenable_reg_6 = 0U;
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_UUdata_converter_FU_15_i0_fu_forward_kernel_500073_510747 
        = (1U & (6U >> ((2U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0 
                               >> 0x1eU)) | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_15__DOT__reg_out1))));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_lut_expr_FU_57_i0_fu_forward_kernel_500073_511100 
        = (1U & (0x80U >> ((4U & ((IData)((0x8000000000000000ULL 
                                           >> ((0x20U 
                                                & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0 
                                                   >> 0x19U)) 
                                               | ((0x10U 
                                                   & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0 
                                                      >> 0x19U)) 
                                                  | ((8U 
                                                      & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0 
                                                         >> 0x17U)) 
                                                     | ((4U 
                                                         & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0 
                                                            >> 0x17U)) 
                                                        | (IData)(vlSelf->__VdfgTmp_h34d5e52a__0))))))) 
                                  << 2U)) | ((2U & 
                                              (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0 
                                               >> 0x1bU)) 
                                             | (1U 
                                                & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0 
                                                   >> 0x1bU))))));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i1_fu___05F_float_adde8m23b_127nih_501195_502107 
        = (0x7fffffffU & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_58__DOT__reg_out1 
                          + (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_59__DOT__reg_out1)));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_118_i0_fu___05F_float_adde8m23b_127nih_501195_503699 
        = (1U & (1U >> (((IData)(bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_106_i0_fu___05F_float_adde8m23b_127nih_501195_510627) 
                         << 3U) | (((IData)(bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_105_i0_fu___05F_float_adde8m23b_127nih_501195_510624) 
                                    << 2U) | (((IData)(bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_104_i0_fu___05F_float_adde8m23b_127nih_501195_510621) 
                                               << 1U) 
                                              | (1U 
                                                 & (0x5500d8d8U 
                                                    >> 
                                                    (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_119_i0_fu___05F_float_adde8m23b_127nih_501195_503708) 
                                                      << 4U) 
                                                     | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_46__DOT__reg_out1) 
                                                         << 3U) 
                                                        | (IData)(vlSelf->__VdfgTmp_h4631f68b__0))))))))));
    vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__0__KET____DOT__Waddr 
        = ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT____VdfgTmp_hca893bdf__0)
            ? 0U : vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT____VdfgTmp_h67aab006__0);
    vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__0__KET____DOT__queue_counter_next 
        = (3U & (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__0__KET____DOT__queue_counter) 
                  + ((((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__fuselector_BMEMORY_CTRLN_83_i0_STORE) 
                       | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__fuselector_BMEMORY_CTRLN_83_i0_LOAD)) 
                      & ((~ (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT____VdfgTmp_hca893bdf__0)) 
                         & (0x40000000U <= vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT____VdfgTmp_h67aab006__0))) 
                     && ((0U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__0__KET____DOT__queue_counter))
                          ? 1U : (3U > vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT____VdfgTmp_h9ddaf863__0)))) 
                 - (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT____VdfgTmp_h6ea6f667__0)));
    vlSelf->__VdfgTmp_h6e163198__0 = (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_16__DOT__reg_out1) 
                                       << 3U) | ((4U 
                                                  & ((0xe0U 
                                                      >> 
                                                      (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_lut_expr_FU_57_i0_fu_forward_kernel_500073_511100) 
                                                        << 2U) 
                                                       | (((0U 
                                                            == 
                                                            (0x7fffffU 
                                                             & vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0)) 
                                                           << 1U) 
                                                          | (0U 
                                                             != 
                                                             (0x7fffffU 
                                                              & vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0))))) 
                                                     << 2U)) 
                                                 | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_12__DOT__reg_out1) 
                                                     << 1U) 
                                                    | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_13__DOT__reg_out1))));
    vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT____VdfgTmp_h752baccc__0 
        = ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__fuselector_BMEMORY_CTRLN_83_i0_STORE)
            ? vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_36__DOT__reg_out1
            : 0U);
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_60__DOT__reg_out1 
        = ((IData)((0xf4f4f4f4f4f45400ULL >> ((((0x1fU 
                                                 >= (IData)(vlSelf->__VdfgTmp_h01c7106c__0))
                                                 ? 
                                                (1U 
                                                 & (0xffff7fffU 
                                                    >> (IData)(vlSelf->__VdfgTmp_h01c7106c__0)))
                                                 : 0U) 
                                               << 5U) 
                                              | (IData)(vlSelf->__VdfgTmp_hd3e91219__0)))) 
           << 0x1fU);
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_3) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_3__DOT__reg_out1 
            = (1U & (0xeU >> (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_140_i0_fu___05F_float_adde8m23b_127nih_501195_510689) 
                               << 1U) | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_136_i0_fu___05F_float_adde8m23b_127nih_501195_510675))));
    }
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_1) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_1__DOT__reg_out1 
            = (0x400000U & ((0xefccaa00U >> (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_140_i0_fu___05F_float_adde8m23b_127nih_501195_510689) 
                                              << 4U) 
                                             | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_136_i0_fu___05F_float_adde8m23b_127nih_501195_510675) 
                                                 << 3U) 
                                                | ((4U 
                                                    & ((0xf4f45e0bU 
                                                        >> (IData)(vlSelf->__VdfgTmp_h648d1a24__0)) 
                                                       << 2U)) 
                                                   | (((0U 
                                                        != 
                                                        (0x7fffffU 
                                                         & vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_ior_expr_FU_32_32_32_176_i1_fu___05F_float_adde8m23b_127nih_501195_501285)) 
                                                       << 1U) 
                                                      | (0U 
                                                         != 
                                                         (0x7fffffU 
                                                          & vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_ior_expr_FU_32_32_32_176_i0_fu___05F_float_adde8m23b_127nih_501195_501275))))))) 
                            << 0x16U));
    }
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_61__DOT__reg_out1 
        = (1U & (IData)((0xffffff2fffffff0fULL >> (
                                                   ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_57__DOT__reg_out1) 
                                                    << 5U) 
                                                   | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_25__DOT__reg_out1) 
                                                       << 4U) 
                                                      | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_24__DOT__reg_out1) 
                                                          << 3U) 
                                                         | ((((0x1fU 
                                                               >= (IData)(vlSelf->__VdfgTmp_h01c7106c__0))
                                                               ? 
                                                              (1U 
                                                               & (0xffff7fffU 
                                                                  >> (IData)(vlSelf->__VdfgTmp_h01c7106c__0)))
                                                               : 0U) 
                                                             << 2U) 
                                                            | (IData)(vlSelf->__VdfgTmp_h331422dd__0))))))));
    bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_cond_expr_FU_64_64_64_64_181_i2_fu___05F_float_adde8m23b_127nih_501195_501726 
        = (0x7fffffffffffffULL & ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_118_i0_fu___05F_float_adde8m23b_127nih_501195_503699)
                                   ? (bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_cond_expr_FU_64_64_64_64_181_i1_fu___05F_float_adde8m23b_127nih_501195_501691 
                                      << 4U) : bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_cond_expr_FU_64_64_64_64_181_i1_fu___05F_float_adde8m23b_127nih_501195_501691));
    bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_111_i0_fu___05F_float_adde8m23b_127nih_501195_510639 
        = (1U & (0xe2U >> ((4U & ((0x5500d8d8U >> (
                                                   ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_119_i0_fu___05F_float_adde8m23b_127nih_501195_503708) 
                                                    << 4U) 
                                                   | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_55__DOT__reg_out1) 
                                                       << 3U) 
                                                      | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_33__DOT__reg_out1) 
                                                          << 2U) 
                                                         | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_41__DOT__reg_out1) 
                                                             << 1U) 
                                                            | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_29__DOT__reg_out1)))))) 
                                  << 2U)) | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_118_i0_fu___05F_float_adde8m23b_127nih_501195_503699) 
                                              << 1U) 
                                             | (IData)(bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_106_i0_fu___05F_float_adde8m23b_127nih_501195_510627)))));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_lut_expr_FU_68_i0_fu_forward_kernel_500073_511134 
        = (1U & (IData)((0xee00bef0fffffaf0ULL >> (
                                                   (0x20U 
                                                    & ((0xf110f00U 
                                                        >> 
                                                        (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_lut_expr_FU_64_i0_fu_forward_kernel_500073_511121) 
                                                          << 4U) 
                                                         | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_lut_expr_FU_57_i0_fu_forward_kernel_500073_511100) 
                                                             << 3U) 
                                                            | (((0U 
                                                                 != 
                                                                 (0x7fffffU 
                                                                  & vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__out_BMEMORY_CTRLN_83_i0_BMEMORY_CTRLN_83_i0)) 
                                                                << 2U) 
                                                               | (IData)(vlSelf->__VdfgTmp_h34d5e52a__0))))) 
                                                       << 5U)) 
                                                   | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_17__DOT__reg_out1) 
                                                       << 4U) 
                                                      | (IData)(vlSelf->__VdfgTmp_h6e163198__0))))));
    vlSelf->__VdfgTmp_h331422dd__0 = (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_19__DOT__reg_out1) 
                                       << 1U) | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_18__DOT__reg_out1));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_117_i0_fu___05F_float_adde8m23b_127nih_501195_503690 
        = (1U & (0x1dU >> (((IData)(bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_111_i0_fu___05F_float_adde8m23b_127nih_501195_510639) 
                            << 3U) | ((4U & ((0x5500d8d8U 
                                              >> (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_119_i0_fu___05F_float_adde8m23b_127nih_501195_503708) 
                                                   << 4U) 
                                                  | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_54__DOT__reg_out1) 
                                                      << 3U) 
                                                     | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_32__DOT__reg_out1) 
                                                         << 2U) 
                                                        | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_40__DOT__reg_out1) 
                                                            << 1U) 
                                                           | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_29__DOT__reg_out1)))))) 
                                             << 2U)) 
                                      | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_118_i0_fu___05F_float_adde8m23b_127nih_501195_503699) 
                                          << 1U) | (IData)(bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_105_i0_fu___05F_float_adde8m23b_127nih_501195_510624))))));
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_25) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_25__DOT__reg_out1 
            = vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_140_i0_fu___05F_float_adde8m23b_127nih_501195_510689;
    }
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_24) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_24__DOT__reg_out1 
            = vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_136_i0_fu___05F_float_adde8m23b_127nih_501195_510675;
    }
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_57__DOT__reg_out1 
        = (1U & (IData)((0xffffffffffffULL & (0xf40000000000ULL 
                                              >> (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_23__DOT__reg_out1) 
                                                   << 5U) 
                                                  | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_20__DOT__reg_out1) 
                                                      << 4U) 
                                                     | ((8U 
                                                         & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i2_fu___05F_float_adde8m23b_127nih_501195_503543 
                                                            >> 0x15U)) 
                                                        | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_11__DOT__reg_out1) 
                                                            << 2U) 
                                                           | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_14__DOT__reg_out1) 
                                                               << 1U) 
                                                              | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_2__DOT__reg_out1))))))))));
    vlSelf->__VdfgTmp_h69898377__0 = ((0x10U & ((0x5500d8d8U 
                                                 >> 
                                                 (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_119_i0_fu___05F_float_adde8m23b_127nih_501195_503708) 
                                                   << 4U) 
                                                  | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_53__DOT__reg_out1) 
                                                      << 3U) 
                                                     | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_31__DOT__reg_out1) 
                                                         << 2U) 
                                                        | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_39__DOT__reg_out1) 
                                                            << 1U) 
                                                           | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_29__DOT__reg_out1)))))) 
                                                << 4U)) 
                                      | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_117_i0_fu___05F_float_adde8m23b_127nih_501195_503690) 
                                          << 3U) | 
                                         (((IData)(bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_111_i0_fu___05F_float_adde8m23b_127nih_501195_510639) 
                                           << 2U) | 
                                          (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_118_i0_fu___05F_float_adde8m23b_127nih_501195_503699) 
                                            << 1U) 
                                           | (IData)(bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_104_i0_fu___05F_float_adde8m23b_127nih_501195_510621)))));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_14__DOT__reg_out1 
        = vlSelf->__Vdly__bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_14__DOT__reg_out1;
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_lshift_expr_FU_64_64_64_195_i0_fu___05F_float_adde8m23b_127nih_501195_501802 
        = (0x3ffffffU & ((IData)((0x1ffffffffffffffULL 
                                  & ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_117_i0_fu___05F_float_adde8m23b_127nih_501195_503690)
                                      ? (bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_cond_expr_FU_64_64_64_64_181_i2_fu___05F_float_adde8m23b_127nih_501195_501726 
                                         << 2U) : bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_cond_expr_FU_64_64_64_64_181_i2_fu___05F_float_adde8m23b_127nih_501195_501726))) 
                         << (1U & (0x110fdd0fU >> (IData)(vlSelf->__VdfgTmp_h69898377__0)))));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_23__DOT__reg_out1 
        = vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_135_i0_fu___05F_float_adde8m23b_127nih_501195_510672;
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_20) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_20__DOT__reg_out1 
            = vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_46_i0_fu___05F_float_adde8m23b_127nih_501195_510575;
    }
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_11__DOT__reg_out1 
        = (1U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_and_expr_FU_32_32_32_162_i0_fu___05F_float_adde8m23b_127nih_501195_501268 
                 >> 0x1aU));
    if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_2) {
        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_2__DOT__reg_out1 
            = vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_2_i0_fu___05F_float_adde8m23b_127nih_501195_501259;
    }
    __Vtableidx1 = (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__selector_IN_UNBOUNDED_forward_kernel_500073_500104) 
                     << 4U) | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Controller_i__DOT___present_state));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_1 
        = Vbambu_testbench__ConstPool__TABLE_h1826ca45_0
        [__Vtableidx1];
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_10 
        = Vbambu_testbench__ConstPool__TABLE_h1826ca45_0
        [__Vtableidx1];
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_12 
        = Vbambu_testbench__ConstPool__TABLE_h1826ca45_0
        [__Vtableidx1];
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_13 
        = Vbambu_testbench__ConstPool__TABLE_h1826ca45_0
        [__Vtableidx1];
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_15 
        = Vbambu_testbench__ConstPool__TABLE_h1826ca45_0
        [__Vtableidx1];
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_16 
        = Vbambu_testbench__ConstPool__TABLE_h1826ca45_0
        [__Vtableidx1];
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_17 
        = Vbambu_testbench__ConstPool__TABLE_h1826ca45_0
        [__Vtableidx1];
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_18 
        = Vbambu_testbench__ConstPool__TABLE_h1826ca45_0
        [__Vtableidx1];
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_19 
        = Vbambu_testbench__ConstPool__TABLE_h1826ca45_0
        [__Vtableidx1];
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_2 
        = Vbambu_testbench__ConstPool__TABLE_h1826ca45_0
        [__Vtableidx1];
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_20 
        = Vbambu_testbench__ConstPool__TABLE_h1826ca45_0
        [__Vtableidx1];
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_21 
        = Vbambu_testbench__ConstPool__TABLE_h1826ca45_0
        [__Vtableidx1];
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_22 
        = Vbambu_testbench__ConstPool__TABLE_h1826ca45_0
        [__Vtableidx1];
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_24 
        = Vbambu_testbench__ConstPool__TABLE_h1826ca45_0
        [__Vtableidx1];
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_25 
        = Vbambu_testbench__ConstPool__TABLE_h1826ca45_0
        [__Vtableidx1];
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_3 
        = Vbambu_testbench__ConstPool__TABLE_h1826ca45_0
        [__Vtableidx1];
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_6 
        = Vbambu_testbench__ConstPool__TABLE_h1826ca45_0
        [__Vtableidx1];
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_7 
        = Vbambu_testbench__ConstPool__TABLE_h1826ca45_0
        [__Vtableidx1];
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_8 
        = Vbambu_testbench__ConstPool__TABLE_h1826ca45_0
        [__Vtableidx1];
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__wrenable_reg_9 
        = Vbambu_testbench__ConstPool__TABLE_h1826ca45_0
        [__Vtableidx1];
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Controller_i__DOT___next_state 
        = Vbambu_testbench__ConstPool__TABLE_ha8015fa6_0
        [__Vtableidx1];
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_2_i0_fu___05F_float_adde8m23b_127nih_501195_501259 
        = ((0x7fffffffU & vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_9__DOT__reg_out1) 
           < (0x7fffffffU & vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_35__DOT__reg_out1));
    vlSelf->__VdfgTmp_h01c7106c__0 = ((0x20U & ((IData)(
                                                        (0xfffffffffffULL 
                                                         & (0xa0b00000000ULL 
                                                            >> 
                                                            ((0x20U 
                                                              & ((IData)(
                                                                         (0xe0808080e0e0e080ULL 
                                                                          >> 
                                                                          ((0x20U 
                                                                            & ((IData)(
                                                                                (0x3ffffffffffffffULL 
                                                                                & (0x33f0fff011f077fULL 
                                                                                >> 
                                                                                ((0x20U 
                                                                                & ((0xeef022f0U 
                                                                                >> (IData)(vlSelf->__VdfgTmp_h69898377__0)) 
                                                                                << 5U)) 
                                                                                | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_117_i0_fu___05F_float_adde8m23b_127nih_501195_503690) 
                                                                                << 4U) 
                                                                                | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_118_i0_fu___05F_float_adde8m23b_127nih_501195_503699) 
                                                                                << 3U) 
                                                                                | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_20__DOT__reg_out1) 
                                                                                << 2U) 
                                                                                | (IData)(vlSelf->__VdfgTmp_h331422dd__0)))))))) 
                                                                               << 5U)) 
                                                                           | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_119_i0_fu___05F_float_adde8m23b_127nih_501195_503708) 
                                                                               << 4U) 
                                                                              | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_21__DOT__reg_out1) 
                                                                                << 3U) 
                                                                                | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_17__DOT__reg_out1) 
                                                                                << 2U) 
                                                                                | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_22__DOT__reg_out1) 
                                                                                << 1U) 
                                                                                | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_29__DOT__reg_out1)))))))) 
                                                                 << 5U)) 
                                                             | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_13__DOT__reg_out1) 
                                                                 << 4U) 
                                                                | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_16__DOT__reg_out1) 
                                                                    << 3U) 
                                                                   | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_12__DOT__reg_out1) 
                                                                       << 2U) 
                                                                      | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_15__DOT__reg_out1) 
                                                                          << 1U) 
                                                                         | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_2__DOT__reg_out1))))))))) 
                                                << 5U)) 
                                      | ((0x10U & (
                                                   (0xeef022f0U 
                                                    >> (IData)(vlSelf->__VdfgTmp_h69898377__0)) 
                                                   << 4U)) 
                                         | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_117_i0_fu___05F_float_adde8m23b_127nih_501195_503690) 
                                             << 3U) 
                                            | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_118_i0_fu___05F_float_adde8m23b_127nih_501195_503699) 
                                                << 2U) 
                                               | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_119_i0_fu___05F_float_adde8m23b_127nih_501195_503708) 
                                                   << 1U) 
                                                  | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_29__DOT__reg_out1))))));
    vlSelf->__VdfgTmp_hd3e91219__0 = (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_8__DOT__reg_out1) 
                                       << 4U) | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_10__DOT__reg_out1) 
                                                  << 3U) 
                                                 | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_7__DOT__reg_out1) 
                                                     << 2U) 
                                                    | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_9__DOT__reg_out1) 
                                                        << 1U) 
                                                       | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_2__DOT__reg_out1)))));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_and_expr_FU_32_32_32_162_i1_fu___05F_float_adde8m23b_127nih_501195_501278 
        = ((- (IData)((1U & (IData)(VL_SHIFTRS_QQI(64,64,6, 
                                                   (VL_EXTENDS_QI(64,2, (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_2_i0_fu___05F_float_adde8m23b_127nih_501195_501259)) 
                                                    << 0x3fU), 0x3fU))))) 
           & vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_9__DOT__reg_out1);
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_and_expr_FU_32_32_32_162_i0_fu___05F_float_adde8m23b_127nih_501195_501268 
        = ((- (IData)((1U & (IData)(VL_SHIFTRS_QQI(64,64,6, 
                                                   (VL_EXTENDS_QI(64,2, (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_2_i0_fu___05F_float_adde8m23b_127nih_501195_501259)) 
                                                    << 0x3fU), 0x3fU))))) 
           & vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_35__DOT__reg_out1);
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i0_fu___05F_float_adde8m23b_127nih_501195_501582 
        = (0x7ffffffU & (((0x1bU >= (((0U != vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_4__DOT__reg_out1) 
                                      << 5U) | (IData)(vlSelf->__VdfgTmp_hd3e91219__0)))
                           ? (1U & (0xb0ba1f4U >> (
                                                   ((0U 
                                                     != vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_4__DOT__reg_out1) 
                                                    << 5U) 
                                                   | (IData)(vlSelf->__VdfgTmp_hd3e91219__0))))
                           : 0U) + vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_0__DOT__reg_out1));
    vlSelf->__VdfgTmp_h04849622__0 = ((0x10U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_and_expr_FU_32_32_32_162_i1_fu___05F_float_adde8m23b_127nih_501195_501278 
                                                >> 0x18U)) 
                                      | ((8U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_35__DOT__reg_out1 
                                                >> 0x19U)) 
                                         | ((4U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_and_expr_FU_32_32_32_162_i1_fu___05F_float_adde8m23b_127nih_501195_501278 
                                                   >> 0x19U)) 
                                            | ((2U 
                                                & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_35__DOT__reg_out1 
                                                   >> 0x1aU)) 
                                               | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_2_i0_fu___05F_float_adde8m23b_127nih_501195_501259)))));
    vlSelf->__VdfgTmp_hfc0a1d14__0 = ((0x10U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_and_expr_FU_32_32_32_162_i1_fu___05F_float_adde8m23b_127nih_501195_501278 
                                                >> 0x16U)) 
                                      | ((8U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_35__DOT__reg_out1 
                                                >> 0x17U)) 
                                         | ((4U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_and_expr_FU_32_32_32_162_i1_fu___05F_float_adde8m23b_127nih_501195_501278 
                                                   >> 0x17U)) 
                                            | ((2U 
                                                & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_35__DOT__reg_out1 
                                                   >> 0x18U)) 
                                               | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_2_i0_fu___05F_float_adde8m23b_127nih_501195_501259)))));
    vlSelf->__VdfgTmp_h8c900521__0 = ((0x10U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_and_expr_FU_32_32_32_162_i1_fu___05F_float_adde8m23b_127nih_501195_501278 
                                                >> 0x14U)) 
                                      | ((8U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_35__DOT__reg_out1 
                                                >> 0x15U)) 
                                         | ((4U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_and_expr_FU_32_32_32_162_i1_fu___05F_float_adde8m23b_127nih_501195_501278 
                                                   >> 0x15U)) 
                                            | ((2U 
                                                & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_35__DOT__reg_out1 
                                                   >> 0x16U)) 
                                               | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_2_i0_fu___05F_float_adde8m23b_127nih_501195_501259)))));
    vlSelf->__VdfgTmp_h6cbb337b__0 = ((0x10U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_and_expr_FU_32_32_32_162_i1_fu___05F_float_adde8m23b_127nih_501195_501278 
                                                >> 0x1aU)) 
                                      | ((8U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_35__DOT__reg_out1 
                                                >> 0x1bU)) 
                                         | ((4U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_and_expr_FU_32_32_32_162_i1_fu___05F_float_adde8m23b_127nih_501195_501278 
                                                   >> 0x1bU)) 
                                            | ((2U 
                                                & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_35__DOT__reg_out1 
                                                   >> 0x1cU)) 
                                               | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_2_i0_fu___05F_float_adde8m23b_127nih_501195_501259)))));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_ior_expr_FU_32_32_32_176_i1_fu___05F_float_adde8m23b_127nih_501195_501285 
        = (0x7fffffffU & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_and_expr_FU_32_32_32_162_i1_fu___05F_float_adde8m23b_127nih_501195_501278 
                          | ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_2_i0_fu___05F_float_adde8m23b_127nih_501195_501259)
                              ? 0U : vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_35__DOT__reg_out1)));
    vlSelf->__VdfgTmp_h648d1a24__0 = ((0x10U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_and_expr_FU_32_32_32_162_i1_fu___05F_float_adde8m23b_127nih_501195_501278 
                                                >> 0x1bU)) 
                                      | ((8U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_35__DOT__reg_out1 
                                                >> 0x1cU)) 
                                         | ((4U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_and_expr_FU_32_32_32_162_i0_fu___05F_float_adde8m23b_127nih_501195_501268 
                                                   >> 0x1dU)) 
                                            | ((2U 
                                                & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_9__DOT__reg_out1 
                                                   >> 0x1eU)) 
                                               | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_2_i0_fu___05F_float_adde8m23b_127nih_501195_501259)))));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_ior_expr_FU_32_32_32_176_i0_fu___05F_float_adde8m23b_127nih_501195_501275 
        = (0x7fffffffU & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_and_expr_FU_32_32_32_162_i0_fu___05F_float_adde8m23b_127nih_501195_501268 
                          | ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_2_i0_fu___05F_float_adde8m23b_127nih_501195_501259)
                              ? 0U : vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_9__DOT__reg_out1)));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_44_i0_fu___05F_float_adde8m23b_127nih_501195_510569 
        = (1U & (0xbU >> ((4U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_and_expr_FU_32_32_32_162_i0_fu___05F_float_adde8m23b_127nih_501195_501268 
                                 >> 0x15U)) | ((2U 
                                                & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_9__DOT__reg_out1 
                                                   >> 0x16U)) 
                                               | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_2_i0_fu___05F_float_adde8m23b_127nih_501195_501259)))));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_45_i0_fu___05F_float_adde8m23b_127nih_501195_510572 
        = (1U & (0xbU >> ((4U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_and_expr_FU_32_32_32_162_i0_fu___05F_float_adde8m23b_127nih_501195_501268 
                                 >> 0x16U)) | ((2U 
                                                & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_9__DOT__reg_out1 
                                                   >> 0x17U)) 
                                               | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_2_i0_fu___05F_float_adde8m23b_127nih_501195_501259)))));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_46_i0_fu___05F_float_adde8m23b_127nih_501195_510575 
        = (1U & (0xbU >> ((4U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_and_expr_FU_32_32_32_162_i0_fu___05F_float_adde8m23b_127nih_501195_501268 
                                 >> 0x17U)) | ((2U 
                                                & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_9__DOT__reg_out1 
                                                   >> 0x18U)) 
                                               | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_2_i0_fu___05F_float_adde8m23b_127nih_501195_501259)))));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_47_i0_fu___05F_float_adde8m23b_127nih_501195_510578 
        = (1U & (0xbU >> ((4U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_and_expr_FU_32_32_32_162_i0_fu___05F_float_adde8m23b_127nih_501195_501268 
                                 >> 0x18U)) | ((2U 
                                                & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_9__DOT__reg_out1 
                                                   >> 0x19U)) 
                                               | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_2_i0_fu___05F_float_adde8m23b_127nih_501195_501259)))));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_42_i0_fu___05F_float_adde8m23b_127nih_501195_510563 
        = (1U & (0xbU >> ((4U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_and_expr_FU_32_32_32_162_i0_fu___05F_float_adde8m23b_127nih_501195_501268 
                                 >> 0x1bU)) | ((2U 
                                                & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_9__DOT__reg_out1 
                                                   >> 0x1cU)) 
                                               | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_2_i0_fu___05F_float_adde8m23b_127nih_501195_501259)))));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_43_i0_fu___05F_float_adde8m23b_127nih_501195_510566 
        = (1U & (0xbU >> ((4U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_and_expr_FU_32_32_32_162_i0_fu___05F_float_adde8m23b_127nih_501195_501268 
                                 >> 0x1cU)) | ((2U 
                                                & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_9__DOT__reg_out1 
                                                   >> 0x1dU)) 
                                               | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_2_i0_fu___05F_float_adde8m23b_127nih_501195_501259)))));
    vlSelf->__VdfgTmp_h4ab71bb9__0 = ((4U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_and_expr_FU_32_32_32_162_i0_fu___05F_float_adde8m23b_127nih_501195_501268 
                                             >> 0x19U)) 
                                      | ((2U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_9__DOT__reg_out1 
                                                >> 0x1aU)) 
                                         | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_2_i0_fu___05F_float_adde8m23b_127nih_501195_501259)));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i2_fu___05F_float_adde8m23b_127nih_501195_503543 
        = (0x1ffffffU & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__reg_5__DOT__reg_out1 
                         + (0x7ffffffU & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i0_fu___05F_float_adde8m23b_127nih_501195_501582 
                                          >> 2U))));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_140_i0_fu___05F_float_adde8m23b_127nih_501195_510689 
        = (1U & (IData)((0xf4f4540000000000ULL >> (
                                                   (0x20U 
                                                    & ((IData)(
                                                               (0xf4f4540000000000ULL 
                                                                >> 
                                                                ((0x20U 
                                                                  & ((IData)(
                                                                             (0xf4f4540000000000ULL 
                                                                              >> 
                                                                              ((0x20U 
                                                                                & ((0xf4f45400U 
                                                                                >> (IData)(vlSelf->__VdfgTmp_hfc0a1d14__0)) 
                                                                                << 5U)) 
                                                                               | (IData)(vlSelf->__VdfgTmp_h8c900521__0)))) 
                                                                     << 5U)) 
                                                                 | (IData)(vlSelf->__VdfgTmp_h6cbb337b__0)))) 
                                                       << 5U)) 
                                                   | (IData)(vlSelf->__VdfgTmp_h04849622__0)))));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_ior_expr_FU_0_32_32_168_i0_fu___05F_float_adde8m23b_127nih_501195_501465 
        = (0xffffffU & ((0x800000U & ((IData)((0xfffff5f4ffffffffULL 
                                               >> (
                                                   (0x20U 
                                                    & ((IData)(
                                                               (0xfffffffffffULL 
                                                                & (0xa0b00000000ULL 
                                                                   >> 
                                                                   ((0x20U 
                                                                     & ((IData)(
                                                                                (0xfffffffffffULL 
                                                                                & (0xa0b00000000ULL 
                                                                                >> 
                                                                                ((0x20U 
                                                                                & ((0xa0bU 
                                                                                >> (IData)(vlSelf->__VdfgTmp_hfc0a1d14__0)) 
                                                                                << 5U)) 
                                                                                | (IData)(vlSelf->__VdfgTmp_h8c900521__0))))) 
                                                                        << 5U)) 
                                                                    | (IData)(vlSelf->__VdfgTmp_h6cbb337b__0))))) 
                                                       << 5U)) 
                                                   | (IData)(vlSelf->__VdfgTmp_h04849622__0)))) 
                                      << 0x17U)) | 
                        (0x7fffffU & vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_ior_expr_FU_32_32_32_176_i1_fu___05F_float_adde8m23b_127nih_501195_501285)));
    bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_minus_expr_FU_8_8_8_201_i0_fu___05F_float_adde8m23b_127nih_501195_501436 
        = (0xffU & ((0x7fffffffU & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_ior_expr_FU_32_32_32_176_i0_fu___05F_float_adde8m23b_127nih_501195_501275 
                                    >> 0x17U)) - (0x7fffffffU 
                                                  & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_ior_expr_FU_32_32_32_176_i1_fu___05F_float_adde8m23b_127nih_501195_501285 
                                                     >> 0x17U))));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_135_i0_fu___05F_float_adde8m23b_127nih_501195_510672 
        = ((7U >= (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_43_i0_fu___05F_float_adde8m23b_127nih_501195_510566) 
                    << 5U) | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_42_i0_fu___05F_float_adde8m23b_127nih_501195_510563) 
                               << 4U) | ((8U & ((0xbU 
                                                 >> (IData)(vlSelf->__VdfgTmp_h4ab71bb9__0)) 
                                                << 3U)) 
                                         | ((4U & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_and_expr_FU_32_32_32_162_i0_fu___05F_float_adde8m23b_127nih_501195_501268 
                                                   >> 0x1aU)) 
                                            | ((2U 
                                                & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_9__DOT__reg_out1 
                                                   >> 0x1bU)) 
                                               | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_2_i0_fu___05F_float_adde8m23b_127nih_501195_501259)))))))
            ? (1U & (0xf4U >> (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_43_i0_fu___05F_float_adde8m23b_127nih_501195_510566) 
                                << 5U) | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_42_i0_fu___05F_float_adde8m23b_127nih_501195_510563) 
                                           << 4U) | 
                                          ((8U & ((0xbU 
                                                   >> (IData)(vlSelf->__VdfgTmp_h4ab71bb9__0)) 
                                                  << 3U)) 
                                           | ((4U & 
                                               (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_and_expr_FU_32_32_32_162_i0_fu___05F_float_adde8m23b_127nih_501195_501268 
                                                >> 0x1aU)) 
                                              | ((2U 
                                                  & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__reg_9__DOT__reg_out1 
                                                     >> 0x1bU)) 
                                                 | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_UUdata_converter_FU_2_i0_fu___05F_float_adde8m23b_127nih_501195_501259))))))))
            : 0U);
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_ior_concat_expr_FU_166_i0_fu___05F_float_adde8m23b_127nih_501195_501585 
        = ((0x7fffffcU & (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i2_fu___05F_float_adde8m23b_127nih_501195_503543 
                          << 2U)) | (3U & vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_plus_expr_FU_32_32_32_204_i0_fu___05F_float_adde8m23b_127nih_501195_501582));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_bit_ior_expr_FU_8_8_8_177_i0_fu___05F_float_adde8m23b_127nih_501195_501506 
        = (0x1fU & ((IData)(bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_minus_expr_FU_8_8_8_201_i0_fu___05F_float_adde8m23b_127nih_501195_501436) 
                    | (- (IData)((1U & VL_SHIFTRS_III(1,32,5, 
                                                      (VL_EXTENDS_II(32,2, 
                                                                     (1U 
                                                                      & (0xfeU 
                                                                         >> 
                                                                         ((4U 
                                                                           & ((IData)(bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_minus_expr_FU_8_8_8_201_i0_fu___05F_float_adde8m23b_127nih_501195_501436) 
                                                                              >> 5U)) 
                                                                          | ((2U 
                                                                              & ((IData)(bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_minus_expr_FU_8_8_8_201_i0_fu___05F_float_adde8m23b_127nih_501195_501436) 
                                                                                >> 5U)) 
                                                                             | (1U 
                                                                                & ((IData)(bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_ui_minus_expr_FU_8_8_8_201_i0_fu___05F_float_adde8m23b_127nih_501195_501436) 
                                                                                >> 5U))))))) 
                                                       << 0x1fU), 0x1fU))))));
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_136_i0_fu___05F_float_adde8m23b_127nih_501195_510675 
        = (1U & (0x10000U >> (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_135_i0_fu___05F_float_adde8m23b_127nih_501195_510672) 
                               << 4U) | (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_47_i0_fu___05F_float_adde8m23b_127nih_501195_510578) 
                                          << 3U) | 
                                         (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_46_i0_fu___05F_float_adde8m23b_127nih_501195_510575) 
                                           << 2U) | 
                                          (((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_45_i0_fu___05F_float_adde8m23b_127nih_501195_510572) 
                                            << 1U) 
                                           | (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__fu_forward_kernel_500073_500104__DOT__Datapath_i__DOT__out_lut_expr_FU_44_i0_fu___05F_float_adde8m23b_127nih_501195_510569)))))));
}

VL_INLINE_OPT void Vbambu_testbench___024root___nba_sequent__TOP__2(Vbambu_testbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbambu_testbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbambu_testbench___024root___nba_sequent__TOP__2\n"); );
    // Body
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__done_delayed_REG__DOT__reg_out1 
        = ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__rst) 
           & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__done_delayed_REG_signal_in));
}

void Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__m_write_TOP(CData/*7:0*/ id, VlWide<128>/*4095:0*/ data, SData/*15:0*/ bitsize, IData/*31:0*/ addr, CData/*7:0*/ shift, IData/*31:0*/ &m_write__Vfuncrtn);

VL_INLINE_OPT void Vbambu_testbench___024root___nba_sequent__TOP__3(Vbambu_testbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbambu_testbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbambu_testbench___024root___nba_sequent__TOP__3\n"); );
    // Init
    IData/*31:0*/ __Vtask_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__write_sa__5__data;
    __Vtask_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__write_sa__5__data = 0;
    SData/*15:0*/ __Vtask_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__write_sa__5__bitsize;
    __Vtask_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__write_sa__5__bitsize = 0;
    IData/*31:0*/ __Vtask_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__write_sa__5__addr;
    __Vtask_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__write_sa__5__addr = 0;
    VlWide<128>/*4095:0*/ __Vtask_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__write_sa__5___data;
    VL_ZERO_W(4096, __Vtask_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__write_sa__5___data);
    IData/*31:0*/ __Vfunc_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__m_write__6__Vfuncout;
    __Vfunc_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__m_write__6__Vfuncout = 0;
    // Body
    vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__1__KET____DOT__Wready = 0U;
    vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__0__KET____DOT__Wready = 0U;
    if ((((~ (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT____VdfgTmp_hca893bdf__0)) 
          & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__fuselector_BMEMORY_CTRLN_83_i0_STORE)) 
         & (0x40000000U <= vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__0__KET____DOT__Waddr))) {
        __Vtask_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__write_sa__5__addr 
            = vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__0__KET____DOT__Waddr;
        if (vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT____VdfgTmp_hca893bdf__0) {
            __Vtask_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__write_sa__5__bitsize = 0U;
            __Vtask_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__write_sa__5__data = 0U;
        } else {
            __Vtask_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__write_sa__5__bitsize 
                = ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT__BMEMORY_CTRLN_83_i0__DOT____VdfgTmp_h9c0114c5__0)
                    ? 0x20U : 0U);
            __Vtask_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__write_sa__5__data 
                = vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT____VdfgTmp_h752baccc__0;
        }
        vlSelf->bambu_testbench__DOT__system__DOT__SystemMEM__DOT__channel__BRA__0__KET____DOT__Wready = 1U;
        VL_CONST_W_1X(4096,__Vtask_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__write_sa__5___data,0x00000000);
        __Vtask_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__write_sa__5___data[0U] 
            = __Vtask_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__write_sa__5__data;
        Vbambu_testbench___024root____Vdpiimwrap_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__m_write_TOP(3U, __Vtask_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__write_sa__5___data, (IData)(__Vtask_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__write_sa__5__bitsize), __Vtask_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__write_sa__5__addr, 0U, __Vfunc_bambu_testbench__DOT__system__DOT__SystemMEM__DOT__m_utils__DOT__m_write__6__Vfuncout);
    }
}

VL_INLINE_OPT void Vbambu_testbench___024root___nba_sequent__TOP__4(Vbambu_testbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbambu_testbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbambu_testbench___024root___nba_sequent__TOP__4\n"); );
    // Body
    vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__done_delayed_REG_signal_in = 0U;
    if ((1U & (~ ((((((((0x2000U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state)) 
                        | (0x800U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) 
                       | (0x1000U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) 
                      | (1U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) 
                     | (2U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) 
                    | (4U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) 
                   | (8U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) 
                  | (0x10U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state)))))) {
        if ((0x20U != (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
            if ((0x40U != (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                if ((0x80U != (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                    if ((0x100U != (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                        if ((0x200U != (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                            if ((0x400U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Controller_i__DOT___present_state))) {
                                if ((1U != (1U & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT____Vcellinp__fu_forward_kernel_500073_503980__in1)))) {
                                    if ((2U != (IData)(vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__Datapath_i__DOT____Vcellinp__fu_forward_kernel_500073_503980__in1))) {
                                        vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__done_delayed_REG_signal_in = 1U;
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__rst 
        = vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__rst_next;
    vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__rst_next 
        = vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__rst;
    if ((1U & (~ ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state) 
                  >> 6U)))) {
        if ((1U & (~ ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state) 
                      >> 5U)))) {
            if ((1U & (~ ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state) 
                          >> 4U)))) {
                if ((1U & (~ ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state) 
                              >> 3U)))) {
                    if ((1U & (~ ((IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state) 
                                  >> 2U)))) {
                        if ((2U & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state))) {
                            if ((1U & (~ (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state)))) {
                                if (VL_LTS_III(32, 1U, vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__rst_count)) {
                                    vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__rst_next = 0U;
                                } else if ((1U == vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__rst_count)) {
                                    vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__rst_next = 1U;
                                }
                            }
                        } else if ((1U & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state))) {
                            if ((2U == (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_succ))) {
                                if (VL_LTS_III(32, 0U, vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__rst_count)) {
                                    vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__rst_next = 0U;
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

VL_INLINE_OPT void Vbambu_testbench___024root___nba_comb__TOP__0(Vbambu_testbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbambu_testbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbambu_testbench___024root___nba_comb__TOP__0\n"); );
    // Body
    vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next 
        = vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state;
    if ((0x40U & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state))) {
        vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next = 1U;
    } else if ((0x20U & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state))) {
        if ((0x10U & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state))) {
            vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next = 1U;
        } else if ((8U & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state))) {
            vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next = 1U;
        } else if ((4U & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state))) {
            vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next = 1U;
        } else if ((2U & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state))) {
            vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next = 1U;
        } else if ((1U & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state))) {
            vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next = 1U;
        }
    } else if ((0x10U & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state))) {
        vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next = 1U;
    } else if ((8U & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state))) {
        if ((4U & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state))) {
            vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next = 1U;
        } else if ((2U & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state))) {
            vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next = 1U;
        } else if ((1U & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state))) {
            vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next = 1U;
        }
    } else if ((4U & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state))) {
        if ((2U & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state))) {
            vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next = 1U;
        } else if ((1U & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state))) {
            vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next = 1U;
        } else if (vlSelf->bambu_testbench__DOT__system__DOT__DUT__DOT__top__DOT___forward_kernel_i0__DOT__done_delayed_REG__DOT__reg_out1) {
            vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next = 0x40U;
        }
    } else if ((2U & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state))) {
        if ((1U & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state))) {
            vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next = 1U;
        } else if (VL_GTES_III(32, 1U, vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__rst_count)) {
            if ((1U != vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__rst_count)) {
                vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next = 4U;
            }
        }
    } else {
        vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_next 
            = ((1U & (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state))
                ? (IData)(vlSelf->bambu_testbench__DOT__system__DOT__SystemFSM__DOT__state_succ)
                : 1U);
    }
}

void Vbambu_testbench___024root___eval_nba(Vbambu_testbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbambu_testbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbambu_testbench___024root___eval_nba\n"); );
    // Body
    if (vlSelf->__VnbaTriggered.at(0U)) {
        Vbambu_testbench___024root___nba_sequent__TOP__0(vlSelf);
        Vbambu_testbench___024root___nba_sequent__TOP__1(vlSelf);
    }
    if (vlSelf->__VnbaTriggered.at(1U)) {
        Vbambu_testbench___024root___nba_sequent__TOP__2(vlSelf);
    }
    if (vlSelf->__VnbaTriggered.at(2U)) {
        Vbambu_testbench___024root___nba_sequent__TOP__3(vlSelf);
    }
    if (vlSelf->__VnbaTriggered.at(0U)) {
        Vbambu_testbench___024root___nba_sequent__TOP__4(vlSelf);
    }
    if ((vlSelf->__VnbaTriggered.at(0U) | vlSelf->__VnbaTriggered.at(1U))) {
        Vbambu_testbench___024root___nba_comb__TOP__0(vlSelf);
    }
}

void Vbambu_testbench___024root___eval_triggers__act(Vbambu_testbench___024root* vlSelf);
#ifdef VL_DEBUG
VL_ATTR_COLD void Vbambu_testbench___024root___dump_triggers__act(Vbambu_testbench___024root* vlSelf);
#endif  // VL_DEBUG
#ifdef VL_DEBUG
VL_ATTR_COLD void Vbambu_testbench___024root___dump_triggers__nba(Vbambu_testbench___024root* vlSelf);
#endif  // VL_DEBUG

void Vbambu_testbench___024root___eval(Vbambu_testbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbambu_testbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbambu_testbench___024root___eval\n"); );
    // Init
    VlTriggerVec<3> __VpreTriggered;
    IData/*31:0*/ __VnbaIterCount;
    CData/*0:0*/ __VnbaContinue;
    // Body
    __VnbaIterCount = 0U;
    __VnbaContinue = 1U;
    while (__VnbaContinue) {
        __VnbaContinue = 0U;
        vlSelf->__VnbaTriggered.clear();
        vlSelf->__VactIterCount = 0U;
        vlSelf->__VactContinue = 1U;
        while (vlSelf->__VactContinue) {
            vlSelf->__VactContinue = 0U;
            Vbambu_testbench___024root___eval_triggers__act(vlSelf);
            if (vlSelf->__VactTriggered.any()) {
                vlSelf->__VactContinue = 1U;
                if (VL_UNLIKELY((0x64U < vlSelf->__VactIterCount))) {
#ifdef VL_DEBUG
                    Vbambu_testbench___024root___dump_triggers__act(vlSelf);
#endif
                    VL_FATAL_MT("HLS_output/simulation/bambu_testbench.v", 955, "", "Active region did not converge.");
                }
                vlSelf->__VactIterCount = ((IData)(1U) 
                                           + vlSelf->__VactIterCount);
                __VpreTriggered.andNot(vlSelf->__VactTriggered, vlSelf->__VnbaTriggered);
                vlSelf->__VnbaTriggered.set(vlSelf->__VactTriggered);
                Vbambu_testbench___024root___eval_act(vlSelf);
            }
        }
        if (vlSelf->__VnbaTriggered.any()) {
            __VnbaContinue = 1U;
            if (VL_UNLIKELY((0x64U < __VnbaIterCount))) {
#ifdef VL_DEBUG
                Vbambu_testbench___024root___dump_triggers__nba(vlSelf);
#endif
                VL_FATAL_MT("HLS_output/simulation/bambu_testbench.v", 955, "", "NBA region did not converge.");
            }
            __VnbaIterCount = ((IData)(1U) + __VnbaIterCount);
            Vbambu_testbench___024root___eval_nba(vlSelf);
        }
    }
}

#ifdef VL_DEBUG
void Vbambu_testbench___024root___eval_debug_assertions(Vbambu_testbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbambu_testbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbambu_testbench___024root___eval_debug_assertions\n"); );
    // Body
    if (VL_UNLIKELY((vlSelf->clock & 0xfeU))) {
        Verilated::overWidthError("clock");}
}
#endif  // VL_DEBUG
