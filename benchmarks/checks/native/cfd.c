/* One complete three-stage RK Euler update on a LARGE tetrahedral mesh. */
#include <stdlib.h>
#ifndef LASSI_CFD_N
#define LASSI_CFD_N 105456
#endif
int lassi_cfd(int,const float*,float*,int*,float*,float*);
int main(void) {
  int n=LASSI_CFD_N;
  float (*state)[LASSI_CFD_N]=calloc(5,sizeof(*state));
  float *areas=calloc((size_t)n,sizeof(*areas));
  int (*neighbors)[LASSI_CFD_N]=calloc(4,sizeof(*neighbors));
  float (*normals)[4][LASSI_CFD_N]=calloc(3,sizeof(*normals));
  float (*updated)[LASSI_CFD_N]=calloc(5,sizeof(*updated));
  if (!state || !areas || !neighbors || !normals || !updated) return 2;
  for (int i=0;i<n;++i) {
    areas[i]=1.0f/6.0f;state[0][i]=1.4f;state[1][i]=1.68f;state[4][i]=3.508f;
    for(int j=0;j<4;++j) neighbors[j][i]=-2;
    normals[0][0][i]=-0.5f;normals[1][1][i]=-0.5f;normals[2][2][i]=-0.5f;
    normals[0][3][i]=normals[1][3][i]=normals[2][3][i]=0.5f;
  }
  /* LASSI_BEGIN */
  if(lassi_cfd(n,(float*)state,areas,(int*)neighbors,(float*)normals,(float*)updated)) return 3;
  /* LASSI_END */
  free(state);free(areas);free(neighbors);free(normals);free(updated);return 0;
}
