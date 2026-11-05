/* Trusted fixture allocator: define unused storage before native initialization.
 * The upstream initializers and computational kernels are unchanged. */
#define polybench_alloc_data lassi_original_alloc_data
#include "polybench.c"
#undef polybench_alloc_data

void *polybench_alloc_data(unsigned long long int n, int elt_size)
{
  void *result = lassi_original_alloc_data(n, elt_size);
  memset(result, 0, (size_t)n * (size_t)elt_size);
  return result;
}
