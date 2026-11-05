! ABI/grid setup around original setup/resid/mg3P/comm3 routines.
subroutine lassi_npb_mg(rhs,solution) bind(C)
  use iso_c_binding
  use mg_data
  use mg_fields
  implicit none
  real(c_double),intent(in) :: rhs(nx_default,ny_default,nz_default)
  real(c_double),intent(out) :: solution(nx_default,ny_default,nz_default)
  real(c_double),allocatable :: padded(:,:,:),out(:,:,:)
  integer :: n1,n2,n3,k,iteration
  call alloc_space
  u=0;v=0;r=0;timeron=.false.;debug_vec=0
  lt=lt_default;lb=1;nx(lt)=nx_default;ny(lt)=ny_default;nz(lt)=nz_default
  call setup(n1,n2,n3,k)
  allocate(padded(n1,n2,n3),out(n1,n2,n3))
  padded=0;padded(2:n1-1,2:n2-1,2:n3-1)=rhs
  call comm3(padded,n1,n2,n3,lt)
  v=reshape(padded,[size(v)])
  a=[-8.0d0/3.0d0,0.0d0,1.0d0/6.0d0,1.0d0/12.0d0]
  c=[-3.0d0/17.0d0,1.0d0/33.0d0,-1.0d0/61.0d0,0.0d0]
  call resid(u,v,r,n1,n2,n3,a,lt)
  do iteration=1,4
    call mg3P(u,v,r,a,c,n1,n2,n3,lt)
    call resid(u,v,r,n1,n2,n3,a,lt)
  end do
  out=reshape(u(1:n1*n2*n3),[n1,n2,n3])
  solution=out(2:n1-1,2:n2-1,2:n3-1)
  deallocate(padded,out)
  call free_space
end subroutine
