/*
 * High-fidelity serialization for the original PolyBench/C jacobi-2d oracle.
 * Keep MINI's dimensions and FP64 arithmetic; change only the dump precision.
 */
#ifndef LASSI_X_JACOBI_2D_ORACLE_PRECISION_H
#define LASSI_X_JACOBI_2D_ORACLE_PRECISION_H

#define _JACOBI_2D_H

#define MINI_DATASET
#define TSTEPS 20
#define N 30

#define _PB_TSTEPS POLYBENCH_LOOP_BOUND(TSTEPS, tsteps)
#define _PB_N POLYBENCH_LOOP_BOUND(N, n)

#define DATA_TYPE double
#define DATA_PRINTF_MODIFIER "%.17g "
#define SCALAR_VAL(x) x
#define SQRT_FUN(x) sqrt(x)
#define EXP_FUN(x) exp(x)
#define POW_FUN(x, y) pow(x, y)

#endif
