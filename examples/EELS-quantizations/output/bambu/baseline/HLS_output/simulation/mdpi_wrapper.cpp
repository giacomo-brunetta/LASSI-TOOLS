/*
 * Politecnico di Milano
 * Code created using PandA - Version: PandA 2024.10 - Revision c2ba6936ca2ed63137095fea0b630a1c66e20e63 - Date 2026-02-23T23:56:58
 * Bambu executed with: bambu -v3 --print-dot -lm --soft-float --compiler=I386_CLANG16 --device=xc7z020-1clg484 --clock-period=10 --experimental-setup=BAMBU-BALANCED-MP --channels-number=2 --memory-allocation-policy=ALL_BRAM --disable-function-proxy --generate-tb=../../forward_kernel_testbench.c --simulate --simulator=VERILATOR --verilator-parallel --top-fname=forward_kernel input.ll 
 */

#if !defined(__cplusplus) || __cplusplus < 201103L
#error This file must be compiled with C++ 11 standard
#endif

#define _FILE_OFFSET_BITS 64

#undef printf

#include <cstdio>
#include <cstdlib>

typedef bool _Bool;

#include <sys/types.h>

#ifdef __AC_NAMESPACE
using namespace __AC_NAMESPACE;
#endif



#ifndef CDECL
#define CDECL extern "C"
#endif

#ifndef EXTERN_CDECL
#define EXTERN_CDECL extern "C"
#endif

CDECL void forward_kernel(void* P0, void* P1, void* P2);
#ifndef MDPI_MEMMAP_MODE
#define MDPI_MEMMAP_MODE MDPI_MEMMAP_DEVICE
#endif

#ifdef __cplusplus
#include <cstring>
#else
#include <string.h>
#endif

#define __LOCAL_ENTITY MDPI_ENTITY_DRIVER
#include <mdpi/mdpi_debug.h>
#include <mdpi/mdpi_driver.h>
#include <mdpi/mdpi_user.h>

#define typeof __typeof__
#ifdef __cplusplus
template <typename T> struct __m_type { typedef T type; };
template <typename T> struct __m_type<T*> { typedef typename __m_type<T>::type type; };
template <> struct __m_type<void*> { typedef typename __m_type<unsigned char>::type type; };
#define m_getptrt(val) __m_type<typeof(val)>::type*
#define m_getvalt(val) __m_type<typeof(val)>::type
template <typename T> T* m_getptr(T& obj) { return &obj; }
template <typename T> T* m_getptr(T* obj) { return obj; }
#define __m_float_distance(a, b) m_float_distance(a, b)
#else
#define m_getptrt(val) typeof(val)
#define m_getvalt(val) typeof(*val)
#define m_getptr(ptr) (ptr)
#define __m_float_distance(a, b) \
   ((typeof(a)(*)(typeof(a), typeof(a)))((sizeof(a) == sizeof(float)) ? m_float_distancef : m_float_distance))(a, b)
#define __m_floats_distance(a, b) \
   ((typeof(a)(*)(typeof(a), typeof(a)))((sizeof(a) == sizeof(float)) ? m_floats_distancef : m_floats_distance))(a, b)
#endif

#define m_cmpval(ptra, ptrb) *(ptra) != *(ptrb)
#define m_cmpmem(ptra, ptrb) memcmp(ptra, ptrb, sizeof(m_getvalt(ptrb)))
#define m_cmpflt(ptra, ptrb) __m_float_distance(*(ptra), *(ptrb)) > max_ulp
#define m_cmpflts(ptra, ptrb) __m_floats_distance(*(ptra), *(ptrb)) > max_ulp

