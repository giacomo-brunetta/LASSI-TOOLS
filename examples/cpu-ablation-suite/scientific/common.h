/* Deterministic double-precision scientific validation fixtures (not performance benchmarks). */
#ifndef LASSI_SCIENCE_COMMON_H
#define LASSI_SCIENCE_COMMON_H
#include <math.h>
#include <stdio.h>
#if defined(MEDIUM_DATASET)
#define SIZE 128
#define STEPS 100
#elif defined(SMALL_DATASET)
#define SIZE 64
#define STEPS 50
#else
#define SIZE 32
#define STEPS 20
#endif
static void dump(double value) { printf("%.17g\n", value); }
#endif
