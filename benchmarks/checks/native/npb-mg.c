/* Four complete NPB 3.4.4 multigrid V-cycles with periodic boundaries. */
#include <stdlib.h>
#include <math.h>
#ifndef LASSI_MG_SIDE
#define LASSI_MG_SIDE 256
#endif
void lassi_npb_mg(const double*,double*);
int main(void) {
  int side=LASSI_MG_SIDE;
  double (*rhs)[LASSI_MG_SIDE][LASSI_MG_SIDE]=calloc((size_t)side,sizeof(*rhs));
  double (*solution)[LASSI_MG_SIDE][LASSI_MG_SIDE]=calloc((size_t)side,sizeof(*solution));
  if(!rhs || !solution) return 2;
  for(int k=0;k<side;++k) for(int j=0;j<side;++j) for(int i=0;i<side;++i)
    rhs[k][j][i]=sin(6.283185307179586*i/side)+cos(6.283185307179586*j/side);
  /* LASSI_BEGIN */
  lassi_npb_mg((double*)rhs,(double*)solution);
  /* LASSI_END */
  free(rhs);free(solution);return 0;
}
