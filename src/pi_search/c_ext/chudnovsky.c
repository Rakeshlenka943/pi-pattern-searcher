/* Chudnovsky binary splitting for pi, using GMP.
 *
 * pi = 426880 * sqrt(10005) * Q(0,N) / T(0,N)
 *
 * where P, Q, T come from binary splitting of the Chudnovsky series.
 * Portable across Linux/macOS; Windows falls back to gmpy2/mpmath
 * (no GMP headers on default Windows installs).
 */
#include <stdlib.h>
#include <string.h>
#include <gmp.h>

#define A_COEF 13591409UL
#define B_COEF 545140134UL


static void bs(mpz_t P, mpz_t Q, mpz_t T,
               unsigned long a, unsigned long b, const mpz_t c3_24) {
    if (b - a == 1) {
        if (a == 0) {
            mpz_set_ui(P, 1);
            mpz_set_ui(Q, 1);
        } else {
            mpz_set_ui(P, 6 * a - 5);
            mpz_mul_ui(P, P, 2 * a - 1);
            mpz_mul_ui(P, P, 6 * a - 1);

            mpz_set_ui(Q, a);
            mpz_mul_ui(Q, Q, a);
            mpz_mul_ui(Q, Q, a);
            mpz_mul(Q, Q, c3_24);
        }
        mpz_set_ui(T, B_COEF);
        mpz_mul_ui(T, T, a);
        mpz_add_ui(T, T, A_COEF);
        mpz_mul(T, T, P);
        if (a & 1) mpz_neg(T, T);
    } else {
        unsigned long m = a + (b - a) / 2;
        mpz_t P1, Q1, T1, P2, Q2, T2;
        mpz_inits(P1, Q1, T1, P2, Q2, T2, (mpz_ptr)0);
        bs(P1, Q1, T1, a, m, c3_24);
        bs(P2, Q2, T2, m, b, c3_24);
        mpz_mul(P, P1, P2);
        mpz_mul(Q, Q1, Q2);
        mpz_mul(T, Q2, T1);
        mpz_addmul(T, P1, T2);
        mpz_clears(P1, Q1, T1, P2, Q2, T2, (mpz_ptr)0);
    }
}


char* compute_pi_c(int digits) {
    if (digits <= 0) return NULL;

    int bits = (int)((double)digits * 3.3219280948873626) + 128;
    unsigned long N = (unsigned long)((double)digits / 14.181647462725477) + 5;

    mpz_t c3_24, base;
    mpz_inits(c3_24, base, (mpz_ptr)0);
    mpz_set_ui(base, 640320);
    mpz_pow_ui(c3_24, base, 3);
    mpz_divexact_ui(c3_24, c3_24, 24);
    mpz_clear(base);

    mpz_t P, Q, T;
    mpz_inits(P, Q, T, (mpz_ptr)0);
    bs(P, Q, T, 0, N, c3_24);

    mpz_mul_ui(Q, Q, 426880);

    mpf_set_default_prec((mp_bitcnt_t)(bits + 128));

    mpf_t q_f, t_f, sqrt5;
    mpf_inits(q_f, t_f, sqrt5, (mpf_ptr)0);

    mpf_set_z(q_f, Q);
    mpf_set_z(t_f, T);
    mpf_div(q_f, q_f, t_f);

    mpf_set_ui(sqrt5, 10005);
    mpf_sqrt(sqrt5, sqrt5);

    mpf_mul(q_f, q_f, sqrt5);

    mp_exp_t exp;
    char* s = mpf_get_str(NULL, &exp, 10, (size_t)(digits + 20), q_f);

    char* result = (char*)malloc((size_t)digits + 1);
    if (result == NULL) {
        free(s);
        mpz_clears(P, Q, T, c3_24, (mpz_ptr)0);
        mpf_clears(q_f, t_f, sqrt5, (mpf_ptr)0);
        return NULL;
    }

    size_t slen = strlen(s);
    size_t copy_len = slen < (size_t)digits ? slen : (size_t)digits;
    memcpy(result, s, copy_len);
    if (copy_len < (size_t)digits) {
        memset(result + copy_len, '0', (size_t)digits - copy_len);
    }
    result[digits] = '\0';

    free(s);
    mpz_clears(P, Q, T, c3_24, (mpz_ptr)0);
    mpf_clears(q_f, t_f, sqrt5, (mpf_ptr)0);

    return result;
}


void free_pi_string(char* s) {
    free(s);
}
