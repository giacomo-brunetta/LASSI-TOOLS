#include <stdio.h>

/**
 * Calculates the n-th Fibonacci number iteratively.
 * @param n The index of the Fibonacci number to calculate.
 * @return The n-th Fibonacci number.
 */
long long fibonacci(int n) {
    if (n <= 0) return 0;
    if (n == 1) return 1;
    
    long long prev = 0;
    long long curr = 1;
    long long next;
    
    for (int i = 2; i <= n; i++) {
        next = prev + curr;
        prev = curr;
        curr = next;
    }
    return curr;
}

int main(int argc, char *argv[]) {
    int n;
    
    if (argc != 2) {
        printf("Usage: %s <non-negative integer>\n", argv[0]);
        return 1;
    }

    n = atoi(argv[1]);
    
    if (n < 0) {
        printf("Please enter a non-negative integer.\n");
        return 1;
    }
    
    printf("Fibonacci(%d) = %lld\n", n, fibonacci(n));
    
    return 0;
}
