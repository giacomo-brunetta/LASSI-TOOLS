/* In-memory C interface to the pinned ITK histogram/entropy computation. */
#include <stdlib.h>
#ifndef LASSI_MI_SIDE
#define LASSI_MI_SIDE 2048
#endif
int lassi_mutual_information(int,int,const unsigned char*,const unsigned char*,double*,double*);
int main(void) {
  int width=LASSI_MI_SIDE,height=LASSI_MI_SIDE;
  unsigned char (*image1)[LASSI_MI_SIDE]=calloc((size_t)height,sizeof(*image1));
  unsigned char (*image2)[LASSI_MI_SIDE]=calloc((size_t)height,sizeof(*image2));
  double histogram[255][255]={{0}},statistics[4]={0};
  if(!image1 || !image2) return 2;
  for(int y=0;y<height;++y) for(int x=0;x<width;++x) image1[y][x]=image2[y][x]=(unsigned char)((x+y)%256);
  /* LASSI_BEGIN */
  if(lassi_mutual_information(width,height,(unsigned char*)image1,(unsigned char*)image2,(double*)histogram,statistics)) return 3;
  /* LASSI_END */
  free(image1);free(image2);return 0;
}
