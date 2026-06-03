
#include <stddef.h>
#include <stdint.h>
#include <string.h>

extern "C" double kernel(double);

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size < sizeof(double)) return 0;
    double x;
    memcpy(&x, data, sizeof(double));
    kernel(x);
    return 0;
}
