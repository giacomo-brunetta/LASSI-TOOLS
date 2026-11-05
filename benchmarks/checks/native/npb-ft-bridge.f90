! Pack/unpack padding around the unchanged NPB 3.4.4 FFT routine.
subroutine lassi_npb_ft(field,spectrum) bind(C)
  use iso_c_binding
  use ft_data
  implicit none
  complex(c_double_complex),intent(in) :: field(nx,ny,nz)
  complex(c_double_complex),intent(out) :: spectrum(nx,ny,nz)
  complex(c_double_complex),allocatable :: first(:,:,:),second(:,:,:)
  allocate(first(nx+1,ny,nz),second(nx+1,ny,nz))
  first=0;second=0;first(1:nx,:,:)=field
  dims=[nx,ny,nz];fftblock=fftblock_default;fftblockpad=fftblockpad_default
  timers_enabled=.false.
  call fft_init(nx)
  call fft(1,first,second)
  spectrum=second(1:nx,:,:)
  deallocate(first,second)
end subroutine