#define _ms_setargptr(suffix, idx, ptr)                       \
   const size_t P##idx##_size_##suffix = __m_param_size(idx); \
   void* P##idx##_##suffix = malloc(P##idx##_size_##suffix);  \
   memcpy(P##idx##_##suffix, ptr, P##idx##_size_##suffix)

#define _ms_argcmp(suffix, idx, cmp)                                                                          \
   const size_t P##idx##_count_##suffix = P##idx##_size_##suffix / sizeof(m_getvalt(P##idx));                 \
   for(i = 0; i < P##idx##_count_##suffix; ++i)                                                               \
   {                                                                                                          \
      if(m_cmp##cmp((m_getptrt(P##idx))P##idx##_##suffix + i, (m_getptrt(P##idx))m_getptr(P##idx) + i))       \
      {                                                                                                       \
         error("Memory parameter %u (%zu/%zu) mismatch with respect to " #suffix " reference.\n", idx, i + 1, \
               P##idx##_count_##suffix);                                                                      \
         ++mismatch_count;                                                                                    \
      }                                                                                                       \
   }                                                                                                          \
   free(P##idx##_##suffix)

#define _ms_setargchannel(suffix, idx) m_getvalt(P##idx) P##idx##_##suffix = *m_getptr(P##idx)

#define _ms_channelcmp(suffix, idx, cmp)                                                                          \
   if(m_getptr(P##idx)->size() != m_getptr(P##idx##_##suffix)->size())                                            \
   {                                                                                                              \
      error("Channel parameter %u size mismatch with respect to " #suffix " reference: %zu != %zu.\n", idx,       \
            m_getptr(P##idx)->size(), m_getptr(P##idx##_##suffix)->size());                                       \
      ++mismatch_count;                                                                                           \
   }                                                                                                              \
   else                                                                                                           \
   {                                                                                                              \
      for(i = 0; i < m_getptr(P##idx)->size(); ++i)                                                               \
      {                                                                                                           \
         if(m_cmp##cmp(&m_getptr(P##idx)->operator[](i), &m_getptr(P##idx##_##suffix)->operator[](i)))            \
         {                                                                                                        \
            error("Channel parameter %u (%zu/%zu) mismatch with respect to " #suffix " reference.\n", idx, i + 1, \
                  m_getptr(P##idx)->size());                                                                      \
            ++mismatch_count;                                                                                     \
         }                                                                                                        \
      }                                                                                                           \
   }

#define _ms_retvalcmp(suffix, cmp)                                             \
   if(m_cmp##cmp(&retval, &retval_##suffix))                                   \
   {                                                                           \
      error("Return value mismatch with respect to " #suffix " reference.\n"); \
      ++mismatch_count;                                                        \
   }

#ifndef CUSTOM_VERIFICATION
#define _m_setargptr(idx, ptr) _ms_setargptr(gold, idx, ptr)
#define _m_argcmp(idx, cmp) _ms_argcmp(gold, idx, cmp)
#define _m_setargchannel(idx) _ms_setargchannel(gold, idx)
#define _m_channelcmp(idx, cmp) _ms_channelcmp(gold, idx, cmp)
#define _m_retvalcmp(cmp) _ms_retvalcmp(gold, cmp)

EXTERN_CDECL void __m_forward_kernel(void*, void*, void*);
#else
#define _m_setargptr(...)
#define _m_argcmp(...)
#define _m_setargchannel(...)
#define _m_channelcmp(...)
#define _m_retvalcmp(...)
#endif

#ifdef PP_VERIFICATION
#define _m_pp_setargptr(idx, ptr) _ms_setargptr(pp, idx, ptr)
#define _m_pp_argcmp(idx, cmp) _ms_argcmp(pp, idx, cmp)
#define _m_pp_retvalcmp(cmp) _ms_retvalcmp(pp, cmp)

EXTERN_CDECL void __m_pp_forward_kernel(const void*, const void*, void*);
#else
#define _m_pp_setargptr(...)
#define _m_pp_argcmp(...)
#define _m_pp_retvalcmp(...)
#endif

#ifdef DUMP_COSIM_OUTPUT
static size_t __m_call_count = 0;

#ifndef CUSTOM_VERIFICATION
#define _m_golddump(idx)                                                                                            \
   do                                                                                                               \
   {                                                                                                                \
      char filename[32];                                                                                            \
      sprintf(filename, "P" #idx "_gold.%zu.dat", __m_call_count);                                                  \
      FILE* out = fopen(filename, "wb");                                                                            \
      if(out != NULL)                                                                                               \
      {                                                                                                             \
         fwrite(P##idx##_gold, 1, __m_param_size(idx), out);                                                        \
         fclose(out);                                                                                               \
         debug("Parameter " #idx " gold output dump for execution %zu stored in '%s'\n", __m_call_count, filename); \
      }                                                                                                             \
      else                                                                                                          \
      {                                                                                                             \
         error("Unable to open parameter dump file '%s'\n", filename);                                              \
      }                                                                                                             \
   } while(0)
#else
#define _m_golddump(idx)
#endif

#define _m_argdump(idx)                                                                                        \
   do                                                                                                          \
   {                                                                                                           \
      char filename[32];                                                                                       \
      sprintf(filename, "P" #idx ".%zu.dat", __m_call_count);                                                  \
      FILE* out = fopen(filename, "wb");                                                                       \
      if(out != NULL)                                                                                          \
      {                                                                                                        \
         fwrite(P##idx, 1, __m_param_size(idx), out);                                                          \
         fclose(out);                                                                                          \
         debug("Parameter " #idx " output dump for execution %zu stored in '%s'\n", __m_call_count, filename); \
      }                                                                                                        \
      else                                                                                                     \
      {                                                                                                        \
         error("Unable to open parameter dump file '%s'\n", filename);                                         \
      }                                                                                                        \
   } while(0)
#else
#define _m_argdump(idx)
#define _m_golddump(idx)
#endif

#define m_map_default(ptr) NULL
#define m_interface_default(idx, ptr, bitsize, align) \
   __m_interface_port(idx, ptr, bitsize);             \
   _m_pp_setargptr(idx, ptr);                         \
   _m_setargptr(idx, ptr)

#define m_map_ptr(ptr) (void*)ptr
#define m_interface_ptr(idx, ptr, bitsize, align)               \
   bptr_t __ptrval_##idx = (bptr_t)ptr;                         \
   __m_interface_ptr(idx, &__ptrval_##idx, sizeof(bptr_t) * 8); \
   _m_pp_setargptr(idx, ptr);                                   \
   _m_setargptr(idx, ptr)

#define m_map_array(...) m_map_default(__VA_ARGS__)
#define m_interface_array(idx, ptr, bitsize, align)                            \
   __m_interface_array(idx, ptr, bitsize, align, __m_param_size(idx) / align); \
   _m_pp_setargptr(idx, ptr);                                                  \
   _m_setargptr(idx, ptr)

#define m_map_fifo(...) m_map_default(__VA_ARGS__)
#define m_interface_fifo(idx, ptr, bitsize, align)                            \
   __m_interface_fifo(idx, ptr, bitsize, align, __m_param_size(idx) / align); \
   _m_pp_setargptr(idx, ptr);                                                 \
   _m_setargptr(idx, ptr)

#define m_map_channel(ptr) NULL
#define m_interface_channel(idx, ptr, bitsize, align)                  \
   __m_interface_channel(idx, *m_getptr(P##idx), __m_param_size(idx)); \
   _m_setargchannel(idx)

#define m_map_none(...) m_map_default(__VA_ARGS__)
#define m_interface_none(...) m_interface_default(__VA_ARGS__)

#define m_map_valid(...) m_map_default(__VA_ARGS__)
#define m_interface_valid(...) m_interface_default(__VA_ARGS__)

#define m_map_ovalid(...) m_map_default(__VA_ARGS__)
#define m_interface_ovalid(...) m_interface_default(__VA_ARGS__)

#define m_map_acknowledge(...) m_map_default(__VA_ARGS__)
#define m_interface_acknowledge(...) m_interface_default(__VA_ARGS__)

#define m_map_handshake(...) m_map_default(__VA_ARGS__)
#define m_interface_handshake(...) m_interface_default(__VA_ARGS__)

#define m_map_axis(...) m_map_fifo(__VA_ARGS__)
#define m_interface_axis(...) m_interface_fifo(__VA_ARGS__)

#define m_map_m_axi(...) m_map_ptr(__VA_ARGS__)
#define m_interface_m_axi(...) m_interface_ptr(__VA_ARGS__)

#define m_argcmp(idx, cmp) \
   _m_argdump(idx);        \
   _m_golddump(idx);       \
   _m_pp_argcmp(idx, cmp); \
   _m_argcmp(idx, cmp)

#define m_channelcmp(idx, cmp) _m_channelcmp(idx, cmp)

#define m_retvalcmp(cmp) _m_pp_retvalcmp(cmp) _m_retvalcmp(cmp)

typedef struct
{
   const char* filename;
   size_t size;
   const ptr_t addrmap;
   void* addr;
} __m_memmap_t;

typedef struct
{
   void* addr;
   size_t align;
   void* map_addr;
} __m_argmap_t;

static void __m_memsetup(__m_argmap_t args[], size_t args_count)
{
   int error = 0;
   size_t i;
   static __m_memmap_t memmap_init[] = {
   };
   const ptr_t align = 8;
   ptr_t base_addr = 1073741824;
   
   __m_memmap_init(MDPI_MEMMAP_MODE);
   
   
   // Memory-mapped internal variables initialization
   for(i = 0; i < sizeof(memmap_init) / sizeof(*memmap_init); ++i)
   {
      FILE* fp = fopen(memmap_init[i].filename, "rb");
      if(!fp)
      {
         error("Unable to open file: %s\n", memmap_init[i].filename);
         perror("Unable to open memory variable initialization file");
         error |= 2;
         continue;
      }
      if(memmap_init[i].addr == NULL)
      {
         memmap_init[i].addr = malloc(memmap_init[i].size);
      }
      size_t nbytes = fread(memmap_init[i].addr, 1, memmap_init[i].size, fp);
      if(nbytes != memmap_init[i].size)
      {
         error("Only %zu/%zu bytes were read from file: %s\n", nbytes, memmap_init[i].size, memmap_init[i].filename);
         if(ferror(fp))
         {
            perror("Unable to read from memory variable initialization file");
         }
         error |= 4;
         fclose(fp);
         continue;
      }
      fclose(fp);
      error |= __m_memmap(memmap_init[i].addrmap, memmap_init[i].addr, memmap_init[i].size);
   }
   
   for(i = 0; i < args_count; ++i)
   {
      if(args[i].map_addr == NULL)
      {
         args[i].map_addr = args[i].addr;
         continue;
      }
      const size_t arg_size = __m_param_size(i);
      size_t map_size = arg_size;
      base_addr += (align - 1) - ((base_addr - 1) % align);
      args[i].map_addr = args[i].addr;
      if(arg_size % args[i].align)
      {
         map_size = arg_size + (args[i].align - 1) - ((arg_size - 1) % args[i].align);
         info("Parameter %zu map size extended: %zu bytes -> %zu bytes\n", i, arg_size, map_size);
         args[i].map_addr = malloc(map_size);
         memcpy(args[i].map_addr, args[i].addr, arg_size);
      }
      error |= __m_memmap(base_addr, args[i].map_addr, map_size);
      base_addr += map_size;
   }
   if(error)
   {
      __m_abort();
   }
}

static void __m_argmap_fini(__m_argmap_t args[], size_t args_count)
{
   size_t i = 0;
   for(i = 0; i < args_count; i++)
   {
      if(args[i].map_addr != args[i].addr)
      {
         memcpy(args[i].addr, args[i].map_addr, __m_param_size(i));
         free(args[i].map_addr);
         args[i].map_addr = args[i].addr;
      }
   }
}

void forward_kernel(void* P0, void* P1, void* P2)
{
   const long double max_ulp = 1;
   size_t i;
   __m_argmap_t args[] = {
      {(void*)P0, 4, m_map_ptr((void*)P0)},
      {(void*)P1, 4, m_map_ptr((void*)P1)},
      {(void*)P2, 4, m_map_ptr((void*)P2)}};
   __m_param_alloc(0, 1);
   __m_param_alloc(1, 1);
   __m_param_alloc(2, 1);
   __m_memsetup(args, 3);
   
   m_interface_ptr(0, args[0].map_addr, 32, 4);
   m_interface_ptr(1, args[1].map_addr, 32, 4);
   m_interface_ptr(2, args[2].map_addr, 32, 4);
   __m_interface_mem(3);
   
   __m_sim_start();
   
   #ifndef CUSTOM_VERIFICATION
   __m_forward_kernel((void*)P0_gold, (void*)P1_gold, (void*)P2_gold);
   #endif
   
   #ifdef PP_VERIFICATION
   __m_pp_forward_kernel((const void*)P0_pp, (const void*)P1_pp, (void*)P2_pp);
   #endif
   
   __m_sim_end();
   __m_interface_fini();
   
   
   #ifdef __clang__
   #pragma clang diagnostic push
   #pragma clang diagnostic ignored "-Wpointer-type-mismatch"
   #endif
   
   __m_argmap_fini(args, 3);
   
   size_t mismatch_count = 0;
   m_argcmp(0, mem);
   m_argcmp(1, mem);
   m_argcmp(2, mem);
   
   
   if(mismatch_count)
   {
      error("Memory parameter mismatch has been found.\n");
      __m_abort();
   }
   
   #ifdef DUMP_COSIM_OUTPUT
   ++__m_call_count;
   #endif
   
   #ifdef __clang__
   #pragma clang diagnostic pop
   #endif
}


