#ifndef LASSI_X_3MM_ORACLE_PRECISION_MEDIUM_H
#define LASSI_X_3MM_ORACLE_PRECISION_MEDIUM_H

#define _3MM_H
#define MEDIUM_DATASET
#define NI 180
#define NJ 190
#define NK 200
#define NL 210
#define NM 220
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
