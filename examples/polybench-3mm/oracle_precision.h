/*
 * Serialization-only override for the PolyBench/C 4.2.1 3mm oracle.
 *
 * This mirrors 3mm.h's MINI dimensions and FP64 type while changing only
 * DATA_PRINTF_MODIFIER from two decimal places to 17 significant digits.
 * The computational source remains the original, unchanged 3mm.c.
 */
#ifndef LASSI_X_3MM_ORACLE_PRECISION_H
#define LASSI_X_3MM_ORACLE_PRECISION_H

#define _3MM_H

#define MINI_DATASET
#define NI 16
#define NJ 18
#define NK 20
#define NL 22
#define NM 24

#define _PB_NI POLYBENCH_LOOP_BOUND(NI, ni)
#define _PB_NJ POLYBENCH_LOOP_BOUND(NJ, nj)
#define _PB_NK POLYBENCH_LOOP_BOUND(NK, nk)
#define _PB_NL POLYBENCH_LOOP_BOUND(NL, nl)
#define _PB_NM POLYBENCH_LOOP_BOUND(NM, nm)

#define DATA_TYPE double
#define DATA_PRINTF_MODIFIER "%.17g "
#define SCALAR_VAL(x) x
#define SQRT_FUN(x) sqrt(x)
#define EXP_FUN(x) exp(x)
#define POW_FUN(x, y) pow(x, y)

#endif
