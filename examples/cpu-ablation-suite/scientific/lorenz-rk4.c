/* Batched Lorenz systems: sigma=10, rho=28, beta=8/3, dt=.001; final states. */
#include "common.h"
static void rhs(const double y[3], double result[3]) {
  result[0] = 10*(y[1]-y[0]);
  result[1] = y[0]*(28-y[2])-y[1];
  result[2] = y[0]*y[1]-(8.0/3.0)*y[2];
}
int main(void) {
  double state[SIZE][3];
  const double dt = 0.001;
  for (int i = 0; i < SIZE; ++i)
    for (int d = 0; d < 3; ++d) state[i][d] = 1.0 + 0.01*i + 0.1*d;
  for (int step = 0; step < STEPS; ++step)
    for (int i = 0; i < SIZE; ++i) {
      double k1[3], k2[3], k3[3], k4[3], temp[3];
      rhs(state[i], k1);
      for (int d = 0; d < 3; ++d) temp[d] = state[i][d]+dt*0.5*k1[d];
      rhs(temp, k2);
      for (int d = 0; d < 3; ++d) temp[d] = state[i][d]+dt*0.5*k2[d];
      rhs(temp, k3);
      for (int d = 0; d < 3; ++d) temp[d] = state[i][d]+dt*k3[d];
      rhs(temp, k4);
      for (int d = 0; d < 3; ++d)
        state[i][d] += dt*(k1[d]+2*k2[d]+2*k3[d]+k4[d])/6;
    }
  for (int i = 0; i < SIZE; ++i)
    for (int d = 0; d < 3; ++d) dump(state[i][d]);
  return 0;
}
