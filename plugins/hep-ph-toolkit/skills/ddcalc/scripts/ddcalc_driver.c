/*
 * DDCalc driver shim — links against libDDCalc.a and calls the DDCalc C API.
 *
 * Reads sigma JSON from argv[1] (or stdin if "-"), halo JSON from argv[2] (or ""),
 * and emits structured output to stdout.
 *
 * Output format (one block per experiment):
 *   EXPERIMENT: <name>
 *   LOGL: <value>
 *   PVALUE: <value>
 *   EXCLUDED90: <0|1>
 *   ---
 *
 * Footer:
 *   STATUS: ok
 *   VERSION: 2.2.0
 *
 * Build: gcc -std=c11 -Wno-implicit-function-declaration ddcalc_driver.c -L<dir>/lib -lDDCalc -lgfortran -o ddcalc_driver
 *
 * DDCalc C API is declared in include/DDCalc.hpp (C extern "C" block).
 * Key functions used:
 *   DDCalc_InitWIMP()     → WIMP handle (int index)
 *   DDCalc_InitHalo()     → Halo handle
 *   DDCalc_InitDetector() → Detector handle for default experiment
 *   C_DDCalc_<exp>_init() → Experiment-specific detector handle
 *   DDCalc_SetWIMP_msigma(WIMP, m, sigSIp, sigSIn, sigSDp, sigSDn)
 *   DDCalc_SetSHM(Halo, rho, vrot, v0, vesc)
 *   DDCalc_CalcRates(Detector, WIMP, Halo)
 *   DDCalc_LogLikelihood(Detector)
 *   DDCalc_SignalSI(Detector)
 *
 * p-value / exclusion statistic:
 *   PVALUE and EXCLUDED90 below are a **likelihood ratio to background-only**,
 *   NOT DDCalc's own `DDCalc_ScaleToPValue`. See
 *   /Users/yianni/.claude/jobs/c703354a/tmp/ddcalc-diag/DIAGNOSIS.md for the
 *   full root-cause writeup. Summary: `ScaleToPValue(D, lnp)` takes a
 *   *target* log-p and returns a sigma-scale factor; it does not convert a
 *   log-likelihood into a p-value. The prior code fed it the *current* logL
 *   as the target, which just asks "what scale reproduces the logL I already
 *   have at x=1" — the trivial answer x≈1 for every sigma, which is why the
 *   old driver's reported "p_value" pinned near 1.0 for every XENON1T/LZ
 *   point. Additionally, `ScaleToPValue` used correctly (target = ln 0.1) is
 *   structurally unusable for high-count xenon TPCs: it guards on the
 *   background-only *absolute* log-likelihood being close to 0 (valid only
 *   for near-background-free counting experiments like PICO/DarkSide), and
 *   returns a 0/HUGE sentinel for XENON1T/LZ/PandaX/LUX instead of a real
 *   crossing. The likelihood-ratio statistic below —
 *     p = exp(lnL_signal - lnL_background), excluded_90 = (p <= 0.1)
 *   — reduces to DDCalc's native convention in the background-free limit
 *   (matching ScaleToPValue exactly in the regime where the latter is
 *   valid); the ratio normalization follows the standard GAMBIT/DarkBit
 *   generalization. Empirically verified for the SI channel across every
 *   experiment in the registry. NOTE: the driver's SD channel currently
 *   produces zero signal in every experiment (pre-existing bug independent
 *   of this statistic, tracked separately), so the statistic is unverified
 *   for SD and SD-driven verdicts are not yet meaningful.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

/* DDCalc C API forward declarations (subset used by this driver).
 *
 * DDCalc 2.2.0 uses Fortran-module-mangled symbol names. The mapping is:
 *   InitWIMP       → _C_DDWIMP_ddcalc_initwimp
 *   InitHalo       → _C_DDHalo_ddcalc_inithalo
 *   InitDetector   → _C_DDExperiments_ddcalc_initdetector
 *   SetWIMP_msigma → _C_DDCalc_ddcalc_setwimp_msigma
 *   SetSHM         → _C_DDCalc_ddcalc_setshm
 *   CalcRates      → _C_DDRates_ddcalc_calcrates
 *   LogLikelihood  → _C_DDStats_ddcalc_loglikelihood
 * Experiment init functions keep the _C_DDCalc_<exp>_init pattern.
 * (Verified via `nm libDDCalc.a` on 2026-04-25, DDCalc commit 9364c02d.)
 */
