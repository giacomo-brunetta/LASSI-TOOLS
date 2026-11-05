/* C fixture entry point for Parboil's original CPU gridding_Gold. */
#include <stdlib.h>
#include "UDTypes.h"
#ifndef LASSI_GRID_SIDE
#define LASSI_GRID_SIDE 128
#endif
#ifndef LASSI_GRID_SAMPLES
#define LASSI_GRID_SAMPLES 262144
#endif
int gridding_Gold(unsigned int,parameters,ReconstructionSample*,float*,unsigned int,cmplx*,float*);
int main(void) {
  int n=LASSI_GRID_SAMPLES, side=LASSI_GRID_SIDE;
  int cells=side*side*side;
  float (*samples)[6]=calloc((size_t)n,sizeof(*samples));
  float (*grid)[2]=calloc((size_t)cells,sizeof(*grid));
  float *density=calloc((size_t)cells,sizeof(*density));
  if (!samples || !grid || !density) return 2;
  for (int i=0;i<n;++i) {
    samples[i][0]=1; samples[i][1]=0.5; samples[i][2]=(float)(i%side);
    samples[i][3]=(float)((i/side)%side); samples[i][4]=(float)((i/(side*side))%side); samples[i][5]=1;
  }
  parameters parameters_value={.numSamples=n,.gridSize={side,side,side},.oversample=1.25f,.kernelWidth=3,.useLUT=0};
  /* LASSI_BEGIN */
  gridding_Gold((unsigned int)n,parameters_value,(ReconstructionSample*)samples,NULL,0,(cmplx*)grid,density);
  /* LASSI_END */
  free(samples);free(grid);free(density);return 0;
}
