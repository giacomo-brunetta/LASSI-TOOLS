/* Three-level 2D Haar transform, coefficient thresholding, and reconstruction. */
#include "common.h"

#define LEVELS 3

int main(void) {
  double image[SIZE][SIZE], coefficients[SIZE][SIZE], temporary[SIZE][SIZE];
  const double inverse_sqrt_two = 1.0/sqrt(2.0);

  for (int row = 0; row < SIZE; ++row)
    for (int column = 0; column < SIZE; ++column) {
      image[row][column] = 64.0 + 18.0*sin(2.0*row/SIZE)
          + 11.0*cos(3.0*column/SIZE) + 0.2*((row/8 + column/8) % 2)
          + 0.04*row*column/SIZE;
      coefficients[row][column] = image[row][column];
    }

  int width = SIZE;
  for (int level = 0; level < LEVELS; ++level) {
    int half = width/2;
    for (int row = 0; row < width; ++row)
      for (int column = 0; column < half; ++column) {
        double even = coefficients[row][2*column];
        double odd = coefficients[row][2*column+1];
        temporary[row][column] = (even+odd)*inverse_sqrt_two;
        temporary[row][column+half] = (even-odd)*inverse_sqrt_two;
      }
    for (int column = 0; column < width; ++column)
      for (int row = 0; row < half; ++row) {
        double even = temporary[2*row][column];
        double odd = temporary[2*row+1][column];
        coefficients[row][column] = (even+odd)*inverse_sqrt_two;
        coefficients[row+half][column] = (even-odd)*inverse_sqrt_two;
      }
    width = half;
  }

  int low_pass_width = width, retained = 0;
  for (int row = 0; row < SIZE; ++row)
    for (int column = 0; column < SIZE; ++column) {
      if ((row >= low_pass_width || column >= low_pass_width)
          && fabs(coefficients[row][column]) < 0.6)
        coefficients[row][column] = 0.0;
      if (coefficients[row][column] != 0.0) ++retained;
    }

  width = low_pass_width*2;
  for (int level = LEVELS-1; level >= 0; --level) {
    int half = width/2;
    for (int column = 0; column < width; ++column)
      for (int row = 0; row < half; ++row) {
        double average = coefficients[row][column];
        double detail = coefficients[row+half][column];
        temporary[2*row][column] = (average+detail)*inverse_sqrt_two;
        temporary[2*row+1][column] = (average-detail)*inverse_sqrt_two;
      }
    for (int row = 0; row < width; ++row)
      for (int column = 0; column < half; ++column) {
        double average = temporary[row][column];
        double detail = temporary[row][column+half];
        coefficients[row][2*column] = (average+detail)*inverse_sqrt_two;
        coefficients[row][2*column+1] = (average-detail)*inverse_sqrt_two;
      }
    width *= 2;
  }

  double squared_error = 0.0;
  for (int row = 0; row < SIZE; ++row)
    for (int column = 0; column < SIZE; ++column) {
      double error = coefficients[row][column] - image[row][column];
      squared_error += error*error;
      dump(coefficients[row][column]);
    }
  dump(squared_error/(SIZE*SIZE));
  dump((double)retained);
  return 0;
}
