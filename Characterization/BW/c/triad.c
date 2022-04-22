#define LEN 10000000

double a[LEN], b[LEN], c[LEN];

void __attribute__((always_inline)) // Force inline
triad() {
    for (int i = 0; i < LEN; i++) {
        // Double a[i] = b[i] + c[i] (Similar to Triad, three access to memory)
        __asm__("movsd (%0), %%xmm0;" // xmm0 = MEM(c[i])
                "addsd (%1), %%xmm0;" // xmm0 = c[i] + b[i]
                "movsd %%xmm0, (%2);" // MEM(a[i]) = xmm0
                : 
                : "r" (&c[i]), "r" (&b[i]), "r" (&a[i])
                : "%xmm0"
            );
    }
}

int
main() {
    // Initialize the vectors array
    for (int i = 0; i < LEN; ++i) {
        a[i] = 1.0; b[i] = 2.0; c[i] = 3.0;
    }

   
    // Execute Triad kernel 'N' Times
    for (;;) {
        triad();
    }

    return 0;
}
