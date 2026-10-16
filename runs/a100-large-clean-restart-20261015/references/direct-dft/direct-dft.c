/* Direct (not FFT) forward DFT; output interleaved real/imaginary pairs. */
#include "common.h"
int main(void) {
  double signal[SIZE], real[SIZE], imag[SIZE];
  const double pi = acos(-1.0);
  for (int j = 0; j < SIZE; ++j)
    signal[j] = sin(2*pi*3*j/SIZE) + 0.25*cos(2*pi*5*j/SIZE) + 0.01*j;
  for (int k = 0; k < SIZE; ++k) {
    real[k] = imag[k] = 0.0;
    for (int j = 0; j < SIZE; ++j) {
      double angle = 2*pi*k*j/SIZE;
      real[k] += signal[j]*cos(angle);
      imag[k] -= signal[j]*sin(angle);
    }
  }
  for (int k = 0; k < SIZE; ++k) { dump(real[k]); dump(imag[k]); }
  return 0;
}
