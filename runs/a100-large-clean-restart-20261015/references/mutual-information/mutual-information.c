/**
 * mutual-information.c: this file is part of the LASSI
 * scientific-computing suite.
 *
 * Compute Shannon mutual information in bits from an N x N joint probability
 * matrix:
 *
 *   I(X;Y) = sum_x sum_y p(x,y) log2(p(x,y) / (p(x) p(y))).
 *
 * The deterministic input is the equal mixture of a uniform independent
 * distribution and a uniform diagonal distribution. It is normalized,
 * strictly positive, and exercises both marginal reductions and the
 * transcendental part of the kernel. The LARGE profile uses the 256 x 256
 * shape from the accelerator example.
 */
#include <math.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

/* Include PolyBench common header. */
#include <polybench.h>

/* Include benchmark-specific header. */
#include "mutual-information.h"


static
void init_array(int n,
		DATA_TYPE POLYBENCH_2D(joint,N,N,n,n))
{
  int x, y;
  DATA_TYPE independent = SCALAR_VAL(0.5) / (n * n);
  DATA_TYPE diagonal = SCALAR_VAL(0.5) / n;

  for (x = 0; x < n; x++)
    for (y = 0; y < n; y++) {
      joint[x][y] = independent;
      if (x == y)
        joint[x][y] += diagonal;
    }
}


/* DCE code. Must scan the entire live-out data. */
static
void print_array(DATA_TYPE POLYBENCH_1D(mi,1,1))
{
  POLYBENCH_DUMP_START;
  POLYBENCH_DUMP_BEGIN("mi");
  fprintf(POLYBENCH_DUMP_TARGET, "\n");
  fprintf(POLYBENCH_DUMP_TARGET, DATA_PRINTF_MODIFIER, mi[0]);
  POLYBENCH_DUMP_END("mi");
  POLYBENCH_DUMP_FINISH;
}


/* Main computational kernel. Marginals are scratch arrays; mi is live-out. */
static
void kernel_mutual_information(int n,
		DATA_TYPE POLYBENCH_2D(joint,N,N,n,n),
		DATA_TYPE POLYBENCH_1D(marginal_x,N,n),
		DATA_TYPE POLYBENCH_1D(marginal_y,N,n),
		DATA_TYPE POLYBENCH_1D(mi,1,1))
{
  int x, y;
  DATA_TYPE probability;
  DATA_TYPE nats_to_bits = SCALAR_VAL(1.0) / LOG_FUN(SCALAR_VAL(2.0));

#pragma scop
  for (x = 0; x < _PB_N; x++) {
    marginal_x[x] = SCALAR_VAL(0.0);
    marginal_y[x] = SCALAR_VAL(0.0);
  }

  for (x = 0; x < _PB_N; x++)
    for (y = 0; y < _PB_N; y++) {
      marginal_x[x] += joint[x][y];
      marginal_y[y] += joint[x][y];
    }

  mi[0] = SCALAR_VAL(0.0);
  for (x = 0; x < _PB_N; x++)
    for (y = 0; y < _PB_N; y++) {
      probability = joint[x][y];
      if (probability > SCALAR_VAL(0.0))
        mi[0] += probability
          * (LOG_FUN(probability) - LOG_FUN(marginal_x[x])
             - LOG_FUN(marginal_y[y]))
          * nats_to_bits;
    }
#pragma endscop
}


int main(int argc, char** argv)
{
  int n = N;

  POLYBENCH_2D_ARRAY_DECL(joint, DATA_TYPE, N, N, n, n);
  POLYBENCH_1D_ARRAY_DECL(marginal_x, DATA_TYPE, N, n);
  POLYBENCH_1D_ARRAY_DECL(marginal_y, DATA_TYPE, N, n);
  POLYBENCH_1D_ARRAY_DECL(mi, DATA_TYPE, 1, 1);

  init_array(n, POLYBENCH_ARRAY(joint));

  polybench_start_instruments;

  kernel_mutual_information(n, POLYBENCH_ARRAY(joint),
			    POLYBENCH_ARRAY(marginal_x),
			    POLYBENCH_ARRAY(marginal_y),
			    POLYBENCH_ARRAY(mi));

  polybench_stop_instruments;
  polybench_print_instruments;

  polybench_prevent_dce(print_array(POLYBENCH_ARRAY(mi)));

  POLYBENCH_FREE_ARRAY(joint);
  POLYBENCH_FREE_ARRAY(marginal_x);
  POLYBENCH_FREE_ARRAY(marginal_y);
  POLYBENCH_FREE_ARRAY(mi);

  return 0;
}