extern int C_DDWIMP_ddcalc_initwimp(void);
extern int C_DDHalo_ddcalc_inithalo(void);
extern int C_DDExperiments_ddcalc_initdetector(int);
extern int C_DDCalc_xenon1t_2018_init(void);
extern int C_DDCalc_lux_2016_init(void);
extern int C_DDCalc_pandax_2017_init(void);
extern int C_DDCalc_pico_60_2019_init(void);
extern int C_DDCalc_darkside_50_init(void);
extern int C_DDCalc_lz_init(void);

extern void C_DDCalc_ddcalc_setwimp_msigma(
    const int *WIMP, const double *m,
    const double *sigSIp, const double *sigSIn,
    const double *sigSDp, const double *sigSDn);
/* SetSHM: (HaloIndex, rho, vrot, v0, vesc) */
extern void C_DDCalc_ddcalc_setshm(
    const int *Halo, const double *rho, const double *vrot,
    const double *v0, const double *vesc);
extern void C_DDRates_ddcalc_calcrates(const int *D, const int *W, const int *H);
extern double C_DDStats_ddcalc_loglikelihood(const int *D);

/* Experiment registry */
#define MAX_EXP 32
typedef struct { const char *name; int (*init_fn)(void); } Experiment;

static int n_exps = 0;
static Experiment experiments[MAX_EXP];

static void register_exp(const char *name, int (*fn)(void)) {
    if (n_exps >= MAX_EXP) return;
    experiments[n_exps].name = name;
    experiments[n_exps].init_fn = fn;
    n_exps++;
}

/* Simple JSON field parser for doubles */
static double json_get_double(const char *json, const char *key, double defval) {
    char search[256];
    snprintf(search, sizeof(search), "\"%s\"", key);
    const char *p = strstr(json, search);
    if (!p) return defval;
    p = strchr(p, ':');
    if (!p) return defval;
    p++;
    while (*p == ' ' || *p == '\t') p++;
    if (*p == 'n' || *p == 'N') return defval; /* null */
    return strtod(p, NULL);
}

