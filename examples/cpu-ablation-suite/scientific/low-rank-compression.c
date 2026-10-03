/* Fixed-iteration power deflation for a rank-four image approximation. */
#include "common.h"

#define COMPONENTS 4
#define POWER_STEPS 8

int main(void) {
  double image[SIZE][SIZE], residual[SIZE][SIZE], approximation[SIZE][SIZE];
  double left[SIZE], right[SIZE];

  for (int row = 0; row < SIZE; ++row)
    for (int column = 0; column < SIZE; ++column) {
      image[row][column] = 2.0*sin(0.07*(row+1))*cos(0.11*(column+1))
          + 1.3*cos(0.03*(row+1))*sin(0.05*(column+1))
          + 0.8*(row+1)*(column+1)/(SIZE*SIZE)
          + 0.12*sin(0.013*(row+1)*(column+1));
      residual[row][column] = image[row][column];
      approximation[row][column] = 0.0;
    }

  for (int component = 0; component < COMPONENTS; ++component) {
    double norm = 0.0;
    for (int column = 0; column < SIZE; ++column) {
      right[column] = 1.0 + 0.01*(column+component);
      norm += right[column]*right[column];
    }
    norm = sqrt(norm);
    for (int column = 0; column < SIZE; ++column) right[column] /= norm;

    for (int step = 0; step < POWER_STEPS; ++step) {
      norm = 0.0;
      for (int row = 0; row < SIZE; ++row) {
        left[row] = 0.0;
        for (int column = 0; column < SIZE; ++column)
          left[row] += residual[row][column]*right[column];
        norm += left[row]*left[row];
      }
      norm = sqrt(norm);
      for (int row = 0; row < SIZE; ++row) left[row] /= norm;

      norm = 0.0;
      for (int column = 0; column < SIZE; ++column) {
        right[column] = 0.0;
        for (int row = 0; row < SIZE; ++row)
          right[column] += residual[row][column]*left[row];
        norm += right[column]*right[column];
      }
      norm = sqrt(norm);
      for (int column = 0; column < SIZE; ++column) right[column] /= norm;
    }

    double singular_value = 0.0;
    for (int row = 0; row < SIZE; ++row)
      for (int column = 0; column < SIZE; ++column)
        singular_value += left[row]*residual[row][column]*right[column];
    for (int row = 0; row < SIZE; ++row)
      for (int column = 0; column < SIZE; ++column) {
        double contribution = singular_value*left[row]*right[column];
        approximation[row][column] += contribution;
        residual[row][column] -= contribution;
      }
  }

  double squared_error = 0.0, signal_energy = 0.0;
  for (int row = 0; row < SIZE; ++row)
    for (int column = 0; column < SIZE; ++column) {
      squared_error += residual[row][column]*residual[row][column];
      signal_energy += image[row][column]*image[row][column];
      dump(approximation[row][column]);
    }
  dump(squared_error/signal_energy);
  dump((double)COMPONENTS);
  return 0;
}
