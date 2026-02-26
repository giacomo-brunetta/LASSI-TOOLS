/*
 * Politecnico di Milano
 * Code created using PandA - Version: PandA 2024.10 - Revision c2ba6936ca2ed63137095fea0b630a1c66e20e63 - Date 2026-02-23T23:56:58
 * Bambu executed with: bambu -v3 --print-dot -lm --soft-float --compiler=I386_CLANG16 --device=xc7z020-1clg484 --clock-period=10 --experimental-setup=BAMBU-BALANCED-MP --channels-number=2 --memory-allocation-policy=ALL_BRAM --disable-function-proxy --generate-tb=../../forward_kernel_testbench.c --simulate --simulator=VERILATOR --verilator-parallel --top-fname=forward_kernel input.ll 
 */

#define _FILE_OFFSET_BITS 64

#define __Inf (1.0 / 0.0)
#define __Nan (0.0 / 0.0)

#ifdef __cplusplus
#undef printf

#include <cstdio>
#include <cstdlib>

typedef bool _Bool;
#else
#include <stdio.h>
#include <stdlib.h>

extern void exit(int status);
#endif

#include <sys/types.h>

#ifdef __AC_NAMESPACE
using namespace __AC_NAMESPACE;
#endif



#ifndef CDECL
#ifdef __cplusplus
#define CDECL extern "C"
#else
#define CDECL
#endif
#endif

#ifndef EXTERN_CDECL
#ifdef __cplusplus
#define EXTERN_CDECL extern "C"
#else
#define EXTERN_CDECL extern
#endif
#endif

#include <mdpi/mdpi_user.h>

CDECL void forward_kernel(void*, void*, void*);


