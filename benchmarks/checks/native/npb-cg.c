/* C entry point to the exact NPB 3.4.4 25-iteration conjugate-gradient solve. */
#include <stdlib.h>
#ifndef LASSI_CG_N
#define LASSI_CG_N 75000
#endif
void lassi_npb_cg(int,int,const int*,const int*,const double*,const double*,double*,double*);
int main(void) {
  int n=LASSI_CG_N,nnz=3*n-2;
  int *rows=calloc((size_t)n+1,sizeof(*rows)),*columns=calloc((size_t)nnz,sizeof(*columns));
  double *values=calloc((size_t)nnz,sizeof(*values)),*rhs=calloc((size_t)n,sizeof(*rhs));
  double *solution=calloc((size_t)n,sizeof(*solution)),residual=0;
  if(!rows || !columns || !values || !rhs || !solution) return 2;
  int cursor=0;
  for(int i=0;i<n;++i) {
    rows[i]=cursor+1;
    if(i>0) {columns[cursor]=i;values[cursor++]=-1;}
    columns[cursor]=i+1;values[cursor++]=4.0+(i%7)*0.1;
    if(i<n-1) {columns[cursor]=i+2;values[cursor++]=-1;}
    rhs[i]=1+(i%13)*0.03;
  }
  rows[n]=cursor+1;
  /* LASSI_BEGIN */
  lassi_npb_cg(n,nnz,rows,columns,values,rhs,solution,&residual);
  /* LASSI_END */
  free(rows);free(columns);free(values);free(rhs);free(solution);return 0;
}
