/*
 * DDCalc driver shim — links against libDDCalc.a and calls the DDCalc C API.
 *
 * Reads sigma JSON from argv[1] (or stdin if "-"), halo JSON from argv[2] (or ""),
 * and emits structured output to stdout.
 *
 * Output format (one block per experiment):
 *   EXPERIMENT: <name>
 *   LOGL: <value>            (signal log-likelihood)
 *   DELTACHI2: <value>       (-2 (lnL_signal - lnL_background), clamped >= 0)
 *   SIGNIFICANCE: <value>    (sqrt(DELTACHI2), Gaussian-sigma Z)
 *   PVALUE: <value>          (chi^2_1 survival = erfc(sqrt(DELTACHI2/2)))
 *   EXCLUDED90: <0|1>        (DELTACHI2 > 2.706 <=> PVALUE < 0.1)
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
 * Exclusion statistic — Wilks / one-parameter profile-likelihood-ratio test:
 *   For each detector the driver evaluates the DDCalc log-likelihood at the
 *   physical cross section (lnL_signal) and at zero cross section
 *   (lnL_background, via a second zero-signal WIMP handle), and reports the
 *   likelihood-ratio test statistic
 *
 *     DELTACHI2   = -2 (lnL_signal - lnL_background)   [clamped >= 0]
 *     SIGNIFICANCE = sqrt(DELTACHI2)                    [Gaussian-sigma Z]
 *     PVALUE      = erfc( sqrt(DELTACHI2 / 2) )         [chi^2_1 survival func]
 *     EXCLUDED90  = (PVALUE < 0.1)  <=>  (DELTACHI2 > 2.70554)
 *
 *   This is the standard asymptotic (Wilks) statistic that GAMBIT/DarkBit
 *   consumers apply to DDCalc log-likelihoods: -2 dln L is chi^2_1-distributed
 *   under the null, so the 90% CL exclusion threshold is the chi^2_1 90%
 *   quantile DELTACHI2 = 2.706 (equivalently sqrt(-2 dlnL) > 1.645). It fixes
 *   three problems with the prior statistics:
 *     - It is NOT DDCalc's own `DDCalc_ScaleToPValue` (that takes a target
 *       log-p and returns a sigma-scale factor; it does not convert a
 *       log-likelihood into a p-value, and it is structurally unusable for
 *       high-count xenon TPCs whose background-only absolute log-likelihood is
 *       far from 0 — see ddcalc-diag/DIAGNOSIS.md). That misuse pinned the
 *       reported "p" near 1.0 for every XENON1T/LZ point.
 *     - It replaces the interim `p = exp(lnL_signal - lnL_background)` ratio
 *       (which was smooth and monotone but *uncalibrated* — its 0.1 cut is
 *       Z~2.15, not 90% CL — and which UNDERFLOWED to a hard 0 for large
 *       signals, turning any bisection-for-p=0.1 into a numerical-underflow
 *       contour). DELTACHI2 stays finite and monotone where exp() underflows,
 *       so limit bisection must bracket on DELTACHI2 = 2.706, never on PVALUE.
 *     - "90% CL" now carries an actual chi^2/Wilks calibration.
 *
 *   Validation (SI, SHM defaults, 2026-07-11): the DELTACHI2 > 2.706 crossing
 *   reproduces the *published* per-nucleon SI limits of the analyses DDCalc
 *   actually implements to within a factor ~2 across 30-200 GeV — LZ vs the LZ
 *   *projected* design sensitivity (LZ.f90 cites arXiv:1509.02910 +
 *   1712.04793; floor ~1.4e-48 cm^2 as in arXiv:1802.06039; see
 *   the LZ_projected note below), XENON1T_2018 vs the observed 1t-yr result
 *   (arXiv:1805.12562). Covered by tests/test_integration_pvalue_statistic.py
 *   and tests/test_integration_xenon1t_golden.py.
 *
 *   SD channel: the spin-dependent rate flows through the same
 *   CalcRates/LogLikelihood path as SI, so the same statistic applies; SD
 *   liveness and isospin structure (PICO SD-proton-led, xenon TPCs
 *   SD-neutron-led) are covered by TestSDChannel.
 *
 *   SD channel: the spin-dependent rate flows through the same
 *   CalcRates/LogLikelihood path as SI, so the same (uncalibrated) statistic
 *   applies. DDCalc loads the SD nuclear form factors from a data directory
 *   (DATA_DIR/SDFF/<Z>_<A>.dat); the /ddcalc wrapper
 *   (run_ddcalc._ensure_ddcalc_data_symlinks) heals DDCalc's compile-time
 *   DATA_DIR so those tables resolve. If SDFF/ is missing DDCalc silently
 *   zeroes the SD form factor (SD signal -> 0) while SI is unaffected; that
 *   was the historical "dead SD channel" bug, now fixed and covered by
 *   tests/test_integration_pvalue_statistic.py::TestSDChannel.
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

    /* Extract physics parameters.
     *
     * Loud input guard: json_get_double returns its default when a key is
     * missing, so garbage input used to run silently as m=100 GeV / sigma=0
     * -> delta_chi2=0, p=1, "not excluded", exit 0 — a silent false-negative.
     * Require the two load-bearing keys (m_dm_gev, sigma_si_proton_cm2) to be
     * present and finite, and reject negative cross sections, erroring out
     * with nonzero exit (the Python wrapper turns that into a
     * DDCALC_DRIVER_FAILED blocker). The wrapper's jsonschema validation
     * normally catches this first; this guard covers direct driver invocation. */
    double m_dm     = json_get_double(sigma_json, "m_dm_gev", NAN);
    double sig_si_p = json_get_double(sigma_json, "sigma_si_proton_cm2", NAN);
    if (isnan(m_dm) || isnan(sig_si_p)) {
        fprintf(stderr,
            "ERROR: input JSON missing required field(s) m_dm_gev and/or "
            "sigma_si_proton_cm2 (or not valid JSON). Refusing to run with "
            "silent defaults (m=100 GeV, sigma=0 would fake a 'not excluded' "
            "verdict).\n");
        return 1;
    }
    double sig_si_n = json_get_double(sigma_json, "sigma_si_neutron_cm2", sig_si_p);
    double sig_sd_p = json_get_double(sigma_json, "sigma_sd_proton_cm2", 0.0);
    double sig_sd_n = json_get_double(sigma_json, "sigma_sd_neutron_cm2", 0.0);
    if (m_dm <= 0.0 || sig_si_p < 0.0 || sig_si_n < 0.0 ||
        sig_sd_p < 0.0 || sig_sd_n < 0.0) {
        fprintf(stderr,
            "ERROR: unphysical input (m_dm_gev=%g must be > 0; cross sections "
            "sigma_si_p=%g sigma_si_n=%g sigma_sd_p=%g sigma_sd_n=%g must be "
            ">= 0).\n", m_dm, sig_si_p, sig_si_n, sig_sd_p, sig_sd_n);
        return 1;
    }

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
    /* NOTE: DDCalc 2.2.0's built-in `lz` analysis (C_DDCalc_lz_init) is the LZ
     * *projected design sensitivity* — LZ.f90 cites the LZ CDR
     * (arXiv:1509.02910) with TDR binning (arXiv:1712.04793): zero observed
     * events (Nev_bin all 0), 5.6e6 kg-day design exposure, 90%-CL floor
     * ~1.4e-48 cm^2 (as in the projected-sensitivity paper arXiv:1802.06039).
     * It is NOT the observed LZ WS2022 first-results limit
     * (arXiv:2207.03764, min ~9.2e-48 cm^2). It is therefore registered as
     * "LZ_projected", not "LZ_2022": the old "LZ_2022" label caused a headline
     * artifact — a projected-sensitivity contour was presented and compared as
     * if it were the published observed WS2022 limit (~6x more stringent, wrong
     * direction). The observed WS2022 analysis is a v1.1 overlay bundle
     * (LZ_WS2024), not present in the native install. */
    register_exp("LZ_projected",  C_DDCalc_lz_init);

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

        /* Wilks one-parameter likelihood-ratio test statistic. delta_chi2 is
         * -2 dln L, clamped at 0 (a signal that fits *better* than background,
         * dln L > 0, is not evidence for exclusion — the upper-limit test
         * statistic is 0 there). Unlike exp(dln L), delta_chi2 stays finite and
         * monotone for arbitrarily large signals, so it is the quantity a limit
         * finder must bracket on (crossing delta_chi2 = 2.706); PVALUE below can
         * underflow to a hard 0 and must never be bisected on. */
        double delta_chi2 = -2.0 * (logL - logLbg);
        if (isnan(delta_chi2) || isinf(delta_chi2)) {  /* e.g. inf - inf */
            fprintf(stderr,
                "ERROR: non-finite delta_chi2 for %s (logL=%f, logL_bg=%f)\n",
                experiments[i].name, logL, logLbg);
            return 1;
        }
        if (delta_chi2 <= 0.0) delta_chi2 = 0.0;  /* also normalizes -0.0 */
        double significance = sqrt(delta_chi2);
        /* chi^2_1 survival function = erfc(sqrt(chi2/2)); a real p-value in
         * [0,1], monotone non-increasing in signal. Excluded at 90% CL when
         * p < 0.1, i.e. delta_chi2 > 2.70554 (chi^2_1 90% quantile). */
        double pval = erfc(sqrt(delta_chi2 / 2.0));
        if (pval < 0.0) pval = 0.0;
        if (pval > 1.0) pval = 1.0;
        int excl90 = (delta_chi2 > 2.705543) ? 1 : 0;

        printf("EXPERIMENT: %s\n", experiments[i].name);
        printf("LOGL: %.6e\n", logL);
        printf("DELTACHI2: %.6e\n", delta_chi2);
        printf("SIGNIFICANCE: %.6e\n", significance);
        printf("PVALUE: %.6e\n", pval);
        printf("EXCLUDED90: %d\n", excl90);
        printf("---\n");
    }

    printf("STATUS: ok\n");
    printf("VERSION: 2.2.0\n");
    return 0;
}
