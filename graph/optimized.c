#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/* Fast integer -> decimal writer.
   Returns number of bytes written into out (no NUL).
   Handles INT_MIN safely via unsigned arithmetic. */
static inline int write_int_space(char *out, int v) {
  static const char digits2[201] =
    "00010203040506070809"
    "10111213141516171819"
    "20212223242526272829"
    "30313233343536373839"
    "40414243444546474849"
    "50515253545556575859"
    "60616263646566676869"
    "70717273747576777879"
    "80818283848586878889"
    "90919293949596979899";
  char buf[12];
  int n = 0;
  unsigned int u;
  int neg = 0;
  if (v < 0) { neg = 1; u = (unsigned int)(-(long long)v); }
  else       { u = (unsigned int)v; }

  while (u >= 100) {
    unsigned int q = u / 100;
    unsigned int r = u - q * 100;
    buf[n++] = digits2[r * 2 + 1];
    buf[n++] = digits2[r * 2];
    u = q;
  }
  if (u >= 10) {
    buf[n++] = digits2[u * 2 + 1];
    buf[n++] = digits2[u * 2];
  } else {
    buf[n++] = (char)('0' + u);
  }
  if (neg) buf[n++] = '-';

  int o = 0;
  while (n--) out[o++] = buf[n];
  out[o++] = ' ';
  return o;
}

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

  /* Match reference behavior for degenerate sizes:
     - a <= 0 or c <= 0: emit nothing (reference would not enter outer loops). */
  if (a <= 0 || c <= 0) return 0;

  /* Upper-bound bytes per cell: '-' + 10 digits + ' '. */
  const size_t cell_cap = 12;
  const size_t row_cap = (size_t)c * cell_cap + 1; /* +1 for '\n' */

  /* Output batching (Strategy 2): aim for ~1 MiB buffer, at least one row. */
  size_t target_bytes = (size_t)1 << 20;
  int batch_rows = (int)(target_bytes / row_cap);
  if (batch_rows < 1) batch_rows = 1;
  if (batch_rows > a) batch_rows = a;
  size_t out_cap = (size_t)batch_rows * row_cap;
  char *outbuf = (char*)malloc(out_cap);
  if (!outbuf) return 1;
  size_t outlen = 0;
  int rows_in_batch = 0;

  /* b <= 0: every cell of C is zero; skip GEMM entirely. */
  if (b <= 0) {
    for (int i = 0; i < a; i++) {
      char *p = outbuf + outlen;
      for (int j = 0; j < c; j++) {
        *p++ = '0';
        *p++ = ' ';
      }
      *p++ = '\n';
      outlen = (size_t)(p - outbuf);
      rows_in_batch++;
      if (rows_in_batch == batch_rows) {
        fwrite(outbuf, 1, outlen, stdout);
        outlen = 0;
        rows_in_batch = 0;
      }
    }
    if (outlen) fwrite(outbuf, 1, outlen, stdout);
    free(outbuf);
    return 0;
  }

  /* Flat allocations replace VLAs so that large sizes (e.g. 400^3) succeed. */
  int *A = (int*)calloc((size_t)a * (size_t)b, sizeof(int));
  int *B = (int*)calloc((size_t)b * (size_t)c, sizeof(int));
  int *C = (int*)calloc((size_t)a * (size_t)c, sizeof(int));
  if (!A || !B || !C) {
    free(A); free(B); free(C); free(outbuf);
    return 1;
  }

  /* Identity init (same as reference). */
  {
    int mab = a < b ? a : b;
    for (int i = 0; i < mab; i++) A[(size_t)i * b + i] = 1;
    int mbc = b < c ? b : c;
    for (int i = 0; i < mbc; i++) B[(size_t)i * c + i] = 1;
  }

  /* Strategy 1: cache-blocked i-k-j GEMM.
     C is zero-initialised by calloc, so accumulation is correct. */
  {
    const int JB = 128;
    const int KB = 64;
    int * __restrict__ Cp = C;
    const int * __restrict__ Ap = A;
    const int * __restrict__ Bp = B;
    for (int jj = 0; jj < c; jj += JB) {
      int jmax = jj + JB; if (jmax > c) jmax = c;
      for (int kk = 0; kk < b; kk += KB) {
        int kmax = kk + KB; if (kmax > b) kmax = b;
        for (int i = 0; i < a; i++) {
          int * __restrict__ Crow = Cp + (size_t)i * c;
          const int * __restrict__ Arow = Ap + (size_t)i * b;
          for (int k = kk; k < kmax; k++) {
            int aik = Arow[k];
            if (aik == 0) continue;
            const int * __restrict__ Brow = Bp + (size_t)k * c;
            #pragma clang loop vectorize(enable) interleave(enable)
            for (int j = jj; j < jmax; j++) {
              Crow[j] += aik * Brow[j];
            }
          }
        }
      }
    }
  }

  /* Output phase (Strategy 2): build rows into outbuf, fwrite per batch. */
  for (int i = 0; i < a; i++) {
    const int *Crow = C + (size_t)i * c;
    char *p = outbuf + outlen;
    for (int j = 0; j < c; j++) {
      p += write_int_space(p, Crow[j]);
    }
    *p++ = '\n';
    outlen = (size_t)(p - outbuf);
    rows_in_batch++;
    if (rows_in_batch == batch_rows) {
      fwrite(outbuf, 1, outlen, stdout);
      outlen = 0;
      rows_in_batch = 0;
    }
  }
  if (outlen) fwrite(outbuf, 1, outlen, stdout);

  free(A); free(B); free(C); free(outbuf);
  return 0;
}
