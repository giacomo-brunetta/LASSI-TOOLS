/**
 * This version is stamped on May 10, 2016
 *
 * Contact:
 *   Louis-Noel Pouchet <pouchet.ohio-state.edu>
 *   Tomofumi Yuki <tomofumi.yuki.fr>
 *
 * Web address: http://polybench.sourceforge.net
 */
/* 3mm.c: this file is part of PolyBench/C */

#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <math.h>

/* Include polybench common header. */
#include <polybench.h>

/* Include benchmark-specific header. */
#include "3mm.h"


/* Array initialization. */
static
void init_array(int ni, int nj, int nk, int nl, int nm,
		DATA_TYPE POLYBENCH_2D(A,NI,NK,ni,nk),
		DATA_TYPE POLYBENCH_2D(B,NK,NJ,nk,nj),
		DATA_TYPE POLYBENCH_2D(C,NJ,NM,nj,nm),
		DATA_TYPE POLYBENCH_2D(D,NM,NL,nm,nl))
{
  int i, j;

  for (i = 0; i < ni; i++)
    for (j = 0; j < nk; j++)
      A[i][j] = (DATA_TYPE) ((i*j+1) % ni) / (5*ni);
  for (i = 0; i < nk; i++)
    for (j = 0; j < nj; j++)
      B[i][j] = (DATA_TYPE) ((i*(j+1)+2) % nj) / (5*nj);
  for (i = 0; i < nj; i++)
    for (j = 0; j < nm; j++)
      C[i][j] = (DATA_TYPE) (i*(j+3) % nl) / (5*nl);
  for (i = 0; i < nm; i++)
    for (j = 0; j < nl; j++)
      D[i][j] = (DATA_TYPE) ((i*(j+2)+2) % nk) / (5*nk);
}


/* DCE code. Must scan the entire live-out data.
   Can be used also to check the correctness of the output. */
static
void print_array(int ni, int nl,
		 DATA_TYPE POLYBENCH_2D(G,NI,NL,ni,nl))
{
  int i, j;

  POLYBENCH_DUMP_START;
  POLYBENCH_DUMP_BEGIN("G");
  for (i = 0; i < ni; i++)
    for (j = 0; j < nl; j++) {
	if ((i * ni + j) % 20 == 0) fprintf (POLYBENCH_DUMP_TARGET, "\n");
	fprintf (POLYBENCH_DUMP_TARGET, DATA_PRINTF_MODIFIER, G[i][j]);
    }
  POLYBENCH_DUMP_END("G");
  POLYBENCH_DUMP_FINISH;
}


/* Main computational kernel. The whole function will be timed,
   including the call and return. */
