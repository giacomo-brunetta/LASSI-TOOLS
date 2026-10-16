/* Four stable biquad filters over a deterministic multi-tone signal. */
#include "common.h"

#define FILTERS 4

int main(void) {
  const double b0[FILTERS] = {0.06745527, 0.20657208, 0.39133577, 0.63894553};
  const double b1[FILTERS] = {0.13491055, 0.41314417, 0.0, -1.27789105};
  const double b2[FILTERS] = {0.06745527, 0.20657208, -0.39133577, 0.63894553};
  const double a1[FILTERS] = {-1.14298050, -0.36952738, -0.36952738, -1.14298050};
  const double a2[FILTERS] = {0.41280160, 0.19581571, 0.21767222, 0.41280160};
  double signal[SIZE], output[FILTERS][SIZE];

  for (int sample = 0; sample < SIZE; ++sample)
    signal[sample] = sin(0.09*sample) + 0.35*cos(0.31*sample)
        + 0.12*sin(0.71*sample) + (sample % 17 == 0 ? 0.5 : 0.0);

  for (int filter = 0; filter < FILTERS; ++filter) {
    double state_one = 0.0, state_two = 0.0;
    for (int sample = 0; sample < SIZE; ++sample) {
      double value = b0[filter]*signal[sample] + state_one;
      state_one = b1[filter]*signal[sample] - a1[filter]*value + state_two;
      state_two = b2[filter]*signal[sample] - a2[filter]*value;
      output[filter][sample] = value;
    }
  }

  for (int filter = 0; filter < FILTERS; ++filter)
    for (int sample = 0; sample < SIZE; ++sample)
      dump(output[filter][sample]);
  return 0;
}
