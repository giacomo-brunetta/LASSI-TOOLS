/* C fixture entry point for the pinned Rodinia LavaMD kernel. */
#include <stdlib.h>
#include <math.h>
#include "main.h"
#include "kernel/kernel_cpu.h"
#ifndef LASSI_LAVA_SIDE
#define LASSI_LAVA_SIDE 10
#endif
int main(int argc, char **argv) {
  (void)argc; (void)argv;
  int side = LASSI_LAVA_SIDE, boxes = side*side*side, n = boxes*NUMBER_PAR_PER_BOX;
  double alpha = 0.5;
  double (*positions)[4] = calloc((size_t)n, sizeof(*positions));
  double *charges = calloc((size_t)n, sizeof(*charges));
  double (*forces)[4] = calloc((size_t)n, sizeof(*forces));
  box_str *box = calloc((size_t)boxes, sizeof(*box));
  if (!positions || !charges || !forces || !box) return 2;
  for (int b=0; b<boxes; ++b) {
    box[b].x = b%side; box[b].y = (b/side)%side; box[b].z = b/(side*side);
    box[b].number=b; box[b].offset=(long)b*NUMBER_PAR_PER_BOX;
    for (int dz=-1; dz<=1; ++dz) for (int dy=-1; dy<=1; ++dy) for (int dx=-1; dx<=1; ++dx) {
      int x=box[b].x+dx, y=box[b].y+dy, z=box[b].z+dz;
      if ((!dx&&!dy&&!dz) || x<0 || y<0 || z<0 || x>=side || y>=side || z>=side) continue;
      nei_str *neighbor=&box[b].nei[box[b].nn++];
      neighbor->x=x; neighbor->y=y; neighbor->z=z;
      neighbor->number=(z*side+y)*side+x;
      neighbor->offset=(long)neighbor->number*NUMBER_PAR_PER_BOX;
    }
  }
  for (int i=0; i<n; ++i) {
    charges[i]=1; positions[i][1]=0.2; positions[i][2]=0.3; positions[i][3]=0.4;
    positions[i][0]=0.29;
  }
  par_str par = {.alpha=alpha};
  dim_str dim = {.cores_arg=1, .boxes1d_arg=side, .number_boxes=boxes, .space_elem=n};
  /* LASSI_BEGIN */
  par.alpha=alpha;
  kernel_cpu(par,dim,box,(FOUR_VECTOR*)positions,charges,(FOUR_VECTOR*)forces);
  /* LASSI_END */
  free(box); free(positions); free(charges); free(forces);
  return 0;
}