static
void kernel_3mm(int ni, int nj, int nk, int nl, int nm,
		DATA_TYPE POLYBENCH_2D(E,NI,NJ,ni,nj),
		DATA_TYPE POLYBENCH_2D(A,NI,NK,ni,nk),
		DATA_TYPE POLYBENCH_2D(B,NK,NJ,nk,nj),
		DATA_TYPE POLYBENCH_2D(F,NJ,NL,nj,nl),
		DATA_TYPE POLYBENCH_2D(C,NJ,NM,nj,nm),
		DATA_TYPE POLYBENCH_2D(D,NM,NL,nm,nl),
		DATA_TYPE POLYBENCH_2D(G,NI,NL,ni,nl))
{
  int i, j, k;

#pragma scop
  /* E := A*B  (i,k,j with i unrolled by 8; tail keeps original i,j,k) */
  {
    int i_bound_e = _PB_NI - (_PB_NI % 8);
    for (i = 0; i < i_bound_e; i++)
      for (j = 0; j < _PB_NJ; j++)
	E[i][j] = SCALAR_VAL(0.0);
    for (i = 0; i < i_bound_e; i += 8) {
      for (k = 0; k < _PB_NK; ++k) {
	DATA_TYPE a0 = A[i+0][k], a1 = A[i+1][k], a2 = A[i+2][k], a3 = A[i+3][k];
	DATA_TYPE a4 = A[i+4][k], a5 = A[i+5][k], a6 = A[i+6][k], a7 = A[i+7][k];
	for (j = 0; j < _PB_NJ; j++) {
	  DATA_TYPE b = B[k][j];
	  E[i+0][j] += a0 * b;
	  E[i+1][j] += a1 * b;
	  E[i+2][j] += a2 * b;
	  E[i+3][j] += a3 * b;
	  E[i+4][j] += a4 * b;
	  E[i+5][j] += a5 * b;
	  E[i+6][j] += a6 * b;
	  E[i+7][j] += a7 * b;
	}
      }
    }
    for (i = i_bound_e; i < _PB_NI; i++)
      for (j = 0; j < _PB_NJ; j++)
	{
	  E[i][j] = SCALAR_VAL(0.0);
	  for (k = 0; k < _PB_NK; ++k)
	    E[i][j] += A[i][k] * B[k][j];
	}
  }
  /* F := C*D  (i,k,j with i unrolled by 8; tail keeps original i,j,k) */
  {
    int i_bound_f = _PB_NJ - (_PB_NJ % 8);
    for (i = 0; i < i_bound_f; i++)
      for (j = 0; j < _PB_NL; j++)
	F[i][j] = SCALAR_VAL(0.0);
    for (i = 0; i < i_bound_f; i += 8) {
      for (k = 0; k < _PB_NM; ++k) {
	DATA_TYPE c0 = C[i+0][k], c1 = C[i+1][k], c2 = C[i+2][k], c3 = C[i+3][k];
	DATA_TYPE c4 = C[i+4][k], c5 = C[i+5][k], c6 = C[i+6][k], c7 = C[i+7][k];
	for (j = 0; j < _PB_NL; j++) {
	  DATA_TYPE d = D[k][j];
	  F[i+0][j] += c0 * d;
	  F[i+1][j] += c1 * d;
	  F[i+2][j] += c2 * d;
	  F[i+3][j] += c3 * d;
	  F[i+4][j] += c4 * d;
	  F[i+5][j] += c5 * d;
	  F[i+6][j] += c6 * d;
	  F[i+7][j] += c7 * d;
	}
      }
    }
    for (i = i_bound_f; i < _PB_NJ; i++)
      for (j = 0; j < _PB_NL; j++)
	{
	  F[i][j] = SCALAR_VAL(0.0);
	  for (k = 0; k < _PB_NM; ++k)
	    F[i][j] += C[i][k] * D[k][j];
	}
  }
  /* G := E*F  (i,k,j with i unrolled by 8; tail keeps original i,j,k) */
  {
    int i_bound_g = _PB_NI - (_PB_NI % 8);
    for (i = 0; i < i_bound_g; i++)
      for (j = 0; j < _PB_NL; j++)
	G[i][j] = SCALAR_VAL(0.0);
    for (i = 0; i < i_bound_g; i += 8) {
      for (k = 0; k < _PB_NJ; ++k) {
	DATA_TYPE e0 = E[i+0][k], e1 = E[i+1][k], e2 = E[i+2][k], e3 = E[i+3][k];
	DATA_TYPE e4 = E[i+4][k], e5 = E[i+5][k], e6 = E[i+6][k], e7 = E[i+7][k];
	for (j = 0; j < _PB_NL; j++) {
	  DATA_TYPE f = F[k][j];
	  G[i+0][j] += e0 * f;
	  G[i+1][j] += e1 * f;
	  G[i+2][j] += e2 * f;
	  G[i+3][j] += e3 * f;
	  G[i+4][j] += e4 * f;
	  G[i+5][j] += e5 * f;
	  G[i+6][j] += e6 * f;
	  G[i+7][j] += e7 * f;
	}
      }
    }
    for (i = i_bound_g; i < _PB_NI; i++)
      for (j = 0; j < _PB_NL; j++)
	{
	  G[i][j] = SCALAR_VAL(0.0);
	  for (k = 0; k < _PB_NJ; ++k)
	    G[i][j] += E[i][k] * F[k][j];
	}
  }
#pragma endscop

}


int main(int argc, char** argv)
{
  /* Retrieve problem size. */
  int ni = NI;
  int nj = NJ;
  int nk = NK;
  int nl = NL;
  int nm = NM;

  /* Variable declaration/allocation. */
  POLYBENCH_2D_ARRAY_DECL(E, DATA_TYPE, NI, NJ, ni, nj);
  POLYBENCH_2D_ARRAY_DECL(A, DATA_TYPE, NI, NK, ni, nk);
  POLYBENCH_2D_ARRAY_DECL(B, DATA_TYPE, NK, NJ, nk, nj);
  POLYBENCH_2D_ARRAY_DECL(F, DATA_TYPE, NJ, NL, nj, nl);
  POLYBENCH_2D_ARRAY_DECL(C, DATA_TYPE, NJ, NM, nj, nm);
  POLYBENCH_2D_ARRAY_DECL(D, DATA_TYPE, NM, NL, nm, nl);
  POLYBENCH_2D_ARRAY_DECL(G, DATA_TYPE, NI, NL, ni, nl);

  /* Initialize array(s). */
  init_array (ni, nj, nk, nl, nm,
	      POLYBENCH_ARRAY(A),
	      POLYBENCH_ARRAY(B),
	      POLYBENCH_ARRAY(C),
	      POLYBENCH_ARRAY(D));

  /* Start timer. */
  polybench_start_instruments;

  /* Run kernel. */
  kernel_3mm (ni, nj, nk, nl, nm,
	      POLYBENCH_ARRAY(E),
	      POLYBENCH_ARRAY(A),
	      POLYBENCH_ARRAY(B),
	      POLYBENCH_ARRAY(F),
	      POLYBENCH_ARRAY(C),
	      POLYBENCH_ARRAY(D),
	      POLYBENCH_ARRAY(G));

  /* Stop and print timer. */
  polybench_stop_instruments;
  polybench_print_instruments;

  /* Prevent dead-code elimination. All live-out data must be printed
     by the function call in argument. */
  polybench_prevent_dce(print_array(ni, nl,  POLYBENCH_ARRAY(G)));

  /* Be clean. */
  POLYBENCH_FREE_ARRAY(E);
  POLYBENCH_FREE_ARRAY(A);
  POLYBENCH_FREE_ARRAY(B);
  POLYBENCH_FREE_ARRAY(F);
  POLYBENCH_FREE_ARRAY(C);
  POLYBENCH_FREE_ARRAY(D);
  POLYBENCH_FREE_ARRAY(G);

  return 0;
}
