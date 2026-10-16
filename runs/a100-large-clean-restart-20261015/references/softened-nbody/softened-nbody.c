/* Gravitational acceleration, G=1, softening squared=0.01; exclude self terms. */
#include "common.h"
int main(void) {
  double position[SIZE][3], mass[SIZE], acceleration[SIZE][3];
  for (int i = 0; i < SIZE; ++i) {
    mass[i] = 1.0 + (i % 7)*0.125;
    for (int d = 0; d < 3; ++d)
      position[i][d] = sin((i+1)*(d+1)*0.37) + 0.01*i;
  }
  for (int i = 0; i < SIZE; ++i) {
    for (int d = 0; d < 3; ++d) acceleration[i][d] = 0;
    for (int j = 0; j < SIZE; ++j) if (j != i) {
      double delta[3], squared = 0.01;
      for (int d = 0; d < 3; ++d) {
        delta[d] = position[j][d]-position[i][d];
        squared += delta[d]*delta[d];
      }
      double weight = mass[j]/(squared*sqrt(squared));
      for (int d = 0; d < 3; ++d) acceleration[i][d] += weight*delta[d];
    }
  }
  for (int i = 0; i < SIZE; ++i)
    for (int d = 0; d < 3; ++d) dump(acceleration[i][d]);
  return 0;
}
