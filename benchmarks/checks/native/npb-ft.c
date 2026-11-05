/* Full NPB 3.4.4 three-dimensional forward FFT; interleaved real/imaginary ABI. */
#include <stdlib.h>
#include <math.h>
#ifndef LASSI_FT_X
#define LASSI_FT_X 512
#define LASSI_FT_Y 256
#define LASSI_FT_Z 256
#endif
void lassi_npb_ft(const double*,double*);
int main(void) {
  int nx=LASSI_FT_X,ny=LASSI_FT_Y,nz=LASSI_FT_Z;
  double (*field)[LASSI_FT_Y][LASSI_FT_X][2]=calloc((size_t)nz,sizeof(*field));
  double (*spectrum)[LASSI_FT_Y][LASSI_FT_X][2]=calloc((size_t)nz,sizeof(*spectrum));
  if(!field || !spectrum) return 2;
  for(int k=0;k<nz;++k) for(int j=0;j<ny;++j) for(int i=0;i<nx;++i) {
    field[k][j][i][0]=sin(i*0.1)+cos(j*0.2);field[k][j][i][1]=sin(k*0.3);
  }
  /* LASSI_BEGIN */
  lassi_npb_ft((double*)field,(double*)spectrum);
  /* LASSI_END */
  free(field);free(spectrum);return 0;
}
