/* Retain Rodinia's original flux, timestep and RK update implementations. */
#define main rodinia_cfd_original_main
#include "euler3d_cpu.cpp"
#undef main
#include <vector>
extern "C" int lassi_cfd(int n,const float *state,float *areas,int *neighbors,float *normals,float *updated) {
  float ff[5]={1.4f,1.68f,0,0,3.508f};
  float3 velocity={1.2f,0,0},momentum={1.68f,0,0},mx,my,mz,energy;
  float pressure=1.0f;
  compute_flux_contribution(ff[0],momentum,ff[4],pressure,velocity,mx,my,mz,energy);
  std::vector<float> old(state,state+5*n),flux(5*n),step(n);
  std::copy(state,state+5*n,updated);
  compute_step_factor(n,updated,areas,step.data());
  for(int j=0;j<RK;++j) {
    compute_flux(n,neighbors,normals,updated,flux.data(),ff,mx,my,mz,energy);
    time_step(j,n,old.data(),updated,step.data(),flux.data());
  }
  return 0;
}
