/* JPEG-like 8x8 DCT, scalar quantization, and reconstruction. */
#include "common.h"

#define BLOCK 8

int main(void) {
  double image[SIZE][SIZE], coefficients[SIZE][SIZE], reconstructed[SIZE][SIZE];
  const double pi = acos(-1.0);
  int nonzero = 0;

  for (int row = 0; row < SIZE; ++row)
    for (int column = 0; column < SIZE; ++column)
      image[row][column] = 96.0 + 28.0*sin(2*pi*row/SIZE)
          + 19.0*cos(4*pi*column/SIZE) + 0.15*row + 0.08*column
          + 7.0*sin(2*pi*(row + column)/SIZE);

  for (int block_row = 0; block_row < SIZE; block_row += BLOCK)
    for (int block_column = 0; block_column < SIZE; block_column += BLOCK) {
      for (int u = 0; u < BLOCK; ++u)
        for (int v = 0; v < BLOCK; ++v) {
          double sum = 0.0;
          double scale_u = u == 0 ? 1.0/sqrt(2.0) : 1.0;
          double scale_v = v == 0 ? 1.0/sqrt(2.0) : 1.0;
          for (int x = 0; x < BLOCK; ++x)
            for (int y = 0; y < BLOCK; ++y)
              sum += image[block_row+x][block_column+y]
                  * cos(pi*(2*x+1)*u/16.0) * cos(pi*(2*y+1)*v/16.0);
          double quantum = 1.0 + 0.75*(u+v);
          double transformed = 0.25*scale_u*scale_v*sum;
          coefficients[block_row+u][block_column+v] = round(transformed/quantum)*quantum;
          if (coefficients[block_row+u][block_column+v] != 0.0) ++nonzero;
        }
      for (int x = 0; x < BLOCK; ++x)
        for (int y = 0; y < BLOCK; ++y) {
          double sum = 0.0;
          for (int u = 0; u < BLOCK; ++u)
            for (int v = 0; v < BLOCK; ++v) {
              double scale_u = u == 0 ? 1.0/sqrt(2.0) : 1.0;
              double scale_v = v == 0 ? 1.0/sqrt(2.0) : 1.0;
              sum += scale_u*scale_v*coefficients[block_row+u][block_column+v]
                  * cos(pi*(2*x+1)*u/16.0) * cos(pi*(2*y+1)*v/16.0);
            }
          reconstructed[block_row+x][block_column+y] = 0.25*sum;
        }
    }

  double squared_error = 0.0;
  for (int row = 0; row < SIZE; ++row)
    for (int column = 0; column < SIZE; ++column) {
      double error = reconstructed[row][column] - image[row][column];
      squared_error += error*error;
      dump(reconstructed[row][column]);
    }
  dump(squared_error/(SIZE*SIZE));
  dump((double)nonzero);
  return 0;
}
