#include <stdio.h>
#include <stdlib.h>
#include <errno.h>

int main(int argc, char *argv[])
{
    if (argc != 2) {
        fprintf(stderr, "Usage: %s N\n", argv[0]);
        return EXIT_FAILURE;
    }

    char *endptr;
    errno = 0;
    long n_long = strtol(argv[1], &endptr, 10);
    if (errno != 0 || *endptr != '\0' || n_long < 0) {
        fprintf(stderr, "Invalid non‑negative integer: %s\n", argv[1]);
        return EXIT_FAILURE;
    }
    int N = (int)n_long;

    if (N == 0) {
        /* Nothing to print */
        return EXIT_SUCCESS;
    }

    unsigned long long a = 0, b = 1;
    for (int i = 0; i < N; ++i) {
        if (i == 0) {
            printf("%llu", a);
        } else if (i == 1) {
            printf(" %llu", b);
        } else {
            unsigned long long c = a + b;
            printf(" %llu", c);
            a = b;
            b = c;
        }
    }
    printf("\n");
    return EXIT_SUCCESS;
}
