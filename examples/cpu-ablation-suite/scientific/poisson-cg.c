/* SPD 1D Dirichlet Poisson operator, fixed 10 CG steps, x0=0; output solution. */
#include "common.h"
int main(void) {
  double x[SIZE], r[SIZE], p[SIZE], ap[SIZE];
  double rr = 0;
  for (int i = 0; i < SIZE; ++i) {
    x[i] = 0;
    r[i] = p[i] = 1.0 + sin(0.3*(i+1));
    rr += r[i]*r[i];
  }
  for (int step = 0; step < 10; ++step) {
    double pap = 0, next_rr = 0;
    for (int i = 0; i < SIZE; ++i) {
      ap[i] = 2*p[i] - (i > 0 ? p[i-1] : 0) - (i+1 < SIZE ? p[i+1] : 0);
      pap += p[i]*ap[i];
    }
    double alpha = rr/pap;
    for (int i = 0; i < SIZE; ++i) {
      x[i] += alpha*p[i];
      r[i] -= alpha*ap[i];
      next_rr += r[i]*r[i];
    }
    double beta = next_rr/rr;
    for (int i = 0; i < SIZE; ++i) p[i] = r[i] + beta*p[i];
    rr = next_rr;
  }
  for (int i = 0; i < SIZE; ++i) dump(x[i]);
  return 0;
}
