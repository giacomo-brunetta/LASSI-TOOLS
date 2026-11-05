/* Execute the complete pinned Rodinia adaptive ODE solver on an ensemble. */
#include <stdlib.h>
#include <string.h>
#include "myocyte-initial.h"
#ifndef LASSI_MYO_CELLS
#define LASSI_MYO_CELLS 64
#endif
#ifndef LASSI_MYO_STEPS
#define LASSI_MYO_STEPS 100
#endif
int solver(float **,float *,int,float *,int);
int main(void) {
  int n=LASSI_MYO_CELLS, steps=LASSI_MYO_STEPS;
  float (*initial)[91]=calloc((size_t)n,sizeof(*initial));
  float parameters[16]; memcpy(parameters,parameter_values,sizeof(parameters));
  float (*trajectory)[LASSI_MYO_STEPS+1][91]=calloc((size_t)n,sizeof(*trajectory));
  float *times=calloc((size_t)steps+1,sizeof(*times));
  float **frames=calloc((size_t)steps+1,sizeof(*frames));
  if (!initial || !trajectory || !times || !frames) return 2;
  for (int i=0;i<n;++i) memcpy(initial[i],initial_values,sizeof(initial_values));
  /* LASSI_BEGIN */
  for (int i=0;i<n;++i) {
    for (int j=0;j<=steps;++j) frames[j]=trajectory[i][j];
    memcpy(frames[0],initial[i],sizeof(initial[i]));
    if (solver(frames,times,steps,parameters,1)) return 3;
  }
  /* LASSI_END */
  free(initial);free(trajectory);free(times);free(frames);return 0;
}
