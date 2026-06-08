#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>

int main(int argc, char** argv){
  int a = 8;
  int b = 6;
  int c = 8;

  if (argc == 4) {
    a = atoi(argv[1]);
    b = atoi(argv[2]);
    c = atoi(argv[3]);
  } else if (argc != 1) {
    printf("Usage: %s <a> <b> <c>\n", argv[0]);
    return 1;
  }

  /* Strategy 2: large fully-buffered stdout to amortize per-printf overhead.
     Must be set before any write to stdout other than the usage error path
     (which returns before reaching here). */
  static char io_buf[1 << 16];
  setvbuf(stdout, io_buf, _IOFBF, sizeof io_buf);

  int matA[a][b];
  int matB[b][c];

 for(int i = 0; i < a; i++){
    for(int j = 0; j < b; j++){
      matA[i][j] = i==j?1:0;
    }
 }

  for(int i = 0; i < b; i++){
    for(int j = 0; j < c; j++){
      matB[i][j] = i==j?1:0;
    }
 }

  int matC[a][c];

  /* Strategy 1: zero C, then GEMM in i,k,j order so the inner j loop is
     stride-1 on both B[k][j] and C[i][j] (vectorizable, cache-friendly).
     A[i][k] is hoisted to a scalar in the middle loop. */
  for(int i = 0; i < a; i++){
    for(int j = 0; j < c; j++){
      matC[i][j] = 0;
    }
  }

  for(int i = 0; i < a; i++){
    for(int k = 0; k < b; k++){
      int aik = matA[i][k];
      for(int j = 0; j < c; j++){
        matC[i][j] += aik * matB[k][j];
      }
    }
  }

  /* Print phase: identical format to the original (space after each int,
     newline per row, no trailing-byte changes). */
  for(int i = 0; i < a; i++){
    for(int j = 0; j < c; j++){
      printf("%d ", matC[i][j]);
    }
    printf("\n");
  }
	return 0;

}