int main(int argc, char *argv[]) {
    /* Read sigma JSON */
    char sigma_json[16384] = {0};
    if (argc >= 2 && strcmp(argv[1], "-") != 0) {
        FILE *f = fopen(argv[1], "r");
        if (!f) { fprintf(stderr, "ERROR: cannot open %s\n", argv[1]); return 1; }
        fread(sigma_json, 1, sizeof(sigma_json)-1, f);
        fclose(f);
    } else {
        fread(sigma_json, 1, sizeof(sigma_json)-1, stdin);
    }

    /* Extract physics parameters */
    double m_dm     = json_get_double(sigma_json, "m_dm_gev", 100.0);
    double sig_si_p = json_get_double(sigma_json, "sigma_si_proton_cm2", 0.0);
    double sig_si_n = json_get_double(sigma_json, "sigma_si_neutron_cm2", sig_si_p);
    double sig_sd_p = json_get_double(sigma_json, "sigma_sd_proton_cm2", 0.0);
    double sig_sd_n = json_get_double(sigma_json, "sigma_sd_neutron_cm2", 0.0);

    /* Halo parameters (SHM defaults per skill spec) */
    double rho0  = json_get_double(sigma_json, "rho0_gev_per_cm3", 0.3);
    double v0    = json_get_double(sigma_json, "v0_km_per_s", 238.0);
    double vesc  = json_get_double(sigma_json, "vesc_km_per_s", 544.0);
    double vrot  = v0;  /* DDCalc SetSHM uses vrot = v0 for SHM */

    /* Convert cm² → pb (DDCalc_SetWIMP_msigma expects pb) */
    /* 1 pb = 1e-36 cm² */
    sig_si_p *= 1e36;
    sig_si_n *= 1e36;
    sig_sd_p *= 1e36;
    sig_sd_n *= 1e36;

    /* Register native experiments */
    register_exp("XENON1T_2018",  C_DDCalc_xenon1t_2018_init);
    register_exp("LUX_2016",      C_DDCalc_lux_2016_init);
    register_exp("PandaX_2017",   C_DDCalc_pandax_2017_init);
    register_exp("PICO_60_2019",  C_DDCalc_pico_60_2019_init);
    register_exp("DarkSide_50",   C_DDCalc_darkside_50_init);
    register_exp("LZ_2022",       C_DDCalc_lz_init);

    /* Initialize WIMP and Halo */
    int WIMP = C_DDWIMP_ddcalc_initwimp();
    int Halo = C_DDHalo_ddcalc_inithalo();

    C_DDCalc_ddcalc_setwimp_msigma(&WIMP, &m_dm,
        &sig_si_p, &sig_si_n, &sig_sd_p, &sig_sd_n);
    C_DDCalc_ddcalc_setshm(&Halo, &rho0, &vrot, &v0, &vesc);

    /* Second, zero-signal WIMP handle used to evaluate the background-only
     * log-likelihood per detector (see file-header comment for why this
     * replaces DDCalc_ScaleToPValue). */
    int WIMP0 = C_DDWIMP_ddcalc_initwimp();
    double zero = 0.0;
    C_DDCalc_ddcalc_setwimp_msigma(&WIMP0, &m_dm, &zero, &zero, &zero, &zero);

    /* Loop over experiments */
    for (int i = 0; i < n_exps; i++) {
        int D = experiments[i].init_fn();

        C_DDRates_ddcalc_calcrates(&D, &WIMP, &Halo);
        double logL = C_DDStats_ddcalc_loglikelihood(&D);      /* signal + background */

        C_DDRates_ddcalc_calcrates(&D, &WIMP0, &Halo);
        double logLbg = C_DDStats_ddcalc_loglikelihood(&D);    /* background only */

        /* A non-finite log-likelihood means DDCalc itself failed for this
         * detector; error out loudly (the Python wrapper converts a nonzero
         * exit into a DDCALC_DRIVER_FAILED blocker with stderr attached)
         * rather than silently mapping NaN to p=0, which would bias the
         * verdict toward "excluded". */
        if (isnan(logL) || isnan(logLbg)) {
            fprintf(stderr,
                "ERROR: non-finite log-likelihood for %s (logL=%f, logL_bg=%f)\n",
                experiments[i].name, logL, logLbg);
            return 1;
        }

        /* Likelihood-ratio p-value, clamped to [0, 1]. exp() underflow of a
         * very negative exponent yields +0.0, which is the correct limit. */
        double pval = exp(logL - logLbg);
        if (isnan(pval)) {  /* e.g. inf - inf in the exponent */
            fprintf(stderr,
                "ERROR: non-finite p-value for %s (logL=%f, logL_bg=%f)\n",
                experiments[i].name, logL, logLbg);
            return 1;
        }
        if (pval > 1.0) pval = 1.0;
        int excl90 = (pval <= 0.1) ? 1 : 0;

        printf("EXPERIMENT: %s\n", experiments[i].name);
        printf("LOGL: %.6e\n", logL);
        printf("PVALUE: %.6e\n", pval);
        printf("EXCLUDED90: %d\n", excl90);
        printf("---\n");
    }

    printf("STATUS: ok\n");
    printf("VERSION: 2.2.0\n");
    return 0;
}
