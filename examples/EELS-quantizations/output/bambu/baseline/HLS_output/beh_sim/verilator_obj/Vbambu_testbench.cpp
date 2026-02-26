// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Model implementation (design independent parts)

#include "Vbambu_testbench.h"
#include "Vbambu_testbench__Syms.h"
#include "verilated_dpi.h"

//============================================================
// Constructors

Vbambu_testbench::Vbambu_testbench(VerilatedContext* _vcontextp__, const char* _vcname__)
    : VerilatedModel{*_vcontextp__}
    , vlSymsp{new Vbambu_testbench__Syms(contextp(), _vcname__, this)}
    , clock{vlSymsp->TOP.clock}
    , rootp{&(vlSymsp->TOP)}
{
    // Register model with the context
    contextp()->addModel(this);
}

Vbambu_testbench::Vbambu_testbench(const char* _vcname__)
    : Vbambu_testbench(Verilated::threadContextp(), _vcname__)
{
}

//============================================================
// Destructor

Vbambu_testbench::~Vbambu_testbench() {
    delete vlSymsp;
}

//============================================================
// Evaluation function

#ifdef VL_DEBUG
void Vbambu_testbench___024root___eval_debug_assertions(Vbambu_testbench___024root* vlSelf);
#endif  // VL_DEBUG
void Vbambu_testbench___024root___eval_static(Vbambu_testbench___024root* vlSelf);
void Vbambu_testbench___024root___eval_initial(Vbambu_testbench___024root* vlSelf);
void Vbambu_testbench___024root___eval_settle(Vbambu_testbench___024root* vlSelf);
void Vbambu_testbench___024root___eval(Vbambu_testbench___024root* vlSelf);

void Vbambu_testbench::eval_step() {
    VL_DEBUG_IF(VL_DBG_MSGF("+++++TOP Evaluate Vbambu_testbench::eval_step\n"); );
#ifdef VL_DEBUG
    // Debug assertions
    Vbambu_testbench___024root___eval_debug_assertions(&(vlSymsp->TOP));
#endif  // VL_DEBUG
    if (VL_UNLIKELY(!vlSymsp->__Vm_didInit)) {
        vlSymsp->__Vm_didInit = true;
        VL_DEBUG_IF(VL_DBG_MSGF("+ Initial\n"););
        Vbambu_testbench___024root___eval_static(&(vlSymsp->TOP));
        Vbambu_testbench___024root___eval_initial(&(vlSymsp->TOP));
        Vbambu_testbench___024root___eval_settle(&(vlSymsp->TOP));
    }
    // MTask 0 start
    VL_DEBUG_IF(VL_DBG_MSGF("MTask0 starting\n"););
    Verilated::mtaskId(0);
    VL_DEBUG_IF(VL_DBG_MSGF("+ Eval\n"););
    Vbambu_testbench___024root___eval(&(vlSymsp->TOP));
    // Evaluate cleanup
    Verilated::endOfThreadMTask(vlSymsp->__Vm_evalMsgQp);
    Verilated::endOfEval(vlSymsp->__Vm_evalMsgQp);
}

//============================================================
// Events and timing
bool Vbambu_testbench::eventsPending() { return false; }

uint64_t Vbambu_testbench::nextTimeSlot() {
    VL_FATAL_MT(__FILE__, __LINE__, "", "%Error: No delays in the design");
    return 0;
}

//============================================================
// Utilities

const char* Vbambu_testbench::name() const {
    return vlSymsp->name();
}

//============================================================
// Invoke final blocks

void Vbambu_testbench___024root___eval_final(Vbambu_testbench___024root* vlSelf);

VL_ATTR_COLD void Vbambu_testbench::final() {
    Vbambu_testbench___024root___eval_final(&(vlSymsp->TOP));
}

//============================================================
// Implementations of abstract methods from VerilatedModel

const char* Vbambu_testbench::hierName() const { return vlSymsp->name(); }
const char* Vbambu_testbench::modelName() const { return "Vbambu_testbench"; }
unsigned Vbambu_testbench::threads() const { return 1; }
