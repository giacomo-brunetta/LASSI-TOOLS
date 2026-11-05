/* Algorithm object construction follows pinned test/drivers/test_rsvd.cc. */
#include <RandLAPACK.hh>
#include <RandBLAS.hh>
#include <vector>
#include <cstdlib>
#include <algorithm>
extern "C" int lassi_randomized_svd(int m,int n,int rank,const double *input,double *singular,double *output) {
  using T=double;using RNG=r123::Philox4x32;
  try {
    std::vector<T> a((size_t)m*n);for(int i=0;i<m;++i) for(int j=0;j<n;++j) a[i+(size_t)j*m]=input[(size_t)i*n+j];
    RandLAPACK::PLUL<T> stab(false,false);
    RandLAPACK::RS<T,RNG> rs(stab,2,1,false,false);
    RandLAPACK::CholQRQ<T> orth_rf(false,false);
    RandLAPACK::RF<T,RNG> rf(rs,orth_rf,false,false);
    RandLAPACK::CholQRQ<T> orth_qb(false,false);
    RandLAPACK::QB<T,RNG> qb(rf,orth_qb,false,false);
    RandLAPACK::RSVD<T,RNG> rsvd(qb,rank);
    RandBLAS::RNGState<RNG> state(42);
    int64_t k=rank;T *u=nullptr,*s=nullptr,*v=nullptr;
    int status=rsvd.call(m,n,a.data(),k,1e-10,u,s,v,state);
    if(status || k>rank || k<1) {free(u);free(s);free(v);return 1;}
    std::fill(singular,singular+rank,0.0);std::copy(s,s+k,singular);
    for(int i=0;i<m;++i) for(int j=0;j<n;++j) {
      double value=0;for(int64_t p=0;p<k;++p) value+=u[i+p*m]*s[p]*v[j+p*n];
      output[(size_t)i*n+j]=value;
    }
    free(u);free(s);free(v);return 0;
  } catch(const std::exception &e) {std::cerr<<e.what()<<std::endl;return 1;}
}
