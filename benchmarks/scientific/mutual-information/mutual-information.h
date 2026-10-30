/**
 * mutual-information.h: this file is part of the LASSI scientific-computing
 * suite.
 *
 * Shannon mutual information for an N x N joint-probability matrix. The LARGE
 * profile is the 256 x 256 problem used by the accelerator example.
 */
#ifndef _MUTUAL_INFORMATION_H
# define _MUTUAL_INFORMATION_H

/* Default to LARGE_DATASET. */
# if !defined(MINI_DATASET) && !defined(SMALL_DATASET) && !defined(MEDIUM_DATASET) && !defined(LARGE_DATASET) && !defined(EXTRALARGE_DATASET)
#  define LARGE_DATASET
# endif

# if !defined(N)
/* Define sample dataset sizes. */
#  ifdef MINI_DATASET
#   define N 32
#  endif

#  ifdef SMALL_DATASET
#   define N 64
#  endif

#  ifdef MEDIUM_DATASET
#   define N 128
#  endif

#  ifdef LARGE_DATASET
#   define N 256
#  endif

#  ifdef EXTRALARGE_DATASET
#   define N 512
#  endif
# endif /* !N */

# define _PB_N POLYBENCH_LOOP_BOUND(N,n)

/* Default data type. */
# if !defined(DATA_TYPE_IS_INT) && !defined(DATA_TYPE_IS_FLOAT) && !defined(DATA_TYPE_IS_DOUBLE)
#  define DATA_TYPE_IS_DOUBLE
# endif

#ifdef DATA_TYPE_IS_INT
#  define DATA_TYPE int
#  ifndef DATA_PRINTF_MODIFIER
#   define DATA_PRINTF_MODIFIER "%d "
#  endif
#endif

#ifdef DATA_TYPE_IS_FLOAT
#  define DATA_TYPE float
#  ifndef DATA_PRINTF_MODIFIER
#   define DATA_PRINTF_MODIFIER "%0.2f "
#  endif
#  define SCALAR_VAL(x) x##f
#  define LOG_FUN(x) logf(x)
#endif

#ifdef DATA_TYPE_IS_DOUBLE
#  define DATA_TYPE double
#  ifndef DATA_PRINTF_MODIFIER
#   define DATA_PRINTF_MODIFIER "%0.2lf "
#  endif
#  define SCALAR_VAL(x) x
#  define LOG_FUN(x) log(x)
#endif

#endif /* !_MUTUAL_INFORMATION_H */
