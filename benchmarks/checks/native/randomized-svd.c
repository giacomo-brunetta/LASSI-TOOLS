/* Full RandLAPACK RSVD and reconstruction, with a fixed algorithm RNG seed. */
#include <stdlib.h>
#include <math.h>
#ifndef LASSI_RSVD_M
#define LASSI_RSVD_M 2048
#define LASSI_RSVD_N 1024
#define LASSI_RSVD_K 32
#endif
int lassi_randomized_svd(int,int,int,const double*,double*,double*);
int main(void) {
  int m=LASSI_RSVD_M,n=LASSI_RSVD_N,rank=LASSI_RSVD_K;
  double (*matrix)[LASSI_RSVD_N]=calloc((size_t)m,sizeof(*matrix));
  double (*reconstruction)[LASSI_RSVD_N]=calloc((size_t)m,sizeof(*reconstruction));
  double singular_values[LASSI_RSVD_K]={0};
  if(!matrix || !reconstruction) return 2;
  for(int i=0;i<m;++i) for(int j=0;j<n;++j) {
    double v=0;for(int k=0;k<rank*2;++k) v+=sin((i+1)*(k+1)*0.03)*cos((j+1)*(k+1)*0.02)/(k+1);
    matrix[i][j]=v + 0.001*cos((i+1)*(j+1)*0.731);
  }
  /* LASSI_BEGIN */
  if(lassi_randomized_svd(m,n,rank,(double*)matrix,singular_values,(double*)reconstruction)) return 3;
  /* LASSI_END */
  free(matrix);free(reconstruction);return 0;
}
