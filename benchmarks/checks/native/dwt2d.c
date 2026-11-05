///
/// @file    fdwt97.cu
/// @brief   CUDA implementation of forward 9/7 2D DWT.
/// @author  Martin Jirman (207962@mail.muni.cz)
/// @date    2011-01-20 13:18
///
///
/// Copyright (c) 2011 Martin Jirman
/// All rights reserved.
///
/// Redistribution and use in source and binary forms, with or without
/// modification, are permitted provided that the following conditions are met:
///
///     * Redistributions of source code must retain the above copyright
///       notice, this list of conditions and the following disclaimer.
///     * Redistributions in binary form must reproduce the above copyright
///       notice, this list of conditions and the following disclaimer in the
///       documentation and/or other materials provided with the distribution.
///
/// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
/// AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
/// IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
/// ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
/// LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
/// CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
/// SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
/// INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
/// CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
/// ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
/// POSSIBILITY OF SUCH DAMAGE.
///


/* Serial C port of the pinned lifting, mirrored edges, normalization and packed
 * LL/HL/LH/HH layout. This is a CPU reference profile, not CUDA execution. */
#include <stdlib.h>
#include <string.h>
#include <math.h>
#ifndef LASSI_DWT_SIDE
#define LASSI_DWT_SIDE 2048
#define LASSI_DWT_LEVELS 5
#endif
static void lifting(float *v,int n,int stride,int inverse) {
  const float coefficients[4]={-1.586134342f,-0.05298011854f,0.8829110762f,0.4435068522f};
  const float scale=1.23017410491400f;
  if(inverse) for(int i=0;i<n;++i) v[i*stride]*=(i&1)?1.0f/scale:scale;
  for(int step=0;step<4;++step) {
    int k=inverse?3-step:step, parity=(k&1)?0:1;
    float c=inverse?-coefficients[k]:coefficients[k];
    for(int i=parity;i<n;i+=2) {
      int left=i?i-1:1,right=i+1<n?i+1:n-2;
      v[i*stride]+=c*(v[left*stride]+v[right*stride]);
    }
  }
  if(!inverse) for(int i=0;i<n;++i) v[i*stride]*=(i&1)?scale:1.0f/scale;
}
static void transform(const float *input,float *output,int w,int h,int levels,int inverse) {
  size_t count=(size_t)w*h,quarter=count/4;
  float *temp=malloc(count*sizeof(*temp));
  float *nested=malloc(count*sizeof(*nested));
  if(!temp || !nested) exit(2);
  if(inverse) {
    memcpy(nested,input,count*sizeof(*nested));
    if(levels>1) transform(input,nested,w/2,h/2,levels-1,1);
    for(int y=0;y<h;++y) for(int x=0;x<w;++x)
      temp[(size_t)y*w+x]=nested[((y&1)*2+(x&1))*quarter+(size_t)(y/2)*(w/2)+x/2];
    for(int x=0;x<w;++x) lifting(temp+x,h,w,1);
    for(int y=0;y<h;++y) lifting(temp+(size_t)y*w,w,1,1);
    memcpy(output,temp,count*sizeof(*temp));
  } else {
    memcpy(temp,input,count*sizeof(*temp));
    for(int y=0;y<h;++y) lifting(temp+(size_t)y*w,w,1,0);
    for(int x=0;x<w;++x) lifting(temp+x,h,w,0);
    for(int y=0;y<h;++y) for(int x=0;x<w;++x)
      output[((y&1)*2+(x&1))*quarter+(size_t)(y/2)*(w/2)+x/2]=temp[(size_t)y*w+x];
    if(levels>1) {
      transform(output,nested,w/2,h/2,levels-1,0);
      memcpy(output,nested,quarter*sizeof(*output));
    }
  }
  free(temp);free(nested);
}
int main(void) {
  int width=LASSI_DWT_SIDE,height=LASSI_DWT_SIDE,levels=LASSI_DWT_LEVELS;
  float (*image)[LASSI_DWT_SIDE]=calloc((size_t)height,sizeof(*image));
  float *coefficients=calloc((size_t)width*height,sizeof(*coefficients));
  float (*reconstruction)[LASSI_DWT_SIDE]=calloc((size_t)height,sizeof(*reconstruction));
  if(!image || !coefficients || !reconstruction) return 2;
  for(int y=0;y<height;++y) for(int x=0;x<width;++x) image[y][x]=(float)((x+3*y)%256)/255.0f;
  /* LASSI_BEGIN */
  transform((float*)image,coefficients,width,height,levels,0);
  transform(coefficients,(float*)reconstruction,width,height,levels,1);
  /* LASSI_END */
  free(image);free(coefficients);free(reconstruction);return 0;
}
