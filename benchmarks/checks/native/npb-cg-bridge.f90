! Only ABI and storage setup; conj_grad remains the pinned NASA routine.
subroutine lassi_npb_cg(n,nnz,rows,columns,values,rhs,solution,residual) bind(C)
  use iso_c_binding
  use cg_data
  implicit none
  integer(c_int),value :: n,nnz
  integer(c_int),intent(in) :: rows(n+1),columns(nnz)
  real(c_double),intent(in) :: values(nnz),rhs(n)
  real(c_double),intent(out) :: solution(n),residual
  allocate(a(nnz),colidx(nnz),rowstr(n+1),x(n+2),z(n+2),p(n+2),q(n+2),r(n+2))
  naa=n;firstrow=1;lastrow=n;firstcol=1;lastcol=n;nzz=nnz;timeron=.false.
  a=values;colidx=columns;rowstr=rows;x=0;x(1:n)=rhs
  call conj_grad(residual)
  solution=z(1:n)
  deallocate(a,colidx,rowstr,x,z,p,q,r)
end subroutine
