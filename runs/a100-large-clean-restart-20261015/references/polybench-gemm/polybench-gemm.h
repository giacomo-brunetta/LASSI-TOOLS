#include "gemm.h"
#undef DATA_PRINTF_MODIFIER
#ifdef DATA_TYPE_IS_INT
#define DATA_PRINTF_MODIFIER "%d "
#else
#define DATA_PRINTF_MODIFIER "%.17g "
#endif
