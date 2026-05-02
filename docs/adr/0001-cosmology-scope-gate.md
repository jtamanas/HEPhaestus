# ADR 0001 — Cosmology scope gate for HEPhaestus

**Status:** Accepted (2026-05-02)

---

## Context

HEPhaestus is a particle-physics-first marketplace. With the onboarding of
CLASS v3.3.4 as the first cosmology tool, a policy question arose: should
HEPhaestus become a general-purpose cosmological analysis platform, or should
cosmology remain scoped to its role in constraining BSM particle content?

General-purpose cosmology tooling (MontePython, Cobaya, class_sz, CAMB,
ExoCLASS variants, GW_CLASS, classnet) overlaps with projects like Cobaya,
CosmoSIS, and MontePython wrappers that are designed for that purpose.
Absorbing them into HEPhaestus without a clear physics motivation would dilute
the toolkit's focus, balloon maintenance surface, and confuse users who come
for particle-phenomenology workflows.

At the same time, cosmology is genuinely relevant to HEP phenomenology: Planck
constraints on the effective number of relativistic species (N_eff) bound light
relics, CMB lensing modifications probe interacting dark-matter scenarios (IDM),
and late-ISW effects constrain decaying cold dark matter (DCDM). CLASS is the
standard Boltzmann solver for these computations, and its outputs directly feed
HEPhaestus constraint workflows.

---

## Decision

**HEPhaestus is a particle-physics-first marketplace.** Cosmology is in scope
only when it directly constrains BSM particle content. CLASS is onboarded as
the linear-cosmology Boltzmann driver for this purpose, producing schema-pinned
`cosmology/v1` JSON that downstream constraint skills can consume.

Future cosmology tools or skills (MontePython, class_sz, CAMB, ExoCLASS fork,
GW_CLASS, classnet, or any cosmological sampler) may be added only if **one**
of the following conditions is met:

1. **Paper-fidelity reproduction gate:** a maintainer demonstrates that an
   existing or planned HEPhaestus workflow requires the tool to reproduce a
   specific published result (arXiv paper with a figure number and parameter
   point, verifiable end-to-end).
2. **Maintainer ADR gate:** a new ADR is filed and accepted by the project
   maintainer, explicitly scoping the tool's role, owned by an identified
   maintainer willing to sustain it, and citing a concrete use case in BSM
   phenomenology.

Tools that provide only general-purpose cosmological analysis without a clear
BSM-constraint use case are explicitly out of scope and should be declined at
PR review.

---

## Consequences

**Positive:**
- Toolkit focus is preserved; HEPhaestus remains particle-physics-first.
- Future cosmology PRs have a clear acceptance criterion, reducing scope-creep debates.
- The `cosmology` bundle namespace is reserved; `cosmology-linear` is the first entry.
- CLASS's energy-injection capability (in upstream v3.x) is in scope — it is
  not an ExoCLASS fork but part of the upstream codebase and directly relevant
  to BSM exotic-injection constraints.

**Negative / trade-offs:**
- Contributors wanting to add MontePython or class_sz must file an ADR,
  raising the bar slightly above a normal feature PR.
- The scope gate is a policy, not an automated check; it relies on maintainer
  enforcement at PR review.

---

## Alternatives Rejected

**Alternative A — accept all cosmology tools with a physics motivation note.**
Rejected because "physics motivation" is too vague a gate; it would not prevent
gradual scope drift toward general-purpose CMB analysis.

**Alternative B — no cosmology at all; decline CLASS.**
Rejected because CLASS is the standard tool for Planck N_eff, IDM, and DCDM
constraints — all of which are active research areas in BSM phenomenology and
directly supported by HEPhaestus workflows.

**Alternative C — separate cosmology plugin.**
Deferred. A standalone `cosmology-toolkit` plugin is a valid long-term
direction if demand grows, but premature splitting before a second cosmology
tool is onboarded would create unnecessary overhead.
