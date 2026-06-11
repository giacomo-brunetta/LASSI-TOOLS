#include <stdio.h>
#include <stdlib.h>

/* Smoke kernel for the graph pipeline.
 *
 * Computes C = A * B where A is NxM, B is MxK, with both seeded as
 * identity-on-the-diagonal up to their min dimension. The resulting C
 * is the identity up to min(N,M,K), zero elsewhere. Output is C as
 * space-separated integers, one row per line.
 *
 * argv: [N M K]  (defaults: 8 6 8)
 */
int main(int argc, char **argv) {
    int N = 8, M = 6, K = 8;
    if (argc == 4) {
        N = atoi(argv[1]);
        M = atoi(argv[2]);
        K = atoi(argv[3]);
    }

    double *A = (double *)calloc((size_t)N * M, sizeof(double));
    double *B = (double *)calloc((size_t)M * K, sizeof(double));
    double *C = (double *)calloc((size_t)N * K, sizeof(double));

    for (int i = 0; i < N && i < M; i++) A[i * M + i] = 1.0;
    for (int i = 0; i < M && i < K; i++) B[i * K + i] = 1.0;

    for (int i = 0; i < N; i++) {
        for (int j = 0; j < K; j++) {
            double s = 0.0;
            for (int k = 0; k < M; k++) {
                s += A[i * M + k] * B[k * K + j];
            }
            C[i * K + j] = s;
        }
    }

    for (int i = 0; i < N; i++) {
        for (int j = 0; j < K; j++) {
            printf("%d ", (int)C[i * K + j]);
        }
        printf("\n");
    }

    free(A);
    free(B);
    free(C);
    return 0;
}
