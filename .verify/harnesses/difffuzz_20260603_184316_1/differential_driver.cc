
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>
#include <dlfcn.h>

typedef double (*kernel_t)(double);
static kernel_t fa = NULL;
static kernel_t fb = NULL;
static double g_rtol = 1e-9;
static double g_atol = 1e-9;

__attribute__((constructor))
static void _lassi_load(void) {
    const char *pa = getenv("LASSI_LIB_A");
    const char *pb = getenv("LASSI_LIB_B");
    const char *entry = getenv("LASSI_ENTRY");
    const char *rtol_s = getenv("LASSI_RTOL");
    const char *atol_s = getenv("LASSI_ATOL");
    if (!entry || !*entry) entry = "kernel";
    if (rtol_s) g_rtol = strtod(rtol_s, NULL);
    if (atol_s) g_atol = strtod(atol_s, NULL);
    if (!pa || !pb) {
        fprintf(stderr, "LASSI_LIB_A and LASSI_LIB_B must be set\n");
        abort();
    }
    void *ha = dlopen(pa, RTLD_NOW | RTLD_LOCAL);
    if (!ha) { fprintf(stderr, "dlopen A failed: %s\n", dlerror()); abort(); }
    void *hb = dlopen(pb, RTLD_NOW | RTLD_LOCAL);
    if (!hb) { fprintf(stderr, "dlopen B failed: %s\n", dlerror()); abort(); }
    fa = (kernel_t) dlsym(ha, entry);
    fb = (kernel_t) dlsym(hb, entry);
    if (!fa || !fb) {
        fprintf(stderr, "dlsym %s failed\n", entry);
        abort();
    }
}

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size < sizeof(double)) return 0;
    double x;
    memcpy(&x, data, sizeof(double));
    if (!isfinite(x)) return 0;
    double a = fa(x);
    double b = fb(x);
    int a_fin = isfinite(a);
    int b_fin = isfinite(b);
    if (!a_fin && !b_fin) return 0;
    if (a_fin != b_fin) {
        fprintf(stderr, "DIFFERENTIAL MISMATCH (finiteness) at x=%a a=%a b=%a\n", x, a, b);
        abort();
    }
    double diff = fabs(a - b);
    double tol = g_atol + g_rtol * fabs(b);
    if (diff > tol) {
        fprintf(stderr, "DIFFERENTIAL MISMATCH at x=%a a=%a b=%a diff=%a tol=%a\n",
                x, a, b, diff, tol);
        abort();
    }
    return 0;
}
