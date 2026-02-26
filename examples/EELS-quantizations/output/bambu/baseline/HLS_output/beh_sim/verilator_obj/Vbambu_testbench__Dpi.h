// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Prototypes for DPI import and export functions.
//
// Verilator includes this file in all generated .cpp files that use DPI functions.
// Manually include this file where DPI .c import functions are declared to ensure
// the C functions match the expectations of the DPI imports.

#ifndef VERILATED_VBAMBU_TESTBENCH__DPI_H_
#define VERILATED_VBAMBU_TESTBENCH__DPI_H_  // guard

#include "svdpi.h"

#ifdef __cplusplus
extern "C" {
#endif


    // DPI IMPORTS
    // DPI import at HLS_output/simulation/bambu_testbench.v:188:31
    extern int m_fini();
    // DPI import at HLS_output/simulation/bambu_testbench.v:187:40
    extern unsigned int m_next(unsigned int state);
    // DPI import at HLS_output/simulation/bambu_testbench.v:406:31
    extern int m_read(unsigned char id, svLogicVecVal* data, unsigned short bitsize, unsigned int addr, unsigned char shift);
    // DPI import at HLS_output/simulation/bambu_testbench.v:408:31
    extern int m_state(unsigned char id, int data);
    // DPI import at HLS_output/simulation/bambu_testbench.v:407:31
    extern int m_write(unsigned char id, const svLogicVecVal* data, unsigned short bitsize, unsigned int addr, unsigned char shift);

#ifdef __cplusplus
}
#endif

#endif  // guard
